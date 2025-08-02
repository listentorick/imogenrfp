#!/usr/bin/env python3
"""
Manual test runner to verify the current behavior of question_answering_service
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from question_answering_service import QuestionAnsweringService

def test_current_behavior():
    """Test the current behavior to confirm it fails as expected"""
    service = QuestionAnsweringService()
    
    # Test an answer that should be classified as 'notAnswered'
    unanswered_response = "Based on the available documents, I cannot find sufficient information to answer this question."
    
    # Test the _determine_answer_status method
    status = service._determine_answer_status(unanswered_response)
    print(f"Answer status determined as: {status}")
    
    # Test the _clean_answer method
    cleaned_answer = service._clean_answer(unanswered_response)
    print(f"Cleaned answer: '{cleaned_answer}'")
    print(f"Cleaned answer length: {len(cleaned_answer)}")
    
    # Simulate what happens in update_question_status
    if status == 'notAnswered':
        print("✓ Status correctly determined as 'notAnswered'")
        if cleaned_answer == "":
            print("✓ Test would PASS: answer_text is empty when status is notAnswered")
        else:
            print("✗ Test would FAIL: answer_text is not empty when status is notAnswered")
            print(f"  Expected: ''")
            print(f"  Actual: '{cleaned_answer}'")
    else:
        print(f"✗ Unexpected status: {status}")

if __name__ == "__main__":
    test_current_behavior()