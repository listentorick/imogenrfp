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
    standard_answers = relationship("StandardAnswer", back_populates="tenant")
    rfp_requests = relationship("RFPRequest", back_populates="tenant")
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
    standard_answers = relationship("StandardAnswer", back_populates="created_by_user")
    rfp_requests = relationship("RFPRequest", back_populates="created_by_user")
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
    standard_answers = relationship("StandardAnswer", back_populates="project")
    rfp_requests = relationship("RFPRequest", back_populates="project")
    documents = relationship("Document", back_populates="project")
    deals = relationship("Deal", back_populates="project")

class StandardAnswer(Base):
    __tablename__ = "standard_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    question = Column(String(1000), nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(ARRAY(Text))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="standard_answers")
    project = relationship("Project", back_populates="standard_answers")
    created_by_user = relationship("User", back_populates="standard_answers")

class RFPRequest(Base):
    __tablename__ = "rfp_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True)  # Optional deal association
    title = Column(String(255), nullable=False)
    client_name = Column(String(255))
    due_date = Column(Date)
    status = Column(String(50), default='draft')
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="rfp_requests")
    project = relationship("Project", back_populates="rfp_requests")
    deal = relationship("Deal", back_populates="rfp_requests")
    created_by_user = relationship("User", back_populates="rfp_requests")
    questions = relationship("RFPQuestion", back_populates="rfp_request")

class RFPQuestion(Base):
    __tablename__ = "rfp_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfp_request_id = Column(UUID(as_uuid=True), ForeignKey("rfp_requests.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_order = Column(Integer)
    generated_answer = Column(Text)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    rfp_request = relationship("RFPRequest", back_populates="questions")

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
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default='uploaded', nullable=False)  # uploaded, processing, processed, error
    processing_error = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant")
    project = relationship("Project", back_populates="documents")
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
    rfp_requests = relationship("RFPRequest", back_populates="deal")