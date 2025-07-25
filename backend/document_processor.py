import os
import time
import logging
from typing import Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sqlalchemy.orm import Session
from database import get_db
from models import Document
from queue_service import queue_service
from websocket_manager import websocket_manager
from chroma_service import chroma_service

# Document processing libraries
import PyPDF2
from docx import Document as DocxDocument
import magic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Initialize ChromaDB client
        chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
        chroma_port = os.getenv('CHROMA_PORT', '8000')
        
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=int(chroma_port)
        )
        
        # Get or create collection for documents
        try:
            self.collection = self.chroma_client.get_collection("documents")
        except:
            self.collection = self.chroma_client.create_collection("documents")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file types"""
        try:
            # Detect file type
            mime_type = magic.from_file(file_path, mime=True)
            
            if mime_type == 'application/pdf':
                return self._extract_from_pdf(file_path)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                              'application/msword']:
                return self._extract_from_docx(file_path)
            elif mime_type.startswith('text/'):
                return self._extract_from_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {mime_type}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return ""
    
    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    
    def store_in_vector_db(self, document_id: str, text: str, metadata: dict):
        """Store document text in ChromaDB"""
        try:
            # Split text into chunks for better vector storage
            chunks = self._split_text_into_chunks(text)
            
            # Store each chunk with metadata
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        **metadata,
                        'document_id': document_id,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }],
                    ids=[chunk_id]
                )
            
            logger.info(f"Stored document {document_id} in vector DB with {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error storing document {document_id} in vector DB: {e}")
            return False
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
                else:
                    # Look for word boundaries
                    for i in range(end, max(start + chunk_size // 2, end - 50), -1):
                        if text[i] == ' ':
                            end = i
                            break
            
            chunks.append(text[start:end].strip())
            start = max(end - overlap, start + 1)
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None, tenant_id: str = None):
        """Update document status in database and notify via WebSocket"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                if error_message:
                    document.processing_error = error_message
                db.commit()
                logger.info(f"Updated document {document_id} status to {status}")
                
                # Publish status update via WebSocket
                if tenant_id:
                    websocket_manager.publish_document_status_update(
                        tenant_id=tenant_id,
                        document_id=document_id,
                        status=status,
                        error_message=error_message
                    )
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            db.rollback()
        finally:
            db.close()
    
    def process_document(self, job_data: dict):
        """Process a single document"""
        document_id = job_data['document_id']
        file_path = job_data['file_path']
        tenant_id = job_data['tenant_id']
        project_id = job_data['project_id']
        
        logger.info(f"Processing document {document_id} at {file_path}")
        
        try:
            # Update status to processing
            self.update_document_status(document_id, 'processing', tenant_id=tenant_id)
            
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            if not text.strip():
                raise Exception("No text content extracted from file")
            
            # Prepare metadata
            metadata = {
                'tenant_id': tenant_id,
                'project_id': project_id,
                'file_path': file_path
            }
            
            # Store in project-specific ChromaDB collection
            text_chunks = self._split_text_into_chunks(text)
            
            success = chroma_service.add_document_to_project(
                project_id=project_id,
                document_id=document_id,
                text_chunks=text_chunks,
                metadata={
                    'tenant_id': tenant_id,
                    'project_id': project_id,
                    'file_path': file_path,
                    'filename': os.path.basename(file_path)
                }
            )
            
            if success:
                self.update_document_status(document_id, 'processed', tenant_id=tenant_id)
                logger.info(f"Successfully processed document {document_id}")
            else:
                raise Exception("Failed to store in vector database")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing document {document_id}: {error_msg}")
            self.update_document_status(document_id, 'error', error_msg, tenant_id=tenant_id)

def run_document_processor():
    """Main worker loop"""
    processor = DocumentProcessor()
    logger.info("Document processor started")
    
    while True:
        try:
            # Get next job from queue
            job_data = queue_service.dequeue_document_processing()
            
            if job_data:
                processor.process_document(job_data)
            else:
                # No jobs available, wait a bit
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Document processor stopped")
            break
        except Exception as e:
            logger.error(f"Error in document processor: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_document_processor()