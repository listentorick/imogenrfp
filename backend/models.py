from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Date, ARRAY, Numeric, CheckConstraint
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
    original_text = Column(Text)  # Original text from document before conversion to question format
    question_type = Column(String(50), default='question')  # question, requirement, criteria, specification, form_field, other
    answer_text = Column(Text)  # Initially null, filled when answered
    reasoning = Column(Text)  # LLM reasoning extracted from <think> tags
    extraction_confidence = Column(Numeric(precision=3, scale=2))  # 0.00 to 1.00
    answer_relevance_score = Column(Numeric(precision=5, scale=2))  # 0.00 to 100.00 - average similarity score from vector search
    answer_sources = Column(ARRAY(String))  # Array of document IDs that were used as sources for the answer
    answer_source_filenames = Column(ARRAY(String))  # Array of original filenames corresponding to answer_sources
    question_order = Column(Integer)  # Order of question in document
    processing_status = Column(String(50), default='pending', nullable=False)  # pending, processing, processed, error
    processing_error = Column(Text)  # Error message if processing fails
    answer_status = Column(String(50), default='notAnswered', nullable=False)  # answered, notAnswered, partiallyAnswered
    # Excel-specific fields
    answer_cell_reference = Column(String(10))  # e.g., "B2", "C15" for Excel documents
    cell_confidence = Column(Numeric(precision=3, scale=2))  # Confidence in cell location (0.00-1.00)
    sheet_name = Column(String(255))  # Excel sheet name
    document_type = Column(String(50))  # "excel", "word", "pdf", etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Table constraints
    __table_args__ = (
        CheckConstraint("answer_status IN ('answered', 'notAnswered', 'partiallyAnswered')", name='check_answer_status'),
        CheckConstraint("processing_status IN ('pending', 'processing', 'processed', 'error')", name='check_processing_status'),
    )

    # Relationships
    tenant = relationship("Tenant")
    deal = relationship("Deal", back_populates="questions")
    document = relationship("Document")

class Export(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status = Column(String(50), default='pending', nullable=False)  # pending, processing, completed, failed
    file_path = Column(String(500))  # Path to generated export file
    original_filename = Column(String(255), nullable=False)  # Original document filename
    export_filename = Column(String(255))  # Generated export filename
    error_message = Column(Text)  # Error details if failed
    questions_count = Column(Integer, default=0)  # Total questions exported
    answered_count = Column(Integer, default=0)  # Questions with answers
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    # Table constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_export_status'),
    )

    # Relationships
    tenant = relationship("Tenant")
    deal = relationship("Deal")
    document = relationship("Document")
    created_by_user = relationship("User")
