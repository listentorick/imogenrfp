import os
import logging
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self):
        chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
        chroma_port = os.getenv('CHROMA_PORT', '8000')
        
        # Initialize ChromaDB client (v1.0.15) - simplified for compatibility
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=int(chroma_port)
        )
        logger.info(f"ChromaDB 1.0.15 client initialized for {chroma_host}:{chroma_port}")
    
    def get_collection(self, project_id: str):
        """Get the collection for a project"""
        try:
            collection_name = str(project_id)
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.debug(f"Collection {project_id} not found: {e}")
            return None

    def create_project_collection(self, project_id: str, project_name: str) -> bool:
        """Create a ChromaDB collection for a project"""
        try:
            # First check if collection already exists
            existing_collection = self.get_collection(project_id)
            if existing_collection:
                logger.info(f"Collection for project {project_id} already exists")
                return True
            
            # Create new collection with cosine distance for better text embedding similarity
            collection = self.client.create_collection(
                name=str(project_id),
                metadata={
                    "description": f"Document collection for project: {project_name}",
                    "project_name": project_name,
                    "created_by": "rfp_system",
                    "hnsw:space": "cosine"  # Use cosine distance instead of default L2
                }
            )
            
            logger.info(f"Created ChromaDB collection for project {project_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error creating collection for project {project_id}: {e}")
            return False
    
    def delete_project_collection(self, project_id: str) -> bool:
        """Delete a ChromaDB collection for a project"""
        try:
            collection = self.get_collection(project_id)
            if not collection:
                logger.warning(f"Collection for project {project_id} not found")
                return True  # Already deleted
            
            self.client.delete_collection(name=str(project_id))
            logger.info(f"Deleted ChromaDB collection for project {project_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting collection for project {project_id}: {e}")
            return False
    
    def add_document_to_project(self, project_id: str, document_id: str, text_chunks: List[str], 
                               metadata: Dict[str, Any]) -> bool:
        """Add document chunks to a project's ChromaDB collection"""
        try:
            # Get collection
            collection = self.get_collection(project_id)
            if not collection:
                logger.error(f"Collection for project {project_id} not found")
                return False
            
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
            
            # Add documents to collection (ChromaDB client handles embeddings automatically)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added document {document_id} to project {project_id} collection ({len(documents)} chunks)")
            return True
                
        except Exception as e:
            logger.error(f"Error adding document {document_id} to project {project_id}: {e}")
            return False
    
    def get_all_documents_in_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all documents stored in a project's collection for debugging"""
        try:
            collection = self.get_collection(project_id)
            if not collection:
                logger.warning(f"No collection found for project {project_id}")
                return []
            
            # Get all documents
            results = collection.get(include=['documents', 'metadatas'])
            
            documents = results.get('documents', [])
            metadatas = results.get('metadatas', [])
            ids = results.get('ids', [])
            
            formatted_results = []
            for i, doc in enumerate(documents):
                formatted_results.append({
                    'id': ids[i] if i < len(ids) else None,
                    'content': doc,
                    'metadata': metadatas[i] if i < len(metadatas) else {}
                })
            
            logger.info(f"Retrieved {len(formatted_results)} documents from project {project_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting documents from project {project_id}: {e}")
            return []
    
    def search_project_documents(self, project_id: str, query_text: str, n_results: int = 5,
                                tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search documents within a project's collection"""
        try:
            # Get collection
            collection = self.get_collection(project_id)
            if not collection:
                logger.warning(f"No collection found for project {project_id}")
                return []
            
            # Prepare query filters
            where_clause = None
            if tenant_id:
                where_clause = {'tenant_id': tenant_id}
            
            # Perform query (ChromaDB client handles embeddings automatically)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results.get('documents') and len(results['documents'][0]) > 0:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                logger.info(f"Raw search results for query '{query_text}': {len(documents)} documents found")
                
                for i, doc in enumerate(documents):
                    distance = distances[i] if i < len(distances) else None
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    
                    # Log relevance debugging info
                    if distance is not None:
                        similarity_score = max(0, (1 - distance) * 100)
                        logger.info(f"Result {i+1}: distance={distance:.4f}, similarity={similarity_score:.1f}%, chunk_index={metadata.get('chunk_index', 'unknown')}")
                        logger.debug(f"Content preview: {doc[:100]}...")
                    
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'distance': distance
                    })
            
            logger.info(f"Search in project {project_id} returned {len(formatted_results)} results")
            return formatted_results
                
        except Exception as e:
            logger.error(f"Error searching project {project_id}: {e}")
            return []
    
    def clear_project_collection(self, project_id: str) -> bool:
        """Clear all documents from a project's collection"""
        try:
            collection = self.get_collection(project_id)
            if not collection:
                logger.warning(f"No collection found for project {project_id}")
                return True  # Already empty
            
            # Delete the entire collection and recreate it
            self.client.delete_collection(name=str(project_id))
            logger.info(f"Deleted collection for project {project_id}")
            
            # Recreate empty collection with cosine distance
            self.client.create_collection(
                name=str(project_id),
                metadata={
                    "description": f"Document collection for project: {project_id}",
                    "project_id": project_id,
                    "created_by": "rfp_system",
                    "recreated_for": "langchain_chunking",
                    "hnsw:space": "cosine"  # Use cosine distance for better text embeddings
                }
            )
            logger.info(f"Recreated empty collection for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection for project {project_id}: {e}")
            return False
    
    def remove_document_from_project(self, project_id: str, document_id: str) -> bool:
        """Remove all chunks of a document from a project's collection"""
        try:
            # Get collection
            collection = self.get_collection(project_id)
            if not collection:
                logger.warning(f"No collection found for project {project_id}")
                return True  # Already doesn't exist
            
            # Get all chunk IDs for this document
            results = collection.get(
                where={'document_id': document_id},
                include=['metadatas']
            )
            
            ids_to_delete = results.get('ids', [])
            
            if ids_to_delete:
                # Delete the chunks
                collection.delete(ids=ids_to_delete)
                logger.info(f"Removed document {document_id} from project {project_id} ({len(ids_to_delete)} chunks)")
                return True
            else:
                logger.info(f"No chunks found for document {document_id} in project {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing document {document_id} from project {project_id}: {e}")
            return False

# Global service instance
chroma_service = ChromaService()