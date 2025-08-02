import requests
import json
import logging
from typing import Optional, List, Dict, Any
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
    
    def perform_semantic_search(self, question: str, project_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search against ChromaDB to find relevant context
        
        Returns:
            List of dicts with 'content' and 'relevance_score' keys
        """
        try:
            logger.info(f"Performing semantic search for question in project {project_id}")
            
            # Use the chroma service to search for relevant documents
            search_results = self.chroma_service.search_project_documents(
                project_id=project_id,
                query_text=question,
                n_results=max_results
            )
            
            if search_results:
                # Extract the text content with individual relevance scores and document sources
                context_with_relevance = []
                
                for result in search_results:
                    if 'content' in result:
                        # Calculate similarity score from distance (ChromaDB uses cosine distance)
                        distance = result.get('distance')
                        relevance_score = max(0, (1 - distance) * 100) if distance is not None else 0.0
                        
                        # Extract document metadata for sources
                        metadata = result.get('metadata', {})
                        document_id = metadata.get('document_id')
                        
                        context_with_relevance.append({
                            'content': result['content'],
                            'relevance_score': relevance_score,
                            'document_id': document_id,
                            'filename': metadata.get('filename', 'Unknown'),
                            'chunk_index': metadata.get('chunk_index', 0)
                        })
                
                logger.info(f"Found {len(context_with_relevance)} relevant context chunks")
                return context_with_relevance
            else:
                logger.warning(f"No search results found for question in project {project_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []
    
    def generate_answer_with_context(self, question: str, context_chunks: List[str]) -> Optional[Dict]:
        """Generate a structured answer using the question and context from semantic search"""
        
        # Combine context chunks into a single context string
        context = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."
        
        # Define the JSON schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The detailed answer to the question"
                },
                "status": {
                    "type": "string",
                    "enum": ["answered", "partiallyAnswered", "notAnswered"],
                    "description": "Classification of the answer completeness"
                }
            },
            "required": ["answer", "status"]
        }
        
        prompt = f"""You are an AI assistant helping to answer questions based on document content.


Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.


<context>{context}</context>

<question> {question}</question>

Instructions:
- Provide a clear, concise answer based on the context provided
- Use the "status" field to classify how completely the question is answered:
  * "answered" - when the question is fully addressed using the context
  * "partiallyAnswered" - when only partial information is available 
  * "notAnswered" - when the context doesn't contain relevant information
- Be specific and reference the relevant information from the context
- Keep your answer focused and professional"""

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": response_schema,  # Use schema for structured output
                "options": {
                    "temperature": 0.3,  # Slightly creative but consistent
                    "max_tokens": 1000   # Reasonable answer length
                }
            }
            
            # Log the full prompt being sent to Ollama
            logger.info(f"=== OLLAMA REQUEST START ===")
            logger.info(f"Model: {self.model}")
            logger.info(f"URL: {self.ollama_url}")
            logger.info(f"Temperature: {data['options']['temperature']}")
            logger.info(f"Max Tokens: {data['options']['max_tokens']}")
            logger.info(f"PROMPT:\n{prompt}")
            logger.info(f"SCHEMA: {response_schema}")
            logger.info(f"=== OLLAMA REQUEST END ===")
            
            response = requests.post(self.ollama_url, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            # Log the raw response from Ollama
            logger.info(f"=== OLLAMA RESPONSE START ===")
            logger.info(f"Raw Response: {response_text}")
            logger.info(f"Full Result: {result}")
            
            if response_text:
                try:
                    # Parse the structured JSON response
                    structured_response = json.loads(response_text)
                    logger.info(f"Parsed Structured Response: {structured_response}")
                    logger.info(f"Answer Status: {structured_response.get('status', 'unknown')}")
                    logger.info(f"Answer Length: {len(structured_response.get('answer', ''))}")
                    logger.info(f"=== OLLAMA RESPONSE END ===")
                    return structured_response
                        
                except json.JSONDecodeError as e:
                    logger.error(f"=== JSON PARSE ERROR ===")
                    logger.error(f"Failed to parse structured response: {e}")
                    logger.error(f"Raw response that failed to parse: {response_text}")
                    logger.error(f"=== JSON PARSE ERROR END ===")
                    return None
            else:
                logger.warning(f"=== EMPTY RESPONSE ===")
                logger.warning("Empty response from Ollama")
                logger.warning(f"Full result was: {result}")
                logger.warning(f"=== EMPTY RESPONSE END ===")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"=== OLLAMA CONNECTION ERROR ===")
            logger.error(f"Error communicating with Ollama: {e}")
            logger.error(f"URL: {self.ollama_url}")
            logger.error(f"=== OLLAMA CONNECTION ERROR END ===")
            return None
        except Exception as e:
            logger.error(f"=== UNEXPECTED ERROR ===")
            logger.error(f"Unexpected error in answer generation: {e}")
            logger.error(f"=== UNEXPECTED ERROR END ===")
            return None
    
    def _determine_answer_status(self, answer: str) -> str:
        """Determine if an answer should be classified as 'answered' or 'notAnswered'"""
        if not answer or not answer.strip():
            return 'notAnswered'
        
        # Remove <think> sections to focus on the actual answer content
        import re
        # Remove anything between <think> and </think> tags
        cleaned_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
        cleaned_answer = cleaned_answer.strip()
        
        if not cleaned_answer:
            return 'notAnswered'
        
        # Convert to lowercase for case-insensitive matching
        answer_lower = cleaned_answer.lower().strip()
        
        # Phrases that indicate the question couldn't be answered
        notAnswered_indicators = [
            "cannot find sufficient information",
            "i cannot find",
            "not enough information",
            "insufficient information",
            "no information available",
            "unable to answer",
            "cannot answer",
            "not provided in",
            "no relevant information",
            "information is not available",
            "cannot determine",
            "not specified",
            "not mentioned",
            "no details provided",
            "cannot locate",
            "not found in the documents",
            "based on the available documents, i cannot"
        ]
        
        # Check if the answer contains any notAnswered indicators
        for indicator in notAnswered_indicators:
            if indicator in answer_lower:
                return 'notAnswered'
        
        # If the cleaned answer is very short (less than 20 characters) and doesn't contain meaningful content
        if len(cleaned_answer.strip()) < 20:
            # Check if it's just a generic response
            generic_responses = ["no", "n/a", "not available", "unknown", "none", "not specified"]
            if answer_lower in generic_responses:
                return 'notAnswered'
        
        # If none of the notAnswered indicators are found and we have substantial content, classify as answered
        return 'answered'
    
    def _extract_reasoning(self, answer: str) -> Optional[str]:
        """Extract reasoning content from <think></think> tags"""
        if not answer:
            return None
        
        import re
        # Extract content between <think> and </think> tags
        think_match = re.search(r'<think>(.*?)</think>', answer, flags=re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            return reasoning if reasoning else None
        return None
    
    def _clean_answer(self, answer: str) -> str:
        """Remove <think></think> sections from answer text"""
        if not answer:
            return answer
        
        import re
        # Remove anything between <think> and </think> tags
        cleaned_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
        return cleaned_answer.strip()
    
    def update_question_status(self, question_id: str, status: str, answer: Optional[str] = None, error_message: Optional[str] = None, structured_status: Optional[str] = None, relevance_score: Optional[float] = None, sources: Optional[List[str]] = None, source_filenames: Optional[List[str]] = None):
        """Update question processing status and answer in database"""
        db = next(get_db())
        try:
            question = db.query(Question).filter(Question.id == question_id).first()
            if question:
                question.processing_status = status
                if answer is not None:  # Allow empty string answers
                    # Extract reasoning from <think> tags
                    reasoning = self._extract_reasoning(answer)
                    if reasoning:
                        question.reasoning = reasoning
                    
                    # Clean answer text by removing <think> tags
                    cleaned_answer = self._clean_answer(answer)
                    question.answer_text = cleaned_answer
                    
                    # Set answer_status from structured status
                    if structured_status:
                        question.answer_status = structured_status
                    
                    # Set answer relevance score
                    if relevance_score is not None:
                        question.answer_relevance_score = relevance_score
                    
                    # Set answer sources
                    if sources is not None:
                        question.answer_sources = sources
                    
                    # Set answer source filenames
                    if source_filenames is not None:
                        question.answer_source_filenames = source_filenames
                    
                if error_message:
                    question.processing_error = error_message
                elif status == 'processed':
                    # Clear error message when processing succeeds
                    question.processing_error = None
                db.commit()
                logger.info(f"Updated question {question_id} status to {status}, answer_status: {question.answer_status if answer is not None else 'N/A'}")
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
            context_with_relevance = self.perform_semantic_search(question_text, project_id)
            
            # Extract context chunks and calculate average relevance
            context_chunks = [item['content'] for item in context_with_relevance]
            relevance_scores = [item['relevance_score'] for item in context_with_relevance]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            # Extract unique document IDs and filenames from search results for sources
            document_ids = []
            filenames = []
            seen_docs = set()
            
            for item in context_with_relevance:
                doc_id = item.get('document_id')
                filename = item.get('filename', 'Unknown')
                
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    document_ids.append(doc_id)
                    filenames.append(filename)
            
            logger.info(f"Found context from {len(document_ids)} unique documents: {document_ids}")
            logger.info(f"Source filenames: {filenames}")
            
            # Generate structured answer using context
            structured_answer = self.generate_answer_with_context(question_text, context_chunks)
            
            if structured_answer:
                # Extract answer text and status from structured response
                answer_text = structured_answer.get('answer', '')
                answer_status = structured_answer.get('status', 'notAnswered')
                
                # Only set answer_text if status is NOT "notAnswered"
                final_answer_text = "" if answer_status == "notAnswered" else answer_text
                
                # Only set sources if we actually have an answer
                final_sources = document_ids if answer_status != "notAnswered" and document_ids else None
                final_filenames = filenames if answer_status != "notAnswered" and filenames else None
                
                # Update question with generated answer, structured status, relevance score, sources, and filenames
                self.update_question_status(question_id, 'processed', answer=final_answer_text, structured_status=answer_status, relevance_score=avg_relevance, sources=final_sources, source_filenames=final_filenames)
                logger.info(f"Successfully processed question {question_id} with status: {answer_status}, relevance: {avg_relevance:.2f}%, sources: {len(document_ids) if document_ids else 0} documents")
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