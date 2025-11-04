# JiraJitsu Installation Guide

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (optional, for cloning)
- Access to JIRA and JitBit APIs

### 2. Installation

```bash
# Clone or navigate to the jirajitsu directory
cd jirajitsu

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### Step 1: Create .env file

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```ini
JITBIT_API_URL=https://your-company.jitbit.com/helpdesk/api
JITBIT_USER=your_username
JITBIT_PWD=your_password

JIRA_API_URL=https://your-jira.com/rest/api/2
JIRA_USER=your_jira_username
JIRA_PWD=your_jira_password
```

#### Step 2: Create config.yml

```bash
cp config/config.yml.example config/config.yml
```

Edit `config/config.yml` with your settings:

```yaml
log_dir: logs/
jitbit_migrate_category_id: YOUR_CATEGORY_ID
jitbit_delete_category_id: YOUR_DELETE_CATEGORY_ID
jitbit_default_assign_email: default@yourcompany.com
jira_filter_id: YOUR_FILTER_ID
attachment_folder: /path/to/attachments
```

#### Step 3: Create required directories

```bash
mkdir -p logs
mkdir -p /path/to/attachments  # Use your actual path
```

### 4. Verify Installation

Test that everything is configured correctly:

```bash
python -m jirajitsu.process_data --level INFO
```

Or use the installed command (if installed via pip):

```bash
jirajitsu --level INFO
```

### 5. Run Migration

```bash
# Full migration
python -m jirajitsu.process_data

# With specific log level
python -m jirajitsu.process_data --level DEBUG
```

## Development Installation

If you want to contribute or modify the code:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Check code coverage
pytest --cov=jirajitsu tests/

# Format code
black jirajitsu/ tests/

# Run linter
flake8 jirajitsu/

# Type checking
mypy jirajitsu/ --ignore-missing-imports
```

## Package Installation

To install as a package:

```bash
# Install in development mode (editable)
pip install -e .

# Or install normally
pip install .

# Now you can use the command anywhere
jirajitsu --level INFO
```

## Docker Installation (Optional)

If you prefer using Docker, create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "jirajitsu.process_data"]
```

Build and run:

```bash
docker build -t jirajitsu .
docker run -v $(pwd)/.env:/app/.env -v $(pwd)/config:/app/config jirajitsu
```

## Troubleshooting

### "Module not found" errors

Make sure you're running from the correct directory and have activated your virtual environment.

### Configuration errors

- Verify `.env` file exists and has correct credentials
- Verify `config/config.yml` exists and has valid settings
- Check that all required directories exist

### Permission errors

Ensure the attachment folder and log directory are writable:

```bash
chmod 755 logs/
chmod 755 /path/to/attachments/
```

### API connection errors

- Test JIRA and JitBit URLs in a browser
- Verify credentials are correct
- Check that API access is enabled for your accounts

## Next Steps

- Review [README.md](README.md) for usage instructions
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- See [docs/NEW_FEATURES.md](docs/NEW_FEATURES.md) for feature details
- Read [CHANGELOG.md](CHANGELOG.md) for version history
