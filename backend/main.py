from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from database import get_db, engine
from models import Base, User, Tenant, Project, StandardAnswer, RFPRequest, RFPQuestion, Template
from schemas import (
    User as UserSchema, UserCreate, Tenant as TenantSchema, TenantCreate,
    Project as ProjectSchema, ProjectCreate, StandardAnswer as StandardAnswerSchema,
    StandardAnswerCreate, RFPRequest as RFPRequestSchema, RFPRequestCreate,
    Template as TemplateSchema, TemplateCreate, Token
)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)