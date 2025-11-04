"""
Pytest configuration and fixtures for JiraJitsu tests
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'JITBIT_API_URL': 'https://test.jitbit.com/api',
        'JITBIT_USER': 'test_user',
        'JITBIT_PWD': 'test_password',
        'JIRA_API_URL': 'https://test.jira.com/rest/api/2',
        'JIRA_USER': 'jira_user',
        'JIRA_PWD': 'jira_password'
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def temp_config_file():
    """Create a temporary config.yml file for testing"""
    config_content = """
log_dir: logs/
log_max_bytes: 10485760
log_backup_count: 5
jitbit_migrate_category_id: 12345
jitbit_delete_category_id: 12346
jitbit_default_assign_email: test@example.com
jira_filter_id: 10000
jira_tag_field: customfield_10800
fetch_attachments: NEW_ONLY
attachment_folder: /tmp/attachments
"""
    # Create temporary directory and file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    # Create attachment folder
    os.makedirs('/tmp/attachments', exist_ok=True)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_requests_response():
    """Mock requests response object"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'key': 'value'}
    mock_response.text = 'success'
    return mock_response


@pytest.fixture
def sample_jira_issue():
    """Sample JIRA issue data for testing"""
    return {
        'key': 'TEST-123',
        'fields': {
            'summary': 'Test Issue',
            'description': 'Test description',
            'status': {'name': 'Done'},
            'assignee': {
                'displayName': 'Test User',
                'emailAddress': 'test@example.com'
            },
            'creator': {
                'displayName': 'Creator User',
                'emailAddress': 'creator@example.com'
            },
            'created': '2024-01-01T10:00:00.000+0000',
            'resolutiondate': '2024-01-02T10:00:00.000+0000',
            'attachment': [],
            'comment': {
                'comments': []
            }
        }
    }
