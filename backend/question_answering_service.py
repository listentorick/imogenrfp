import requests
import json
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from database import get_db
from models import Question
from chroma_service import chroma_service

logger = logging.getLogger(__name__)

class QuestionAnsweringService:
    def __init__(self, ollama_url: str = "http://ollama:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "qwen3:4b"
        self.chroma_service = chroma_service
    
    def perform_semantic_search(self, question: str, project_id: str, max_results: int = 5) -> List[str]:
        """Perform semantic search against ChromaDB to find relevant context"""
        try:
            logger.info(f"Performing semantic search for question in project {project_id}")
            
            # Use the chroma service to search for relevant documents
            search_results = self.chroma_service.search_project_documents(
                project_id=project_id,
                query_text=question,
                n_results=max_results
            )
            
            if search_results:
                # Extract the text content from search results
                context_chunks = []
                for result in search_results:
                    if 'content' in result:
                        context_chunks.append(result['content'])
                
                logger.info(f"Found {len(context_chunks)} relevant context chunks")
                return context_chunks
            else:
                logger.warning(f"No search results found for question in project {project_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
    
    def generate_answer_with_context(self, question: str, context_chunks: List[str]) -> Optional[str]:
        """Generate an answer using the question and context from semantic search"""
        
        # Combine context chunks into a single context string
        context = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."
        
        prompt = f"""You are an AI assistant helping to answer questions based on document content. 

Context from relevant documents:
{context}

Question: {question}

Instructions:
- Provide a clear, concise answer based on the context provided
- If the context doesn't contain enough information to answer the question, say "Based on the available documents, I cannot find sufficient information to answer this question."
- Be specific and reference the relevant information from the context
- Keep your answer focused and professional

Answer:"""

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Slightly creative but consistent
                    "max_tokens": 1000   # Reasonable answer length
                }
            }
            
            logger.info(f"Sending answer generation request to Ollama")
            response = requests.post(self.ollama_url, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "").strip()
            
            if answer:
                logger.info(f"Generated answer with {len(answer)} characters")
                return answer
            else:
                logger.warning("Empty response from Ollama")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in answer generation: {e}")
            return None
    
    def update_question_status(self, question_id: str, status: str, answer: Optional[str] = None, error_message: Optional[str] = None):
        """Update question processing status and answer in database"""
        db = next(get_db())
        try:
            question = db.query(Question).filter(Question.id == question_id).first()
            if question:
                question.processing_status = status
                if answer:
                    question.answer_text = answer
                if error_message:
                    question.processing_error = error_message
                elif status == 'processed':
                    # Clear error message when processing succeeds
                    question.processing_error = None
                db.commit()
                logger.info(f"Updated question {question_id} status to {status}")
            else:
                logger.error(f"Question {question_id} not found")
                
        except Exception as e:
            logger.error(f"Error updating question status: {e}")
            db.rollback()
        finally:
            db.close()
    
    def process_question(self, job_data: dict):
        """Process a single question by finding context and generating an answer"""
        question_id = job_data['question_id']
        tenant_id = job_data['tenant_id']
        project_id = job_data['project_id']
        deal_id = job_data['deal_id']
        
        logger.info(f"Processing question {question_id} for deal {deal_id}")
        
        try:
            # Update status to processing
            self.update_question_status(question_id, 'processing')
            
            # Get question details from database
            db = next(get_db())
            try:
                question = db.query(Question).filter(Question.id == question_id).first()
                if not question:
                    raise Exception(f"Question {question_id} not found")
                
                question_text = question.question_text
            finally:
                db.close()
            
            # Perform semantic search to find relevant context
            context_chunks = self.perform_semantic_search(question_text, project_id)
            
            # Generate answer using context
            answer = self.generate_answer_with_context(question_text, context_chunks)
            
            if answer:
                # Update question with generated answer
                self.update_question_status(question_id, 'processed', answer=answer)
                logger.info(f"Successfully processed question {question_id}")
            else:
                raise Exception("Failed to generate answer")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing question {question_id}: {error_msg}")
            self.update_question_status(question_id, 'error', error_message=error_msg)

def run_question_processor():
    """Main worker loop for processing questions"""
    from queue_service import queue_service
    
    processor = QuestionAnsweringService()
    logger.info("Question processor started")
    
    while True:
        try:
            # Get next job from queue
            job_data = queue_service.dequeue_question_processing()
            
            if job_data:
                processor.process_question(job_data)
            else:
                # No jobs available, wait a bit
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Question processor stopped")
            break
        except Exception as e:
            logger.error(f"Error in question processor: {e}")
            import time
            time.sleep(5)  # Wait before retrying

# Create singleton instance
question_answering_service = QuestionAnsweringService()

if __name__ == "__main__":
    run_question_processor()