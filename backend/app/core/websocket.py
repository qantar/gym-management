from typing import Dict, Set
from fastapi import WebSocket
import json
from datetime import datetime, timezone


class ConnectionManager:
    def __init__(self):
        # branch_id -> set of websockets
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, branch_id: int):
        await websocket.accept()
        if branch_id not in self.rooms:
            self.rooms[branch_id] = set()
        self.rooms[branch_id].add(websocket)

    def disconnect(self, websocket: WebSocket, branch_id: int):
        if branch_id in self.rooms:
            self.rooms[branch_id].discard(websocket)

    async def broadcast_to_branch(self, branch_id: int, event: str, data: dict):
        if branch_id not in self.rooms:
            return
        payload = json.dumps({"event": event, "data": data, "ts": datetime.now(timezone.utc).isoformat()})
        dead = set()
        for ws in self.rooms[branch_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.rooms[branch_id].discard(ws)

    async def broadcast_all(self, event: str, data: dict):
        for branch_id in self.rooms:
            await self.broadcast_to_branch(branch_id, event, data)


ws_manager = ConnectionManager()
