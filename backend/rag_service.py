import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import os
from sqlalchemy.orm import Session

class RAGService:
    def __init__(self):
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        
        try:
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(allow_reset=True)
            )
            self.client.heartbeat()  # Test connection
        except Exception as e:
            print(f"Warning: Could not connect to ChromaDB at {self.chroma_host}:{self.chroma_port}: {e}")
            self.client = None
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_tenant_collection_name(self, tenant_id: str) -> str:
        return f"tenant_{tenant_id.replace('-', '_')}"
    
    def create_tenant_collection(self, tenant_id: str):
        if not self.is_available():
            return None
        
        collection_name = self.get_tenant_collection_name(tenant_id)
        try:
            collection = self.client.get_collection(collection_name)
            return collection
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"tenant_id": tenant_id}
            )
            return collection

rag_service = RAGService()