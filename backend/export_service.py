import redis
import json
import logging
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        self.export_queue = 'export_jobs'
    
    def enqueue_export_job(self, export_id: str, tenant_id: str, deal_id: str, document_id: str) -> bool:
        """Add an export job to the Redis queue"""
        try:
            job_data = {
                'export_id': export_id,
                'tenant_id': tenant_id,
                'deal_id': deal_id,
                'document_id': document_id,
                'job_type': 'export'
            }
            
            logger.info(f"Enqueuing export job: {job_data}")
            
            # Push job to the queue
            result = self.redis_client.lpush(self.export_queue, json.dumps(job_data))
            
            logger.info(f"Export job enqueued successfully, queue length: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue export job: {e}")
            return False
    
    def dequeue_export_job(self) -> Dict[str, Any] | None:
        """Get the next export job from the Redis queue"""
        try:
            # Blocking pop with timeout (10 seconds)
            result = self.redis_client.brpop(self.export_queue, timeout=10)
            
            if result:
                queue_name, job_data = result
                job = json.loads(job_data)
                logger.info(f"Dequeued export job: {job}")
                return job
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue export job: {e}")
            return None
    
    def get_queue_length(self) -> int:
        """Get the current length of the export queue"""
        try:
            return self.redis_client.llen(self.export_queue)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0
    
    def clear_queue(self) -> bool:
        """Clear all jobs from the export queue (for testing/debugging)"""
        try:
            result = self.redis_client.delete(self.export_queue)
            logger.info(f"Cleared export queue, removed {result} items")
            return True
        except Exception as e:
            logger.error(f"Failed to clear export queue: {e}")
            return False

# Create singleton instance
export_service = ExportService()