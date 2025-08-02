import pytest
from unittest.mock import Mock, patch, MagicMock
from question_answering_service import QuestionAnsweringService
from models import Question


class TestQuestionAnsweringService:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = QuestionAnsweringService()
    
    def test_answer_text_empty_when_status_notAnswered(self):
        """Test that answer_text is empty when determine_answer_status returns 'notAnswered'"""
        question_id = "test-question-id"
        
        # Create a mock question object
        mock_question = Mock(spec=Question)
        mock_question.id = question_id
        mock_question.answer_text = None
        mock_question.answer_status = None
        mock_question.processing_status = None
        mock_question.reasoning = None
        mock_question.processing_error = None
        
        # Mock the database session and query
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        # Test with an answer that should be classified as 'notAnswered'
        unanswered_response = "Based on the available documents, I cannot find sufficient information to answer this question."
        
        with patch('question_answering_service.get_db') as mock_get_db:
            mock_get_db.return_value = iter([mock_db])
            
            # Call the method
            self.service.update_question_status(
                question_id=question_id,
                status='processed',
                answer=unanswered_response
            )
            
            # Verify that when answer_status is 'notAnswered', answer_text should be empty
            assert mock_question.answer_status == 'notAnswered'
            assert mock_question.answer_text == "", f"Expected empty answer_text when status is notAnswered, but got: '{mock_question.answer_text}'"
    
    def test_determine_answer_status_notAnswered_cases(self):
        """Test _determine_answer_status method for various notAnswered cases"""
        test_cases = [
            "Based on the available documents, I cannot find sufficient information to answer this question.",
            "I cannot find relevant information in the provided documents.",
            "Not enough information is available to answer this question.",
            "The information is not available in the documents.",
            "Cannot determine the answer from the provided context."
        ]
        
        for test_answer in test_cases:
            status = self.service._determine_answer_status(test_answer)
            assert status == 'notAnswered', f"Expected 'notAnswered' for answer: {test_answer}"
    
    def test_determine_answer_status_answered_cases(self):
        """Test _determine_answer_status method for answered cases"""
        test_cases = [
            "The project timeline is 6 months based on the requirements document.",
            "According to the specifications, the system will support 1000 concurrent users.",
            "The budget allocation for this project is $500,000 as outlined in the proposal."
        ]
        
        for test_answer in test_cases:
            status = self.service._determine_answer_status(test_answer)
            assert status == 'answered', f"Expected 'answered' for answer: {test_answer}"