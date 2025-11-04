"""
Tests for configuration loading
"""
import pytest
import os
from unittest.mock import patch, mock_open
import yaml


def test_env_variables_loaded(mock_env_vars):
    """Test that environment variables are loaded correctly"""
    assert os.getenv('JITBIT_API_URL') == 'https://test.jitbit.com/api'
    assert os.getenv('JITBIT_USER') == 'test_user'
    assert os.getenv('JIRA_API_URL') == 'https://test.jira.com/rest/api/2'


def test_config_constants():
    """Test configuration constants"""
    # Import after mocking environment
    with patch.dict(os.environ, {
        'JITBIT_API_URL': 'https://test.jitbit.com/api',
        'JITBIT_USER': 'test_user',
        'JITBIT_PWD': 'test_password',
        'JIRA_API_URL': 'https://test.jira.com/rest/api/2',
        'JIRA_USER': 'jira_user',
        'JIRA_PWD': 'jira_password'
    }):
        # Create a temporary config file
        config_yaml = """
log_dir: logs/
jitbit_migrate_category_id: 12345
jitbit_default_assign_email: test@example.com
jira_filter_id: 10000
attachment_folder: /tmp/attachments
"""
        os.makedirs('/tmp/attachments', exist_ok=True)

        with patch('builtins.open', mock_open(read_data=config_yaml)):
            # Import config module
            import importlib
            import jirajitsu.config as config
            importlib.reload(config)

            assert config.MODEL_NAME == 'JiraJitsu - Migrating issue tickets from JIRA to JitBit'
            assert config.LOG_ALIAS == 'jirajitsu_log'
            assert config.JITBIT_MIGRATION_SUCCESS == 'JITBIT_MIGRATION_SUCCESS'
            assert config.NEW_ONLY == 'NEW_ONLY'
            assert config.DELETE_REFETCH == 'DELETE_REFETCH'


def test_missing_env_var_raises_assertion():
    """Test that missing required environment variables raise AssertionError"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(AssertionError):
            import importlib
            import jirajitsu.config as config
            importlib.reload(config)
