from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
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
    document_type: str = 'rfp'
    project_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None

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

# Deal schemas
class DealBase(BaseModel):
    name: str
    company: str
    value: Optional[Decimal] = None
    status: str = "prospect"
    description: Optional[str] = None
    expected_close_date: Optional[date] = None

class DealCreate(DealBase):
    project_id: UUID

class DealUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    value: Optional[Decimal] = None
    status: Optional[str] = None
    description: Optional[str] = None
    expected_close_date: Optional[date] = None

class Deal(DealBase):
    id: UUID
    tenant_id: UUID
    project_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Question schemas
class QuestionBase(BaseModel):
    question_text: str
    answer_text: Optional[str] = None
    extraction_confidence: Optional[Decimal] = None
    question_order: Optional[int] = None
    processing_status: str = 'pending'
    processing_error: Optional[str] = None

class QuestionCreate(QuestionBase):
    deal_id: UUID
    document_id: UUID

class QuestionUpdate(BaseModel):
    answer_text: Optional[str] = None

class Question(QuestionBase):
    id: UUID
    tenant_id: UUID
    deal_id: UUID
    document_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
