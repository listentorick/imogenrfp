import json
import redis
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import os

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        
    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        
        # Subscribe to tenant-specific channel
        channel = f"tenant_{tenant_id}"
        self.pubsub.subscribe(channel)
        
    def disconnect(self, websocket: WebSocket, tenant_id: str):
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
    
    async def send_personal_message(self, message: str, tenant_id: str):
        if tenant_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[tenant_id].discard(connection)
    
    def publish_document_status_update(self, tenant_id: str, document_id: str, status: str, error_message: str = None):
        """Publish document status update to Redis"""
        message = {
            'type': 'document_status_update',
            'document_id': document_id,
            'status': status,
            'error_message': error_message,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        channel = f"tenant_{tenant_id}"
        self.redis_client.publish(channel, json.dumps(message))
    
    async def listen_for_updates(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients"""
        while True:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    tenant_id = channel.replace('tenant_', '')
                    data = message['data']
                    
                    await self.send_personal_message(data, tenant_id)
            except Exception as e:
                print(f"Error in WebSocket listener: {e}")
                await asyncio.sleep(1)

# Global instance
websocket_manager = WebSocketManager()