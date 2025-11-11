# JiraJitsu

A Python 3.10+ CLI tool for migrating issue tickets from JIRA to JitBit helpdesk, preserving ticket history, comments, attachments, and metadata.

## Features

- **Complete Ticket Migration**: Migrates JIRA issues to JitBit including:
  - Issue summary, description, and status
  - Original assignees and creators
  - Creation and resolution timestamps
  - Comments with original authors and timestamps
  - File attachments (with smart filtering)

- **Enhanced Metadata Preservation**:
  - Tracks and preserves original JIRA assignee information
  - Maintains original creation and resolution dates
  - Links comment authors to JitBit users by email
  - Preserves comment timestamps
  - Stores original JIRA assignee in custom field

- **Smart User Management**:
  - **Auto-creates missing JitBit users by default** (with `--ignore-missing-users` to disable)
  - Automatically grants technician permissions for assigned categories
  - Validates technician status before assignment
  - Falls back to default user for invalid assignments
  - Handles missing or anonymous comment authors

- **Duplicate Detection**:
  - Prevents recreating already-migrated tickets
  - Checks for existing tickets in JitBit before migration
  - Skips duplicate comments based on timestamps

- **Content Formatting Options**:
  - Default: JIRA wiki markup with color tags removed
  - `--html` flag: HTML-rendered content with internal images stripped
  - Cleaner, more readable content in JitBit

- **Interactive Setup Wizard**:
  - `jirajitsu setup` command for guided configuration
  - Loads existing settings as defaults
  - Validates API connections
  - Smart authentication method detection
  - Automatic configuration backups

- **Comprehensive CLI Interface**:
  - Rich console UI with tables and progress bars
  - Multiple commands for setup, validation, and migration
  - Dry-run mode for previewing migrations
  - Detailed migration statistics and summary tables
  - Manual API testing tools

- **Flexible Authentication**:
  - JIRA Cloud API tokens (email + token)
  - JIRA Server/DC Personal Access Tokens (PAT)
  - JitBit token or basic authentication
  - Hybrid configuration (environment variables for secrets, YAML for settings)

- **Secure Configuration**:
  - python-dotenv integration
  - No hardcoded credentials
  - Automatic config file backups

- **Flexible Attachment Handling**:
  - NEW_ONLY mode: Skip re-downloading existing attachments
  - DELETE_REFETCH mode: Re-download all attachments
  - Automatic filtering of small files (< 5KB logos/icons)

- **Robust Error Handling**:
  - Comprehensive logging with rotating file handlers
  - Failed tickets automatically moved to "deleted" category
  - Continues processing on individual ticket failures
  - Detailed error reporting and validation

- **Filter Pagination**:
  - Handles JIRA filters with >1000 issues automatically
  - Supports up to 10,000 issues per migration

## Requirements

- Python 3.10 or higher
- JIRA instance with REST API access
- JitBit helpdesk with API access
- Local storage for attachment caching

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd jirajitsu
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the interactive setup wizard

The easiest way to configure JiraJitsu is using the interactive setup wizard:

```bash
jirajitsu setup
```

The wizard will guide you through:
- JIRA API configuration (URL, authentication method, credentials)
- JitBit API configuration (URL, authentication method, credentials)
- Migration settings (category IDs, default assignee, filter)
- Validation of API connections
- Automatic configuration file creation

### Manual Configuration (Alternative)

If you prefer to configure manually:

#### Create .env file (for secrets)

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```ini
# JitBit API Credentials
JITBIT_API_URL=https://your-company.jitbit.com/helpdesk/api
JITBIT_AUTH_METHOD=token  # or "basic"
JITBIT_TOKEN=your_jitbit_api_token
# OR for basic auth:
# JITBIT_USER=your_jitbit_username
# JITBIT_PWD=your_jitbit_password

# JIRA API Credentials
JIRA_API_URL=https://your-jira-instance.com/rest/api/2
JIRA_AUTH_METHOD=token  # Options: "token" or "basic"
JIRA_TOKEN=your_jira_token
# For JIRA Cloud, also include:
JIRA_USER=your.email@company.com
# OR for basic auth:
# JIRA_USER=your_jira_username
# JIRA_PWD=your_jira_password
```

#### Create config.yml file (for settings)

```bash
cp config/config.yml.example config/config.yml
```

Edit `config/config.yml`:

```yaml
# Logging Configuration
log_dir: logs/
log_max_bytes: 10485760  # 10MB
log_backup_count: 5

# JitBit Settings
jitbit_migrate_category_id: 12345  # Your migration category ID
jitbit_delete_category_id: 12346   # Your deleted items category ID
jitbit_default_assign_email: default@yourcompany.com
jitbit_jira_assignee_field_id: 66782  # Custom field for storing JIRA assignee

# Rate Limiting (optional)
jitbit_rate_limit_default: 90  # Calls per minute
jitbit_rate_limit_restricted: 60  # Calls per minute for restricted endpoints
jitbit_rate_limit_retry_delay: 60  # Seconds to wait on rate limit
jitbit_rate_limit_max_retries: 3

# JIRA Settings
jira_filter_id: 10000  # Your JIRA filter ID for migration
jira_tag_field: customfield_10800  # Custom field for tagging migrated issues

# Attachment Settings
fetch_attachments: NEW_ONLY  # Options: NEW_ONLY or DELETE_REFETCH
attachment_folder: /path/to/attachments
```

### 4. Create required directories

```bash
mkdir -p logs
mkdir -p /path/to/attachments  # Use the same path from config.yml
```

## Usage

### Verify Configuration

Test your API connections:

```bash
jirajitsu config test-connection
```

View current configuration:

```bash
jirajitsu config show
```

### List Available Resources

List JIRA projects:

```bash
jirajitsu list projects
```

List JIRA filters:

```bash
jirajitsu list filters
```

List JitBit categories:

```bash
jirajitsu list categories
```

### Validate Configuration

Validate user mappings:

```bash
jirajitsu validate users
```

Validate status mappings:

```bash
jirajitsu validate status
```

### Migration

#### Preview Migration (Dry Run)

Preview what would be migrated without actually migrating:

```bash
jirajitsu migrate --dry-run
```

Limit preview to first 10 issues:

```bash
jirajitsu migrate --dry-run --limit 10
```

#### Run Full Migration

Migrate using default filter from config:

```bash
jirajitsu migrate
```

Migrate with HTML-rendered content (cleaner formatting):

```bash
jirajitsu migrate --html
```

Migrate specific issues:

```bash
jirajitsu migrate --issues PROJ-123,PROJ-456,PROJ-789
```

Migrate using custom JQL:

```bash
jirajitsu migrate --jql "project = PROJ AND status = Done"
```

Migrate specific project:

```bash
jirajitsu migrate --project PROJ
```

Migrate project with issue range:

```bash
jirajitsu migrate --project PROJ --range 100:200
```

Disable auto-create users (use default assignee for missing users):

```bash
jirajitsu migrate --ignore-missing-users
```

### Testing with a Single Issue

Test migration with a specific issue:

```bash
jirajitsu test --issue PROJ-123
```

### Manual API Testing

Test JitBit API endpoints directly:

```bash
# Get user by email
jirajitsu jitapi UserByEmail --email user@example.com

# Get ticket details
jirajitsu jitapi ticket --id 12345

# List categories
jirajitsu jitapi Categories
```

### User Management

Create a new JitBit user:

```bash
jirajitsu users create --email user@example.com --first-name John --last-name Doe
```

### Setting Log Level

All commands support `--log-level`:

```bash
jirajitsu --log-level debug migrate
jirajitsu --log-level info list projects
jirajitsu --log-level warning validate users
```

## How It Works

### Migration Process

1. **Authentication**: Validates JIRA and JitBit credentials via API
2. **Duplicate Check**: Checks if ticket already exists in JitBit (skips if found)
3. **Filter Execution**: Runs configured JIRA filter to get issues list (with automatic pagination)
4. **User Cache Pre-loading**: Fetches all JitBit users and technicians upfront
5. **For Each Issue**:
   - Fetches complete issue details from JIRA (with optional HTML rendering)
   - Downloads attachments to local storage
   - Creates ticket in JitBit with original metadata
   - Adds all comments with timestamps (skips duplicates)
   - Uploads attachments
   - Sets assignee (with technician validation and auto-creation)
   - Updates ticket with final status and close date
   - Optionally tags issue in JIRA
6. **Summary Report**: Displays detailed migration statistics table

### Content Formatting

**Default (Wiki Markup Mode)**:
- Uses JIRA's raw wiki markup
- Automatically removes color tags (`{color:...}`)
- Preserves basic formatting

**HTML Mode (`--html` flag)**:
- Uses JIRA's HTML-rendered content
- Cleaner formatting and structure
- Automatically strips internal images (192.168.x.x URLs)
- Better for complex formatting

### User Management

**Auto-Create Users (Default)**:
- Automatically creates missing JitBit users from JIRA info
- Grants technician permissions for assigned categories
- Tracks created users in migration summary

**Disable Auto-Create (`--ignore-missing-users`)**:
- Uses default assignee for all missing users
- Useful for testing or restricted environments

**User Mapping**:
- Maps JIRA users to JitBit users by email address
- Validates that assignees have technician flag in JitBit
- Falls back to default user for:
  - Invalid email addresses
  - Users not found in JitBit (when auto-create disabled)
  - Non-technician users
  - Anonymous commenters

### Duplicate Detection

- Before creating each ticket, checks if it already exists in JitBit
- Searches by JIRA key in ticket subject
- Skips ticket creation if found (reports as "updated")
- Also prevents duplicate comments using timestamp comparison

### Attachment Handling

- Downloads attachments to `attachment_folder/ISSUE-KEY/`
- Skips files < 5KB (typically logos/icons)
- Handles duplicate filenames with numeric prefixes
- Two modes:
  - **NEW_ONLY**: Skip if folder exists (faster, for reruns)
  - **DELETE_REFETCH**: Always re-download (slower, ensures latest)

### Error Recovery

- Individual ticket failures don't stop migration
- Failed tickets moved to "deleted" category
- All errors logged with full details
- Progress bar shows migration status
- Summary table shows success/failure counts

### Filter Pagination

- Automatically handles JIRA filters with >1000 issues
- Paginates API requests to fetch all results
- Supports up to 10,000 total issues per migration

## CLI Commands Reference

### Main Commands

- `jirajitsu setup` - Interactive setup wizard
- `jirajitsu migrate` - Migrate issues from JIRA to JitBit
- `jirajitsu test` - Test migration with a single issue
- `jirajitsu config` - Configuration management
- `jirajitsu list` - List resources (projects, filters, categories, etc.)
- `jirajitsu validate` - Validate configuration and mappings
- `jirajitsu users` - User management operations
- `jirajitsu jitapi` - Manual JitBit API testing

### Common Options

- `--log-level` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--help` - Show help for any command

For detailed command usage, see [CLI_USAGE_GUIDE.md](CLI_USAGE_GUIDE.md)

## API Methods

### JiraApi

- `check_url_and_user()`: Validate JIRA connection
- `get_filter_for_id(filter_id)`: Get filter search URL
- `get_filter(url)`: Execute filter and return issues (with pagination)
- `get_issue_info(key, fetch_rendered)`: Get detailed issue information
- `get_attachment(key, issue_info)`: Download all attachments
- `post_tag(key, tag)`: Tag issue in JIRA (optional)
- `get_projects()`: List all JIRA projects
- `get_filters()`: List user's favorite filters
- `get_issues_by_jql(jql)`: Execute custom JQL query
- `get_all_users()`: Fetch all JIRA users

### JitbitApi

- `check_url_and_user()`: Validate JitBit connection
- `post_ticket(...)`: Create new ticket
- `post_comment(...)`: Add comment to ticket
- `post_attach_file(...)`: Upload attachment
- `get_user_id_by_email(email)`: Get user ID from email
- `get_user_is_technician(user_id)`: Check technician flag
- `post_update_ticket(**kwargs)`: Universal ticket update method
- `post_set_ticket_status(...)`: Set ticket status (New/Closed)
- `post_mark_deleted(...)`: Move ticket to deleted category
- `get_ticket(ticket_id)`: Fetch ticket details
- `preload_user_caches()`: Pre-load all users and technicians
- `create_user(...)`: Create new JitBit user
- `add_category_tech_permission(...)`: Grant technician permissions

## Development

### Running Tests

```bash
pytest tests/
```

### Running Tests with Coverage

```bash
pytest --cov=jirajitsu tests/
```

### Code Style

This project uses Python 3.10+ type hints and follows PEP 8 style guidelines.

## Migration from Sandpiper

JiraJitsu is based on the [sandpiper](https://github.com/ajegam/sandpiper) project with significant enhancements:

### What's New in JiraJitsu v1.2:

1. **Full CLI Interface**: Rich command-line interface with multiple commands
2. **Interactive Setup**: Guided setup wizard with validation
3. **HTML Rendering**: Optional HTML content rendering with `--html` flag
4. **Auto-Create Users**: Automatically creates missing JitBit users
5. **Duplicate Detection**: Prevents recreating existing tickets
6. **Migration Statistics**: Detailed summary tables after migration
7. **Filter Pagination**: Handles filters with >1000 issues
8. **Enhanced Validation**: Multiple validation commands
9. **User Management**: Create users and manage permissions via CLI
10. **Manual API Testing**: `jitapi` command for testing endpoints
11. **Token Authentication**: Support for API tokens and PATs
12. **Content Cleaning**: Automatic removal of JIRA markup tags
13. **Rate Limiting**: Configurable API rate limiting
14. **Custom User-Agent**: Identifies traffic in server logs

### What's New in JiraJitsu v1.1:

1. **Python 3.10+ Compatibility**: Complete rewrite for modern Python
2. **Enhanced Security**: Environment-based credential management
3. **Better User Tracking**: Comment author preservation with timestamps
4. **Assignee Management**: Original assignee name preservation in ticket body
5. **Timestamp Preservation**: Original creation and resolution dates maintained
6. **Technician Validation**: Automatic validation of user permissions
7. **Improved API Methods**: Universal `post_update_ticket()` method
8. **Type Hints**: Full type annotations for better IDE support
9. **Comprehensive Tests**: pytest-based test suite
10. **Better Error Handling**: Python 3 exception handling throughout

### Breaking Changes from Sandpiper:

- Renamed package from `sandpiper` to `jirajitsu`
- Changed log alias from `sandpiper_log` to `jirajitsu_log`
- Credentials now required in `.env` file instead of `config.yml`
- Python 2 support removed
- Requires Python 3.10+ (for modern type hints)
- **Script invocation replaced with CLI commands**
- Configuration structure updated

## Troubleshooting

### Configuration Issues

Run the setup wizard to reconfigure:
```bash
jirajitsu setup
```

Or test your current configuration:
```bash
jirajitsu config test-connection
```

### Import Errors

Ensure JiraJitsu is installed properly:
```bash
pip install -e .
```

### Attachment Folder Errors

Verify the attachment folder exists and has write permissions:
```bash
mkdir -p /path/to/attachments
chmod 755 /path/to/attachments
```

### API Authentication Failures

Test your connection:
```bash
jirajitsu config test-connection
```

Common issues:
- Verify credentials in `.env` are correct
- Check that API URLs don't have trailing slashes
- Ensure JIRA/JitBit users have API access permissions
- For JIRA Cloud, ensure you're using email + API token (not password)
- For JIRA Server/DC PAT, ensure JIRA_USER is not set

### User Not Found Errors

Check user mappings:
```bash
jirajitsu validate users
```

Common issues:
- Verify email addresses match between JIRA and JitBit
- Enable auto-create users (default behavior)
- Or use `--ignore-missing-users` to assign to default user
- Ensure default assignee email is valid

### Filter Returns No Issues

Verify your filter:
```bash
jirajitsu list filters
```

Test with custom JQL:
```bash
jirajitsu migrate --jql "project = YOURPROJECT" --dry-run
```

### Rate Limiting

If you hit rate limits, adjust in `config.yml`:
```yaml
jitbit_rate_limit_default: 60  # Reduce from 90
jitbit_rate_limit_retry_delay: 120  # Increase wait time
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original [sandpiper](https://github.com/ajegam/sandpiper) project by ajegam
- Fork by andy@clownshoemotorsports.com (November 2023)
- Rebranded and enhanced as JiraJitsu (2024)

## Support

For issues, questions, or contributions, please open an issue on the project repository.
