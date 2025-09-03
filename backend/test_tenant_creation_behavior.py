import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid

from models import User, Tenant, TenantInvitation
from schemas import UserCreate, TenantCreate, InvitationAcceptance


class TestTenantCreationBehavior:
    """Test that tenants are created during signup but NOT during invitation acceptance"""

    def test_regular_registration_creates_tenant(self):
        """Test that /auth/register creates both tenant and user"""
        from main import register_user
        
        # Mock database session
        mock_db = Mock()
        
        # Mock queries to return None (no existing user/tenant)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
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
        
        # Verify that db.add was called three times (tenant, user, default project)
        assert mock_db.add.call_count == 3
        
        # Verify tenant was created first
        first_add_call = mock_db.add.call_args_list[0][0][0]
        assert isinstance(first_add_call, Tenant)
        assert first_add_call.name == "New Company"
        assert first_add_call.slug == "new-company"
        
        # Verify user was created second with tenant_id
        second_add_call = mock_db.add.call_args_list[1][0][0]
        assert isinstance(second_add_call, User)
        assert second_add_call.email == "newuser@company.com"
        assert second_add_call.first_name == "New"
        assert second_add_call.last_name == "User"
        # tenant_id should be set to the created tenant's id
        assert hasattr(second_add_call, 'tenant_id')
        
        # Verify default project was created third
        from models import Project
        third_add_call = mock_db.add.call_args_list[2][0][0]
        assert isinstance(third_add_call, Project)
        assert third_add_call.name == "Default Project"
        assert third_add_call.description == "Default project for organizing your knowledge base documents"
        
        # Verify commit and refresh called
        assert mock_db.commit.call_count == 4  # Tenant, user, project, tenant update
        assert mock_db.refresh.call_count == 4  # Tenant, user, project, tenant update

    def test_invitation_acceptance_does_not_create_tenant(self):
        """Test that /auth/register-from-invitation does NOT create a new tenant"""
        from main import register_from_invitation
        
        # Mock database session
        mock_db = Mock()
        
        # Create existing tenant
        existing_tenant_id = uuid.uuid4()
        
        # Create sample invitation
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
        
        user_data = InvitationAcceptance(
            first_name="Invited",
            last_name="User",
            password="password123"
        )
        
        # Mock password hashing
        with patch('main.get_password_hash', return_value="hashed_password"):
            result = register_from_invitation(
                token="test-token-123",
                user_data=user_data,
                db=mock_db
            )
        
        # Verify that db.add was called only ONCE (for user only, not tenant)
        assert mock_db.add.call_count == 1
        
        # Verify only a user was created, not a tenant
        added_object = mock_db.add.call_args_list[0][0][0]
        assert isinstance(added_object, User)
        assert added_object.email == "invited@company.com"  # From invitation
        assert added_object.first_name == "Invited"
        assert added_object.last_name == "User" 
        assert added_object.tenant_id == existing_tenant_id  # Uses existing tenant
        
        # Verify invitation was marked as accepted
        assert sample_invitation.status == "accepted"
        assert sample_invitation.accepted_at is not None
        
        # Verify only one commit (no tenant creation)
        assert mock_db.commit.call_count == 1

    def test_regular_registration_fails_if_tenant_slug_exists(self):
        """Test that regular registration fails if tenant slug already exists"""
        from main import register_user
        
        mock_db = Mock()
        
        # Mock existing tenant with same slug
        existing_tenant = Tenant(
            id=uuid.uuid4(),
            name="Existing Company",
            slug="company-slug"
        )
        
        def mock_query_side_effect(model):
            if model == User:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = None  # No existing user
                return mock_query
            elif model == Tenant:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = existing_tenant  # Existing tenant
                return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        user_data = UserCreate(
            email="newuser@company.com",
            first_name="New",
            last_name="User",
            password="password123"
        )
        
        tenant_data = TenantCreate(
            name="Another Company",
            slug="company-slug"  # Same slug as existing tenant
        )
        
        # Should raise HTTPException for duplicate slug
        with pytest.raises(HTTPException) as exc_info:
            register_user(user_data, tenant_data, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Tenant slug already exists" in str(exc_info.value.detail)
        
        # Verify no objects were added to database
        assert mock_db.add.call_count == 0

    def test_invitation_acceptance_uses_correct_tenant_id(self):
        """Test that invitation acceptance uses the tenant_id from the invitation"""
        from main import register_from_invitation
        
        mock_db = Mock()
        
        # Create specific tenant ID for testing
        specific_tenant_id = uuid.uuid4()
        
        sample_invitation = TenantInvitation(
            id=uuid.uuid4(),
            tenant_id=specific_tenant_id,  # This should be used for the new user
            email="invited@company.com",
            invitation_token="test-token-456",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow()
        )
        
        def mock_query_side_effect(model):
            if model == TenantInvitation:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = sample_invitation
                return mock_query
            elif model == User:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = None
                return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        user_data = InvitationAcceptance(
            first_name="Test",
            last_name="User",
            password="password123"
        )
        
        with patch('main.get_password_hash', return_value="hashed_password"):
            register_from_invitation(
                token="test-token-456",
                user_data=user_data,
                db=mock_db
            )
        
        # Verify user was created with the invitation's tenant_id
        created_user = mock_db.add.call_args_list[0][0][0]
        assert isinstance(created_user, User)
        assert created_user.tenant_id == specific_tenant_id
        
        # Verify no tenant was created (only one db.add call for user)
        assert mock_db.add.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])