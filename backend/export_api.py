from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import logging
from datetime import datetime

from database import get_db
from models import Export, Deal, Document, Question, User
from schemas import Export as ExportSchema, ExportCreate, ExportStatus
from auth import get_current_user
from export_service import export_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/deals/{deal_id}/export", response_model=ExportStatus)
async def start_export(
    deal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start an export job for a deal's questions and answers"""
    
    # Verify deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    # Find the source document for this deal (first document uploaded)
    source_document = db.query(Document).filter(
        Document.deal_id == deal_id,
        Document.tenant_id == current_user.tenant_id
    ).order_by(Document.created_at.asc()).first()
    
    if not source_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No source document found for this deal"
        )
    
    # Count questions for this deal
    questions_count = db.query(Question).filter(
        Question.deal_id == deal_id,
        Question.tenant_id == current_user.tenant_id
    ).count()
    
    # Count answered questions
    answered_count = db.query(Question).filter(
        Question.deal_id == deal_id,
        Question.tenant_id == current_user.tenant_id,
        Question.answer_text.isnot(None),
        Question.answer_text != ""
    ).count()
    
    if questions_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No questions found for this deal"
        )
    
    # Create export record
    export_record = Export(
        tenant_id=current_user.tenant_id,
        deal_id=deal_id,
        document_id=source_document.id,
        original_filename=source_document.original_filename,
        questions_count=questions_count,
        answered_count=answered_count,
        created_by=current_user.id
    )
    
    db.add(export_record)
    db.commit()
    db.refresh(export_record)
    
    # Enqueue export job
    try:
        export_service.enqueue_export_job(
            export_id=str(export_record.id),
            tenant_id=str(current_user.tenant_id),
            deal_id=deal_id,
            document_id=str(source_document.id)
        )
        logger.info(f"Enqueued export job for export {export_record.id}")
    except Exception as e:
        logger.error(f"Failed to enqueue export job: {e}")
        # Update export status to failed
        export_record.status = 'failed'
        export_record.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start export job"
        )
    
    return ExportStatus(
        id=export_record.id,
        status=export_record.status,
        created_at=export_record.created_at,
        questions_count=export_record.questions_count,
        answered_count=export_record.answered_count,
        export_filename=export_record.original_filename
    )

@router.post("/deals/{deal_id}/documents/{document_id}/export", response_model=ExportStatus)
async def start_document_export(
    deal_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start an export job for a specific document's questions and answers"""
    
    # Verify deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found"
        )
    
    # Find the specific document
    source_document = db.query(Document).filter(
        Document.id == document_id,
        Document.deal_id == deal_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not source_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Count questions for this specific document
    questions_count = db.query(Question).filter(
        Question.document_id == document_id,
        Question.tenant_id == current_user.tenant_id
    ).count()
    
    # Count answered questions for this specific document
    answered_count = db.query(Question).filter(
        Question.document_id == document_id,
        Question.tenant_id == current_user.tenant_id,
        Question.answer_text.isnot(None),
        Question.answer_text != ""
    ).count()
    
    if questions_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No questions found for this document"
        )
    
    # Create export record
    export_record = Export(
        tenant_id=current_user.tenant_id,
        deal_id=deal_id,
        document_id=source_document.id,
        original_filename=source_document.original_filename,
        questions_count=questions_count,
        answered_count=answered_count,
        created_by=current_user.id
    )
    
    db.add(export_record)
    db.commit()
    db.refresh(export_record)
    
    # Enqueue export job
    try:
        export_service.enqueue_export_job(
            export_id=str(export_record.id),
            tenant_id=str(current_user.tenant_id),
            deal_id=deal_id,
            document_id=str(source_document.id)
        )
        logger.info(f"Enqueued export job for document {document_id}, export {export_record.id}")
    except Exception as e:
        logger.error(f"Failed to enqueue export job: {e}")
        # Update export status to failed
        export_record.status = 'failed'
        export_record.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start export job"
        )
    
    return ExportStatus(
        id=export_record.id,
        status=export_record.status,
        created_at=export_record.created_at,
        questions_count=export_record.questions_count,
        answered_count=export_record.answered_count,
        export_filename=export_record.original_filename
    )

@router.get("/exports/{export_id}")
async def get_export_status(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of an export job"""
    export_record = db.query(Export).filter(
        Export.id == export_id,
        Export.tenant_id == current_user.tenant_id
    ).first()
    
    if not export_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    return ExportStatus(
        id=export_record.id,
        status=export_record.status,
        created_at=export_record.created_at,
        completed_at=export_record.completed_at,
        questions_count=export_record.questions_count,
        answered_count=export_record.answered_count,
        export_filename=export_record.original_filename,
        error_message=export_record.error_message
    )

@router.get("/exports/{export_id}/status")
async def get_export_status_with_suffix(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of an export job (with /status suffix for frontend compatibility)"""
    export_record = db.query(Export).filter(
        Export.id == export_id,
        Export.tenant_id == current_user.tenant_id
    ).first()
    
    if not export_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    return ExportStatus(
        id=export_record.id,
        status=export_record.status,
        created_at=export_record.created_at,
        completed_at=export_record.completed_at,
        questions_count=export_record.questions_count,
        answered_count=export_record.answered_count,
        export_filename=export_record.original_filename,
        error_message=export_record.error_message
    )

@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the completed export file"""
    export_record = db.query(Export).filter(
        Export.id == export_id,
        Export.tenant_id == current_user.tenant_id
    ).first()
    
    if not export_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    if export_record.status != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready for download. Status: {export_record.status}"
        )
    
    if not export_record.file_path or not os.path.exists(export_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Generate download filename
    timestamp = export_record.created_at.strftime("%Y%m%d_%H%M%S")
    download_filename = f"export_{timestamp}_{export_record.original_filename}"
    
    return FileResponse(
        path=export_record.file_path,
        filename=download_filename,
        media_type='application/octet-stream'
    )

@router.get("/exports")
async def list_exports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all export jobs for the current user"""
    exports = db.query(Export).filter(
        Export.tenant_id == current_user.tenant_id
    ).order_by(Export.created_at.desc()).limit(50).all()
    
    return [
        ExportStatus(
            id=export.id,
            status=export.status,
            created_at=export.created_at,
            completed_at=export.completed_at,
            questions_count=export.questions_count,
            answered_count=export.answered_count,
            export_filename=export.original_filename,
            error_message=export.error_message
        )
        for export in exports
    ]