"""
Rulebook Retrieval and Grounding Engine.
Indexes knowledge/ markdown summaries of Indian Railways Operating Rules using BM25
and provides grounded rule lookup and citation validation.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

logger = logging.getLogger("rulebook")


class RuleChunk:
    def __init__(self, rule_id: str, title: str, content: str, source_file: str):
        self.rule_id = rule_id.strip()
        self.title = title.strip()
        self.content = content.strip()
        self.source_file = source_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "summary": self.content,
            "source_file": self.source_file
        }


class RulebookEngine:
    """
    BM25-indexed retrieval engine for Indian Railways Operating Rulebook summaries.
    """
    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or self._find_knowledge_dir()
        self.chunks: List[RuleChunk] = []
        self.bm25: Optional[Any] = None
        self.tokenized_corpus: List[List[str]] = []
        self._load_and_index()

    def _find_knowledge_dir(self) -> Path:
        candidates = [
            Path.cwd() / "knowledge",
            Path(__file__).resolve().parent.parent.parent.parent / "knowledge",
            Path(__file__).resolve().parent.parent.parent / "knowledge",
            Path(__file__).resolve().parent / "knowledge"
        ]
        for p in candidates:
            if p.is_dir():
                return p
        return Path.cwd() / "knowledge"

    def _load_and_index(self):
        self.chunks.clear()
        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory not found at: {self.knowledge_dir}")
            return

        md_files = list(self.knowledge_dir.glob("*.md"))
        for f in md_files:
            try:
                text = f.read_text(encoding="utf-8")
                sections = re.split(r"\n(?=##\s+)", text)
                for sec in sections:
                    sec = sec.strip()
                    if not sec.startswith("##"):
                        continue
                    # Parse header: ## ID: Title
                    lines = sec.splitlines()
                    header = lines[0].replace("##", "").strip()
                    body = "\n".join(lines[1:]).strip()

                    rule_id = "UNKNOWN"
                    title = header
                    if ":" in header:
                        parts = header.split(":", 1)
                        rule_id = parts[0].strip()
                        title = parts[1].strip()

                    self.chunks.append(RuleChunk(
                        rule_id=rule_id,
                        title=title,
                        content=body,
                        source_file=f.name
                    ))
            except Exception as e:
                logger.warning(f"Failed to index rule file {f}: {e}")

        logger.info(f"Loaded {len(self.chunks)} rule chunks from {len(md_files)} files in {self.knowledge_dir}")

        # Build BM25 index
        if self.chunks:
            self.tokenized_corpus = [
                self._tokenize(f"{c.rule_id} {c.title} {c.content}")
                for c in self.chunks
            ]
            if BM25Okapi:
                self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant rule chunks for a query using BM25 ranking.
        """
        if not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return [c.to_dict() for c in self.chunks[:top_k]]

        if self.bm25:
            scores = self.bm25.get_scores(tokens)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            results = []
            for idx in ranked_indices[:top_k]:
                item = self.chunks[idx].to_dict()
                item["bm25_score"] = round(float(scores[idx]), 3)
                results.append(item)
            return results

        # Simple term match fallback if BM25Okapi is not available
        scored = []
        for c in self.chunks:
            text = f"{c.rule_id} {c.title} {c.content}".lower()
            match_count = sum(1 for t in tokens if t in text)
            scored.append((match_count, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c.to_dict() for _, c in scored[:top_k]]

    def get_all_rule_ids(self) -> Set[str]:
        return {c.rule_id for c in self.chunks if c.rule_id != "UNKNOWN"}

    def validate_citations(self, citations: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Validates rule citation IDs.
        Returns (is_all_valid, valid_citations, invalid_citations).
        """
        valid_ids = self.get_all_rule_ids()
        valid = []
        invalid = []

        for cit in citations:
            clean = cit.strip().upper()
            if clean in valid_ids:
                valid.append(clean)
            else:
                invalid.append(clean)

        return len(invalid) == 0, valid, invalid


# Global singleton instance
_rulebook_engine: Optional[RulebookEngine] = None

def get_rulebook_engine() -> RulebookEngine:
    global _rulebook_engine
    if _rulebook_engine is None:
        _rulebook_engine = RulebookEngine()
    return _rulebook_engine
