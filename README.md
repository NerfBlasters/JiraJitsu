# JiraJitsu

A Python 3.10+ tool for migrating issue tickets from JIRA to JitBit helpdesk, preserving ticket history, comments, attachments, and metadata.

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

- **Smart User Management**:
  - Validates technician status before assignment
  - Falls back to default user for invalid assignments
  - Handles missing or anonymous comment authors

- **Secure Configuration**:
  - Hybrid configuration approach (environment variables for secrets, YAML for settings)
  - python-dotenv integration
  - No hardcoded credentials

- **Flexible Attachment Handling**:
  - NEW_ONLY mode: Skip re-downloading existing attachments
  - DELETE_REFETCH mode: Re-download all attachments
  - Automatic filtering of small files (< 5KB logos/icons)

- **Robust Error Handling**:
  - Comprehensive logging with rotating file handlers
  - Failed tickets automatically moved to "deleted" category
  - Continues processing on individual ticket failures

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

### 3. Set up configuration

#### Create .env file (for secrets)

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```ini
# JitBit API Credentials
JITBIT_API_URL=https://your-company.jitbit.com/helpdesk/api
JITBIT_USER=your_jitbit_username
JITBIT_PWD=your_jitbit_password

# JIRA API Credentials
JIRA_API_URL=https://your-jira-instance.com/rest/api/2
JIRA_USER=your_jira_username
JIRA_PWD=your_jira_password
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

# JIRA Settings
jira_filter_id: 10000  # Your JIRA filter ID
jira_tag_field: customfield_10800  # Custom field for tagging

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

### Running a full migration

```bash
python -m jirajitsu.process_data
```

### Testing with a single issue

Edit `jirajitsu/process_data.py` and uncomment the test line:

```python
def main():
    level = ArgumentParser().start()

    if level is not None:
        LogHandler(log_level=level)
    else:
        LogHandler()

    process_data = ProcessData()

    process_data.test_jitbit()  # Uncomment this line
    # process_data.start()       # Comment out this line
```

Then update the `process_key` variable in `test_jitbit()` method to your test issue key.

### Setting log level

```bash
python -m jirajitsu.process_data --level DEBUG
python -m jirajitsu.process_data --level INFO
python -m jirajitsu.process_data --level WARNING
```

## How It Works

### Migration Process

1. **Authentication**: Validates JIRA and JitBit credentials
2. **Filter Execution**: Runs configured JIRA filter to get issues list
3. **For Each Issue**:
   - Fetches complete issue details from JIRA
   - Downloads attachments to local storage
   - Creates ticket in JitBit with original metadata
   - Sets assignee (with technician validation)
   - Adds all comments with timestamps
   - Uploads attachments
   - Sets final ticket status
   - Optionally tags issue in JIRA

### User Mapping

- Maps JIRA users to JitBit users by email address
- Validates that assignees have technician flag in JitBit
- Falls back to default user for:
  - Invalid email addresses
  - Users not found in JitBit
  - Non-technician users
  - Anonymous commenters

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

## API Methods

### JiraApi

- `check_url_and_user()`: Validate JIRA connection
- `get_filter_for_id(filter_id)`: Get filter search URL
- `get_filter(url)`: Execute filter and return issues
- `get_issue_info(key)`: Get detailed issue information
- `get_attachment(key, issue_info)`: Download all attachments
- `post_tag(key, tag)`: Tag issue in JIRA (optional)

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

### What's New in JiraJitsu:

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

## Troubleshooting

### Import Errors

Make sure you're running from the project root:
```bash
cd jirajitsu
python -m jirajitsu.process_data
```

### Configuration Errors

Ensure both `.env` and `config/config.yml` exist and are properly configured.

### Attachment Folder Errors

Verify the attachment folder exists and has write permissions:
```bash
mkdir -p /path/to/attachments
chmod 755 /path/to/attachments
```

### API Authentication Failures

- Verify credentials in `.env` are correct
- Check that API URLs don't have trailing slashes
- Ensure JIRA/JitBit users have API access permissions

### User Not Found Errors

- Verify email addresses match between JIRA and JitBit
- Check that users exist in JitBit
- Ensure default assignee email is valid

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original [sandpiper](https://github.com/ajegam/sandpiper) project by ajegam
- Fork by andy@clownshoemotorsports.com (November 2023)
- Rebranded and enhanced as JiraJitsu (2024)

## Support

For issues, questions, or contributions, please open an issue on the project repository.
