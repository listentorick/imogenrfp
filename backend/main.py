from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import os
import uuid as uuid_lib
import shutil
import asyncio

from database import get_db, engine
from models import Base, User, Tenant, Project, StandardAnswer, RFPRequest, RFPQuestion, Template, Document, Deal
from schemas import (
    User as UserSchema, UserCreate, Tenant as TenantSchema, TenantCreate,
    Project as ProjectSchema, ProjectCreate, StandardAnswer as StandardAnswerSchema,
    StandardAnswerCreate, RFPRequest as RFPRequestSchema, RFPRequestCreate,
    Template as TemplateSchema, TemplateCreate, Token, Document as DocumentSchema,
    DocumentCreate, Deal as DealSchema, DealCreate, DealUpdate
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

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RFP SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/standard-answers/", response_model=StandardAnswerSchema)
def create_standard_answer(
    answer: StandardAnswerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_answer = StandardAnswer(
        **answer.dict(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    
    # Add to RAG system
    rag_service.add_standard_answer(
        tenant_id=str(current_user.tenant_id),
        answer_id=str(db_answer.id),
        question=db_answer.question,
        answer=db_answer.answer,
        tags=db_answer.tags or []
    )
    
    return db_answer

@app.get("/standard-answers/", response_model=List[StandardAnswerSchema])
def read_standard_answers(
    project_id: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(StandardAnswer).filter(
        StandardAnswer.tenant_id == current_user.tenant_id
    )
    if project_id:
        query = query.filter(StandardAnswer.project_id == project_id)
    
    answers = query.offset(skip).limit(limit).all()
    return answers

@app.post("/rfp-requests/", response_model=RFPRequestSchema)
def create_rfp_request(
    rfp: RFPRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_rfp = RFPRequest(
        title=rfp.title,
        client_name=rfp.client_name,
        due_date=rfp.due_date,
        project_id=rfp.project_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(db_rfp)
    db.commit()
    db.refresh(db_rfp)
    
    for idx, question in enumerate(rfp.questions):
        db_question = RFPQuestion(
            rfp_request_id=db_rfp.id,
            question_text=question.question_text,
            question_order=question.question_order or idx + 1
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_rfp)
    return db_rfp

@app.get("/rfp-requests/", response_model=List[RFPRequestSchema])
def read_rfp_requests(
    project_id: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(RFPRequest).filter(
        RFPRequest.tenant_id == current_user.tenant_id
    )
    if project_id:
        query = query.filter(RFPRequest.project_id == project_id)
    
    rfps = query.offset(skip).limit(limit).all()
    return rfps

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

@app.post("/rfp-requests/{rfp_id}/generate-answers")
def generate_rfp_answers(
    rfp_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rfp = db.query(RFPRequest).filter(
        RFPRequest.id == rfp_id,
        RFPRequest.tenant_id == current_user.tenant_id
    ).first()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    questions = db.query(RFPQuestion).filter(
        RFPQuestion.rfp_request_id == rfp_id
    ).all()
    
    generated_count = 0
    for question in questions:
        if not question.generated_answer:
            generated_answer = rag_service.generate_rfp_answer(
                tenant_id=str(current_user.tenant_id),
                rfp_question=question.question_text
            )
            question.generated_answer = generated_answer
            generated_count += 1
    
    db.commit()
    
    return {"message": f"Generated {generated_count} answers", "rfp_id": rfp_id}

@app.post("/rfp-requests/{rfp_id}/render")
def render_rfp_response(
    rfp_id: str,
    template_id: str = None,
    branding_data: dict = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    rfp = db.query(RFPRequest).filter(
        RFPRequest.id == rfp_id,
        RFPRequest.tenant_id == current_user.tenant_id
    ).first()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if template_id:
        template = db.query(Template).filter(
            Template.id == template_id,
            Template.tenant_id == current_user.tenant_id
        ).first()
    else:
        template = db.query(Template).filter(
            Template.tenant_id == current_user.tenant_id,
            Template.is_default == True
        ).first()
    
    if not template:
        template_content = template_service.get_default_html_template()
    else:
        template_content = template.template_content
    
    rfp_data = {
        "id": str(rfp.id),
        "title": rfp.title,
        "client_name": rfp.client_name,
        "due_date": rfp.due_date,
        "status": rfp.status,
        "questions": [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "generated_answer": q.generated_answer,
                "reviewed": q.reviewed
            }
            for q in rfp.questions
        ]
    }
    
    rendered_content = template_service.render_rfp_response(
        template_content=template_content,
        rfp_data=rfp_data,
        branding_data=branding_data or {}
    )
    
    return {
        "rendered_content": rendered_content,
        "template_type": template.template_type if template else "html"
    }

@app.post("/standard-answers/bulk-index")
def bulk_index_answers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    count = rag_service.bulk_index_standard_answers(db, str(current_user.tenant_id))
    return {"message": f"Indexed {count} standard answers"}

@app.post("/documents/", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
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
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
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
            project_id=str(project_id),
            file_path=file_path
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
                queue_service.enqueue_document_processing({
                    'document_id': doc.id,
                    'file_path': doc.file_path,
                    'tenant_id': str(current_user.tenant_id),
                    'project_id': project_id
                })
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

@app.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    await websocket_manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, tenant_id)

# Removed problematic startup event for now
# @app.on_event("startup")
# async def startup_event():
#     # Start WebSocket listener in background
#     asyncio.create_task(websocket_manager.listen_for_updates())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)