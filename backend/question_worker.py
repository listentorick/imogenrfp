#!/usr/bin/env python3
"""
Question Processing Worker

This worker processes individual questions by:
1. Performing semantic search against ChromaDB 
2. Finding relevant context from project documents
3. Using LLM to generate answers based on context
4. Updating the question with the generated answer
"""

import logging
import time
from question_answering_service import run_question_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Question Processing Worker...")
    run_question_processor()