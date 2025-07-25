from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

class TenantBase(BaseModel):
    name: str
    slug: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StandardAnswerBase(BaseModel):
    question: str
    answer: str
    tags: Optional[List[str]] = None
    project_id: Optional[UUID] = None

class StandardAnswerCreate(StandardAnswerBase):
    pass

class StandardAnswer(StandardAnswerBase):
    id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RFPQuestionBase(BaseModel):
    question_text: str
    question_order: Optional[int] = None

class RFPQuestionCreate(RFPQuestionBase):
    pass

class RFPQuestion(RFPQuestionBase):
    id: UUID
    rfp_request_id: UUID
    generated_answer: Optional[str] = None
    reviewed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RFPRequestBase(BaseModel):
    title: str
    client_name: Optional[str] = None
    due_date: Optional[date] = None
    project_id: UUID

class RFPRequestCreate(RFPRequestBase):
    questions: List[RFPQuestionCreate] = []

class RFPRequest(RFPRequestBase):
    id: UUID
    tenant_id: UUID
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    questions: List[RFPQuestion] = []

    class Config:
        from_attributes = True

class TemplateBase(BaseModel):
    name: str
    template_content: str
    template_type: str = 'html'
    is_default: bool = False

class TemplateCreate(TemplateBase):
    pass

class Template(TemplateBase):
    id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    tenant_id: Optional[UUID] = None

class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    project_id: UUID

class DocumentCreate(DocumentBase):
    file_path: str
    status: str = 'uploaded'

class Document(DocumentBase):
    id: UUID
    tenant_id: UUID
    file_path: str
    status: str
    processing_error: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True