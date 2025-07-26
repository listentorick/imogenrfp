import os
import time
import logging
from typing import Optional
from pathlib import Path
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
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # We'll use the chroma_service instead of direct client
        self.chroma_service = chroma_service
        
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Prioritize paragraph, sentence, then word breaks
        )
    
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
    
    def store_in_vector_db(self, project_id: str, document_id: str, text: str, metadata: dict):
        """Store document text in ChromaDB using chroma_service"""
        try:
            # Split text into chunks using LangChain's RecursiveCharacterTextSplitter
            chunks = self.text_splitter.split_text(text)
            
            # Use chroma_service to store the document
            success = self.chroma_service.add_document_to_project(
                project_id=project_id,
                document_id=document_id,
                text_chunks=chunks,
                metadata=metadata
            )
            
            if success:
                logger.info(f"Stored document {document_id} in vector DB with {len(chunks)} chunks")
            else:
                logger.error(f"Failed to store document {document_id} in vector DB")
            
            return success
        except Exception as e:
            logger.error(f"Error storing document {document_id} in vector DB: {e}")
            return False
    
    def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None, tenant_id: str = None):
        """Update document status in database and notify via WebSocket"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                if error_message:
                    document.processing_error = error_message
                elif status == 'processed':
                    # Clear error message when processing succeeds
                    document.processing_error = None
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
            
            # Ensure project collection exists
            self.chroma_service.create_project_collection(project_id, f"Project {project_id}")
            
            # Store in project-specific ChromaDB collection
            success = self.store_in_vector_db(
                project_id=project_id,
                document_id=document_id,
                text=text,
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