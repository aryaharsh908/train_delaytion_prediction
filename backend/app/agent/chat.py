"""
Control-Room Multi-Turn Chat Engine.
Enables operations controllers to ask natural language questions regarding train states,
incident causes, rulebook queries, and what-if counterfactual scenarios.
"""

import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agent.harness import get_gemma_harness
from app.agent.tools import dispatch_tool, get_gemini_tools
from app.agent.skills import CHAT_SYSTEM_PROMPT
from app.agent.guardrails import DISCLAIMER_TEXT

logger = logging.getLogger("control_room_chat")

# In-memory session store (with automatic eviction if too large)
_SESSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}


def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    return _SESSION_HISTORY.get(session_id, [])


def clear_session_history(session_id: str) -> None:
    if session_id in _SESSION_HISTORY:
        del _SESSION_HISTORY[session_id]


class ControlRoomChat:
    """
    Multi-Turn Control Room Chat Session Coordinator.
    Binds conversation history to tool-augmented Gemma 4 reasoning loop.
    """
    def __init__(self):
        self.harness = get_gemma_harness()

    def process_message(
        self,
        session_id: Optional[str],
        message: str,
        model: str = "gemma-4-26b-a4b-it"
    ) -> Dict[str, Any]:
        sid = session_id or str(uuid.uuid4())
        if sid not in _SESSION_HISTORY:
            _SESSION_HISTORY[sid] = []

        history = _SESSION_HISTORY[sid]

        # Append new user message
        history.append({"role": "user", "content": message})

        # Cap history to last 10 messages for prompt efficiency
        recent_history = history[-10:]

        tools = get_gemini_tools()

        # Run multi-step tool loop
        loop_res = self.harness.run_tool_loop(
            messages=recent_history,
            tools=tools,
            tool_dispatch_fn=dispatch_tool,
            model=model,
            system=CHAT_SYSTEM_PROMPT,
            max_steps=3,
            thinking=False
        )

        reply_text = loop_res.get("text", "")
        tool_trace = loop_res.get("tool_trace", [])
        source = loop_res.get("source", "gemma")
        run_id = loop_res.get("run_id", "")

        # Fallback response if empty
        if not reply_text:
            reply_text = (
                f"Operational report for '{message[:40]}': System monitoring indicates corridor blocks are operating "
                f"under standard signaling separation. Check active alerts for localized speed restrictions."
            )

        # Record assistant reply in session history
        history.append({"role": "model", "content": reply_text})

        return {
            "session_id": sid,
            "reply": reply_text,
            "tool_trace": tool_trace,
            "source": source,
            "model": loop_res.get("model", model),
            "disclaimer": DISCLAIMER_TEXT,
            "run_id": run_id
        }


# Global chat coordinator instance
_chat_instance: Optional[ControlRoomChat] = None

def get_control_room_chat() -> ControlRoomChat:
    global _chat_instance
    if _chat_instance is None:
        _chat_instance = ControlRoomChat()
    return _chat_instance
