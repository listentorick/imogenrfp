#!/usr/bin/env python3
"""
Backfill script to create audit records for existing AI-generated answers.

This script identifies questions that have answers but no audit records,
and creates appropriate audit records for them with 'ai_initial' source.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import engine, get_db
from models import Question, QuestionAnswerAudit
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill_audit_records():
    """
    Create audit records for questions that have answers but no audit history.
    """
    db = next(get_db())
    
    try:
        # Find questions with answers but no audit records
        questions_without_audit = db.query(Question).filter(
            Question.answer_text.isnot(None),
            Question.answer_text != "",
            ~Question.id.in_(
                db.query(QuestionAnswerAudit.question_id).distinct()
            )
        ).all()
        
        logger.info(f"Found {len(questions_without_audit)} questions with answers but no audit records")
        
        created_count = 0
        
        for question in questions_without_audit:
            try:
                # Create audit record for the existing answer
                audit = QuestionAnswerAudit(
                    question_id=question.id,
                    tenant_id=question.tenant_id,
                    answer_text=question.answer_text,
                    changed_by_user=None,  # System/AI generated
                    change_source='ai_initial',
                    change_type='ai_generate',
                    ai_confidence_score=None,
                    chromadb_relevance_score=question.answer_relevance_score,
                    previous_answer_length=0,  # This was the initial answer
                    created_at=question.updated_at or question.created_at or datetime.utcnow()
                )
                
                db.add(audit)
                created_count += 1
                
                if created_count % 50 == 0:
                    logger.info(f"Created {created_count} audit records so far...")
                    
            except Exception as e:
                logger.error(f"Error creating audit record for question {question.id}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        logger.info(f"Successfully created {created_count} audit records")
        
        # Verify the results
        total_questions_with_answers = db.query(Question).filter(
            Question.answer_text.isnot(None),
            Question.answer_text != ""
        ).count()
        
        total_audit_records = db.query(QuestionAnswerAudit).count()
        
        logger.info(f"Total questions with answers: {total_questions_with_answers}")
        logger.info(f"Total audit records: {total_audit_records}")
        
    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting audit records backfill...")
    backfill_audit_records()
    logger.info("Backfill completed!")