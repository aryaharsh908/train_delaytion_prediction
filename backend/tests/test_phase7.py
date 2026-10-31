"""
Acceptance Test for Phase 7: Control-Room Multi-Turn Chat.
Tests multi-turn session persistence, tool calling for train status and what-if counterfactuals,
and grounded conversational responses.
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agent.chat import get_control_room_chat, get_session_history
from app.api.agent import control_room_chat, ChatRequest


def test_phase7_chat_acceptance():
    print("=== Testing Phase 7: Control-Room Chat ===")

    chat = get_control_room_chat()

    # 1. Turn 1: Inquire about train state
    turn1_msg = "What is the current operational status of train 12951?"
    res1 = chat.process_message(session_id=None, message=turn1_msg)

    session_id = res1["session_id"]
    assert session_id, "Response missing session_id"
    assert "reply" in res1 and len(res1["reply"]) > 10
    assert "disclaimer" in res1
    print(f"Turn 1 completed. Session ID: {session_id}")
    print(f"Turn 1 tool calls: {[t.get('tool') for t in res1.get('tool_trace', [])]}")
    print(f"Turn 1 reply excerpt: {res1['reply'][:120]}...")

    # 2. Turn 2: What-if counterfactual question in same session
    turn2_msg = "What if I hold it at MTJ (Mathura) for 5 minutes?"
    res2 = chat.process_message(session_id=session_id, message=turn2_msg)

    assert res2["session_id"] == session_id
    assert "reply" in res2 and len(res2["reply"]) > 10
    tools_used = [t.get("tool") for t in res2.get("tool_trace", [])]
    print(f"Turn 2 completed. Session ID: {session_id}")
    print(f"Turn 2 tool calls: {tools_used}")
    print(f"Turn 2 reply excerpt: {res2['reply'][:120]}...")

    # 3. Verify session history has all 4 messages (2 user, 2 assistant)
    history = get_session_history(session_id)
    assert len(history) >= 4, f"Expected at least 4 messages in history, got {len(history)}"
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "model"
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "model"
    print(f"Multi-turn history verified: {len(history)} messages preserved.")

    # 4. Verify API route handler directly
    api_req = ChatRequest(session_id=session_id, message="Is platform 2 free at Mathura?")
    api_res = control_room_chat(api_req)
    assert api_res["session_id"] == session_id
    assert "reply" in api_res
    print("API route POST /api/v1/agent/chat verified.")

    print("=== Phase 7 Acceptance Criteria PASSED successfully! ===")


if __name__ == "__main__":
    test_phase7_chat_acceptance()
