import requests
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self):
        chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
        chroma_port = os.getenv('CHROMA_PORT', '8000')
        self.base_url = f"http://{chroma_host}:{chroma_port}/api/v1"
    
    def create_project_collection(self, project_id: str, project_name: str) -> bool:
        """Create a ChromaDB collection for a project"""
        try:
            # First check if collection already exists
            get_response = requests.get(f"{self.base_url}/collections/{project_id}")
            if get_response.status_code == 200:
                logger.info(f"Collection for project {project_id} already exists")
                return True
            
            collection_data = {
                "name": str(project_id),
                "metadata": {
                    "description": f"Document collection for project: {project_name}",
                    "project_name": project_name,
                    "created_by": "rfp_system"
                }
            }
            
            response = requests.post(f"{self.base_url}/collections", json=collection_data)
            
            if response.status_code == 200:
                logger.info(f"Created ChromaDB collection for project {project_id}")
                return True
            elif response.status_code == 409:
                logger.info(f"Collection for project {project_id} already exists")
                return True
            else:
                logger.error(f"Failed to create collection for project {project_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating collection for project {project_id}: {e}")
            return False
    
    def delete_project_collection(self, project_id: str) -> bool:
        """Delete a ChromaDB collection for a project"""
        try:
            response = requests.delete(f"{self.base_url}/collections/{project_id}")
            
            if response.status_code == 200:
                logger.info(f"Deleted ChromaDB collection for project {project_id}")
                return True
            else:
                logger.warning(f"Failed to delete collection for project {project_id}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting collection for project {project_id}: {e}")
            return False
    
    def add_document_to_project(self, project_id: str, document_id: str, text_chunks: List[str], 
                               metadata: Dict[str, Any]) -> bool:
        """Add document chunks to a project's ChromaDB collection"""
        try:
            collection_name = str(project_id)
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(text_chunks):
                if chunk.strip():  # Only add non-empty chunks
                    documents.append(chunk)
                    
                    chunk_metadata = {
                        **metadata,
                        'chunk_index': i,
                        'total_chunks': len(text_chunks),
                        'document_id': document_id
                    }
                    metadatas.append(chunk_metadata)
                    ids.append(f"{document_id}_chunk_{i}")
            
            if not documents:
                logger.warning(f"No content to add for document {document_id}")
                return False
            
            add_data = {
                'documents': documents,
                'metadatas': metadatas,
                'ids': ids
            }
            
            response = requests.post(f"{self.base_url}/collections/{collection_name}/add", 
                                   json=add_data)
            
            if response.status_code == 200:
                logger.info(f"Added document {document_id} to project {project_id} collection ({len(documents)} chunks)")
                return True
            else:
                logger.error(f"Failed to add document {document_id} to collection: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding document {document_id} to project {project_id}: {e}")
            return False
    
    def search_project_documents(self, project_id: str, query_text: str, n_results: int = 5,
                                tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search documents within a project's collection"""
        try:
            collection_name = str(project_id)
            
            query_data = {
                'query_texts': [query_text],
                'n_results': n_results
            }
            
            # Add tenant filter if provided
            if tenant_id:
                query_data['where'] = {'tenant_id': tenant_id}
            
            response = requests.post(f"{self.base_url}/collections/{collection_name}/query",
                                   json=query_data)
            
            if response.status_code == 200:
                results = response.json()
                
                # Format results
                formatted_results = []
                if results.get('documents') and len(results['documents'][0]) > 0:
                    documents = results['documents'][0]
                    metadatas = results.get('metadatas', [[]])[0]
                    distances = results.get('distances', [[]])[0]
                    
                    for i, doc in enumerate(documents):
                        formatted_results.append({
                            'content': doc,
                            'metadata': metadatas[i] if i < len(metadatas) else {},
                            'distance': distances[i] if i < len(distances) else None
                        })
                
                logger.info(f"Search in project {project_id} returned {len(formatted_results)} results")
                return formatted_results
            else:
                logger.error(f"Search failed for project {project_id}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching project {project_id}: {e}")
            return []
    
    def remove_document_from_project(self, project_id: str, document_id: str) -> bool:
        """Remove all chunks of a document from a project's collection"""
        try:
            collection_name = str(project_id)
            
            # Get all chunk IDs for this document
            # First, we need to query to find all chunks with this document_id
            query_data = {
                'where': {'document_id': document_id},
                'include': ['metadatas']
            }
            
            # Get the document chunks
            response = requests.post(f"{self.base_url}/collections/{collection_name}/get",
                                   json=query_data)
            
            if response.status_code == 200:
                results = response.json()
                ids_to_delete = results.get('ids', [])
                
                if ids_to_delete:
                    # Delete the chunks
                    delete_data = {'ids': ids_to_delete}
                    delete_response = requests.post(f"{self.base_url}/collections/{collection_name}/delete",
                                                  json=delete_data)
                    
                    if delete_response.status_code == 200:
                        logger.info(f"Removed document {document_id} from project {project_id} ({len(ids_to_delete)} chunks)")
                        return True
                    else:
                        logger.error(f"Failed to delete document chunks: {delete_response.text}")
                        return False
                else:
                    logger.info(f"No chunks found for document {document_id} in project {project_id}")
                    return True
            else:
                logger.error(f"Failed to query document chunks: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing document {document_id} from project {project_id}: {e}")
            return False

# Global service instance
chroma_service = ChromaService()