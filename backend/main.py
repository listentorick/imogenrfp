from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import os
import uuid as uuid_lib
import shutil
import asyncio
import json
import logging

from database import get_db, engine
from models import Base, User, Tenant, Project, Template, Document, Deal, Question, ProjectQAPair
from schemas import (
    User as UserSchema, UserCreate, Tenant as TenantSchema, TenantCreate,
    Project as ProjectSchema, ProjectCreate, Template as TemplateSchema, TemplateCreate, Token, Document as DocumentSchema,
    DocumentCreate, Deal as DealSchema, DealCreate, DealUpdate, Question as QuestionSchema, QuestionUpdate,
    ProjectQAPair as ProjectQAPairSchema, ProjectQAPairCreate
)
from queue_service import queue_service
from websocket_manager import websocket_manager
from chroma_service import chroma_service
from auth import (
    authenticate_user, get_password_hash, create_access_token,
    get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
# from rag_service import rag_service
from template_service import template_service
from export_api import router as export_router

logger = logging.getLogger(__name__)

# Note: Database schema is now managed by Alembic migrations
# Run 'alembic upgrade head' to apply latest migrations

app = FastAPI(title="RFP SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(export_router, prefix="/api", tags=["exports"])

def authenticate_user(db: Session, email: str, password: str):
    from auth import verify_password
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

@app.post("/auth/register", response_model=UserSchema)
def register_user(user: UserCreate, tenant: TenantCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    db_tenant = db.query(Tenant).filter(Tenant.slug == tenant.slug).first()
    if db_tenant:
        raise HTTPException(
            status_code=400,
            detail="Tenant slug already exists"
        )
    
    db_tenant = Tenant(**tenant.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        **user.dict(exclude={'password'}),
        password_hash=hashed_password,
        tenant_id=db_tenant.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/auth/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"Login attempt - Username: {form_data.username}, Password length: {len(form_data.password)}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/projects/", response_model=ProjectSchema)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_project = Project(
        **project.dict(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Create ChromaDB collection for this project
    try:
        chroma_service.create_project_collection(
            project_id=str(db_project.id),
            project_name=db_project.name
        )
    except Exception as e:
        # Log error but don't fail project creation
        print(f"Failed to create ChromaDB collection for project {db_project.id}: {e}")
    
    return db_project

@app.get("/projects/", response_model=List[ProjectSchema])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(
        Project.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return projects





@app.post("/templates/", response_model=TemplateSchema)
def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_template = Template(
        **template.dict(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@app.get("/templates/", response_model=List[TemplateSchema])
def read_templates(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    templates = db.query(Template).filter(
        Template.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return templates




@app.post("/documents/", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    document_type: str = Form("other"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify project exists and user has access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == current_user.tenant_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create uploads directory if it doesn't exist
    upload_dir = f"uploads/{current_user.tenant_id}/{project_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid_lib.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    db_document = Document(
        tenant_id=current_user.tenant_id,
        project_id=project_id,
        deal_id=None,  # Project documents don't have deal_id
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
        document_type=document_type,
        created_by=current_user.id
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Queue document for processing
    try:
        queue_service.enqueue_document_processing(
            document_id=str(db_document.id),
            tenant_id=str(current_user.tenant_id),
            file_path=file_path,
            project_id=str(project_id)
        )
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Failed to queue document processing: {e}")
    
    return db_document

@app.get("/projects/{project_id}/documents", response_model=List[DocumentSchema])
def get_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify project exists and user has access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == current_user.tenant_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    documents = db.query(Document).filter(
        Document.project_id == project_id,
        Document.tenant_id == current_user.tenant_id
    ).all()
    
    return documents

@app.get("/documents/{document_id}/download")
def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get document and verify access
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type=document.mime_type
    )

@app.delete("/projects/{project_id}/documents/{document_id}")
def delete_project_document(
    project_id: str,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document from a project"""
    # Check if project exists and user has access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == current_user.tenant_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get document and verify it belongs to this project
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.project_id == project_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found in this project")
    
    # Remove the file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            logger.info(f"Deleted file: {document.file_path}")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
    
    # Remove from ChromaDB (project documents are stored in ChromaDB)
    try:
        from chroma_service import chroma_service
        chroma_service.remove_document_from_project(project_id, document_id)
        logger.info(f"Removed project document {document_id} from ChromaDB")
    except Exception as e:
        logger.error(f"Error removing from ChromaDB: {e}")
    
    # Delete any associated questions
    try:
        from models import Question
        questions = db.query(Question).filter(Question.document_id == document_id).all()
        for question in questions:
            db.delete(question)
        if questions:
            logger.info(f"Deleted {len(questions)} associated questions")
    except Exception as e:
        logger.error(f"Error deleting associated questions: {e}")
    
    # Delete the database record
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@app.get("/projects/{project_id}/search")
def search_project_documents(
    project_id: str,
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search documents within a project using semantic search"""
    # Verify project exists and user has access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == current_user.tenant_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Use ChromaDB for vector search
        search_results = chroma_service.search_project_documents(
            project_id=project_id,
            query_text=query,
            n_results=min(limit, 20),  # Cap at 20 results
            tenant_id=str(current_user.tenant_id)
        )
        
        # Format results for frontend
        formatted_results = []
        for result in search_results:
            metadata = result.get('metadata', {})
            formatted_results.append({
                'content': result.get('content', ''),
                'distance': result.get('distance', 0),
                'document_id': metadata.get('document_id'),
                'filename': metadata.get('filename', 'Unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'total_chunks': metadata.get('total_chunks', 1)
            })
        
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results),
            'project_id': project_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )

@app.get("/projects/{project_id}/documents/debug")
async def debug_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see all documents stored in ChromaDB for a project"""
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == current_user.tenant_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        all_docs = chroma_service.get_all_documents_in_project(project_id)
        return {"project_id": project_id, "total_documents": len(all_docs), "documents": all_docs}
    
    except Exception as e:
        logger.error(f"Error getting debug documents: {e}")
        raise HTTPException(status_code=500, detail="Error getting debug documents")

@app.post("/projects/{project_id}/documents/clear-chunks")
async def clear_project_chunks(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear all chunks from a project's ChromaDB collection"""
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == current_user.tenant_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        success = chroma_service.clear_project_collection(project_id)
        if success:
            return {"message": f"Successfully cleared all chunks for project {project_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chunks")
    
    except Exception as e:
        logger.error(f"Error clearing chunks: {e}")
        raise HTTPException(status_code=500, detail="Error clearing chunks")

@app.post("/projects/{project_id}/documents/reprocess")
async def reprocess_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reprocess all documents in a project with the new chunking algorithm"""
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == current_user.tenant_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Clear existing chunks
        chroma_service.clear_project_collection(project_id)
        
        # Get all processed documents for this project
        documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.status == 'processed'
        ).all()
        
        # Queue documents for reprocessing
        reprocessed_count = 0
        for doc in documents:
            if doc.file_path and os.path.exists(doc.file_path):
                # Reset status and queue for processing
                doc.status = 'pending'
                db.commit()
                
                # Queue for processing with new chunking
                queue_service.enqueue_document_processing(
                    document_id=str(doc.id),
                    tenant_id=str(current_user.tenant_id),
                    file_path=doc.file_path,
                    project_id=project_id
                )
                reprocessed_count += 1
        
        return {
            "message": f"Reprocessing {reprocessed_count} documents with LangChain chunking",
            "reprocessed_count": reprocessed_count
        }
    
    except Exception as e:
        logger.error(f"Error reprocessing documents: {e}")
        raise HTTPException(status_code=500, detail="Error reprocessing documents")

# Deals endpoints
@app.post("/deals/", response_model=DealSchema)
def create_deal(
    deal: DealCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new deal"""
    # Verify project exists and user has access
    project = db.query(Project).filter(
        Project.id == deal.project_id,
        Project.tenant_id == current_user.tenant_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_deal = Deal(
        **deal.dict(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

@app.get("/deals/", response_model=List[DealSchema])
def read_deals(
    project_id: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get deals, optionally filtered by project"""
    query = db.query(Deal).filter(Deal.tenant_id == current_user.tenant_id)
    
    if project_id:
        query = query.filter(Deal.project_id == project_id)
    
    deals = query.offset(skip).limit(limit).all()
    return deals

@app.get("/deals/{deal_id}", response_model=DealSchema)
def read_deal(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific deal"""
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return deal

@app.put("/deals/{deal_id}", response_model=DealSchema)
def update_deal(
    deal_id: str,
    deal_update: DealUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a deal"""
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Update only provided fields
    update_data = deal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deal, field, value)
    
    db.commit()
    db.refresh(deal)
    return deal

@app.delete("/deals/{deal_id}")
def delete_deal(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a deal"""
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    db.delete(deal)
    db.commit()
    return {"message": "Deal deleted successfully"}

# Deal Document endpoints
@app.post("/deals/{deal_id}/documents/", response_model=DocumentSchema)
def upload_deal_document(
    deal_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("rfp"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a document to a deal"""
    # Check if deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid_lib.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create document record
    document = Document(
        tenant_id=current_user.tenant_id,
        project_id=None,  # Deal documents don't have project_id
        deal_id=deal_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        document_type=document_type,
        created_by=current_user.id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Queue document for processing (including question extraction for deals)  
    try:
        queue_service.enqueue_document_processing(
            document_id=str(document.id),
            tenant_id=str(current_user.tenant_id),
            file_path=file_path,
            project_id=str(deal.project_id),  # Use the deal's project_id
            deal_id=str(deal_id)
        )
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Failed to queue document processing: {e}")
    
    return document

@app.get("/deals/{deal_id}/documents", response_model=List[DocumentSchema])
def get_deal_documents(
    deal_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get documents for a specific deal with filtering and sorting"""
    # Check if deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Build query
    query = db.query(Document).filter(
        Document.deal_id == deal_id,
        Document.tenant_id == current_user.tenant_id
    )
    
    # Apply filters
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    if status:
        query = query.filter(Document.status == status)
    
    if search:
        query = query.filter(
            Document.original_filename.ilike(f"%{search}%")
        )
    
    # Apply sorting
    if sort_by and hasattr(Document, sort_by):
        sort_column = getattr(Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column)
    
    documents = query.all()
    return documents

@app.delete("/deals/{deal_id}/documents/{document_id}")
def delete_deal_document(
    deal_id: str,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document from a deal"""
    # Check if deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Find the document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.deal_id == deal_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete associated questions first (due to foreign key constraints)
    try:
        questions = db.query(Question).filter(Question.document_id == document_id).all()
        for question in questions:
            db.delete(question)
        logger.info(f"Deleted {len(questions)} associated questions for document {document_id}")
    except Exception as e:
        logger.error(f"Error deleting associated questions: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting associated questions")
    
    # Delete the file from filesystem
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Remove from ChromaDB if it's a project document (deal documents are not stored in ChromaDB)
    try:
        from chroma_service import chroma_service
        if document.project_id and not document.deal_id:
            # Only project documents are stored in ChromaDB
            chroma_service.remove_document_from_project(str(document.project_id), document_id)
            logger.info(f"Removed project document {document_id} from ChromaDB")
        else:
            logger.info(f"Skipping ChromaDB removal for deal document {document_id}")
    except Exception as e:
        print(f"Error removing from ChromaDB: {e}")
    
    # Delete the database record
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """Secure WebSocket endpoint with token authentication"""
    try:
        # Extract token from query parameter
        if not token:
            # Try to get token from query parameters
            query_params = dict(websocket.query_params)
            token = query_params.get('token')
        
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return
        
        # Validate token and get user
        try:
            from auth import verify_token_string
            payload = verify_token_string(token)
            user_email = payload.get("sub")
            user_tenant_id = payload.get("tenant_id")
            
            if not user_email or not user_tenant_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
                
        except Exception as e:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return
        
        # Connect with authenticated tenant ID
        connection_success = await websocket_manager.connect(websocket, user_tenant_id)
        if not connection_success:
            return  # Connection was rejected due to limits
            
        print(f"Authenticated WebSocket connection for user {user_email}, tenant {user_tenant_id}")
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, user_tenant_id)
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Connection error")
        except:
            pass

# Question endpoints
@app.get("/deals/{deal_id}/questions", response_model=List[QuestionSchema])
def get_deal_questions(
    deal_id: str,
    answer_status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all questions extracted from documents for a deal, optionally filtered by answer status"""
    # Check if deal exists and user has access
    deal = db.query(Deal).filter(
        Deal.id == deal_id,
        Deal.tenant_id == current_user.tenant_id
    ).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Build query with optional answer status filter
    query = db.query(Question).filter(
        Question.deal_id == deal_id,
        Question.tenant_id == current_user.tenant_id
    )
    
    # Apply answer status filter if provided
    if answer_status:
        if answer_status not in ['answered', 'partiallyAnswered', 'notAnswered']:
            raise HTTPException(status_code=400, detail="Invalid answer_status. Must be 'answered', 'partiallyAnswered', or 'notAnswered'")
        query = query.filter(Question.answer_status == answer_status)
    
    questions = query.order_by(Question.document_id, Question.question_order).all()
    return questions

@app.patch("/questions/{question_id}", response_model=QuestionSchema)
def update_question_answer(
    question_id: str,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update the answer for a specific question"""
    # Check if question exists and user has access
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.tenant_id == current_user.tenant_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update the answer
    if question_update.answer_text is not None:
        question.answer_text = question_update.answer_text
        # Mark question as answered when answer text is provided
        if question_update.answer_text.strip():
            question.answer_status = "answered"
        else:
            question.answer_status = "notAnswered"
    
    db.commit()
    db.refresh(question)
    return question

@app.post("/questions/{question_id}/add-to-knowledge-base", response_model=ProjectQAPairSchema)
def add_question_to_knowledge_base(
    question_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add an answered deal question to the project knowledge base"""
    # Get the question and verify access
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.tenant_id == current_user.tenant_id
    ).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if not question.answer_text or not question.answer_text.strip():
        raise HTTPException(status_code=400, detail="Question must have an answer to add to knowledge base")
    
    # Get the deal to find the project_id
    deal = db.query(Deal).filter(Deal.id == question.deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check if already exists in knowledge base
    existing = db.query(ProjectQAPair).filter(
        ProjectQAPair.source_question_id == question_id,
        ProjectQAPair.tenant_id == current_user.tenant_id
    ).first()
    
    if existing:
        # Update existing Q&A pair
        existing.question_text = question.question_text
        existing.answer_text = question.answer_text
        existing.project_id = deal.project_id  # In case deal was moved to different project
        qa_pair = existing
    else:
        # Create new knowledge base entry
        qa_pair = ProjectQAPair(
            tenant_id=current_user.tenant_id,
            project_id=deal.project_id,
            question_text=question.question_text,
            answer_text=question.answer_text,
            source_question_id=question.id,
            created_by=current_user.id
        )
        db.add(qa_pair)
    
    db.commit()
    db.refresh(qa_pair)
    
    # Queue the Q&A pair for ChromaDB processing
    try:
        queue_service.enqueue_qa_pair_processing(
            qa_pair_id=str(qa_pair.id),
            tenant_id=str(current_user.tenant_id),
            project_id=str(deal.project_id)
        )
        logger.info(f"Queued Q&A pair {qa_pair.id} for ChromaDB processing")
    except Exception as e:
        logger.error(f"Failed to queue Q&A pair for processing: {e}")
        # Don't fail the API call if queueing fails
    
    return qa_pair

@app.get("/documents/{document_id}/questions", response_model=List[QuestionSchema])
def get_document_questions(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all questions extracted from a specific document"""
    # Check if document exists and user has access
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get all questions for the document
    questions = db.query(Question).filter(
        Question.document_id == document_id,
        Question.tenant_id == current_user.tenant_id  
    ).order_by(Question.question_order).all()
    
    return questions

@app.on_event("startup")
async def startup_event():
    # Start WebSocket listener in background
    asyncio.create_task(websocket_manager.listen_for_updates())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)