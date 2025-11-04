"""
Tests for JIRA API wrapper
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.fixture
def jira_api(mock_env_vars):
    """Create JiraApi instance with mocked config"""
    config_yaml = """
log_dir: logs/
jitbit_migrate_category_id: 12345
jitbit_default_assign_email: test@example.com
jira_filter_id: 10000
jira_tag_field: customfield_10800
attachment_folder: /tmp/attachments
"""
    os.makedirs('/tmp/attachments', exist_ok=True)

    with patch('builtins.open', MagicMock(return_value=MagicMock())):
        with patch('yaml.load', return_value={
            'log_dir': 'logs/',
            'jitbit_migrate_category_id': 12345,
            'jitbit_default_assign_email': 'test@example.com',
            'jira_filter_id': 10000,
            'jira_tag_field': 'customfield_10800',
            'attachment_folder': '/tmp/attachments'
        }):
            from jirajitsu.jira_api import JiraApi
            return JiraApi()


def test_jira_api_initialization(jira_api):
    """Test JiraApi initialization"""
    assert jira_api is not None


@patch('jirajitsu.jira_api.requests.get')
def test_check_url_and_user_success(mock_get, jira_api):
    """Test successful URL and user check"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = jira_api.check_url_and_user()
    assert result is True


@patch('jirajitsu.jira_api.requests.get')
def test_check_url_and_user_failure(mock_get, jira_api):
    """Test failed URL and user check"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_get.return_value = mock_response

    result = jira_api.check_url_and_user()
    assert result is False


@patch('jirajitsu.jira_api.requests.get')
def test_get_issue_info_success(mock_get, jira_api, sample_jira_issue):
    """Test successful issue info retrieval"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_jira_issue
    mock_get.return_value = mock_response

    success, data = jira_api.get_issue_info('TEST-123')
    assert success is True
    assert data == sample_jira_issue


@patch('jirajitsu.jira_api.requests.get')
def test_get_issue_info_failure(mock_get, jira_api):
    """Test failed issue info retrieval"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    success, data = jira_api.get_issue_info('INVALID-999')
    assert success is False
    assert data is None
