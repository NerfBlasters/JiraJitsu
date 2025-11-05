"""
Tests for JitBit API wrapper
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import time


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


@patch('jirajitsu.jitbit_api.requests.request')
def test_check_url_and_user_success(mock_request, jitbit_api):
    """Test successful URL and user check"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'authorized': True}
    mock_request.return_value = mock_response

    result = jitbit_api.check_url_and_user()
    assert result is True


@patch('jirajitsu.jitbit_api.requests.request')
def test_post_ticket_success(mock_request, jitbit_api):
    """Test successful ticket creation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '12345'
    mock_request.return_value = mock_response

    ticket_id = jitbit_api.post_ticket(
        'TEST-1',
        category_id=100,
        subject='Test Subject',
        body='Test Body',
        priority_id=0,
        created_by=1
    )
    assert ticket_id == 12345


@patch('jirajitsu.jitbit_api.requests.request')
def test_get_user_id_by_email_success(mock_request, jitbit_api):
    """Test successful user ID lookup"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'UserID': 42}
    mock_request.return_value = mock_response

    user_id = jitbit_api.get_user_id_by_email('test@example.com')
    assert user_id == 42


@patch('jirajitsu.jitbit_api.requests.request')
def test_get_user_is_technician_true(mock_request, jitbit_api):
    """Test technician flag check returns True"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'IsTech': True}
    mock_request.return_value = mock_response

    is_tech = jitbit_api.get_user_is_technician(42)
    assert is_tech is True


@patch('jirajitsu.jitbit_api.requests.request')
def test_get_user_is_technician_false(mock_request, jitbit_api):
    """Test technician flag check returns False"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'IsTech': False}
    mock_request.return_value = mock_response

    is_tech = jitbit_api.get_user_is_technician(42)
    assert is_tech is False


@patch('jirajitsu.jitbit_api.requests.request')
def test_post_update_ticket_success(mock_request, jitbit_api):
    """Test universal update ticket method"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    result = jitbit_api.post_update_ticket(
        'TEST-1',
        ticket_id=123,
        assignedUserId=5,
        date='2024-01-01'
    )
    assert result is True


@patch('jirajitsu.jitbit_api.requests.request')
def test_post_comment_success(mock_request, jitbit_api):
    """Test successful comment posting"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    result = jitbit_api.post_comment('TEST-1', 123, 'Test comment', 1)
    assert result is True


# Rate Limiting Tests

@patch('jirajitsu.jitbit_api.config.JITBIT_RATE_LIMIT_DEFAULT', 5)  # Set low limit for testing
@patch('jirajitsu.jitbit_api.requests.request')
@patch('jirajitsu.jitbit_api.time.sleep')
def test_rate_limiting_enforced(mock_sleep, mock_request, jitbit_api):
    """Test that rate limiting enforces delay when limit is reached"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '1'
    mock_request.return_value = mock_response

    # Make 6 rapid requests (limit is 5)
    for i in range(6):
        jitbit_api.post_ticket(
            f'TEST-{i}',
            category_id=100,
            subject='Test',
            body='Test',
            priority_id=0,
            created_by=1
        )

    # Should have triggered at least one sleep due to rate limiting
    assert mock_sleep.call_count >= 1


@patch('jirajitsu.jitbit_api.config.JITBIT_RATE_LIMIT_RESTRICTED', 3)  # Low limit for restricted endpoints
@patch('jirajitsu.jitbit_api.requests.request')
@patch('jirajitsu.jitbit_api.time.sleep')
def test_restricted_endpoint_rate_limiting(mock_sleep, mock_request, jitbit_api):
    """Test that restricted endpoints (like UserByEmail) have lower rate limits"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'UserID': 42}
    mock_request.return_value = mock_response

    # Make 4 rapid requests to restricted endpoint (limit is 3)
    for i in range(4):
        jitbit_api.get_user_id_by_email(f'test{i}@example.com')

    # Should have triggered at least one sleep
    assert mock_sleep.call_count >= 1


@patch('jirajitsu.jitbit_api.config.JITBIT_RATE_LIMIT_MAX_RETRIES', 2)
@patch('jirajitsu.jitbit_api.config.JITBIT_RATE_LIMIT_RETRY_DELAY', 1)
@patch('jirajitsu.jitbit_api.requests.request')
@patch('jirajitsu.jitbit_api.time.sleep')
def test_429_retry_logic(mock_sleep, mock_request, jitbit_api):
    """Test that 429 responses trigger retry with exponential backoff"""
    # First two attempts return 429, third succeeds
    mock_response_429 = Mock()
    mock_response_429.status_code = 429

    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.text = '12345'

    mock_request.side_effect = [mock_response_429, mock_response_429, mock_response_success]

    result = jitbit_api.post_ticket(
        'TEST-1',
        category_id=100,
        subject='Test',
        body='Test',
        priority_id=0,
        created_by=1
    )

    # Should succeed after retries
    assert result == 12345
    # Should have made 3 requests (2 retries + 1 success)
    assert mock_request.call_count == 3
    # Should have slept twice (once per 429 response)
    # Note: sleep is called for both rate limiting AND 429 retries
    assert mock_sleep.call_count >= 2


@patch('jirajitsu.jitbit_api.config.JITBIT_RATE_LIMIT_MAX_RETRIES', 1)
@patch('jirajitsu.jitbit_api.requests.request')
def test_429_max_retries_exceeded(mock_request, jitbit_api):
    """Test that request fails gracefully after max retries on 429"""
    mock_response_429 = Mock()
    mock_response_429.status_code = 429
    mock_request.return_value = mock_response_429

    # Should return -1 (error) after max retries
    result = jitbit_api.post_ticket(
        'TEST-1',
        category_id=100,
        subject='Test',
        body='Test',
        priority_id=0,
        created_by=1
    )

    assert result == -1
    # Should have tried max_retries + 1 times (2 total)
    assert mock_request.call_count == 2


def test_rate_limit_sliding_window(jitbit_api):
    """Test that rate limiting uses sliding window (old requests expire)"""
    # Manually add old timestamps to rate limit history
    old_time = time.time() - 65  # 65 seconds ago (outside 1 minute window)

    # Fill up the default rate limit with old timestamps
    for i in range(90):  # Default limit is 90
        jitbit_api._request_history_default.append(old_time)

    # Check that we can still make a request because old timestamps should be removed
    url = 'http://test.com/ticket'

    # This should not raise an error or cause excessive waiting
    start_time = time.time()
    jitbit_api._check_rate_limit(url)
    elapsed = time.time() - start_time

    # Should be nearly instant since old requests are expired
    assert elapsed < 1.0  # Should take less than 1 second
