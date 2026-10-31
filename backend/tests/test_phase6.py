"""
Acceptance Test for Phase 6: Rulebook Retrieval & Grounding.
Tests 20 rule summaries, BM25 indexing, semantic/keyword search, citation validation, and tool integration.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agent.rulebook import get_rulebook_engine
from app.agent.tools import search_rulebook
from app.agent.guardrails import EntityValidator


def test_phase6_rulebook_acceptance():
    print("=== Testing Phase 6: Rulebook Retrieval & Citations ===")

    engine = get_rulebook_engine()
    all_rule_ids = engine.get_all_rule_ids()
    print(f"Total indexed rules: {len(all_rule_ids)}")
    print(f"Rule IDs: {sorted(list(all_rule_ids))}")

    # 1. Verify at least 20 rule summaries exist in knowledge/
    assert len(all_rule_ids) >= 20, f"Expected at least 20 rule summaries, found {len(all_rule_ids)}"
    for prefix in ["PREC-", "HEAD-", "LOOP-", "SPED-"]:
        matched = [rid for rid in all_rule_ids if rid.startswith(prefix)]
        assert len(matched) >= 5, f"Expected at least 5 rules for prefix {prefix}, found {len(matched)}"
    print("Rulebook corpus count verified: 20 rules loaded across 4 domains.")

    # 2. Test BM25 Search for precedence
    prec_results = engine.search("vande bharat rajdhani precedence merging junction", top_k=3)
    assert len(prec_results) > 0
    top_rule = prec_results[0]
    assert top_rule["rule_id"] == "PREC-01", f"Expected PREC-01 top match, got {top_rule['rule_id']}"
    assert "bm25_score" in top_rule
    print(f"BM25 precedence query top match: {top_rule['rule_id']} - {top_rule['title']} (Score: {top_rule['bm25_score']})")

    # 3. Test BM25 Search for loop regulation
    loop_results = engine.search("loop line overtake 18 km rule trailing", top_k=3)
    assert len(loop_results) > 0
    assert any(r["rule_id"] in ("LOOP-02", "PREC-03") for r in loop_results)
    print(f"BM25 loop query top matches: {[r['rule_id'] for r in loop_results]}")

    # 4. Test BM25 Search for fog speed
    fog_results = engine.search("foggy weather speed restriction visibility test object 60 km/h", top_k=3)
    assert len(fog_results) > 0
    assert fog_results[0]["rule_id"] == "HEAD-04"
    print(f"BM25 fog query top match: {fog_results[0]['rule_id']} - {fog_results[0]['title']}")

    # 5. Test search_rulebook tool integration
    tool_res = search_rulebook("precedence hierarchy express")
    assert tool_res["status"] == "success"
    assert len(tool_res["rules"]) > 0
    print("search_rulebook tool execution verified.")

    # 6. Test citation validation
    valid_cits = ["PREC-01", "HEAD-02", "LOOP-02"]
    is_valid, valid, invalid = engine.validate_citations(valid_cits)
    assert is_valid
    assert len(invalid) == 0
    print(f"Citation validator accepted valid rules: {valid}")

    # Invalid citation rejection
    invalid_cits = ["PREC-01", "INVALID_RULE_999"]
    is_valid, valid, invalid = engine.validate_citations(invalid_cits)
    assert not is_valid
    assert "INVALID_RULE_999" in invalid
    print(f"Citation validator correctly flagged invalid rule: {invalid}")

    # 7. Test EntityValidator rejection of invalid citations in agent dispatch output
    fake_dispatch_output = {
        "recommendation": {"train_id": "12951", "action": "HOLD"},
        "rule_citations": ["FAKE-999"]
    }
    ent_ok, unk, err = EntityValidator.validate(fake_dispatch_output)
    assert not ent_ok
    assert any("InvalidRuleCitation:FAKE-999" in u for u in unk)
    print("EntityValidator correctly rejects invalid rule citations in dispatch output.")

    print("=== Phase 6 Acceptance Criteria PASSED successfully! ===")


if __name__ == "__main__":
    test_phase6_rulebook_acceptance()
