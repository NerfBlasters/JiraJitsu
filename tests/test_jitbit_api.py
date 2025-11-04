"""
Tests for JitBit API wrapper
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.fixture
def jitbit_api(mock_env_vars):
    """Create JitbitApi instance with mocked config"""
    os.makedirs('/tmp/attachments', exist_ok=True)

    with patch('builtins.open', MagicMock(return_value=MagicMock())):
        with patch('yaml.load', return_value={
            'log_dir': 'logs/',
            'jitbit_migrate_category_id': 12345,
            'jitbit_default_assign_email': 'test@example.com',
            'jira_filter_id': 10000,
            'attachment_folder': '/tmp/attachments'
        }):
            from jirajitsu.jitbit_api import JitbitApi
            return JitbitApi()


def test_jitbit_api_initialization(jitbit_api):
    """Test JitbitApi initialization"""
    assert jitbit_api is not None


@patch('jirajitsu.jitbit_api.requests.get')
def test_check_url_and_user_success(mock_get, jitbit_api):
    """Test successful URL and user check"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'authorized': True}
    mock_get.return_value = mock_response

    result = jitbit_api.check_url_and_user()
    assert result is True


@patch('jirajitsu.jitbit_api.requests.post')
def test_post_ticket_success(mock_post, jitbit_api):
    """Test successful ticket creation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '12345'
    mock_post.return_value = mock_response

    ticket_id = jitbit_api.post_ticket(
        'TEST-1',
        category_id=100,
        subject='Test Subject',
        body='Test Body',
        priority_id=0,
        created_by=1
    )
    assert ticket_id == 12345


@patch('jirajitsu.jitbit_api.requests.get')
def test_get_user_id_by_email_success(mock_get, jitbit_api):
    """Test successful user ID lookup"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'UserID': 42}
    mock_get.return_value = mock_response

    user_id = jitbit_api.get_user_id_by_email('test@example.com')
    assert user_id == 42


@patch('jirajitsu.jitbit_api.requests.get')
def test_get_user_is_technician_true(mock_get, jitbit_api):
    """Test technician flag check returns True"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'IsTechie': True}
    mock_get.return_value = mock_response

    is_tech = jitbit_api.get_user_is_technician(42)
    assert is_tech is True


@patch('jirajitsu.jitbit_api.requests.get')
def test_get_user_is_technician_false(mock_get, jitbit_api):
    """Test technician flag check returns False"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'IsTechie': False}
    mock_get.return_value = mock_response

    is_tech = jitbit_api.get_user_is_technician(42)
    assert is_tech is False


@patch('jirajitsu.jitbit_api.requests.post')
def test_post_update_ticket_success(mock_post, jitbit_api):
    """Test universal update ticket method"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = jitbit_api.post_update_ticket(
        'TEST-1',
        ticket_id=123,
        assignedUserId=5,
        date='2024-01-01'
    )
    assert result is True


@patch('jirajitsu.jitbit_api.requests.post')
def test_post_comment_success(mock_post, jitbit_api):
    """Test successful comment posting"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = jitbit_api.post_comment('TEST-1', 123, 'Test comment', 1)
    assert result is True
