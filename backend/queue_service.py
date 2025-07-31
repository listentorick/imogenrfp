import redis
import json
import os
from typing import Dict, Any

class QueueService:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.document_queue = 'document_processing'
    
    def enqueue_document_processing(self, document_id: str, tenant_id: str, file_path: str, project_id: str = None, deal_id: str = None):
        """Queue a document for processing"""
        job_data = {
            'document_id': document_id,
            'tenant_id': tenant_id,
            'project_id': project_id,
            'deal_id': deal_id,
            'file_path': file_path,
            'task_type': 'process_document'
        }
        
        # Add to Redis queue
        self.redis_client.lpush(self.document_queue, json.dumps(job_data))
        return True
    
    def dequeue_document_processing(self) -> Dict[str, Any] | None:
        """Get next document processing job"""
        job_json = self.redis_client.brpop(self.document_queue, timeout=1)
        if job_json:
            return json.loads(job_json[1])
        return None
    
    def get_queue_length(self) -> int:
        """Get the number of jobs in the queue"""
        return self.redis_client.llen(self.document_queue)
    
    def clear_queue(self):
        """Clear all jobs from the queue (for testing)"""
        self.redis_client.delete(self.document_queue)

# Singleton instance
queue_service = QueueService()