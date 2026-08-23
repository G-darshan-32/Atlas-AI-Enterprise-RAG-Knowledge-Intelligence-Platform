"""WebSocket endpoint for real-time notifications and document processing updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List
import asyncio
import json
import uuid

from app.core.security import decode_access_token
from jose import JWTError

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections keyed by user_id."""

    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        if user_id in self.active:
            self.active[user_id] = [c for c in self.active[user_id] if c != ws]
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Push a JSON message to all connections for a user."""
        connections = self.active.get(user_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast_to_workspace(self, workspace_id: str, message: dict, user_ids: List[str]):
        """Broadcast a message to all connected users in a workspace."""
        for uid in user_ids:
            await self.send_to_user(uid, message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket connection authenticated via JWT token query param.
    Usage: ws://host/api/v1/ws?token=<access_token>
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await manager.connect(user_id, websocket)

    # Send connection ack
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "Real-time connection established",
        "user_id": user_id,
    }))

    try:
        while True:
            # Keep connection alive with ping/pong
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


async def notify_document_processed(user_id: str, document_id: str, status: str, title: str):
    """Utility: push document processing status update to user."""
    await manager.send_to_user(user_id, {
        "type": "document_status",
        "document_id": document_id,
        "status": status,
        "title": title,
    })


async def notify_user(user_id: str, notification_type: str, title: str, body: str):
    """Utility: push a general notification to user."""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "notification_type": notification_type,
        "title": title,
        "body": body,
    })
