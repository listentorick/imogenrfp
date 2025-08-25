#!/usr/bin/env python3
"""
Test script to manually create an audit record and verify the process works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import engine, get_db
from models import Question, QuestionAnswerAudit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_audit_creation():
    """
    Test creating an audit record for an existing answered question.
    """
    db = next(get_db())
    
    try:
        # Find a question with an answer but no audit record
        question = db.query(Question).filter(
            Question.answer_text.isnot(None),
            Question.answer_text != "",
            Question.processing_status == 'processed',
            ~Question.id.in_(
                db.query(QuestionAnswerAudit.question_id).distinct()
            )
        ).first()
        
        if not question:
            logger.error("No questions found with answers but no audit records")
            return
            
        logger.info(f"Testing audit creation for question {question.id}")
        logger.info(f"Question answer: {question.answer_text[:100]}...")
        logger.info(f"Question status: {question.answer_status}")
        
        # Create test audit record
        audit = QuestionAnswerAudit(
            question_id=question.id,
            tenant_id=question.tenant_id,
            answer_text=question.answer_text,
            changed_by_user=None,  # System/AI generated
            change_source='ai_initial',
            change_type='ai_generate',
            ai_confidence_score=None,
            chromadb_relevance_score=question.answer_relevance_score,
            previous_answer_length=0  # This was the initial answer
        )
        
        db.add(audit)
        db.commit()
        logger.info(f"Successfully created audit record: {audit.id}")
        
        # Verify it was created
        audit_check = db.query(QuestionAnswerAudit).filter(
            QuestionAnswerAudit.question_id == question.id
        ).first()
        
        if audit_check:
            logger.info(f"Verification successful: Found audit record {audit_check.id} for question {question.id}")
        else:
            logger.error("Verification failed: Could not find created audit record")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting audit creation test...")
    test_audit_creation()
    logger.info("Test completed!")