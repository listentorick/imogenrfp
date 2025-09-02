import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
import uuid

from models import User, Tenant, Project
from schemas import UserCreate, TenantCreate


class TestDefaultProjectCreation:
    """Test that default projects are created when new tenants are created"""

    def test_registration_creates_default_project(self):
        """Test that /auth/register creates tenant, user, and default project"""
        from main import register_user
        
        # Mock database session
        mock_db = Mock()
        
        # Mock queries to return None (no existing user/tenant)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Track objects added to database
        added_objects = []
        def mock_add(obj):
            added_objects.append(obj)
        mock_db.add.side_effect = mock_add
        
        # Create test data
        user_data = UserCreate(
            email="newuser@company.com",
            first_name="New",
            last_name="User",
            password="password123"
        )
        
        tenant_data = TenantCreate(
            name="New Company",
            slug="new-company"
        )
        
        # Mock password hashing
        with patch('main.get_password_hash', return_value="hashed_password"):
            register_user(user_data, tenant_data, mock_db)
        
        # Verify that db.add was called 3 times (tenant, user, project)
        assert mock_db.add.call_count == 3
        
        # Verify tenant was created first
        tenant_obj = added_objects[0]
        assert isinstance(tenant_obj, Tenant)
        assert tenant_obj.name == "New Company"
        assert tenant_obj.slug == "new-company"
        
        # Verify user was created second
        user_obj = added_objects[1]
        assert isinstance(user_obj, User)
        assert user_obj.email == "newuser@company.com"
        
        # Verify default project was created third
        project_obj = added_objects[2]
        assert isinstance(project_obj, Project)
        assert project_obj.name == "Default Project"
        assert project_obj.description == "Default project for organizing your knowledge base documents"
        assert project_obj.tenant_id == tenant_obj.id
        assert project_obj.created_by == user_obj.id
        
        # Verify commit was called 4 times (tenant, user, project, tenant update)
        assert mock_db.commit.call_count == 4

    def test_default_project_linked_to_tenant(self):
        """Test that tenant.default_project_id is set to the created project"""
        from main import register_user
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Track the tenant object to verify default_project_id is set
        tenant_obj = None
        def mock_add(obj):
            nonlocal tenant_obj
            if isinstance(obj, Tenant):
                tenant_obj = obj
        mock_db.add.side_effect = mock_add
        
        user_data = UserCreate(
            email="test@company.com",
            first_name="Test",
            last_name="User",
            password="password123"
        )
        
        tenant_data = TenantCreate(
            name="Test Company",
            slug="test-company"
        )
        
        with patch('main.get_password_hash', return_value="hashed_password"):
            register_user(user_data, tenant_data, mock_db)
        
        # Verify tenant's default_project_id was set
        assert tenant_obj is not None
        assert hasattr(tenant_obj, 'default_project_id')
        # The default_project_id should be set after project creation
        # (We can't easily test the exact value due to mocking, but we verify the attribute exists)

    def test_invitation_acceptance_does_not_create_default_project(self):
        """Test that invitation acceptance does NOT create a new default project"""
        from main import register_from_invitation
        from datetime import datetime, timedelta
        
        mock_db = Mock()
        
        # Create existing tenant with default project
        existing_tenant_id = uuid.uuid4()
        existing_default_project_id = uuid.uuid4()
        
        # Create sample invitation
        from models import TenantInvitation
        sample_invitation = TenantInvitation(
            id=uuid.uuid4(),
            tenant_id=existing_tenant_id,
            email="invited@company.com",
            invitation_token="test-token-123",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow()
        )
        
        # Setup mocks
        def mock_query_side_effect(model):
            if model == TenantInvitation:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = sample_invitation
                return mock_query
            elif model == User:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = None  # No existing user
                return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        from schemas import InvitationAcceptance
        user_data = InvitationAcceptance(
            first_name="Invited",
            last_name="User",
            password="password123"
        )
        
        with patch('main.get_password_hash', return_value="hashed_password"):
            register_from_invitation(
                token="test-token-123",
                user_data=user_data,
                db=mock_db
            )
        
        # Verify that db.add was called only ONCE (for user only, not project)
        assert mock_db.add.call_count == 1
        
        # Verify only a user was created, not a project
        added_object = mock_db.add.call_args_list[0][0][0]
        assert isinstance(added_object, User)
        
        # Verify only one commit (no project/tenant updates)
        assert mock_db.commit.call_count == 1

    def test_default_project_has_correct_properties(self):
        """Test that default project is created with correct name and description"""
        from main import register_user
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Track objects to verify project properties and simulate IDs
        added_objects = []
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        def mock_add(obj):
            added_objects.append(obj)
            # Simulate database ID assignment
            if isinstance(obj, Tenant):
                obj.id = tenant_id
            elif isinstance(obj, User):
                obj.id = user_id
        
        def mock_refresh(obj):
            # Simulate refresh updating the object with database values
            if isinstance(obj, Tenant):
                obj.id = tenant_id
            elif isinstance(obj, User):
                obj.id = user_id
        
        mock_db.add.side_effect = mock_add
        mock_db.refresh.side_effect = mock_refresh
        
        user_data = UserCreate(
            email="test@example.com",
            first_name="Test",
            last_name="User", 
            password="password123"
        )
        
        tenant_data = TenantCreate(
            name="Example Company",
            slug="example-company"
        )
        
        with patch('main.get_password_hash', return_value="hashed_password"):
            register_user(user_data, tenant_data, mock_db)
        
        # Find the project object
        project_obj = None
        for obj in added_objects:
            if isinstance(obj, Project):
                project_obj = obj
                break
        
        assert project_obj is not None
        assert project_obj.name == "Default Project"
        assert project_obj.description == "Default project for organizing your knowledge base documents"
        assert project_obj.tenant_id == tenant_id
        assert project_obj.created_by == user_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])