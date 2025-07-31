import requests
import json
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session  
from database import get_db
from models import Question, Document

logger = logging.getLogger(__name__)

class QuestionExtractionService:
    def __init__(self, ollama_url: str = "http://ollama:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "qwen3:4b"
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, any]]:
        """Extract questions from document text using Ollama/Qwen3 4b"""
        
        prompt = f"""
You are tasked with extracting questions from a document. Please analyze the following text and identify all questions contained within it.

Return your response as a JSON array where each question is an object with:
- "question": the exact question text
- "confidence": a confidence score from 0.0 to 1.0 indicating how certain you are this is a question
- "order": the sequential order this question appears in the document (starting from 1)

Only include actual questions that require answers. Do not include rhetorical questions or questions used as examples.

Document text:
{text}

Response format:
[
    {{"question": "What is your company's experience with similar projects?", "confidence": 0.95, "order": 1}},
    {{"question": "What is your proposed timeline?", "confidence": 0.90, "order": 2}}
]
"""

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1  # Low temperature for consistent extraction
                }
            }
            
            logger.info(f"Sending question extraction request to Ollama")
            response = requests.post(self.ollama_url, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            # Extract JSON from response
            if response_text.startswith('[') and response_text.endswith(']'):
                questions = json.loads(response_text)
                logger.info(f"Extracted {len(questions)} questions from document")
                return questions
            else:
                # Try to find JSON within the response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    json_text = response_text[start_idx:end_idx]
                    questions = json.loads(json_text)
                    logger.info(f"Extracted {len(questions)} questions from document")
                    return questions
                else:
                    logger.warning("No valid JSON found in Ollama response")
                    return []
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Ollama: {e}")
            logger.error(f"Raw response: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in question extraction: {e}")
            return []
    
    def save_questions_to_database(self, questions: List[Dict], document_id: str, deal_id: str, tenant_id: str) -> bool:
        """Save extracted questions to the database"""
        db = next(get_db())
        try:
            for question_data in questions:
                question = Question(
                    tenant_id=tenant_id,
                    deal_id=deal_id,
                    document_id=document_id,
                    question_text=question_data.get('question', ''),
                    extraction_confidence=question_data.get('confidence', 0.0),
                    question_order=question_data.get('order', 0)
                )
                db.add(question)
            
            db.commit()
            logger.info(f"Saved {len(questions)} questions to database for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving questions to database: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def process_document_for_questions(self, document_id: str, text: str) -> bool:
        """Main method to extract questions from a document and save them"""
        db = next(get_db())
        try:
            # Get document details
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document or not document.deal_id:
                logger.error(f"Document {document_id} not found or not associated with a deal")
                return False
            
            # Extract questions using Ollama
            extracted_questions = self.extract_questions_from_text(text)
            
            if not extracted_questions:
                logger.info(f"No questions found in document {document_id}")
                return True  # Not an error, just no questions
            
            # Save questions to database
            success = self.save_questions_to_database(
                extracted_questions, 
                document_id, 
                str(document.deal_id), 
                str(document.tenant_id)
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing document {document_id} for questions: {e}")
            return False
        finally:
            db.close()

# Create singleton instance
question_extraction_service = QuestionExtractionService()