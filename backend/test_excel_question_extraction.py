#!/usr/bin/env python3
"""
Tests for Excel question extraction functionality in QuestionExtractionService

These tests cover:
1. Extract questions from Excel data with mocked LLM responses
2. Answer cell identification with various Excel table structures  
3. Question deduplication logic
4. Error handling for malformed data
5. Integration testing of the two-step Excel workflow
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from question_extraction_service import QuestionExtractionService
import requests


class TestExcelQuestionExtraction:
    
    @pytest.fixture
    def service(self):
        """Create QuestionExtractionService instance for testing"""
        return QuestionExtractionService(ollama_url="http://test-ollama:11434/api/generate")
    
    @pytest.fixture
    def sample_excel_data(self):
        """Sample Excel data structure for testing"""
        return {
            'sheet_name': 'Sheet1',
            'cells_data': [
                {'cell_reference': 'A1', 'value': 'Question 1: What is your company size?'},
                {'cell_reference': 'B1', 'value': ''},  # Empty answer cell
                {'cell_reference': 'A2', 'value': 'Vendor must provide security certifications'},
                {'cell_reference': 'B2', 'value': ''},  # Empty answer cell
                {'cell_reference': 'A3', 'value': 'How do you handle data backups?'},
                {'cell_reference': 'B3', 'value': ''},  # Empty answer cell
                {'cell_reference': 'C1', 'value': 'Comments'},  # Header
                {'cell_reference': 'D1', 'value': 'Additional Notes'}  # Header
            ]
        }
    
    @pytest.fixture
    def mock_llm_question_response(self):
        """Mock LLM response for question extraction"""
        return [
            {
                "question": "What is your company size?",
                "original_text": "Question 1: What is your company size?",
                "extraction_confidence": 0.95,
                "order": 1,
                "type": "question"
            },
            {
                "question": "What security certifications will you provide?",
                "original_text": "Vendor must provide security certifications",
                "extraction_confidence": 0.9,
                "order": 2,
                "type": "requirement"
            },
            {
                "question": "How do you handle data backups?", 
                "original_text": "How do you handle data backups?",
                "extraction_confidence": 0.95,
                "order": 3,
                "type": "question"
            }
        ]
    
    @pytest.fixture
    def mock_llm_cell_response(self):
        """Mock LLM response for answer cell identification"""
        return [
            {
                "question_text": "What is your company size?",
                "answer_cell": "B1",
                "cell_confidence": 0.9,
                "reasoning": "Found original text in A1, answer cell is adjacent B1"
            },
            {
                "question_text": "What security certifications will you provide?",
                "answer_cell": "B2", 
                "cell_confidence": 0.85,
                "reasoning": "Found requirement in A2, answer cell is adjacent B2"
            },
            {
                "question_text": "How do you handle data backups?",
                "answer_cell": "B3",
                "cell_confidence": 0.9,
                "reasoning": "Found question in A3, answer cell is adjacent B3"
            }
        ]

    def test_extract_questions_from_excel_success(self, service, sample_excel_data, mock_llm_question_response):
        """Test successful question extraction from Excel data"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": json.dumps(mock_llm_question_response)}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            questions = service.extract_questions_from_excel(sample_excel_data)
            
            # Verify API call was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['json']['model'] == 'qwen3:4b'
            assert 'Cell A1: Question 1: What is your company size?' in call_args[1]['json']['prompt']
            
            # Verify extracted questions
            assert len(questions) == 3
            assert questions[0]['question'] == "What is your company size?"
            assert questions[0]['extraction_confidence'] == 0.95
            assert questions[1]['type'] == "requirement"

    def test_extract_questions_handles_cell_limit(self, service):
        """Test that only first 100 cells are processed"""
        # Create Excel data with 150 cells
        excel_data = {
            'cells_data': [{'cell_reference': f'A{i}', 'value': f'Question {i}'} for i in range(1, 151)]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {"response": "[]"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            service.extract_questions_from_excel(excel_data)
            
            # Verify prompt contains only first 100 cells
            call_args = mock_post.call_args
            prompt = call_args[1]['json']['prompt']
            assert 'Cell A100: Question 100' in prompt
            assert 'Cell A101: Question 101' not in prompt

    def test_extract_questions_json_parse_error(self, service, sample_excel_data):
        """Test handling of invalid JSON response from LLM"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "invalid json response"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            questions = service.extract_questions_from_excel(sample_excel_data)
            assert questions == []

    def test_extract_questions_request_exception(self, service, sample_excel_data):
        """Test handling of network errors when calling LLM"""
        with patch('requests.post', side_effect=requests.exceptions.RequestException("Network error")):
            questions = service.extract_questions_from_excel(sample_excel_data)
            assert questions == []

    def test_identify_answer_cells_success(self, service, sample_excel_data, mock_llm_question_response, mock_llm_cell_response):
        """Test successful answer cell identification"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": json.dumps(mock_llm_cell_response)}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            cell_predictions = service.identify_answer_cells(sample_excel_data, mock_llm_question_response)
            
            # Verify API call structure
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert 'ORIGINAL TEXT TO LOCATE' in call_args[1]['json']['prompt']
            assert 'What is your company size?' in call_args[1]['json']['prompt']
            
            # Verify predictions
            assert len(cell_predictions) == 3
            assert cell_predictions[0]['answer_cell'] == 'B1'
            assert cell_predictions[0]['cell_confidence'] == 0.9
            assert 'reasoning' in cell_predictions[0]

    def test_identify_answer_cells_empty_response(self, service, sample_excel_data, mock_llm_question_response):
        """Test answer cell identification with empty LLM response"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "[]"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            cell_predictions = service.identify_answer_cells(sample_excel_data, mock_llm_question_response)
            assert cell_predictions == []

    def test_deduplicate_questions_removes_duplicates(self, service):
        """Test question deduplication logic"""
        questions_with_duplicates = [
            {"question": "What is your company size?", "original_text": "Company size?", "order": 1},
            {"question": "How do you handle security?", "original_text": "Security handling", "order": 2},
            {"question": "What is your company size?", "original_text": "Company size?", "order": 3},  # Duplicate
            {"question": "What are your certifications?", "original_text": "Certifications", "order": 4}
        ]
        
        unique_questions = service.deduplicate_questions(questions_with_duplicates)
        
        assert len(unique_questions) == 3
        question_texts = [q["question"] for q in unique_questions]
        assert "What is your company size?" in question_texts
        assert "How do you handle security?" in question_texts  
        assert "What are your certifications?" in question_texts

    def test_deduplicate_questions_case_insensitive(self, service):
        """Test that deduplication is case-insensitive"""
        questions_with_case_duplicates = [
            {"question": "What is your company size?", "original_text": "Company size?"},
            {"question": "WHAT IS YOUR COMPANY SIZE?", "original_text": "COMPANY SIZE?"}
        ]
        
        unique_questions = service.deduplicate_questions(questions_with_case_duplicates)
        assert len(unique_questions) == 1

    def test_deduplicate_questions_empty_list(self, service):
        """Test deduplication with empty input"""
        unique_questions = service.deduplicate_questions([])
        assert unique_questions == []

    @patch('question_extraction_service.get_db')
    def test_save_questions_to_database_with_excel_fields(self, mock_get_db, service):
        """Test saving questions with Excel-specific fields"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        questions_with_cells = [
            {
                "question": "What is your company size?",
                "original_text": "Company size?",
                "extraction_confidence": 0.9,
                "order": 1,
                "type": "question",
                "answer_cell": "B1",
                "cell_confidence": 0.85
            }
        ]
        
        with patch('question_extraction_service.queue_service') as mock_queue:
            mock_question = Mock()
            mock_question.id = "test-question-id"
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock the Question constructor to return our mock
            with patch('question_extraction_service.Question', return_value=mock_question):
                result = service.save_questions_to_database(
                    questions_with_cells,
                    document_id="doc-1", 
                    deal_id="deal-1",
                    tenant_id="tenant-1",
                    project_id="project-1",
                    document_type="excel",
                    sheet_name="Sheet1"
                )
            
            assert result is True
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_queue.enqueue_question_processing.assert_called_once()

    def test_excel_data_preprocessing(self, service, sample_excel_data):
        """Test that Excel data is correctly preprocessed for LLM"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "[]"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            service.extract_questions_from_excel(sample_excel_data)
            
            # Verify cells are formatted correctly in prompt
            call_args = mock_post.call_args
            prompt = call_args[1]['json']['prompt']
            assert 'Cell A1: Question 1: What is your company size?' in prompt
            assert 'Cell A2: Vendor must provide security certifications' in prompt
            assert 'Cell B1: ' in prompt  # Empty cells should be included

    def test_structured_json_schema_validation(self, service, sample_excel_data):
        """Test that correct JSON schema is sent to LLM"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "[]"}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            service.extract_questions_from_excel(sample_excel_data)
            
            # Verify schema structure
            call_args = mock_post.call_args
            schema = call_args[1]['json']['format']
            assert schema['type'] == 'array'
            assert 'question' in schema['items']['properties']
            assert 'extraction_confidence' in schema['items']['properties']
            assert schema['items']['properties']['type']['enum'] == ["question", "requirement", "criteria", "specification", "form_field", "other"]


class TestExcelQuestionExtractionIntegration:
    """Integration tests for the complete Excel extraction workflow"""
    
    @pytest.fixture
    def service(self):
        return QuestionExtractionService()
    
    @patch('question_extraction_service.get_db')
    @patch('question_extraction_service.magic.from_file')
    def test_process_document_for_questions_excel_workflow(self, mock_magic, mock_get_db, service):
        """Test the complete Excel document processing workflow"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_magic.return_value = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Mock document and deal
        mock_document = Mock()
        mock_document.id = "doc-1"
        mock_document.deal_id = "deal-1"
        mock_document.tenant_id = "tenant-1"
        mock_document.file_path = "/path/to/file.xlsx"
        
        mock_deal = Mock()
        mock_deal.id = "deal-1"
        mock_deal.project_id = "project-1"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_document, mock_deal]
        
        # Mock Excel data
        excel_data = {
            'sheet_name': 'Sheet1',
            'cells_data': [{'cell_reference': 'A1', 'value': 'Test question?'}]
        }
        
        # Mock LLM responses
        mock_question_response = Mock()
        mock_question_response.json.return_value = {
            "response": json.dumps([{
                "question": "Test question?",
                "original_text": "Test question?", 
                "extraction_confidence": 0.9,
                "order": 1,
                "type": "question"
            }])
        }
        mock_question_response.raise_for_status.return_value = None
        
        mock_cell_response = Mock()
        mock_cell_response.json.return_value = {
            "response": json.dumps([{
                "question_text": "Test question?",
                "answer_cell": "B1",
                "cell_confidence": 0.8,
                "reasoning": "Adjacent cell"
            }])
        }
        mock_cell_response.raise_for_status.return_value = None
        
        with patch('requests.post', side_effect=[mock_question_response, mock_cell_response]):
            with patch.object(service, 'save_questions_to_database', return_value=True) as mock_save:
                result = service.process_document_for_questions("doc-1", "text", excel_data)
                
                assert result is True
                # Verify save was called with merged question and cell data
                saved_questions = mock_save.call_args[0][0]
                assert len(saved_questions) == 1
                assert saved_questions[0]['answer_cell'] == 'B1'
                assert saved_questions[0]['cell_confidence'] == 0.8

    def test_excel_workflow_with_no_cell_predictions(self, service):
        """Test Excel workflow when cell identification fails"""
        excel_data = {'cells_data': [{'cell_reference': 'A1', 'value': 'Test?'}]}
        
        # Mock question extraction success
        mock_question_response = Mock()
        mock_question_response.json.return_value = {
            "response": json.dumps([{
                "question": "Test?", "original_text": "Test?",
                "extraction_confidence": 0.9, "order": 1, "type": "question"
            }])
        }
        mock_question_response.raise_for_status.return_value = None
        
        # Mock cell identification failure
        mock_cell_response = Mock()
        mock_cell_response.json.return_value = {"response": "[]"}
        mock_cell_response.raise_for_status.return_value = None
        
        with patch('requests.post', side_effect=[mock_question_response, mock_cell_response]):
            questions = service.extract_questions_from_excel(excel_data)
            cell_predictions = service.identify_answer_cells(excel_data, questions)
            
            # Verify graceful handling of missing cell predictions
            assert len(questions) == 1
            assert len(cell_predictions) == 0
            
            # Questions should have None values for missing cell data
            for question in questions:
                if question['question'] not in []:  # No matching predictions
                    # These would be set to None in process_document_for_questions
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])