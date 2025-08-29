#!/usr/bin/env python3
"""
Comprehensive tests for DocumentProcessor class

These tests cover:
1. Text extraction from various file formats (PDF, DOCX, Excel, text)
2. Excel structured data extraction with cell references
3. Vector database storage integration
4. Document status updates and WebSocket notifications
5. Complete document processing workflow
6. Error handling for file processing and storage
7. Different document types (project vs deal documents)
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import json
import PyPDF2

from document_processor import DocumentProcessor


class TestDocumentProcessor:
    
    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance for testing"""
        with patch('document_processor.chroma_service') as mock_chroma:
            processor = DocumentProcessor()
            processor.chroma_service = mock_chroma
            return processor
    
    @pytest.fixture
    def temp_text_file(self):
        """Create a temporary text file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is a test document.\nIt contains multiple lines.\nEnd of test content.")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def mock_pdf_file(self):
        """Mock PDF file data"""
        return {
            'path': '/test/document.pdf',
            'content': 'This is extracted PDF content.\nSecond page content.',
            'mime_type': 'application/pdf'
        }
    
    @pytest.fixture
    def mock_excel_data(self):
        """Mock Excel structured data"""
        return {
            'text_content': 'Cell A1: Question 1\nCell B1: Answer 1\nCell A2: Question 2\n',
            'cells_data': [
                {'cell_reference': 'A1', 'value': 'Question 1', 'row': 1, 'column': 1},
                {'cell_reference': 'B1', 'value': 'Answer 1', 'row': 1, 'column': 2},
                {'cell_reference': 'A2', 'value': 'Question 2', 'row': 2, 'column': 1}
            ],
            'sheet_name': 'Sheet1',
            'total_cells': 3
        }
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for document processing"""
        return {
            'document_id': 'doc-123',
            'file_path': '/test/document.pdf',
            'tenant_id': 'tenant-1',
            'project_id': 'project-1',
            'deal_id': None  # Project document by default
        }

    def test_init_creates_text_splitter(self, processor):
        """Test DocumentProcessor initialization"""
        assert processor.text_splitter is not None
        assert processor.text_splitter._chunk_size == 1000
        assert processor.text_splitter._chunk_overlap == 200

    def test_extract_text_from_text_file(self, processor, temp_text_file):
        """Test text extraction from plain text files"""
        with patch('document_processor.magic.from_file', return_value='text/plain'):
            text = processor.extract_text_from_file(temp_text_file)
            
            assert "This is a test document." in text
            assert "multiple lines" in text
            assert "End of test content." in text

    def test_extract_text_from_pdf_success(self, processor, mock_pdf_file):
        """Test successful PDF text extraction"""
        # Mock PDF reader
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "This is extracted PDF content.\n"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Second page content."
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        
        with patch('document_processor.magic.from_file', return_value='application/pdf'):
            with patch('builtins.open', mock_open()):
                with patch('document_processor.PyPDF2.PdfReader', return_value=mock_reader):
                    text = processor.extract_text_from_file(mock_pdf_file['path'])
                    
                    assert "This is extracted PDF content." in text
                    assert "Second page content." in text

    def test_extract_text_from_pdf_error(self, processor):
        """Test PDF text extraction with error handling"""
        with patch('document_processor.magic.from_file', return_value='application/pdf'):
            with patch('builtins.open', mock_open()):
                with patch('document_processor.PyPDF2.PdfReader', side_effect=Exception("PDF error")):
                    text = processor.extract_text_from_file('/test/bad.pdf')
                    assert text == ""

    def test_extract_text_from_docx_success(self, processor):
        """Test successful DOCX text extraction"""
        # Mock DOCX document
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "First paragraph text"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Second paragraph text"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        
        with patch('document_processor.magic.from_file', return_value='application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            with patch('document_processor.DocxDocument', return_value=mock_doc):
                text = processor.extract_text_from_file('/test/document.docx')
                
                assert text == "First paragraph text\nSecond paragraph text"

    def test_extract_text_from_docx_error(self, processor):
        """Test DOCX text extraction with error handling"""
        with patch('document_processor.magic.from_file', return_value='application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            with patch('document_processor.DocxDocument', side_effect=Exception("DOCX error")):
                text = processor.extract_text_from_file('/test/bad.docx')
                assert text == ""

    def test_extract_text_from_excel_returns_text_content(self, processor):
        """Test Excel text extraction returns text content from structured data"""
        mock_excel_data = {
            'text_content': 'Cell A1: Question 1\nCell B1: Answer 1\n',
            'cells_data': [],
            'sheet_name': 'Sheet1'
        }
        
        with patch('document_processor.magic.from_file', return_value='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            with patch.object(processor, '_extract_from_excel', return_value=mock_excel_data):
                text = processor.extract_text_from_file('/test/document.xlsx')
                
                assert text == 'Cell A1: Question 1\nCell B1: Answer 1\n'

    def test_extract_text_unsupported_file_type(self, processor):
        """Test extraction from unsupported file types"""
        with patch('document_processor.magic.from_file', return_value='application/unknown'):
            text = processor.extract_text_from_file('/test/unknown.file')
            assert text == ""

    def test_extract_text_file_error(self, processor):
        """Test extraction with file access error"""
        with patch('document_processor.magic.from_file', side_effect=Exception("File access error")):
            text = processor.extract_text_from_file('/nonexistent/file.txt')
            assert text == ""

    def test_extract_excel_data_success(self, processor, mock_excel_data):
        """Test successful Excel structured data extraction"""
        with patch('document_processor.magic.from_file', return_value='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            with patch.object(processor, '_extract_from_excel', return_value=mock_excel_data):
                data = processor.extract_excel_data('/test/document.xlsx')
                
                assert data == mock_excel_data
                assert len(data['cells_data']) == 3
                assert data['total_cells'] == 3
                assert data['sheet_name'] == 'Sheet1'

    def test_extract_excel_data_non_excel_file(self, processor):
        """Test Excel data extraction from non-Excel file"""
        with patch('document_processor.magic.from_file', return_value='text/plain'):
            data = processor.extract_excel_data('/test/document.txt')
            assert data == {}

    def test_extract_excel_data_error(self, processor):
        """Test Excel data extraction with error"""
        with patch('document_processor.magic.from_file', return_value='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
            with patch.object(processor, '_extract_from_excel', side_effect=Exception("Excel error")):
                data = processor.extract_excel_data('/test/bad.xlsx')
                assert data == {}

    def test_extract_from_excel_success(self, processor):
        """Test _extract_from_excel method with mock openpyxl"""
        # Mock openpyxl workbook and cells
        mock_cell1 = Mock()
        mock_cell1.value = "Question 1"
        mock_cell1.row = 1
        mock_cell1.column = 1
        
        mock_cell2 = Mock()
        mock_cell2.value = "Answer 1"
        mock_cell2.row = 1
        mock_cell2.column = 2
        
        mock_cell3 = Mock()
        mock_cell3.value = None  # Empty cell
        mock_cell3.row = 2
        mock_cell3.column = 1
        
        mock_row1 = [mock_cell1, mock_cell2]
        mock_row2 = [mock_cell3]
        
        mock_sheet = Mock()
        mock_sheet.iter_rows.return_value = [mock_row1, mock_row2]
        mock_sheet.title = "Sheet1"
        
        mock_workbook = Mock()
        mock_workbook.active = mock_sheet
        
        with patch('document_processor.openpyxl.load_workbook', return_value=mock_workbook):
            with patch('document_processor.get_column_letter', side_effect=['A', 'B']):
                data = processor._extract_from_excel('/test/document.xlsx')
                
                assert len(data['cells_data']) == 2  # Only non-empty cells
                assert data['cells_data'][0]['cell_reference'] == 'A1'
                assert data['cells_data'][0]['value'] == 'Question 1'
                assert data['cells_data'][1]['cell_reference'] == 'B1'
                assert data['cells_data'][1]['value'] == 'Answer 1'
                assert data['sheet_name'] == 'Sheet1'
                assert 'Cell A1: Question 1' in data['text_content']

    def test_extract_from_excel_error(self, processor):
        """Test _extract_from_excel with openpyxl error"""
        with patch('document_processor.openpyxl.load_workbook', side_effect=Exception("Workbook error")):
            data = processor._extract_from_excel('/test/bad.xlsx')
            
            assert data['text_content'] == ''
            assert data['cells_data'] == []
            assert data['sheet_name'] == ''
            assert data['total_cells'] == 0

    def test_extract_from_text_success(self, processor, temp_text_file):
        """Test _extract_from_text method"""
        text = processor._extract_from_text(temp_text_file)
        
        assert "This is a test document." in text
        assert "multiple lines" in text

    def test_extract_from_text_error(self, processor):
        """Test _extract_from_text with file error"""
        text = processor._extract_from_text('/nonexistent/file.txt')
        assert text == ""

    def test_store_in_vector_db_success(self, processor):
        """Test successful vector database storage"""
        test_text = "This is a long document that should be split into chunks. " * 50
        
        # Mock text splitter
        mock_chunks = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        processor.text_splitter.split_text = Mock(return_value=mock_chunks)
        
        # Mock chroma service
        processor.chroma_service.add_document_to_project.return_value = True
        
        result = processor.store_in_vector_db(
            project_id="project-1",
            document_id="doc-123",
            text=test_text,
            metadata={"filename": "test.pdf"}
        )
        
        assert result is True
        processor.text_splitter.split_text.assert_called_once_with(test_text)
        processor.chroma_service.add_document_to_project.assert_called_once_with(
            project_id="project-1",
            document_id="doc-123",
            text_chunks=mock_chunks,
            metadata={"filename": "test.pdf"}
        )

    def test_store_in_vector_db_failure(self, processor):
        """Test vector database storage failure"""
        processor.text_splitter.split_text = Mock(return_value=["Chunk 1"])
        processor.chroma_service.add_document_to_project.return_value = False
        
        result = processor.store_in_vector_db(
            project_id="project-1",
            document_id="doc-123", 
            text="Test text",
            metadata={}
        )
        
        assert result is False

    def test_store_in_vector_db_exception(self, processor):
        """Test vector database storage with exception"""
        processor.text_splitter.split_text = Mock(side_effect=Exception("Split error"))
        
        result = processor.store_in_vector_db(
            project_id="project-1",
            document_id="doc-123",
            text="Test text",
            metadata={}
        )
        
        assert result is False

    @patch('document_processor.get_db')
    def test_update_document_status_success(self, mock_get_db, processor):
        """Test successful document status update"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_document = Mock()
        mock_document.id = "doc-123"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        # Mock WebSocket manager
        with patch('document_processor.websocket_manager') as mock_websocket:
            processor.update_document_status(
                document_id="doc-123",
                status="processed",
                error_message=None,
                tenant_id="tenant-1"
            )
            
            assert mock_document.status == "processed"
            assert mock_document.processing_error is None
            mock_db.commit.assert_called_once()
            mock_websocket.publish_document_status_update.assert_called_once_with(
                tenant_id="tenant-1",
                document_id="doc-123",
                status="processed",
                error_message=None
            )

    @patch('document_processor.get_db')
    def test_update_document_status_with_error(self, mock_get_db, processor):
        """Test document status update with error message"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_document = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        with patch('document_processor.websocket_manager') as mock_websocket:
            processor.update_document_status(
                document_id="doc-123",
                status="error",
                error_message="Processing failed",
                tenant_id="tenant-1"
            )
            
            assert mock_document.status == "error"
            assert mock_document.processing_error == "Processing failed"

    @patch('document_processor.get_db')
    def test_update_document_status_document_not_found(self, mock_get_db, processor):
        """Test document status update when document not found"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Should not crash when document not found
        processor.update_document_status("nonexistent-doc", "processed")
        mock_db.commit.assert_not_called()

    @patch('document_processor.get_db')
    def test_update_document_status_database_error(self, mock_get_db, processor):
        """Test document status update with database error"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")
        
        # Should handle database errors gracefully
        processor.update_document_status("doc-123", "processed")
        mock_db.rollback.assert_called_once()

    @patch('document_processor.get_db')
    @patch('document_processor.magic.from_file')
    @patch('document_processor.question_extraction_service')
    def test_process_document_project_document_success(self, mock_question_service, mock_magic, mock_get_db, processor, sample_job_data):
        """Test successful processing of project document (stored in ChromaDB)"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_document = Mock()
        mock_document.original_filename = "test.pdf"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        # Mock file processing
        with patch.object(processor, 'extract_text_from_file', return_value="Extracted text content"):
            with patch.object(processor, 'update_document_status') as mock_update:
                with patch.object(processor, 'store_in_vector_db', return_value=True):
                    processor.chroma_service.create_project_collection.return_value = True
                    
                    processor.process_document(sample_job_data)
                    
                    # Verify workflow
                    assert mock_update.call_count == 2  # processing, then processed
                    
                    # Check processing status call
                    processing_call = mock_update.call_args_list[0]
                    assert processing_call[0] == ("doc-123", "processing")
                    assert processing_call[1]["tenant_id"] == "tenant-1"
                    
                    # Check final processed call
                    processed_call = mock_update.call_args_list[1]
                    assert processed_call[0] == ("doc-123", "processed")
                    
                    # Verify ChromaDB operations
                    processor.chroma_service.create_project_collection.assert_called_once_with(
                        "project-1", "Project project-1"
                    )

    @patch('document_processor.get_db')
    @patch('document_processor.magic.from_file')
    @patch('document_processor.question_extraction_service')
    def test_process_document_deal_document_with_questions(self, mock_question_service, mock_magic, mock_get_db, processor):
        """Test processing of deal document with question extraction"""
        # Deal document job data
        deal_job_data = {
            'document_id': 'doc-123',
            'file_path': '/test/document.xlsx',
            'tenant_id': 'tenant-1',
            'project_id': 'project-1',
            'deal_id': 'deal-1'  # Has deal_id - triggers question extraction
        }
        
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_document = Mock()
        mock_document.original_filename = "rfp.xlsx"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document
        
        # Mock Excel file detection
        mock_magic.return_value = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        mock_excel_data = {'total_cells': 10, 'cells_data': []}
        
        with patch.object(processor, 'extract_text_from_file', return_value="Excel content"):
            with patch.object(processor, 'extract_excel_data', return_value=mock_excel_data):
                with patch.object(processor, 'update_document_status') as mock_update:
                    mock_question_service.process_document_for_questions.return_value = True
                    
                    processor.process_document(deal_job_data)
                    
                    # Verify question extraction was called
                    mock_question_service.process_document_for_questions.assert_called_once_with(
                        'doc-123', 'Excel content', mock_excel_data
                    )
                    
                    # Verify no ChromaDB storage for deal documents
                    processor.chroma_service.create_project_collection.assert_not_called()

    @patch('document_processor.get_db')
    def test_process_document_no_text_extracted(self, mock_get_db, processor, sample_job_data):
        """Test processing with no text content extracted"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        with patch.object(processor, 'extract_text_from_file', return_value="   "):  # Empty/whitespace only
            with patch.object(processor, 'update_document_status') as mock_update:
                processor.process_document(sample_job_data)
                
                # Should update to error status
                error_call = mock_update.call_args_list[-1]
                assert error_call[0][1] == 'error'
                assert "No text content extracted" in error_call[0][2]

    @patch('document_processor.get_db')
    def test_process_document_vector_storage_failure(self, mock_get_db, processor, sample_job_data):
        """Test processing with vector database storage failure"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        with patch.object(processor, 'extract_text_from_file', return_value="Valid text"):
            with patch.object(processor, 'store_in_vector_db', return_value=False):
                with patch.object(processor, 'update_document_status') as mock_update:
                    processor.chroma_service.create_project_collection.return_value = True
                    
                    processor.process_document(sample_job_data)
                    
                    # Should update to error status due to storage failure
                    error_call = mock_update.call_args_list[-1]
                    assert error_call[0][1] == 'error'
                    assert "Failed to store in vector database" in error_call[0][2]

    @patch('document_processor.get_db')
    def test_process_document_exception_handling(self, mock_get_db, processor, sample_job_data):
        """Test processing with general exception"""
        mock_db = Mock()
        mock_get_db.return_value.__next__.return_value = mock_db
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with patch.object(processor, 'update_document_status') as mock_update:
            processor.process_document(sample_job_data)
            
            # Should handle exception and update status to error
            assert mock_update.call_count >= 1
            final_call = mock_update.call_args_list[-1]
            assert final_call[0][1] == 'error'
            assert "Database connection failed" in final_call[0][2]


class TestDocumentProcessorIntegration:
    """Integration tests for complete document processing workflows"""
    
    @pytest.fixture
    def processor(self):
        with patch('document_processor.chroma_service') as mock_chroma:
            processor = DocumentProcessor()
            processor.chroma_service = mock_chroma
            return processor

    @patch('document_processor.queue_service')
    def test_run_document_processor_processes_job(self, mock_queue_service):
        """Test main worker loop processes jobs from queue"""
        # Mock queue to return one job then empty
        job_data = {
            'document_id': 'doc-123',
            'file_path': '/test/doc.pdf',
            'tenant_id': 'tenant-1',
            'project_id': 'project-1'
        }
        
        mock_queue_service.dequeue_document_processing.side_effect = [job_data, None]
        
        # Import and patch the processor
        from document_processor import run_document_processor
        
        with patch('document_processor.DocumentProcessor') as MockProcessor:
            mock_instance = MockProcessor.return_value
            
            # Mock the while loop to exit after 2 iterations
            with patch('document_processor.time.sleep', side_effect=KeyboardInterrupt):
                try:
                    run_document_processor()
                except KeyboardInterrupt:
                    pass
                
                # Verify job was processed
                mock_instance.process_document.assert_called_once_with(job_data)

    @patch('document_processor.queue_service')
    def test_run_document_processor_handles_exceptions(self, mock_queue_service):
        """Test worker loop handles processing exceptions"""
        mock_queue_service.dequeue_document_processing.side_effect = Exception("Queue error")
        
        from document_processor import run_document_processor
        
        # Mock sleep to raise KeyboardInterrupt after exception handling
        sleep_count = 0
        def mock_sleep(duration):
            nonlocal sleep_count
            sleep_count += 1
            if sleep_count >= 2:  # Exit after handling one exception
                raise KeyboardInterrupt
        
        with patch('document_processor.time.sleep', side_effect=mock_sleep):
            try:
                run_document_processor()
            except KeyboardInterrupt:
                pass
        
        # Should have attempted to sleep after error (error handling)
        assert sleep_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])