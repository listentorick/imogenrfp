import os
import time
import logging
import json
from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db
from models import Document
from queue_service import queue_service

# Simple document processing without heavy ML dependencies
import PyPDF2
from docx import Document as DocxDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDocumentProcessor:
    def __init__(self):
        logger.info("Simple document processor initialized")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file types"""
        try:
            # Simple file type detection based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_ext == '.txt':
                return self._extract_from_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
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
    
    def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None):
        """Update document status in database"""
        db = next(get_db())
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                if error_message:
                    document.processing_error = error_message
                db.commit()
                logger.info(f"Updated document {document_id} status to {status}")
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
            self.update_document_status(document_id, 'processing')
            
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            if not text.strip():
                raise Exception("No text content extracted from file")
            
            # For now, just simulate successful processing
            # In the full version, this would store in ChromaDB
            logger.info(f"Extracted {len(text)} characters from document {document_id}")
            
            # Update status to processed
            self.update_document_status(document_id, 'processed')
            logger.info(f"Successfully processed document {document_id}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing document {document_id}: {error_msg}")
            self.update_document_status(document_id, 'error', error_msg)

def run_simple_worker():
    """Main worker loop"""
    processor = SimpleDocumentProcessor()
    logger.info("Simple document worker started")
    
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
            logger.info("Document worker stopped")
            break
        except Exception as e:
            logger.error(f"Error in document worker: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_simple_worker()