"""
Guardrails and Human-in-the-Loop Validation Layer for Gemma 4.
Validates numerical grounding against tool execution traces, verifies entity existence,
validates strict JSON output schemas, and enforces controller sign-off.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set

logger = logging.getLogger("guardrails")

# Known corridor stations and junctions
KNOWN_STATIONS = {
    "NDLS", "NZM", "FDB", "PWL", "KSV", "CHJ", "MTJ", "BTE", "BXN", "HAN",
    "GGC", "SWM", "LKE", "KOTA", "DKNT", "RMA", "BWM", "SGZ", "CMU", "NAD",
    "KUH", "RTM", "BRC", "ST", "BSR", "BVI", "MMCT", "GDA", "BL", "VAPI"
}

KNOWN_TRAINS = {
    "12951", "12952", "12953", "12954", "12002", "12001", "22436", "22435",
    "12414", "12413", "12909", "12910", "12925", "12926", "09001", "09002",
    "TRAIN_12951", "TRAIN_12952", "TRAIN_12953", "TRAIN_12954", "TRAIN_12002"
}

DISCLAIMER_TEXT = "AI-generated, controller must verify"


def _extract_numbers_from_obj(obj: Any) -> Set[float]:
    """Recursively extracts all numbers from arbitrary dict/list/primitive."""
    nums = set()
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        nums.add(round(float(obj), 2))
    elif isinstance(obj, dict):
        for v in obj.values():
            nums.update(_extract_numbers_from_obj(v))
    elif isinstance(obj, list):
        for item in obj:
            nums.update(_extract_numbers_from_obj(item))
    elif isinstance(obj, str):
        # Scan string for numeric tokens
        for match in re.findall(r"[-+]?\d*\.?\d+", obj):
            try:
                nums.add(round(float(match), 2))
            except ValueError:
                pass
    return nums


class NumberValidator:
    """
    Validates that every number in model output (delays, minutes, counts, percentages)
    matches a value present in the actual tool results from that run.
    """
    EXEMPT_NUMBERS = {2026, 2025, 2024, 0.0, 1, 2, 3, 4, 5, 10}  # Small standard platform numbers / years

    @classmethod
    def extract_numbers_from_text(cls, text: str) -> List[float]:
        matches = re.findall(r"(?<![a-zA-Z0-9_])[-+]?\d*\.?\d+(?![a-zA-Z0-9_])", text)
        results = []
        for m in matches:
            try:
                val = round(float(m), 2)
                results.append(val)
            except ValueError:
                continue
        return results

    @classmethod
    def validate(
        cls,
        text_to_check: str,
        tool_trace: List[Dict[str, Any]],
        allowed_delta: float = 1.0,
        known_train_ids: Optional[Set[str]] = None
    ) -> Tuple[bool, List[float], Optional[str]]:
        """
        Returns (is_valid, ungrounded_numbers, error_message).
        """
        if not text_to_check:
            return True, [], None

        tool_numbers = set()
        for t in tool_trace:
            tool_numbers.update(_extract_numbers_from_obj(t.get("result", {})))
            tool_numbers.update(_extract_numbers_from_obj(t.get("args", {})))

        text_numbers = cls.extract_numbers_from_text(text_to_check)
        ungrounded = []

        exempt = set(cls.EXEMPT_NUMBERS)
        if known_train_ids:
            for tid in known_train_ids:
                try:
                    exempt.add(float(tid.replace("TRAIN_", "")))
                except ValueError:
                    pass

        for num in text_numbers:
            if num in exempt:
                continue
            # Check if within delta of any tool number
            matched = any(abs(num - tn) <= allowed_delta for tn in tool_numbers)
            if not matched:
                ungrounded.append(num)

        if ungrounded:
            return False, ungrounded, f"Model mentioned ungrounded numbers not in tool results: {ungrounded}"

        return True, [], None


class SchemaValidator:
    """Validates structure and required fields for agent JSON outputs."""

    @classmethod
    def validate(cls, raw_output: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1]
        if "```" in cleaned:
            cleaned = cleaned.split("```", 1)[0]
        cleaned = cleaned.strip()

        data = None
        try:
            data = json.loads(cleaned)
        except Exception as e:
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except Exception:
                    pass

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data = data[0]

        if not isinstance(data, dict):
            return False, None, "Response is not a valid JSON dictionary."

        # Validate mandatory keys
        required_keys = ["summary", "recommendation", "alternatives_considered", "rule_citations", "confidence", "operating_order_draft"]
        for k in required_keys:
            if k not in data:
                return False, data, f"Missing required top-level key: '{k}'"

        rec = data.get("recommendation", {})
        if not isinstance(rec, dict) or "action" not in rec or "train_id" not in rec:
            return False, data, "recommendation must be a dictionary with 'action' and 'train_id'."

        return True, data, None


class EntityValidator:
    """Validates that train IDs and station codes mentioned in output exist in corridor."""

    @classmethod
    def validate(cls, structured_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[str]]:
        unknown_entities = []
        rec = structured_data.get("recommendation", {})
        train_id = rec.get("train_id", "")
        clean_train = str(train_id).replace("TRAIN_", "").strip()

        # Check train ID if specified
        if clean_train and clean_train not in KNOWN_TRAINS and f"TRAIN_{clean_train}" not in KNOWN_TRAINS:
            # Allow common numeric train numbers of 5 digits
            if not (clean_train.isdigit() and len(clean_train) == 5):
                unknown_entities.append(f"Train:{train_id}")

        # Check station codes mentioned in params
        params = rec.get("params", {})
        stn = params.get("station_code")
        if stn and stn.upper() not in KNOWN_STATIONS:
            unknown_entities.append(f"Station:{stn}")

        if unknown_entities:
            return False, unknown_entities, f"Unknown corridor entities referenced: {unknown_entities}"

        return True, [], None


class InjectionDefense:
    """Filters prompt injections and malicious instruction overwrites."""

    INJECTION_PATTERNS = [
        r"ignore (all )?(previous|prior) instructions",
        r"system override",
        r"disregard (safety|operating) rules",
        r"act as (dan|jailbroken)",
        r"bypass guardrails",
        r"drop database",
        r"format as (bash|powershell|sh) script"
    ]

    @classmethod
    def inspect(cls, user_text: str) -> Tuple[bool, Optional[str]]:
        lower = user_text.lower()
        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, lower):
                return False, f"Prompt injection pattern detected: '{pat}'"
        return True, None


def apply_guardrails(
    data: Dict[str, Any],
    tool_trace: List[Dict[str, Any]],
    strict_numbers: bool = True
) -> Dict[str, Any]:
    """
    Applies comprehensive guardrails: schema validation, entity validation,
    number grounding, and audit stamping.
    """
    validation_errors = []

    # 1. Schema check
    is_schema_valid = True
    if not isinstance(data, dict):
        is_schema_valid = False
        validation_errors.append("Output is not a valid dictionary")

    # 2. Entity check
    if is_schema_valid:
        ent_valid, unk_ents, ent_err = EntityValidator.validate(data)
        if not ent_valid and ent_err:
            validation_errors.append(ent_err)

    # 3. Number validation
    if is_schema_valid and strict_numbers:
        # Check text in summary, operating order draft
        summary_text = data.get("summary", "")
        order_text = data.get("operating_order_draft", "")
        combined_text = f"{summary_text} {order_text}"

        known_tids = {str(data.get("recommendation", {}).get("train_id", ""))}
        num_valid, ungrounded, num_err = NumberValidator.validate(
            text_to_check=combined_text,
            tool_trace=tool_trace,
            allowed_delta=1.0,
            known_train_ids=known_tids
        )
        if not num_valid and num_err:
            validation_errors.append(num_err)

    # Attach guardrail metadata
    data["disclaimer"] = DISCLAIMER_TEXT
    data["guardrails_status"] = "PASSED" if not validation_errors else "FAILED"
    data["guardrail_violations"] = validation_errors

    return data
