import json
import redis
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import os

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.max_connections_per_tenant = 10  # Limit connections per tenant
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        
    async def connect(self, websocket: WebSocket, tenant_id: str):
        # Check connection limit for tenant
        if tenant_id in self.active_connections:
            if len(self.active_connections[tenant_id]) >= self.max_connections_per_tenant:
                await websocket.close(code=4003, reason="Too many connections for tenant")
                print(f"Connection rejected for tenant {tenant_id}: connection limit exceeded")
                return False
        
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        
        print(f"Secure WebSocket connected for tenant {tenant_id}, total connections: {len(self.active_connections[tenant_id])}")
        return True
        
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
        try:
            # Subscribe to all tenant channels pattern
            self.pubsub.psubscribe('tenant_*')
            print("WebSocket listener: Subscribed to tenant_* pattern")
            
            while True:
                try:
                    # Use non-blocking get_message to avoid hanging startup
                    message = self.pubsub.get_message(timeout=0.1)
                    if message and message['type'] == 'pmessage':
                        channel = message['channel']
                        tenant_id = channel.replace('tenant_', '')
                        data = message['data']
                        
                        print(f"Broadcasting message to tenant {tenant_id}: {data}")
                        await self.send_personal_message(data, tenant_id)
                    elif message and message['type'] in ['psubscribe']:
                        # Ignore subscription confirmation messages
                        print(f"WebSocket listener: Subscribed to {message.get('channel', 'unknown')}")
                        continue
                    
                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error in WebSocket listener inner loop: {e}")
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in WebSocket listener setup: {e}")
            # Don't let WebSocket listener failure block startup
            return

# Global instance
websocket_manager = WebSocketManager()