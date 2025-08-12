import requests
import json
import logging
import magic
from typing import List, Dict, Optional
from sqlalchemy.orm import Session  
from database import get_db
from models import Question, Document, Deal
from queue_service import queue_service

logger = logging.getLogger(__name__)

class QuestionExtractionService:
    def __init__(self, ollama_url: str = "http://ollama:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "qwen3:4b"
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, any]]:
        """Extract questions from document text using Ollama/Qwen3 4b with structured output"""
        
        prompt = f"""
You are tasked with extracting questions and requirements from a document. Analyze the following text and identify all items that request information, regardless of how they are phrased.

Look for:
- Direct questions (e.g., "What is your experience?", "How do you handle security?")
- Requirements (e.g., "Describe your methodology", "Provide details of your approach")
- Criteria statements (e.g., "Must demonstrate compliance with", "Should include examples of")
- Information requests (e.g., "List your certifications", "Outline your process")
- Specification needs (e.g., "Technical specifications required", "Documentation must include")
- Evaluation criteria (e.g., "Bidders must provide evidence of", "Proposals should address")

FORMATTING RULES:
1. **PRESERVE EXISTING QUESTIONS**: If the original text is already in question format (ends with "?", starts with interrogative words like "What", "How", "When", "Where", "Why", "Which", "Who", "Can", "Will", "Do", "Does", "Are", "Is"), keep it exactly as written.
2. **REPHRASE NON-QUESTIONS ONLY**: For statements or requirements that are NOT already questions, convert them to clear question format while preserving the original intent and context.
3. **MAINTAIN CONTEXT**: Always preserve specific details, metrics, and surrounding context from the original text.

EXAMPLES:
- "What is your experience with cloud security?" → Keep as: "What is your experience with cloud security?"
- "Vendor must provide disaster recovery plan" → Convert to: "What is your disaster recovery plan?"

Return as JSON. Each item should be an object with question, original_text, confidence, order, and type fields.

Document text:
{text}
"""

        # JSON Schema for structured output
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The item converted to a clear question format"
                    },
                    "original_text": {
                        "type": "string",
                        "description": "The exact original text from the document"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score from 0.0 to 1.0"
                    },
                    "order": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Sequential order this item appears in the document"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["question", "requirement", "criteria", "specification", "other"],
                        "description": "Type of request"
                    }
                },
                "required": ["question", "original_text", "confidence", "order", "type"],
                "additionalProperties": False
            }
        }


        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0  # Set to 0 for structured outputs as recommended
                }
            }
            
            logger.info(f"Sending question extraction request to Ollama with structured output")
            logger.info(f"=== PROMPT BEING SENT TO LLM ===")
            logger.info(f"Model: {data['model']}")
            logger.info(f"Prompt: {data['prompt']}")
            logger.info(f"=== END PROMPT ===")
            
            response = requests.post(self.ollama_url, json=data, timeout=600)  # Increased timeout for large files
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            logger.info(f"=== LLM RESPONSE RECEIVED ===")
            logger.info(f"Raw response length: {len(response_text)}")
            logger.info(f"Full response: {response_text}")
            logger.info(f"=== END LLM RESPONSE ===")
            
            # With structured output, the response should be valid JSON
            try:
                questions = json.loads(response_text)
                logger.info(f"Successfully extracted {len(questions)} questions from document using structured output")
                return questions
            except json.JSONDecodeError as parse_error:
                logger.error(f"Failed to parse structured output JSON: {parse_error}")
                logger.error(f"Response text: {response_text}")
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
    
    def extract_questions_from_excel(self, excel_data: Dict[str, any]) -> List[Dict[str, any]]:
        """Extract questions from Excel data with cell location identification using structured output"""
        
        # Create a structured representation of the Excel data
        # Limit to first 100 cells to avoid overwhelming Ollama
        cells_data = excel_data.get('cells_data', [])[:100]
        cells_info = []
        for cell in cells_data:
            cells_info.append(f"Cell {cell['cell_reference']}: {cell['value']}")
        
        cells_text = "\n".join(cells_info)
        logger.info(f"Sending {len(cells_data)} cells to Ollama for analysis")
        
        prompt = f"""
EXTRACT ALL QUESTIONS AND REQUIREMENTS FROM THE FOLLOWING DOCUMENT

You are analyzing a document that contains requirements, questions, or information requests. Extract EVERY item that requests information, responses, or vendor action, regardless of document format, structure, or how the request is phrased.

CRITICAL INSTRUCTIONS:
- Process the ENTIRE document from beginning to end - do not skip any sections
- Include ALL requirement types: explicit questions, implicit requests, compliance needs, technical specs
- Extract items even if they contain placeholder values, templates, or incomplete information
- Look beyond obvious question marks - many requirements are stated as declarations
- Start processing from the very first content item and continue to the end

WHAT COUNTS AS EXTRACTABLE:
- Direct questions ("What is your approach to...?", "How do you handle...?")
- Requirement statements ("System must...", "Vendor shall...", "Solution should...")
- Compliance demands ("Must comply with...", "Demonstrate adherence to...")
- Specification requests ("Provide details of...", "Describe your methodology...")
- Performance criteria ("Must achieve...", "Target response time...", "Uptime requirements...")
- Documentation needs ("Include documentation for...", "Provide evidence of...")
- Process descriptions ("Vendors must describe...", "Explain how...")
- Deliverable requirements ("Submit proof of...", "Provide certificates...")
- Template requirements with placeholders ("[X] users", "[Y] seconds", etc.)

EXTRACTION AND FORMATTING RULES:

1. **PRESERVE EXISTING QUESTIONS**: If the original text is already in question format (ends with "?", starts with interrogative words like "What", "How", "When", "Where", "Why", "Which", "Who", "Can", "Will", "Do", "Does", "Are", "Is"), keep it exactly as written.

2. **REPHRASE NON-QUESTIONS ONLY**: For statements, requirements, or demands that are NOT already questions, convert them to clear question format while preserving all specific details, metrics, and context.

3. **PRESERVE CONTEXT**: Always maintain the specific details, metrics, and surrounding context from the original text.

4. **CONFIDENCE RATINGS**:
   - 0.95: Explicit questions or clear "must provide/describe" statements
   - 0.9: Strong requirement statements ("must", "shall", "required")
   - 0.8: Moderate requirements ("should", "expected to")
   - 0.7: Implied needs or criteria that suggest information is needed

EXAMPLES:
- "What is your disaster recovery plan?" → Keep as: "What is your disaster recovery plan?"
- "How do you handle data backups?" → Keep as: "How do you handle data backups?"
- "System must support 1000 concurrent users" → Convert to: "What is the system's capacity for supporting concurrent users?"
- "Vendor shall provide security certifications" → Convert to: "What security certifications will you provide?"

DOCUMENT TO ANALYZE:
{cells_text}
"""

        # JSON Schema for question extraction only (step 1)
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The item converted to a clear question format"
                    },
                    "original_text": {
                        "type": "string",
                        "description": "The exact original text from the document"
                    },
                    "extraction_confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence in question extraction"
                    },
                    "order": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Sequential order this item appears in the document"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["question", "requirement", "criteria", "specification", "form_field", "other"],
                        "description": "Type of request"
                    }
                },
                "required": ["question", "original_text", "extraction_confidence", "order", "type"],
                "additionalProperties": False
            }
        }

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0  # Set to 0 for structured outputs as recommended
                }
            }
            
            logger.info(f"Sending Excel question extraction request to Ollama with structured output")
            logger.info(f"=== EXCEL PROMPT BEING SENT TO LLM ===")
            logger.info(f"Model: {data['model']}")
            logger.info(f"Prompt: {data['prompt']}")
            logger.info(f"=== END EXCEL PROMPT ===")
            
            response = requests.post(self.ollama_url, json=data, timeout=600)  # Increased timeout for large Excel files
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            logger.info(f"=== EXCEL LLM RESPONSE RECEIVED ===")
            logger.info(f"Raw response length: {len(response_text)}")
            logger.info(f"Full response: {response_text}")
            logger.info(f"=== END EXCEL LLM RESPONSE ===")
            
            # With structured output, the response should be valid JSON
            try:
                questions = json.loads(response_text)
                logger.info(f"Successfully extracted {len(questions)} questions from Excel document using structured output")
                return questions
            except json.JSONDecodeError as parse_error:
                logger.error(f"Failed to parse Excel structured output JSON: {parse_error}")
                logger.error(f"Response text: {response_text}")
                return []
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama for Excel extraction: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Ollama for Excel extraction: {e}")
            logger.error(f"Raw response: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Excel question extraction: {e}")
            return []

    def deduplicate_questions(self, questions: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Remove duplicate questions based on question text and original text"""
        seen = set()
        unique_questions = []
        duplicates_removed = 0
        
        for question in questions:
            # Create a unique key based on question text and original text
            question_text = question.get('question', '').strip().lower()
            original_text = question.get('original_text', '').strip().lower()
            unique_key = (question_text, original_text)
            
            if unique_key not in seen:
                seen.add(unique_key)
                unique_questions.append(question)
            else:
                duplicates_removed += 1
                logger.debug(f"Removed duplicate question: {question.get('question', '')[:50]}...")
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate questions")
        
        return unique_questions

    def identify_answer_cells(self, excel_data: Dict[str, any], questions: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Identify answer cell locations for extracted questions using structured output"""
        
        # Create a structured representation of the Excel data
        cells_data = excel_data.get('cells_data', [])[:100]  # Same limit as question extraction
        cells_info = []
        for cell in cells_data:
            cells_info.append(f"Cell {cell['cell_reference']}: {cell['value']}")
        
        cells_text = "\n".join(cells_info)
        
        # Format original text for the prompt - focus on locating these in the Excel data
        original_texts = []
        for i, q in enumerate(questions, 1):
            original_texts.append(f"{i}. ORIGINAL TEXT TO LOCATE: {q['original_text']}")
            original_texts.append(f"   Rephrased Question: {q['question']}")
            original_texts.append("")  # Add blank line for readability
        
        questions_list = "\n".join(original_texts)
        
        logger.info(f"Identifying answer cells for {len(questions)} questions using {len(cells_data)} cells")
        
        prompt = f"""Analyze this Excel data and locate where each original text appears, then determine where answers should be placed.

Excel Data:
{cells_text}

Original Texts to Locate:
{questions_list}

PROCESS:
1. LOCATE ORIGINAL TEXT: For each original text, find where it appears in the Excel data above
2. ANALYZE TABLE STRUCTURE around that location:
   - Identify column headers and their purposes
   - Look for columns with names like "Supplier Response", "Comments", "Answer", "Your Response", "Vendor Input", "Response Required", etc.
   - Determine if this is a form layout (questions in one column, answers in adjacent) or a more complex table structure
   - Note any patterns in cell references (e.g., questions in column A, answers in column B)

3. DETERMINE ANSWER CELL by considering:
   - Is there a dedicated "response" or "comment" column? Use that first
   - For form layouts: typically the cell immediately to the right (same row, next column) 
   - For vertical forms: typically the cell immediately below
   - For table structures: look for the appropriate response column based on headers
   - Consider empty cells adjacent to the original text as potential answer locations
   - If multiple empty cells are available, choose the one that makes most logical sense based on the table structure

Return as JSON. Each item should be an object with question_text (matching the rephrased question exactly), answer_cell, cell_confidence, and reasoning fields. The reasoning should explain WHERE you found the original text and WHY you chose that answer cell location."""

        # JSON Schema for answer cell identification (step 2)
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_text": {
                        "type": "string",
                        "description": "The exact rephrased question text to match"
                    },
                    "answer_cell": {
                        "type": "string",
                        "description": "Predicted cell reference where answer should go (e.g., B2, C15)"
                    },
                    "cell_confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence in answer cell prediction"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of where the original text was found and why this answer cell was predicted"
                    }
                },
                "required": ["question_text", "answer_cell", "cell_confidence", "reasoning"],
                "additionalProperties": False
            }
        }

        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0  # Set to 0 for structured outputs as recommended
                }
            }
            
            logger.info(f"Sending answer cell identification request to Ollama with structured output")
            logger.info(f"=== ANSWER CELL PROMPT BEING SENT TO LLM ===")
            logger.info(f"Model: {data['model']}")
            logger.info(f"Prompt: {data['prompt']}")
            logger.info(f"=== END ANSWER CELL PROMPT ===")
            
            response = requests.post(self.ollama_url, json=data, timeout=600)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "").strip()
            
            logger.info(f"=== ANSWER CELL LLM RESPONSE RECEIVED ===")
            logger.info(f"Raw response length: {len(response_text)}")
            logger.info(f"Full response: {response_text}")
            logger.info(f"=== END ANSWER CELL LLM RESPONSE ===")
            
            # With structured output, the response should be valid JSON
            try:
                cell_predictions = json.loads(response_text)
                logger.info(f"Successfully identified answer cells for {len(cell_predictions)} questions using structured output")
                return cell_predictions
            except json.JSONDecodeError as parse_error:
                logger.error(f"Failed to parse answer cell structured output JSON: {parse_error}")
                logger.error(f"Response text: {response_text}")
                return []
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama for answer cell identification: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Ollama for answer cell identification: {e}")
            logger.error(f"Raw response: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in answer cell identification: {e}")
            return []
    
    def save_questions_to_database(self, questions: List[Dict], document_id: str, deal_id: str, tenant_id: str, project_id: str, document_type: str = None, sheet_name: str = None) -> bool:
        """Save extracted questions to the database and enqueue them for processing"""
        logger.info(f"save_questions_to_database called with {len(questions)} questions")
        logger.info(f"Sample question data: {questions[0] if questions else 'No questions'}")
        
        db = next(get_db())
        try:
            saved_questions = []
            for i, question_data in enumerate(questions):
                logger.info(f"Processing question {i+1}: {question_data.get('question', 'NO QUESTION TEXT')[:100]}...")
                question = Question(
                    tenant_id=tenant_id,
                    deal_id=deal_id,
                    document_id=document_id,
                    question_text=question_data.get('question', ''),
                    original_text=question_data.get('original_text'),
                    question_type=question_data.get('type', 'question'),
                    extraction_confidence=question_data.get('extraction_confidence', question_data.get('confidence', 0.0)),
                    question_order=question_data.get('order', 0),
                    processing_status='pending',
                    # Excel-specific fields
                    answer_cell_reference=question_data.get('answer_cell'),
                    cell_confidence=question_data.get('cell_confidence'),
                    sheet_name=sheet_name,
                    document_type=document_type
                )
                db.add(question)
                saved_questions.append(question)
            
            logger.info(f"About to commit {len(saved_questions)} questions to database")
            db.commit()
            logger.info(f"Successfully committed questions to database")
            
            # Enqueue each question for individual processing
            for question in saved_questions:
                db.refresh(question)  # Get the ID after commit
                try:
                    queue_service.enqueue_question_processing(
                        question_id=str(question.id),
                        tenant_id=tenant_id,
                        project_id=project_id,
                        deal_id=deal_id
                    )
                    logger.info(f"Enqueued question {question.id} for processing")
                except Exception as e:
                    logger.error(f"Failed to enqueue question {question.id}: {e}")
            
            logger.info(f"Saved and enqueued {len(questions)} questions for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving questions to database: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def process_document_for_questions(self, document_id: str, text: str, excel_data: Dict = None) -> bool:
        """Main method to extract questions from a document and save them"""
        db = next(get_db())
        try:
            # Get document details
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document or not document.deal_id:
                logger.error(f"Document {document_id} not found or not associated with a deal")
                return False
            
            # Get deal details to get project_id
            deal = db.query(Deal).filter(Deal.id == document.deal_id).first()
            if not deal:
                logger.error(f"Deal {document.deal_id} not found")
                return False
            
            # Determine document type
            document_type = "text"  # default
            sheet_name = None
            
            if document.file_path:
                try:
                    mime_type = magic.from_file(document.file_path, mime=True)
                    if mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                   'application/vnd.ms-excel']:
                        document_type = "excel"
                    elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                      'application/msword']:
                        document_type = "word"
                    elif mime_type == 'application/pdf':
                        document_type = "pdf"
                except Exception as e:
                    logger.warning(f"Could not determine document type for {document.file_path}: {e}")
            
            # Extract questions based on document type
            logger.info(f"Document type: {document_type}, excel_data present: {excel_data is not None}")
            
            if document_type == "excel" and excel_data:
                logger.info(f"Using two-step Excel extraction for document {document_id}")
                
                # Step 1: Extract questions only
                extracted_questions = self.extract_questions_from_excel(excel_data)
                logger.info(f"Step 1: Excel question extraction returned {len(extracted_questions)} questions")
                
                # Deduplicate questions
                if extracted_questions:
                    extracted_questions = self.deduplicate_questions(extracted_questions)
                    logger.info(f"After deduplication: {len(extracted_questions)} unique questions")
                
                if extracted_questions:
                    # Step 2: Identify answer cell locations
                    logger.info(f"Step 2: Identifying answer cells for {len(extracted_questions)} questions")
                    cell_predictions = self.identify_answer_cells(excel_data, extracted_questions)
                    logger.info(f"Step 2: Answer cell identification returned {len(cell_predictions)} predictions")
                    
                    # Merge question data with cell predictions
                    question_to_cell = {}
                    for prediction in cell_predictions:
                        question_to_cell[prediction['question_text']] = {
                            'answer_cell': prediction['answer_cell'],
                            'cell_confidence': prediction['cell_confidence'],
                            'reasoning': prediction.get('reasoning', '')
                        }
                    
                    # Add cell information to questions
                    for question in extracted_questions:
                        cell_info = question_to_cell.get(question['question'])
                        if cell_info:
                            question['answer_cell'] = cell_info['answer_cell']
                            question['cell_confidence'] = cell_info['cell_confidence']
                            question['reasoning'] = cell_info['reasoning']
                        else:
                            # No cell prediction found
                            question['answer_cell'] = None
                            question['cell_confidence'] = None
                            question['reasoning'] = None
                            logger.warning(f"No cell prediction found for question: {question['question'][:50]}...")
                
                sheet_name = excel_data.get('sheet_name')
            else:
                logger.info(f"Using text extraction for document {document_id}")
                extracted_questions = self.extract_questions_from_text(text)
                logger.info(f"Text extraction returned {len(extracted_questions)} questions")
                
                # Deduplicate questions
                if extracted_questions:
                    extracted_questions = self.deduplicate_questions(extracted_questions)
                    logger.info(f"After deduplication: {len(extracted_questions)} unique questions")
                
                sheet_name = None
            
            if not extracted_questions:
                logger.info(f"No questions found in document {document_id}")
                return True  # Not an error, just no questions
            
            # Save questions to database and enqueue for processing
            success = self.save_questions_to_database(
                extracted_questions, 
                document_id, 
                str(document.deal_id), 
                str(document.tenant_id),
                str(deal.project_id),
                document_type=document_type,
                sheet_name=sheet_name
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing document {document_id} for questions: {e}")
            return False
        finally:
            db.close()

# Create singleton instance
question_extraction_service = QuestionExtractionService()