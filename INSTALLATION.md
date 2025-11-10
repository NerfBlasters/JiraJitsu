# JiraJitsu Installation Guide

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (optional, for cloning)
- Access to JIRA and JitBit APIs
- JIRA API token or Personal Access Token (recommended)
- JitBit API token (recommended)

### 2. Installation

```bash
# Clone or navigate to the jirajitsu directory
cd jirajitsu

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install JiraJitsu as a package (enables CLI commands)
pip install -e .
```

### 3. Configuration

#### Option A: Interactive Setup Wizard (Recommended)

The easiest way to configure JiraJitsu is using the interactive setup wizard:

```bash
jirajitsu setup
```

The wizard will guide you through:
1. **JIRA Configuration**:
   - API URL
   - Authentication method (token or basic)
   - Credentials (email + token for Cloud, PAT for Server/DC, or username + password)
   - Filter ID for migration
   - Custom field for tagging

2. **JitBit Configuration**:
   - API URL
   - Authentication method (token or basic)
   - Credentials (token or username + password)
   - Migration category ID
   - Deleted items category ID
   - Default assignee email
   - Custom field for JIRA assignee

3. **Connection Validation**:
   - Tests JIRA API connection
   - Tests JitBit API connection
   - Validates configured settings

4. **File Creation**:
   - Automatically creates `.env` file with credentials
   - Automatically creates `config/config.yml` with settings
   - Creates backups of existing files

#### Option B: Manual Configuration

If you prefer to configure manually:

##### Step 1: Create .env file

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

**For Token Authentication (Recommended)**:

```ini
# JitBit API Credentials
JITBIT_API_URL=https://your-company.jitbit.com/helpdesk/api
JITBIT_AUTH_METHOD=token
JITBIT_TOKEN=your_jitbit_api_token

# JIRA API Credentials - Cloud (email + API token)
JIRA_API_URL=https://your-company.atlassian.net/rest/api/2
JIRA_AUTH_METHOD=token
JIRA_USER=your.email@company.com
JIRA_TOKEN=your_jira_api_token

# OR JIRA Server/DC (Personal Access Token)
JIRA_API_URL=https://your-jira.company.com/rest/api/2
JIRA_AUTH_METHOD=token
JIRA_TOKEN=your_personal_access_token
# Note: For PAT, do NOT set JIRA_USER
```

**For Basic Authentication (Legacy)**:

```ini
# JitBit API Credentials
JITBIT_API_URL=https://your-company.jitbit.com/helpdesk/api
JITBIT_AUTH_METHOD=basic
JITBIT_USER=your_username
JITBIT_PWD=your_password

# JIRA API Credentials
JIRA_API_URL=https://your-jira.com/rest/api/2
JIRA_AUTH_METHOD=basic
JIRA_USER=your_jira_username
JIRA_PWD=your_jira_password
```

##### Step 2: Create config.yml

```bash
mkdir -p config
cp config/config.yml.example config/config.yml
```

Edit `config/config.yml` with your settings:

```yaml
# Logging Configuration
log_dir: logs/
log_max_bytes: 10485760  # 10MB
log_backup_count: 5

# JitBit Settings
jitbit_migrate_category_id: 12345  # Your migration category ID
jitbit_delete_category_id: 12346   # Your deleted items category ID
jitbit_default_assign_email: default@yourcompany.com
jitbit_jira_assignee_field_id: 66782  # Custom field for storing original JIRA assignee

# Rate Limiting (optional - adjust if hitting rate limits)
jitbit_rate_limit_default: 90  # Calls per minute for normal endpoints
jitbit_rate_limit_restricted: 60  # Calls per minute for restricted endpoints
jitbit_rate_limit_retry_delay: 60  # Seconds to wait on rate limit error
jitbit_rate_limit_max_retries: 3  # Max retries for rate-limited requests

# JIRA Settings
jira_filter_id: 10000  # Your JIRA filter ID for default migrations
jira_tag_field: customfield_10800  # Optional: Custom field for tagging migrated issues

# Attachment Settings
fetch_attachments: NEW_ONLY  # Options: NEW_ONLY (skip existing) or DELETE_REFETCH (always redownload)
attachment_folder: /path/to/attachments
```

##### Step 3: Create required directories

```bash
mkdir -p logs
mkdir -p /path/to/attachments  # Use the same path from config.yml
```

### 4. Verify Installation

Test your configuration and API connections:

```bash
# Test both JIRA and JitBit API connections
jirajitsu config test-connection

# View current configuration
jirajitsu config show

# List available JIRA projects (tests JIRA connection)
jirajitsu list projects

# List JitBit categories (tests JitBit connection)
jirajitsu list categories
```

### 5. Validate Configuration

Before running a migration, validate your setup:

```bash
# Validate user mappings between JIRA and JitBit
jirajitsu validate users

# Validate status mappings
jirajitsu validate status

# Test with a single issue
jirajitsu test --issue PROJ-123
```

### 6. Run Migration

```bash
# Preview what will be migrated (dry run)
jirajitsu migrate --dry-run

# Preview with limited output
jirajitsu migrate --dry-run --limit 10

# Run full migration with default filter
jirajitsu migrate

# Run with HTML-rendered content (cleaner formatting)
jirajitsu migrate --html

# Run with debug logging
jirajitsu --log-level debug migrate
```

## Authentication Methods

### JIRA Authentication

#### JIRA Cloud (Atlassian Cloud)

Use email + API token:

1. Generate API token: https://id.atlassian.com/manage-profile/security/api-tokens
2. Set in `.env`:
   ```ini
   JIRA_AUTH_METHOD=token
   JIRA_USER=your.email@company.com
   JIRA_TOKEN=your_api_token_here
   ```

#### JIRA Server/Data Center

Use Personal Access Token (PAT):

1. Generate PAT in JIRA: Profile → Personal Access Tokens
2. Set in `.env`:
   ```ini
   JIRA_AUTH_METHOD=token
   JIRA_TOKEN=your_pat_token_here
   # DO NOT set JIRA_USER for PAT
   ```

#### Basic Authentication (Not Recommended)

```ini
JIRA_AUTH_METHOD=basic
JIRA_USER=your_username
JIRA_PWD=your_password
```

### JitBit Authentication

#### Token Authentication (Recommended)

1. Generate token in JitBit: Admin → API → Generate Token
2. Set in `.env`:
   ```ini
   JITBIT_AUTH_METHOD=token
   JITBIT_TOKEN=your_api_token_here
   ```

#### Basic Authentication

```ini
JITBIT_AUTH_METHOD=basic
JITBIT_USER=your_username
JITBIT_PWD=your_password
```

## Development Installation

If you want to contribute or modify the code:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .

# Run tests
pytest tests/

# Check code coverage
pytest --cov=jirajitsu tests/

# Format code (if using black)
black jirajitsu/ tests/

# Run linter (if using flake8)
flake8 jirajitsu/

# Type checking (if using mypy)
mypy jirajitsu/ --ignore-missing-imports
```

## Package Installation

To install as a package:

```bash
# Install in development mode (editable - recommended for development)
pip install -e .

# Or install normally (for production use)
pip install .

# Now you can use the CLI commands anywhere
jirajitsu --help
jirajitsu setup
jirajitsu migrate
```

## Docker Installation (Optional)

If you prefer using Docker, create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install JiraJitsu
RUN pip install -e .

# Default command - run setup wizard
CMD ["jirajitsu", "setup"]
```

Build and run:

```bash
# Build image
docker build -t jirajitsu .

# Run setup wizard
docker run -it -v $(pwd)/config:/app/config -v $(pwd)/.env:/app/.env jirajitsu jirajitsu setup

# Run migration
docker run -v $(pwd)/config:/app/config -v $(pwd)/.env:/app/.env -v $(pwd)/logs:/app/logs jirajitsu jirajitsu migrate

# Run with custom command
docker run -it jirajitsu jirajitsu list projects
```

## Directory Structure

After installation and configuration:

```
jirajitsu/
├── .env                    # API credentials (gitignored)
├── config/
│   ├── config.yml          # Application settings (gitignored)
│   └── config.yml.example  # Example configuration
├── logs/                   # Log files (auto-created)
│   └── jirajitsu_YYYYMMDD.log
├── attachments/            # Downloaded JIRA attachments
│   └── ISSUE-KEY/
│       └── filename.ext
├── jirajitsu/              # Source code
│   ├── cli/                # CLI commands
│   ├── config.py           # Configuration loading
│   ├── jira_api.py         # JIRA API client
│   ├── jitbit_api.py       # JitBit API client
│   └── process_data.py     # Migration logic
└── tests/                  # Test suite
```

## Troubleshooting

### "Command not found: jirajitsu"

Install the package:
```bash
pip install -e .
```

Or run directly:
```bash
python -m jirajitsu.cli.main --help
```

### "Module not found" errors

Make sure you've installed dependencies and are in the correct directory:
```bash
pip install -r requirements.txt
cd /path/to/jirajitsu
```

### Configuration errors

Run the setup wizard to reconfigure:
```bash
jirajitsu setup
```

Or verify configuration manually:
- Verify `.env` file exists and has correct credentials
- Verify `config/config.yml` exists and has valid settings
- Check that all required directories exist
- Test connection: `jirajitsu config test-connection`

### Authentication errors

**For JIRA Cloud**:
- Use email + API token (not password)
- Generate token at: https://id.atlassian.com/manage-profile/security/api-tokens
- Set `JIRA_AUTH_METHOD=token`

**For JIRA Server/DC**:
- Use Personal Access Token
- Do NOT set `JIRA_USER` when using PAT
- Set `JIRA_AUTH_METHOD=token`

**For JitBit**:
- Use API token (recommended)
- Generate in JitBit: Admin → API → Generate Token
- Set `JITBIT_AUTH_METHOD=token`

### Permission errors

Ensure directories are writable:
```bash
chmod 755 logs/
chmod 755 /path/to/attachments/
chmod 755 config/
```

### API connection errors

Test connections individually:
```bash
# Test both
jirajitsu config test-connection

# Test JIRA only
jirajitsu list projects

# Test JitBit only
jirajitsu list categories
```

Common issues:
- Verify API URLs don't have trailing slashes
- Check that API access is enabled for your accounts
- Ensure firewall/proxy allows API connections
- Verify tokens haven't expired

### Rate limiting errors

If you hit rate limits, adjust in `config/config.yml`:
```yaml
jitbit_rate_limit_default: 60  # Reduce from 90
jitbit_rate_limit_restricted: 30  # Reduce from 60
jitbit_rate_limit_retry_delay: 120  # Increase wait time
```

### Filter returns 0 issues

Check your filter configuration:
```bash
# List available filters
jirajitsu list filters

# Test with custom JQL
jirajitsu migrate --jql "project = YOURPROJECT" --dry-run
```

## Getting Help

For more information:
- Review [README.md](README.md) for usage instructions
- Check [CLI_USAGE_GUIDE.md](CLI_USAGE_GUIDE.md) for command reference
- See [docs/NEW_FEATURES.md](docs/NEW_FEATURES.md) for feature details
- Read [CHANGELOG.md](CHANGELOG.md) for version history
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

For issues or questions:
- Open an issue on the project repository
- Check existing issues for solutions
- Include log files when reporting bugs (with credentials redacted)
