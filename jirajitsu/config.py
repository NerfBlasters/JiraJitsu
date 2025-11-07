
import os
import yaml
from collections import OrderedDict
from dotenv import load_dotenv

"""
Sets up constants and reads parameters from config.yml and .env
Secrets are loaded from .env, non-sensitive settings from config.yml
"""

MODEL_NAME = 'JiraJitsu - Migrating issue tickets from JIRA to JitBit'

# Load environment variables from .env file
load_dotenv()

# yaml.load by default gives unordered dictionary. This code preserves the order
# That way it is easy to maintain the yaml file.
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

# Constants
LOG_ALIAS = 'jirajitsu_log'
CONFIG_FILE = 'config.yml'
JITBIT_MIGRATION_SUCCESS = 'JITBIT_MIGRATION_SUCCESS'
DELETE_REFETCH = 'DELETE_REFETCH'
NEW_ONLY = 'NEW_ONLY'

# Configuration file
base_dir_name = os.path.dirname(os.path.abspath(__file__))
dir_name = base_dir_name + os.sep + '..' + os.sep + 'config'
config_path = os.path.join(dir_name, CONFIG_FILE)

# Load YAML config (non-sensitive settings)
# Handle missing config file gracefully for commands like 'setup'
try:
    if os.path.exists(config_path):
        data = ordered_load(open(config_path, 'r'), yaml.SafeLoader)
    else:
        data = {}
except Exception:
    data = {}

# Logging
LOG_DIR = data.get('log_dir', base_dir_name + os.sep + '..' + os.sep + 'logs')
LOG_MAX_BYTES = data.get('log_max_bytes', 10485760)
LOG_BACKUP_COUNT = data.get('log_backup_count', 5)

# JitBit Configuration - Load secrets from environment variables
# These may be None if .env doesn't exist yet (e.g., during setup)
JITBIT_API_URL = os.getenv('JITBIT_API_URL')
JITBIT_AUTH_METHOD = os.getenv('JITBIT_AUTH_METHOD', 'basic')
JITBIT_USER = os.getenv('JITBIT_USER')
JITBIT_PWD = os.getenv('JITBIT_PWD')
JITBIT_TOKEN = os.getenv('JITBIT_TOKEN')
JITBIT_MIGRATE_CATEGORY_ID = data.get('jitbit_migrate_category_id', None)
JITBIT_DELETE_CATEGORY_ID = data.get('jitbit_delete_category_id', None)
JITBIT_DEFAULT_ASSIGN_EMAIL = data.get('jitbit_default_assign_email', None)
JITBIT_JIRA_ASSIGNEE_FIELD_ID = data.get('jitbit_jira_assignee_field_id', 66782)  # Custom field for original Jira assignee

# JIRA Configuration - Load secrets from environment variables
# These may be None if .env doesn't exist yet (e.g., during setup)
JIRA_API_URL = os.getenv('JIRA_API_URL')
JIRA_AUTH_METHOD = os.getenv('JIRA_AUTH_METHOD', 'basic')
JIRA_USER = os.getenv('JIRA_USER')
JIRA_PWD = os.getenv('JIRA_PWD')
JIRA_TOKEN = os.getenv('JIRA_TOKEN')
JIRA_FILTER_ID = data.get('jira_filter_id', None)
JIRA_TAG_FIELD = data.get('jira_tag_field', 'customfield_10800')

# Attachment settings
FETCH_ATTACHMENTS = data.get('fetch_attachments', 'NEW_ONLY')
ATTACHMENT_FOLDER = data.get('attachment_folder', None)
# Only validate directory if it's configured
if ATTACHMENT_FOLDER and not os.path.isdir(ATTACHMENT_FOLDER):
    # Don't fail at import time - let individual commands handle this
    pass

# Rate Limiting Configuration
# JitBit API rate limits per their docs:
# - Most resource-intensive methods: 90 requests per minute
# - Search and UserByEmail: 60 requests per minute
JITBIT_RATE_LIMIT_DEFAULT = data.get('jitbit_rate_limit_default', 90)  # requests per minute
JITBIT_RATE_LIMIT_RESTRICTED = data.get('jitbit_rate_limit_restricted', 60)  # for Search and UserByEmail
JITBIT_RATE_LIMIT_RETRY_DELAY = data.get('jitbit_rate_limit_retry_delay', 60)  # seconds to wait after 429
JITBIT_RATE_LIMIT_MAX_RETRIES = data.get('jitbit_rate_limit_max_retries', 3)  # max retry attempts

