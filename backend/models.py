from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Date, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")
    templates = relationship("Template", back_populates="tenant")
    documents = relationship("Document")
    deals = relationship("Deal", back_populates="tenant")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")
    projects = relationship("Project", back_populates="created_by_user")
    templates = relationship("Template", back_populates="created_by_user")
    deals = relationship("Deal", back_populates="created_by_user")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="projects")
    created_by_user = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    deals = relationship("Deal", back_populates="project")




class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    template_content = Column(Text, nullable=False)
    template_type = Column(String(50), default='html')
    is_default = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="templates")
    created_by_user = relationship("User", back_populates="templates")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    document_type = Column(String(50), default='other')  # rfp, rfi, proposal, contract, other
    status = Column(String(50), default='uploaded', nullable=False)  # uploaded, processing, processed, error
    processing_error = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant")
    project = relationship("Project", back_populates="documents")
    deal = relationship("Deal", back_populates="documents")
    created_by_user = relationship("User")

class Deal(Base):
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    value = Column(Numeric(precision=10, scale=2))  # Deal value in currency
    status = Column(String(100), nullable=False, default="prospect")  # prospect, proposal, negotiation, closed_won, closed_lost
    description = Column(Text)
    expected_close_date = Column(Date)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="deals")
    project = relationship("Project", back_populates="deals")
    created_by_user = relationship("User", back_populates="deals")
    documents = relationship("Document", back_populates="deal")
    questions = relationship("Question", back_populates="deal")

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text)  # Initially null, filled when answered
    reasoning = Column(Text)  # LLM reasoning extracted from <think> tags
    extraction_confidence = Column(Numeric(precision=3, scale=2))  # 0.00 to 1.00
    question_order = Column(Integer)  # Order of question in document
    processing_status = Column(String(50), default='pending', nullable=False)  # pending, processing, processed, error
    processing_error = Column(Text)  # Error message if processing fails
    answer_status = Column(String(50), default='unanswered', nullable=False)  # answered, unanswered
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    deal = relationship("Deal", back_populates="questions")
    document = relationship("Document")
