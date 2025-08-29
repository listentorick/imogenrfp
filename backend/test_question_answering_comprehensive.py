#!/usr/bin/env python3
"""
Comprehensive tests for QuestionAnsweringService

These tests cover the current LLM-based architecture:
1. Semantic search with ChromaDB integration
2. Structured answer generation with LLM
3. Question status updates and audit trail creation
4. Complete question processing workflow
5. Error handling and edge cases
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from question_answering_service import QuestionAnsweringService
import requests


class TestQuestionAnsweringService:
    
    @pytest.fixture
    def service(self):
        """Create QuestionAnsweringService instance for testing"""
        return QuestionAnsweringService(ollama_url="http://test-ollama:11434/api/generate")
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample ChromaDB search results"""
        return [
            {
                'content': 'Our company has 500+ employees and 15 years of experience in cloud solutions.',
                'distance': 0.2,
                'metadata': {
                    'document_id': 'doc-1',
                    'filename': 'company-overview.pdf',
                    'chunk_index': 1
                }
            },
            {
                'content': 'We provide 24/7 technical support with average response time of 2 hours.',
                'distance': 0.3,
                'metadata': {
                    'document_id': 'doc-2', 
                    'filename': 'service-details.docx',
                    'chunk_index': 0
                }
            }
        ]
    
    @pytest.fixture
    def sample_structured_response(self):
        """Sample LLM structured response"""
        return {
            "answer": "Based on the available documents, our company has 500+ employees and 15 years of experience in cloud solutions. We provide 24/7 technical support with average response time of 2 hours.",
            "status": "answered"
        }

    def test_perform_semantic_search_success(self, service, sample_search_results):
        """Test successful semantic search with ChromaDB"""
        with patch.object(service.chroma_service, 'search_project_documents', return_value=sample_search_results):
            results = service.perform_semantic_search("What is your company size?", "project-123")
            
            assert len(results) == 2
            assert results[0]['content'] == 'Our company has 500+ employees and 15 years of experience in cloud solutions.'
            assert results[0]['relevance_score'] == 80.0  # (1 - 0.2) * 100
            assert results[0]['document_id'] == 'doc-1'
            assert results[0]['filename'] == 'company-overview.pdf'
            assert results[1]['relevance_score'] == 70.0  # (1 - 0.3) * 100

    def test_perform_semantic_search_no_results(self, service):
        """Test semantic search with no results found"""
        with patch.object(service.chroma_service, 'search_project_documents', return_value=[]):
            results = service.perform_semantic_search("What is your company size?", "project-123")
            assert results == []

    def test_perform_semantic_search_exception(self, service):
        """Test semantic search with ChromaDB exception"""
        with patch.object(service.chroma_service, 'search_project_documents', side_effect=Exception("ChromaDB error")):
            results = service.perform_semantic_search("What is your company size?", "project-123")
            assert results == []

    def test_generate_answer_with_context_success(self, service, sample_structured_response):
        """Test successful answer generation with structured LLM response"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": json.dumps(sample_structured_response)}
        mock_response.raise_for_status.return_value = None
        
        context_chunks = [
            "Our company has 500+ employees and 15 years of experience.",
            "We provide 24/7 technical support with 2-hour response time."
        ]
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = service.generate_answer_with_context("What is your company size?", context_chunks)
            
            # Verify API call structure
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == 'qwen3:4b'
            assert 'temperature' in call_args[1]['json']['options']
            assert 'format' in call_args[1]['json']  # Structured output schema
            
            # Verify response parsing
            assert result['answer'] == sample_structured_response['answer']
            assert result['status'] == 'answered'

    def test_generate_answer_with_no_context(self, service):
        """Test answer generation with empty context"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps({"answer": "No relevant context found.", "status": "notAnswered"})
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = service.generate_answer_with_context("What is your company size?", [])
            assert result['status'] == 'notAnswered'

    def test_generate_answer_json_parse_error(self, service):
        """Test answer generation with invalid JSON response"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "invalid json response"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = service.generate_answer_with_context("What is your company size?", ["context"])
            assert result is None

    def test_generate_answer_request_exception(self, service):
        """Test answer generation with network error"""
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Network error")):
            result = service.generate_answer_with_context("What is your company size?", ["context"])
            assert result is None

    def test_generate_answer_empty_response(self, service):
        """Test answer generation with empty response from LLM"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": ""}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = service.generate_answer_with_context("What is your company size?", ["context"])
            assert result is None


    def test_extract_reasoning_success(self, service):
        """Test reasoning extraction from <think> tags"""
        answer = "<think>This question requires analysis of company size data</think>We have 500+ employees."
        reasoning = service._extract_reasoning(answer)
        assert reasoning == "This question requires analysis of company size data"

    def test_extract_reasoning_no_tags(self, service):
        """Test reasoning extraction with no <think> tags"""
        answer = "We have 500+ employees."
        reasoning = service._extract_reasoning(answer)
        assert reasoning is None

    def test_clean_answer_removes_thinking_tags(self, service):
        """Test answer cleaning removes <think> tags"""
        answer = "<think>Analysis needed</think>We have 500+ employees.<think>Good answer</think>"
        cleaned = service._clean_answer(answer)
        assert cleaned == "We have 500+ employees."

    @patch('question_answering_service.get_db')
    def test_update_question_status_answered(self, mock_get_db, service):
        """Test updating question status with answered response"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_question = Mock()
        mock_question.id = "question-123"
        mock_question.tenant_id = "tenant-1"
        mock_question.answer_text = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        service.update_question_status(
            question_id="question-123",
            status="processed",
            answer="<think>Analysis</think>We have 500+ employees.",
            structured_status="answered",
            relevance_score=85.5,
            sources=["doc-1", "doc-2"],
            source_filenames=["company.pdf", "details.docx"]
        )
        
        # Verify question updates
        assert mock_question.processing_status == "processed"
        assert mock_question.answer_text == "We have 500+ employees."  # <think> removed
        assert mock_question.reasoning == "Analysis"
        assert mock_question.answer_status == "answered"
        assert mock_question.answer_relevance_score == 85.5
        assert mock_question.answer_sources == ["doc-1", "doc-2"]
        assert mock_question.answer_source_filenames == ["company.pdf", "details.docx"]
        
        # Verify audit record creation
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('question_answering_service.get_db')
    def test_update_question_status_not_answered(self, mock_get_db, service):
        """Test updating question status with not answered response"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_question = Mock()
        mock_question.id = "question-123"
        mock_question.tenant_id = "tenant-1"
        mock_question.answer_text = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        service.update_question_status(
            question_id="question-123",
            status="processed",
            answer="Cannot find sufficient information.",
            structured_status="notAnswered"
        )
        
        assert mock_question.processing_status == "processed"
        assert mock_question.answer_status == "notAnswered"
        mock_db.add.assert_called_once()  # Audit record still created
        mock_db.commit.assert_called_once()

    @patch('question_answering_service.get_db')
    def test_update_question_status_question_not_found(self, mock_get_db, service):
        """Test updating status when question doesn't exist"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service.update_question_status("nonexistent-question", "processed", answer="Test answer")
        
        # Should not crash, just log error
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch('question_answering_service.get_db')
    def test_process_question_complete_workflow(self, mock_get_db, service, sample_search_results, sample_structured_response):
        """Test complete question processing workflow"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_question = Mock()
        mock_question.id = "question-123"
        mock_question.question_text = "What is your company size?"
        mock_question.tenant_id = "tenant-1"
        mock_question.answer_text = ""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        # Mock semantic search
        with patch.object(service.chroma_service, 'search_project_documents', return_value=sample_search_results):
            # Mock LLM response
            mock_llm_response = Mock()
            mock_llm_response.json.return_value = {"response": json.dumps(sample_structured_response)}
            mock_llm_response.raise_for_status.return_value = None
            
            with patch('requests.post', return_value=mock_llm_response):
                # Mock update_question_status to avoid recursive mocking
                with patch.object(service, 'update_question_status') as mock_update:
                    job_data = {
                        'question_id': 'question-123',
                        'tenant_id': 'tenant-1',
                        'project_id': 'project-1',
                        'deal_id': 'deal-1'
                    }
                    
                    service.process_question(job_data)
                    
                    # Verify the workflow steps
                    assert mock_update.call_count == 2  # processing, then processed
                    
                    # Check processing status call
                    processing_call = mock_update.call_args_list[0]
                    assert processing_call[0][0] == 'question-123'
                    assert processing_call[0][1] == 'processing'
                    
                    # Check final processed call with answer
                    processed_call = mock_update.call_args_list[1]
                    assert processed_call[0][0] == 'question-123'
                    assert processed_call[0][1] == 'processed'
                    assert processed_call[1]['structured_status'] == 'answered'
                    assert processed_call[1]['relevance_score'] == 75.0  # Average of 80 and 70
                    assert processed_call[1]['sources'] == ['doc-1', 'doc-2']
                    assert processed_call[1]['source_filenames'] == ['company-overview.pdf', 'service-details.docx']

    @patch('question_answering_service.get_db')
    def test_process_question_not_answered_workflow(self, mock_get_db, service):
        """Test question processing workflow when LLM returns notAnswered"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_question = Mock()
        mock_question.id = "question-123"
        mock_question.question_text = "What is your proprietary algorithm?"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_question
        
        # Mock semantic search with no results
        with patch.object(service.chroma_service, 'search_project_documents', return_value=[]):
            # Mock LLM response indicating no answer
            mock_llm_response = Mock()
            mock_llm_response.json.return_value = {
                "response": json.dumps({"answer": "Cannot find relevant information.", "status": "notAnswered"})
            }
            mock_llm_response.raise_for_status.return_value = None
            
            with patch('requests.post', return_value=mock_llm_response):
                with patch.object(service, 'update_question_status') as mock_update:
                    job_data = {
                        'question_id': 'question-123',
                        'tenant_id': 'tenant-1',
                        'project_id': 'project-1',
                        'deal_id': 'deal-1'
                    }
                    
                    service.process_question(job_data)
                    
                    # Verify final call has empty answer and no sources for notAnswered
                    processed_call = mock_update.call_args_list[1]
                    assert processed_call[1]['answer'] == ""  # Empty for notAnswered
                    assert processed_call[1]['structured_status'] == 'notAnswered'
                    assert processed_call[1]['sources'] is None
                    assert processed_call[1]['source_filenames'] is None

    @patch('question_answering_service.get_db')
    def test_process_question_error_handling(self, mock_get_db, service):
        """Test question processing error handling"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None  # Question not found
        
        with patch.object(service, 'update_question_status') as mock_update:
            job_data = {
                'question_id': 'nonexistent-question',
                'tenant_id': 'tenant-1',
                'project_id': 'project-1',
                'deal_id': 'deal-1'
            }
            
            service.process_question(job_data)
            
            # Should set status to processing, then error
            assert mock_update.call_count == 2
            error_call = mock_update.call_args_list[1]
            assert error_call[0][1] == 'error'
            assert error_call[1]['error_message'] is not None

    def test_structured_output_schema_validation(self, service):
        """Test that LLM is called with correct structured output schema"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps({"answer": "Test answer", "status": "answered"})
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            service.generate_answer_with_context("Test question?", ["Test context"])
            
            call_args = mock_post.call_args
            schema = call_args[1]['json']['format']
            
            # Verify schema structure
            assert schema['type'] == 'object'
            assert 'answer' in schema['properties']
            assert 'status' in schema['properties']
            assert schema['properties']['status']['enum'] == ["answered", "partiallyAnswered", "notAnswered"]
            assert schema['required'] == ["answer", "status"]

    def test_relevance_score_calculation(self, service):
        """Test relevance score calculation from ChromaDB distances"""
        search_results = [
            {'content': 'Content 1', 'distance': 0.1, 'metadata': {}},
            {'content': 'Content 2', 'distance': 0.4, 'metadata': {}},
            {'content': 'Content 3', 'distance': 0.8, 'metadata': {}}
        ]
        
        with patch.object(service.chroma_service, 'search_project_documents', return_value=search_results):
            results = service.perform_semantic_search("Test question", "project-1")
            
            # Verify relevance score calculations: (1 - distance) * 100
            assert abs(results[0]['relevance_score'] - 90.0) < 0.01  # (1 - 0.1) * 100
            assert abs(results[1]['relevance_score'] - 60.0) < 0.01  # (1 - 0.4) * 100
            assert abs(results[2]['relevance_score'] - 20.0) < 0.01  # (1 - 0.8) * 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])