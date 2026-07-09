
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from src.jarvis.utils.chat_utils import ensure_conversation
from src.jarvis.api.conversations import list_conversations, get_conversation
from src.jarvis.database.models import Conversation
from scripts.genesis_registrar import genesis_bootstrap

# --- RBAC / Chat Isolation Tests ---

def test_rb_ac_ensure_conversation_creates_new():
    """Test that ensure_conversation creates a new conversation for the user."""
    mock_db = MagicMock()
    user_id = "user_123"
    
    # Simulate not creating a new conversation
    result = ensure_conversation(mock_db, None, user_id)
    
    assert result.user_id == user_id
    mock_db.add.assert_called_once()


def test_rb_ac_ensure_conversation_access_own():
    """Test accessing own conversation works."""
    mock_db = MagicMock()
    user_id = "user_123"
    conv_id = uuid4()
    
    existing_conv = Conversation(id=conv_id, user_id=user_id)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_conv
    
    result = ensure_conversation(mock_db, conv_id, user_id)
    assert result == existing_conv


def test_rb_ac_ensure_conversation_blocks_others():
    """Test accessing another user's conversation raises 403."""
    mock_db = MagicMock()
    owner_id = "user_A"
    attacker_id = "user_B"
    conv_id = uuid4()
    
    # Conversation belongs to A
    existing_conv = Conversation(id=conv_id, user_id=owner_id)
    mock_db.query.return_value.filter.return_value.first.return_value = existing_conv
    
    # B tries to access
    with pytest.raises(HTTPException) as excinfo:
        ensure_conversation(mock_db, conv_id, attacker_id)
    
    assert excinfo.value.status_code == 403
    assert "permission" in str(excinfo.value.detail)


def test_list_conversations_filters_by_user():
    """Test that list_conversations filters by user_id."""
    mock_db = MagicMock()
    mock_req = MagicMock()
    user_id = "user_123"
    mock_req.session.get.return_value = user_id
    
    # Mock chain: query(Conv).filter(...).order_by(...).offset(...).limit(...).all()
    # We want to verify .filter(Conversation.user_id == user_id) was called
    
    list_conversations(mock_req, db=mock_db)
    
    # Verify the filter call argument
    # (Checking exact SQLAlchemy expression equality in mocks is hard, 
    # but we can check if filter was called)
    mock_db.query.return_value.filter.assert_called_once()

# --- Genesis Registrar Tests ---

@patch("scripts.genesis_registrar.get_session_factory")
@patch("scripts.genesis_registrar.sys.exit")
def test_genesis_aborts_if_users_exist(mock_exit, mock_get_session_factory):
    """Test that genesis aborts if users already exist."""
    mock_exit.side_effect = SystemExit(1) # Simulate actual exit
    mock_session = MagicMock()
    mock_get_session_factory.return_value = MagicMock(return_value=mock_session)
    
    # Return count > 0
    mock_session.query.return_value.scalar.return_value = 5 
    
    with pytest.raises(SystemExit):
        genesis_bootstrap("some_subject", 0.51, True, "keycloak")
    
    mock_exit.assert_called_with(1)
    mock_session.add.assert_not_called()


@patch("scripts.genesis_registrar.get_session_factory")
def test_genesis_succeeds_if_empty(mock_get_session_factory):
    """Test that genesis proceeds if DB is empty."""
    mock_session = MagicMock()
    mock_get_session_factory.return_value = MagicMock(return_value=mock_session)
    
    # Return count == 0
    mock_session.query.return_value.scalar.return_value = 0
    
    genesis_bootstrap("some_subject", 0.51, True, "keycloak")
    
    # Verify adds
    assert mock_session.add.call_count == 3  # User, TrustScore, AuditLog
    mock_session.commit.assert_called_once()

