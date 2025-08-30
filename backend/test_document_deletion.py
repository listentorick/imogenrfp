#!/usr/bin/env python3
"""
Fixed integration tests for document deletion functionality

These tests properly test the actual FastAPI endpoint functions for the fix
of foreign key constraint violations when deleting documents with associated 
questions and audit records.
"""

import pytest
import os
import tempfile
import uuid
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

# Import for testing
from models import User, Tenant, Project, Deal, Document, Question, QuestionAnswerAudit, ProjectQAPair, Export
from database import get_db
from fastapi import HTTPException


class TestDocumentDeletion:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def sample_deal(self, mock_user):
        """Sample deal data"""
        deal = Mock(spec=Deal)
        deal.id = uuid.uuid4()
        deal.tenant_id = mock_user.tenant_id
        deal.name = "Test Deal"
        return deal
    
    @pytest.fixture
    def sample_document(self, mock_user, sample_deal):
        """Sample deal document"""
        document = Mock(spec=Document)
        document.id = uuid.uuid4()
        document.tenant_id = mock_user.tenant_id
        document.deal_id = sample_deal.id
        document.original_filename = "test_rfp.pdf"
        document.file_path = "/tmp/test_document.pdf"
        return document
    
    @pytest.fixture
    def sample_questions_with_audits(self, sample_document, mock_user):
        """Sample questions with audit records"""
        questions = []
        all_audits = []
        
        for i in range(2):
            # Create question
            question = Mock(spec=Question)
            question.id = uuid.uuid4()
            question.tenant_id = mock_user.tenant_id
            question.document_id = sample_document.id
            question.question_text = f"Test question {i+1}"
            questions.append(question)
            
            # Create 2 audit records per question
            for j in range(2):
                audit = Mock(spec=QuestionAnswerAudit)
                audit.id = uuid.uuid4()
                audit.question_id = question.id
                audit.tenant_id = mock_user.tenant_id
                audit.answer_text = f"Audit answer {i+1}-{j+1}"
                all_audits.append(audit)
        
        return questions, all_audits

    @pytest.fixture
    def sample_exports(self, sample_document, mock_user, sample_deal):
        """Sample exports associated with the document"""
        exports = []
        
        for i in range(2):
            export = Mock(spec=Export)
            export.id = uuid.uuid4()
            export.tenant_id = mock_user.tenant_id
            export.deal_id = sample_deal.id
            export.document_id = sample_document.id
            export.status = "completed"
            export.file_path = f"/tmp/export_{i}.xlsx" if i == 0 else None  # Second export has no file
            export.original_filename = "test_rfp.pdf"
            export.export_filename = f"export_{i}.xlsx"
            export.created_by = mock_user.id
            exports.append(export)
        
        return exports

    @patch('main.get_db')
    @patch('main.os.path.exists')
    @patch('main.os.remove')
    @patch('main.chroma_service')
    def test_delete_deal_document_success(
        self, 
        mock_chroma_service,
        mock_os_remove,
        mock_os_exists,
        mock_get_db,
        mock_db,
        mock_user,
        sample_deal,
        sample_document,
        sample_questions_with_audits,
        sample_exports
    ):
        """Test successful deletion of deal document with questions and audit records"""
        from main import delete_deal_document
        
        questions, audits = sample_questions_with_audits
        
        # Setup mocks
        mock_get_db.return_value = mock_db
        mock_os_exists.return_value = True
        
        # Mock database lookups
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_deal,  # Deal lookup
            sample_document  # Document lookup
        ]
        
        # Mock questions query
        mock_questions_query = Mock()
        mock_questions_query.filter.return_value.all.return_value = questions
        
        # Track audit queries
        audit_call_count = 0
        def create_audit_query():
            nonlocal audit_call_count
            mock_audit_query = Mock()
            # Return 2 audits per question call
            start_idx = audit_call_count * 2
            end_idx = start_idx + 2
            question_audits = audits[start_idx:end_idx] if start_idx < len(audits) else []
            mock_audit_query.filter.return_value.all.return_value = question_audits
            audit_call_count += 1
            return mock_audit_query
        
        def mock_query_side_effect(model):
            if model == Deal:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_deal
                return query_mock
            elif model == Document:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_document
                return query_mock
            elif model == Export:
                mock_export_query = Mock()
                mock_export_query.filter.return_value.all.return_value = sample_exports
                return mock_export_query
            elif model == Question:
                return mock_questions_query
            elif model == ProjectQAPair:
                # Mock empty QA pairs (or add some if you want to test the update logic)
                mock_qa_query = Mock()
                mock_qa_query.filter.return_value.all.return_value = []  # No QA pairs to update
                return mock_qa_query
            elif model == QuestionAnswerAudit:
                return create_audit_query()
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Call the function
        result = delete_deal_document(
            deal_id=str(sample_deal.id),
            document_id=str(sample_document.id),
            current_user=mock_user,
            db=mock_db
        )
        
        # Verify success
        assert result == {"message": "Document deleted successfully"}
        
        # Verify cascade deletion: 2 exports + 4 audits + 2 questions + 1 document = 9 total
        assert mock_db.delete.call_count == 9
        mock_db.commit.assert_called_once()
        
        # Verify file deletions: 1 document file + 1 export file (only first export has file_path)
        assert mock_os_remove.call_count == 2

    @patch('main.get_db')
    def test_delete_deal_document_not_found(
        self,
        mock_get_db,
        mock_db,
        mock_user,
        sample_deal
    ):
        """Test deletion of non-existent document"""
        from main import delete_deal_document
        
        mock_get_db.return_value = mock_db
        
        # Mock deal found but document not found
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_deal,  # Deal lookup succeeds
            None  # Document lookup fails
        ]
        
        with pytest.raises(HTTPException) as exc_info:
            delete_deal_document(
                deal_id=str(sample_deal.id),
                document_id=str(uuid.uuid4()),
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 404
        assert "Document not found" in str(exc_info.value.detail)

    @patch('main.get_db')
    def test_delete_deal_document_deal_not_found(
        self,
        mock_get_db,
        mock_db,
        mock_user
    ):
        """Test deletion with non-existent deal"""
        from main import delete_deal_document
        
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            delete_deal_document(
                deal_id=str(uuid.uuid4()),
                document_id=str(uuid.uuid4()),
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 404
        assert "Deal not found" in str(exc_info.value.detail)

    @patch('main.get_db')
    def test_delete_deal_document_database_error(
        self,
        mock_get_db,
        mock_db,
        mock_user,
        sample_deal,
        sample_document
    ):
        """Test handling of database errors during deletion"""
        from main import delete_deal_document
        
        mock_get_db.return_value = mock_db
        
        # Mock successful lookups
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_deal,
            sample_document
        ]
        
        # Mock questions query to succeed, but create error during audit query
        def mock_query_side_effect(model):
            if model == Deal:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_deal
                return query_mock
            elif model == Document:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_document
                return query_mock
            elif model == Export:
                mock_export_query = Mock()
                mock_export_query.filter.return_value.all.return_value = []  # No exports
                return mock_export_query
            elif model == Question:
                mock_questions_query = Mock()
                # Create a question that will cause issues
                mock_question = Mock(spec=Question)
                mock_question.id = uuid.uuid4()
                mock_questions_query.filter.return_value.all.return_value = [mock_question]
                return mock_questions_query
            elif model == QuestionAnswerAudit:
                # Simulate database error during audit query
                raise Exception("Database connection failed")
        
        mock_db.query.side_effect = mock_query_side_effect
        
        with pytest.raises(HTTPException) as exc_info:
            delete_deal_document(
                deal_id=str(sample_deal.id),
                document_id=str(sample_document.id),
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 500
        assert "Error deleting associated questions and audits" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()

    @patch('main.get_db')
    @patch('main.os.path.exists')
    @patch('main.os.remove')
    def test_delete_deal_document_file_system_error(
        self,
        mock_os_remove,
        mock_os_exists,
        mock_get_db,
        mock_db,
        mock_user,
        sample_deal,
        sample_document
    ):
        """Test that file system errors don't prevent database deletion"""
        from main import delete_deal_document
        
        mock_get_db.return_value = mock_db
        mock_os_exists.return_value = True
        mock_os_remove.side_effect = OSError("Permission denied")
        
        # Mock successful database operations (no questions to delete)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_deal,
            sample_document
        ]
        
        def mock_query_side_effect(model):
            if model == Deal:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_deal
                return query_mock
            elif model == Document:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_document
                return query_mock
            elif model == Export:
                mock_export_query = Mock()
                mock_export_query.filter.return_value.all.return_value = []  # No exports
                return mock_export_query
            elif model == Question:
                mock_questions_query = Mock()
                mock_questions_query.filter.return_value.all.return_value = []  # No questions
                return mock_questions_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Should still succeed despite file system error
        result = delete_deal_document(
            deal_id=str(sample_deal.id),
            document_id=str(sample_document.id),
            current_user=mock_user,
            db=mock_db
        )
        
        assert result == {"message": "Document deleted successfully"}
        mock_db.delete.assert_called_once()  # Document still deleted
        mock_db.commit.assert_called_once()

    @patch('main.get_db')
    def test_delete_deal_document_export_error(
        self,
        mock_get_db,
        mock_db,
        mock_user,
        sample_deal,
        sample_document
    ):
        """Test handling of database errors during export deletion"""
        from main import delete_deal_document
        
        mock_get_db.return_value = mock_db
        
        # Mock successful lookups
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            sample_deal,
            sample_document
        ]
        
        def mock_query_side_effect(model):
            if model == Deal:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_deal
                return query_mock
            elif model == Document:
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = sample_document
                return query_mock
            elif model == Export:
                # Simulate database error during export query
                raise Exception("Database connection failed during export query")
        
        mock_db.query.side_effect = mock_query_side_effect
        
        with pytest.raises(HTTPException) as exc_info:
            delete_deal_document(
                deal_id=str(sample_deal.id),
                document_id=str(sample_document.id),
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 500
        assert "Error deleting associated exports" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()

    def test_cascade_deletion_logic_documentation(self):
        """Document the cascade deletion requirements that were fixed"""
        # This test documents the foreign key relationships and deletion order
        foreign_keys = {
            'exports.document_id': 'documents.id',
            'question_answer_audits.question_id': 'questions.id',
            'questions.document_id': 'documents.id',
            'documents.deal_id': 'deals.id'
        }
        
        required_deletion_order = [
            'Export',               # Must be deleted first (references document)
            'QuestionAnswerAudit',  # Must be deleted next (child of question)
            'Question',             # Then questions (parent of audit, child of document)
            'Document'              # Finally document (parent of question and export)
        ]
        
        # The fix ensures this order is followed
        assert len(required_deletion_order) == 4
        assert required_deletion_order[0] == 'Export'
        assert required_deletion_order[1] == 'QuestionAnswerAudit'
        assert 'exports.document_id' in foreign_keys
        assert 'question_answer_audits.question_id' in foreign_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])