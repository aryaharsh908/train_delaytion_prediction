import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(tags=["WebSockets"])

orchestrator = None
active_connections: List[WebSocket] = []

def set_orchestrator(orch):
    global orchestrator
    orchestrator = orch

async def broadcast_state():
    if not orchestrator or not active_connections:
        return
    state = orchestrator.get_full_simulation_state()
    data = state.model_dump_json()
    
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.append(ws)
            
    for ws in disconnected:
        if ws in active_connections:
            active_connections.remove(ws)

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep socket open and receive any client ping messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
