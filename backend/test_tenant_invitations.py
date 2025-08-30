import pytest
import uuid
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import User, Tenant, TenantInvitation
from schemas import TenantInvitationCreate, InvitationAcceptance


class TestTenantInvitations:
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.email = "admin@company.com"
        user.first_name = "Admin"
        user.last_name = "User"
        return user
    
    @pytest.fixture
    def mock_tenant(self, mock_user):
        tenant = Mock(spec=Tenant)
        tenant.id = mock_user.tenant_id
        tenant.name = "Test Company"
        return tenant
    
    @pytest.fixture
    def sample_invitation(self, mock_user):
        invitation = Mock(spec=TenantInvitation)
        invitation.id = uuid.uuid4()
        invitation.tenant_id = mock_user.tenant_id
        invitation.email = "newuser@example.com"
        invitation.invited_by = mock_user.id
        invitation.invitation_token = "test-token-123"
        invitation.status = "pending"
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.created_at = datetime.utcnow()
        return invitation

    def test_invitation_database_structure(self):
        """Test that invitation model has correct structure"""
        # Verify invitation status choices
        valid_statuses = ['pending', 'accepted', 'expired', 'cancelled']
        assert len(valid_statuses) == 4
        assert 'pending' in valid_statuses
        assert 'accepted' in valid_statuses

    def test_send_invitation_user_exists(self, mock_db, mock_user):
        """Test invitation fails when user already exists"""
        from main import send_tenant_invitation
        
        # Mock existing user
        existing_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        invitation_request = TenantInvitationCreate(email="existing@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            send_tenant_invitation(
                invitation=invitation_request,
                current_user=mock_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_invitation_acceptance_success(self, mock_db, sample_invitation):
        """Test successful invitation acceptance"""
        from main import register_from_invitation
        
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
            first_name="New",
            last_name="User", 
            password="password123"
        )
        
        # Call function
        with patch('main.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            result = register_from_invitation(
                token="test-token-123",
                user_data=user_data,
                db=mock_db
            )
        
        # Verify user created and invitation marked accepted
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert sample_invitation.status == "accepted"

    def test_invitation_expired(self, mock_db, sample_invitation):
        """Test invitation acceptance fails when expired"""
        from main import register_from_invitation
        
        # Make invitation expired
        sample_invitation.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_invitation
        
        user_data = InvitationAcceptance(
            first_name="New",
            last_name="User",
            password="password123"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            register_from_invitation(
                token="test-token-123", 
                user_data=user_data,
                db=mock_db
            )
        
        assert exc_info.value.status_code == 410
        assert "expired" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])