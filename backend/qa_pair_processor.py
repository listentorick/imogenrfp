import os
import time
import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models import ProjectQAPair
from queue_service import queue_service
from chroma_service import chroma_service
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAPairProcessor:
    def __init__(self):
        self.chroma_service = chroma_service
        
        # Initialize text splitter - same config as document processor
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def process_qa_pair(self, job_data: dict):
        """Process a Q&A pair and add it to ChromaDB"""
        qa_pair_id = job_data['qa_pair_id']
        tenant_id = job_data['tenant_id']
        project_id = job_data['project_id']
        
        logger.info(f"Processing Q&A pair {qa_pair_id} for project {project_id}")
        
        try:
            # Get Q&A pair from database
            db = next(get_db())
            try:
                qa_pair = db.query(ProjectQAPair).filter(ProjectQAPair.id == qa_pair_id).first()
                if not qa_pair:
                    logger.error(f"Q&A pair {qa_pair_id} not found in database")
                    return
                
                # Combine question and answer for vector storage
                combined_text = f"Question: {qa_pair.question_text}\n\nAnswer: {qa_pair.answer_text}"
                
                # Create chunks using the same method as documents
                chunks = self.text_splitter.split_text(combined_text)
                
                # If the combined text is short, ensure we have at least one chunk
                if not chunks and combined_text.strip():
                    chunks = [combined_text]
                
                # Ensure project collection exists
                self.chroma_service.create_project_collection(project_id, f"Project {project_id}")
                
                # Remove any existing Q&A pair with the same ID (for updates)
                existing_doc_id = f"qa_pair_{qa_pair_id}"
                self.chroma_service.remove_document_from_project(project_id, existing_doc_id)
                
                # Store in ChromaDB with special metadata to identify as Q&A pair
                metadata = {
                    'tenant_id': tenant_id,
                    'project_id': project_id,
                    'qa_pair_id': qa_pair_id,
                    'document_type': 'qa_pair',
                    'source_type': 'knowledge_base',
                    'question_text': qa_pair.question_text,
                    'answer_text': qa_pair.answer_text,
                    'filename': f"Knowledge Base Q&A - {qa_pair_id[:8]}"
                }
                
                success = self.chroma_service.add_document_to_project(
                    project_id=project_id,
                    document_id=f"qa_pair_{qa_pair_id}",
                    text_chunks=chunks,
                    metadata=metadata
                )
                
                if success:
                    logger.info(f"Successfully stored Q&A pair {qa_pair_id} in ChromaDB with {len(chunks)} chunks")
                else:
                    logger.error(f"Failed to store Q&A pair {qa_pair_id} in ChromaDB")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing Q&A pair {qa_pair_id}: {e}")

def run_qa_pair_processor():
    """Main worker loop for Q&A pair processing"""
    processor = QAPairProcessor()
    logger.info("Q&A pair processor started")
    
    while True:
        try:
            # Get next job from queue
            job_data = queue_service.dequeue_qa_pair_processing()
            
            if job_data:
                processor.process_qa_pair(job_data)
            else:
                # No jobs available, wait a bit
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Q&A pair processor stopped")
            break
        except Exception as e:
            logger.error(f"Error in Q&A pair processor: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_qa_pair_processor()