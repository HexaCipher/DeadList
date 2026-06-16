"""
DeadList WebSocket Manager
Manages WebSocket connections per analysis and broadcasts real-time events.
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections grouped by analysis_id."""

    def __init__(self):
        # analysis_id → list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, analysis_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = []
        self.active_connections[analysis_id].append(websocket)
        logger.info(f"WebSocket connected for analysis {analysis_id}")

    def disconnect(self, analysis_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if analysis_id in self.active_connections:
            if websocket in self.active_connections[analysis_id]:
                self.active_connections[analysis_id].remove(websocket)
            if not self.active_connections[analysis_id]:
                del self.active_connections[analysis_id]
        logger.info(f"WebSocket disconnected for analysis {analysis_id}")

    async def broadcast(self, analysis_id: str, data: Dict[str, Any]):
        """Send a message to all connections for an analysis."""
        if analysis_id not in self.active_connections:
            return

        disconnected = []
        message = json.dumps(data)

        for connection in self.active_connections[analysis_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(analysis_id, conn)

    async def broadcast_all(self, data: Dict[str, Any]):
        """Send a message to all connected clients across all analyses."""
        for analysis_id in list(self.active_connections.keys()):
            await self.broadcast(analysis_id, data)


# Global connection manager instance
ws_manager = ConnectionManager()


@router.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    """
    WebSocket endpoint for real-time analysis progress streaming.

    Clients connect to /ws/<analysis_id> and receive events as the
    analysis pipeline processes the memory dump.
    """
    await ws_manager.connect(analysis_id, websocket)
    try:
        # Send initial connected message
        await websocket.send_json({
            "event": "connected",
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to DeadList analysis stream",
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (primarily for ping/pong keepalive)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "event": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(analysis_id, websocket)
