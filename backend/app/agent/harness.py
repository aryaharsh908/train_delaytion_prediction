"""
Gemma 4 Agent Harness & Model Execution Layer.
Supports pluggable Gemini API and Ollama backends, caching, retries,
rate limiting, circuit breaker, structured audit logging, and deterministic fallback.
"""

import os
import sys
import time
import json
import uuid
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from app.db.database import SessionLocal
from app.db.models import AgentRun, AgentCache

logger = logging.getLogger("gemma_harness")

def _load_env_api_key() -> Tuple[str, str]:
    """Reads GEMINI_API_KEY and GEMMA_BACKEND from env or .env file."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    backend_type = os.environ.get("GEMMA_BACKEND", "gemini_api")

    if not api_key:
        possible_paths = [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path.cwd() / "backend" / ".env",
            Path.cwd() / ".env"
        ]
        for p in possible_paths:
            if p.is_file():
                try:
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("GEMMA_BACKEND="):
                            backend_type = line.split("=", 1)[1].strip().strip('"').strip("'")
                except Exception as e:
                    logger.warning(f"Failed to read {p}: {e}")
                if api_key:
                    break

    return api_key, backend_type


class ModelBackend(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it",
        thinking: bool = False,
        json_mode: bool = False,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Generates text output from model."""
        pass

    @abstractmethod
    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Any],
        model: str = "gemma-4-26b-a4b-it",
        system: Optional[str] = None,
        thinking: bool = False,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Generates model output with tool function declarations."""
        pass


class GeminiApiBackend(ModelBackend):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai Client: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it",
        thinking: bool = False,
        json_mode: bool = False,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        if not self._client or not self.api_key:
            raise ValueError("Gemini API key is not configured or client failed to initialize.")

        from google.genai import types

        config_args = {}
        if system:
            config_args["system_instruction"] = system
        if json_mode:
            config_args["response_mime_type"] = "application/json"

        # Models to try (fallback to 26b if 31b encounters capacity spikes)
        models_to_try = [model]
        if "31b" in model:
            models_to_try.append("gemma-4-26b-a4b-it")

        last_error = None
        for m in models_to_try:
            try:
                config = types.GenerateContentConfig(**config_args) if config_args else None
                response = self._client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config
                )
                text_out = response.text or ""
                tokens_count = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    tokens_count = getattr(response.usage_metadata, "total_token_count", 0) or 0

                return {
                    "text": text_out,
                    "model_used": m,
                    "tokens": tokens_count,
                    "function_calls": []
                }
            except Exception as e:
                logger.warning(f"Model {m} failed: {e}")
                last_error = e

        raise last_error or RuntimeError("Gemini API generation failed.")

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Any],
        model: str = "gemma-4-26b-a4b-it",
        system: Optional[str] = None,
        thinking: bool = False,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        if not self._client or not self.api_key:
            raise ValueError("Gemini API key is not configured.")

        from google.genai import types

        config_args = {"tools": tools}
        if system:
            config_args["system_instruction"] = system

        models_to_try = [model]
        if "31b" in model:
            models_to_try.append("gemma-4-26b-a4b-it")

        last_error = None
        for m in models_to_try:
            try:
                config = types.GenerateContentConfig(**config_args)
                # Parse messages into SDK content objects or text
                contents = []
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    contents.append(f"[{role.upper()}]: {content}")
                prompt_content = "\n\n".join(contents)

                response = self._client.models.generate_content(
                    model=m,
                    contents=prompt_content,
                    config=config
                )

                fcalls = []
                if hasattr(response, "function_calls") and response.function_calls:
                    for fc in response.function_calls:
                        fcalls.append({
                            "name": fc.name,
                            "args": dict(fc.args) if fc.args else {}
                        })

                tokens_count = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    tokens_count = getattr(response.usage_metadata, "total_token_count", 0) or 0

                return {
                    "text": response.text or "",
                    "model_used": m,
                    "tokens": tokens_count,
                    "function_calls": fcalls
                }
            except Exception as e:
                logger.warning(f"Tool generation on {m} failed: {e}")
                last_error = e

        raise last_error or RuntimeError("Tool call generation failed.")


class OllamaBackend(ModelBackend):
    """Optional local Ollama backend for Gemma 4 if running locally."""
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def generate(self, prompt: str, system: Optional[str] = None, model: str = "gemma-4-26b-a4b-it", **kwargs) -> Dict[str, Any]:
        import urllib.request
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"text": data.get("response", ""), "model_used": model, "tokens": 0, "function_calls": []}

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Any], model: str = "gemma-4-26b-a4b-it", **kwargs) -> Dict[str, Any]:
        prompt = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in messages])
        return self.generate(prompt=prompt, model=model)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 4, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker TRIPPED to OPEN after {self.failure_count} failures.")

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN trial state.")
                return True
            return False
        return True  # HALF_OPEN


class RateLimiter:
    """Token-bucket / sliding interval limiter to stay comfortably within free-tier quotas."""
    def __init__(self, min_interval_seconds: float = 1.0):
        self.min_interval = min_interval_seconds
        self.last_call_time = 0.0

    def wait_if_needed(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call_time = time.time()


class GemmaHarness:
    """
    Central orchestration harness for all Gemma 4 operations.
    Guarantees:
      - Pluggable backends (GeminiApiBackend default, Ollama optional)
      - Retries with exponential backoff
      - Circuit breaker
      - Rate limiting
      - SQLite response caching
      - Structured audit logging to agent_runs table
      - Deterministic domain fallback when offline
    """
    def __init__(self):
        self.api_key, self.backend_type = _load_env_api_key()
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(min_interval_seconds=1.0)
        
        if self.backend_type == "ollama":
            self.backend: ModelBackend = OllamaBackend()
        else:
            self.backend = GeminiApiBackend(self.api_key)

    def _hash_cache_key(self, model: str, prompt: str, system: Optional[str], extra: Any = None) -> str:
        raw = f"{model}:{system or ''}:{prompt}:{json.dumps(extra or '', sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            cached = db.query(AgentCache).filter(AgentCache.cache_key == cache_key).first()
            if cached:
                return json.loads(cached.response)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        finally:
            db.close()
        return None

    def _save_cached_response(self, cache_key: str, model: str, data: Dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            record = AgentCache(
                cache_key=cache_key,
                model=model,
                response=json.dumps(data)
            )
            db.merge(record)
            db.commit()
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
            db.rollback()
        finally:
            db.close()

    def _log_run(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        tool_calls: Optional[List[Any]],
        tool_results: Optional[List[Any]],
        output: str,
        latency_ms: float,
        tokens_used: int,
        source: str,
        status: str
    ) -> str:
        run_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            run = AgentRun(
                id=run_id,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                tool_calls=json.dumps(tool_calls) if tool_calls else None,
                tool_results=json.dumps(tool_results) if tool_results else None,
                output=output,
                latency_ms=round(latency_ms, 2),
                tokens_used=tokens_used,
                source=source,
                status=status
            )
            db.add(run)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log agent run: {e}")
            db.rollback()
        finally:
            db.close()
        return run_id

    def get_fallback_explanation(self, prompt: str) -> str:
        """Deterministic domain fallback when Gemma is unreachable."""
        return (
            "[Deterministic Fallback Advisory]\n"
            "Operational delay prediction stabilized: primary train operating within corridor tolerance bounds. "
            "Headway clearances observed at critical junctions with standard block signaling protocols."
        )

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: str = "gemma-4-26b-a4b-it",
        thinking: bool = False,
        json_mode: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Executes text generation with full resilience, caching, audit trail, and fallback.
        """
        cache_key = self._hash_cache_key(model, prompt, system, {"json_mode": json_mode})
        if use_cache:
            cached = self._get_cached_response(cache_key)
            if cached:
                cached["cached"] = True
                return cached

        if not self.circuit_breaker.allow_request() or not self.api_key:
            # Circuit breaker open or no API key -> fallback
            fallback_text = self.get_fallback_explanation(prompt)
            run_id = self._log_run(
                model=model,
                prompt=prompt,
                system_prompt=system,
                tool_calls=None,
                tool_results=None,
                output=fallback_text,
                latency_ms=1.0,
                tokens_used=0,
                source="fallback",
                status="FALLBACK"
            )
            return {
                "text": fallback_text,
                "model": model,
                "source": "fallback",
                "run_id": run_id,
                "cached": False
            }

        retries = 2
        delay = 1.0
        start_time = time.time()
        last_error = None

        for attempt in range(retries + 1):
            try:
                self.rate_limiter.wait_if_needed()
                result = self.backend.generate(
                    prompt=prompt,
                    system=system,
                    model=model,
                    thinking=thinking,
                    json_mode=json_mode,
                    timeout_seconds=30.0
                )
                latency = (time.time() - start_time) * 1000.0
                self.circuit_breaker.record_success()

                run_id = self._log_run(
                    model=result["model_used"],
                    prompt=prompt,
                    system_prompt=system,
                    tool_calls=None,
                    tool_results=None,
                    output=result["text"],
                    latency_ms=latency,
                    tokens_used=result["tokens"],
                    source="gemma",
                    status="SUCCESS"
                )

                out = {
                    "text": result["text"],
                    "model": result["model_used"],
                    "source": "gemma",
                    "tokens": result["tokens"],
                    "latency_ms": round(latency, 2),
                    "run_id": run_id,
                    "cached": False
                }
                if use_cache:
                    self._save_cached_response(cache_key, result["model_used"], out)
                return out

            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
                    delay *= 2.0

        # All retries exhausted -> record failure and invoke fallback
        self.circuit_breaker.record_failure()
        latency = (time.time() - start_time) * 1000.0
        fallback_text = self.get_fallback_explanation(prompt)
        run_id = self._log_run(
            model=model,
            prompt=prompt,
            system_prompt=system,
            tool_calls=None,
            tool_results=None,
            output=f"FALLBACK ({last_error}): {fallback_text}",
            latency_ms=latency,
            tokens_used=0,
            source="fallback",
            status="FALLBACK"
        )

        return {
            "text": fallback_text,
            "model": model,
            "source": "fallback",
            "error": str(last_error),
            "run_id": run_id,
            "cached": False
        }

    def run_tool_loop(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Any],
        tool_dispatch_fn: Any,
        model: str = "gemma-4-31b-it",
        system: Optional[str] = None,
        max_steps: int = 8,
        thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Executes multi-step reasoning tool loop.
        Calls model, executes requested tools, appends results, and loops until final answer.
        """
        start_time = time.time()
        tool_trace: List[Dict[str, Any]] = []

        if not self.circuit_breaker.allow_request() or not self.api_key:
            fallback_text = json.dumps({
                "summary": "Deterministic fallback engaged due to offline model harness.",
                "recommendation": {"action": "HOLD", "train_id": "TRAIN_12951", "params": {"duration_min": 5}, "expected_passenger_minutes_saved": 45},
                "alternatives_considered": [{"action": "PRIORITIZE", "result": {"passenger_minutes_saved": 10}}],
                "rule_citations": ["PREC-01"],
                "confidence": "medium",
                "operating_order_draft": "Hold Train 12951 at platform 2 for 5 minutes to clear downstream junction headway.",
                "tool_trace": []
            })
            run_id = self._log_run(
                model=model,
                prompt=str(messages),
                system_prompt=system,
                tool_calls=[],
                tool_results=[],
                output=fallback_text,
                latency_ms=1.0,
                tokens_used=0,
                source="fallback",
                status="FALLBACK"
            )
            return {
                "text": fallback_text,
                "model": model,
                "source": "fallback",
                "tool_trace": [],
                "run_id": run_id
            }

        conversation = list(messages)
        final_text = ""
        model_used = model
        tokens_total = 0

        for step in range(max_steps):
            try:
                self.rate_limiter.wait_if_needed()
                resp = self.backend.generate_with_tools(
                    messages=conversation,
                    tools=tools,
                    model=model,
                    system=system,
                    thinking=thinking
                )
                model_used = resp.get("model_used", model)
                tokens_total += resp.get("tokens", 0)
                final_text = resp.get("text", "")
                fcalls = resp.get("function_calls", [])

                if not fcalls:
                    # Model produced final answer without further tool requests
                    break

                for fc in fcalls:
                    fn_name = fc["name"]
                    fn_args = fc["args"]
                    logger.info(f"[Step {step+1}] Calling tool: {fn_name}({fn_args})")
                    try:
                        res = tool_dispatch_fn(fn_name, fn_args)
                    except Exception as te:
                        res = {"error": f"Tool execution failed: {te}"}

                    tool_trace.append({
                        "step": step + 1,
                        "tool": fn_name,
                        "args": fn_args,
                        "result": res
                    })

                    conversation.append({
                        "role": "model",
                        "content": f"Called tool {fn_name} with args {json.dumps(fn_args)}"
                    })
                    conversation.append({
                        "role": "user",
                        "content": f"Tool {fn_name} result: {json.dumps(res)}"
                    })

            except Exception as e:
                logger.warning(f"Tool loop step {step+1} error: {e}")
                break

        latency = (time.time() - start_time) * 1000.0
        source = "gemma" if final_text else "fallback"
        if not final_text:
            final_text = self.get_fallback_explanation("Dispatch intervention")

        run_id = self._log_run(
            model=model_used,
            prompt=str(messages),
            system_prompt=system,
            tool_calls=[t["tool"] for t in tool_trace],
            tool_results=[t["result"] for t in tool_trace],
            output=final_text,
            latency_ms=latency,
            tokens_used=tokens_total,
            source=source,
            status="SUCCESS" if source == "gemma" else "FALLBACK"
        )

        return {
            "text": final_text,
            "model": model_used,
            "source": source,
            "tool_trace": tool_trace,
            "tokens": tokens_total,
            "latency_ms": round(latency, 2),
            "run_id": run_id
        }


# Global harness singleton
_harness_instance: Optional[GemmaHarness] = None

def get_gemma_harness() -> GemmaHarness:
    global _harness_instance
    if _harness_instance is None:
        _harness_instance = GemmaHarness()
    return _harness_instance
