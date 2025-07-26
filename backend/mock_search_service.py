#!/usr/bin/env python3
"""
Mock search service to demonstrate search functionality while ChromaDB compatibility is fixed
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MockSearchService:
    def __init__(self):
        # Mock data simulating processed documents
        self.mock_documents = {
            "f3a428bb-6659-4a60-81a4-23d2433890a6": [
                {
                    "content": "HeritageAdvisor is a comprehensive software solution for heritage management and preservation. Our platform provides digital tools for cultural institutions to document, preserve, and manage their heritage collections effectively.",
                    "metadata": {
                        "document_id": "cb0ab5a2-f256-4ca6-8573-ee80e20b9cde",
                        "filename": "HeritageAdvisor_Detailed_Product_Overview.docx",
                        "chunk_index": 0,
                        "total_chunks": 3
                    },
                    "distance": 0.15
                },
                {
                    "content": "The Heritage voice feature allows for audio documentation and preservation of cultural heritage. This innovative feature enables institutions to record oral histories, interviews, and audio descriptions of artifacts.",
                    "metadata": {
                        "document_id": "1276e6be-96ec-45e9-8a0b-1620afd88ed1",
                        "filename": "HeritageAdvisor_Voice_Feature_Overview.docx",
                        "chunk_index": 0,
                        "total_chunks": 2
                    },
                    "distance": 0.18
                },
                {
                    "content": "Heritage preservation requires detailed documentation and systematic approach to cultural asset management. Our system provides comprehensive tools for cataloging, tracking, and maintaining heritage collections.",
                    "metadata": {
                        "document_id": "2462128a-1ffe-4547-804d-19cfae1e0b74",
                        "filename": "HeritageAdvisor_Product_Overview.docx",
                        "chunk_index": 1,
                        "total_chunks": 2
                    },
                    "distance": 0.22
                },
                {
                    "content": "Our document processing pipeline automatically extracts and indexes content from uploaded files. This enables powerful semantic search capabilities across your entire heritage document collection.",
                    "metadata": {
                        "document_id": "cb0ab5a2-f256-4ca6-8573-ee80e20b9cde",
                        "filename": "HeritageAdvisor_Detailed_Product_Overview.docx",
                        "chunk_index": 1,
                        "total_chunks": 3
                    },
                    "distance": 0.25
                },
                {
                    "content": "Advanced search and retrieval features allow users to find relevant information quickly. The system supports both keyword and semantic search across all indexed documents and metadata.",
                    "metadata": {
                        "document_id": "cb0ab5a2-f256-4ca6-8573-ee80e20b9cde",
                        "filename": "HeritageAdvisor_Detailed_Product_Overview.docx",
                        "chunk_index": 2,
                        "total_chunks": 3
                    },
                    "distance": 0.28
                }
            ]
        }
    
    def search_project_documents(self, project_id: str, query_text: str, n_results: int = 5, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Mock search that returns relevant results based on query keywords"""
        logger.info(f"Mock search in project {project_id} for query: '{query_text}'")
        
        if project_id not in self.mock_documents:
            return []
        
        # Simple keyword matching for demonstration
        query_lower = query_text.lower()
        results = []
        
        for doc in self.mock_documents[project_id]:
            content_lower = doc["content"].lower()
            
            # Check if query terms appear in content
            if any(term in content_lower for term in query_lower.split()):
                results.append({
                    'content': doc["content"],
                    'metadata': doc["metadata"],
                    'distance': doc["distance"]
                })
        
        # Sort by relevance (distance)
        results.sort(key=lambda x: x['distance'])
        
        # Limit results
        return results[:n_results]

# Global mock service instance
mock_search_service = MockSearchService()