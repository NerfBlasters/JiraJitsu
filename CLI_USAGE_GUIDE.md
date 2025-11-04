# JiraJitsu CLI Usage Guide

Complete guide to using the JiraJitsu command-line interface.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Command Reference](#command-reference)
4. [Common Workflows](#common-workflows)
5. [Examples](#examples)

## Installation

```bash
cd jirajitsu
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

After installation, the `jirajitsu` command will be available globally.

## Quick Start

### First-Time Setup

```bash
# Run interactive setup wizard
jirajitsu setup

# Validate configuration
jirajitsu validate config

# Test connections
jirajitsu config test-connection
```

### View Available Resources

```bash
# List JIRA projects with issue counts
jirajitsu list projects

# List JIRA issue types
jirajitsu list issue-types

# List JitBit categories
jirajitsu list jitbit-categories

# List available JIRA filters
jirajitsu list filters
```

### Validate Before Migration

```bash
# Check user mappings
jirajitsu validate users

# Create missing users
jirajitsu validate users --create-missing

# Preview what would be migrated
jirajitsu validate filter

# Test single issue migration
jirajitsu test --issue RFM-123
```

### Perform Migration

```bash
# Preview migration (dry run)
jirajitsu migrate --dry-run

# Migrate using default filter from config
jirajitsu migrate

# Migrate with custom options
jirajitsu migrate --project RFM --range 100:200
```

## Command Reference

### Global Options

Available for all commands:

```bash
-v, --verbose           Enable verbose output
-q, --quiet            Suppress non-essential output
--log-level LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
```

### jirajitsu setup

Interactive configuration wizard.

```bash
jirajitsu setup
```

Guides you through:
- JIRA API configuration
- JitBit API configuration
- Directory setup
- Connection testing

### jirajitsu config

Configuration management commands.

#### config view

Display current configuration:

```bash
jirajitsu config view                # Passwords masked
jirajitsu config view --show-secrets # Show actual passwords
```

#### config set

Update configuration values:

```bash
jirajitsu config set JIRA_FILTER_ID 10001
jirajitsu config set JITBIT_USER newuser
```

#### config validate

Test configuration and connections:

```bash
jirajitsu config validate
```

#### config test-connection

Test specific API connections:

```bash
jirajitsu config test-connection              # Test both
jirajitsu config test-connection --system jira     # JIRA only
jirajitsu config test-connection --system jitbit   # JitBit only
```

#### config export

Export configuration to file:

```bash
jirajitsu config export
jirajitsu config export --output my-config.txt
```

### jirajitsu list

Enumerate and display resources.

#### list projects

Show all JIRA projects:

```bash
jirajitsu list projects                        # Table format with counts
jirajitsu list projects --no-count            # Without counts (faster)
jirajitsu list projects --format json         # JSON output
jirajitsu list projects --format csv          # CSV output
```

#### list issue-types

Show JIRA issue types:

```bash
jirajitsu list issue-types                    # With counts
jirajitsu list issue-types --no-count
jirajitsu list issue-types --format json
```

#### list jitbit-categories

Show JitBit categories:

```bash
jirajitsu list jitbit-categories
jirajitsu list jitbit-categories --format json
```

#### list filters

Show available JIRA filters:

```bash
jirajitsu list filters
jirajitsu list filters --format csv
```

### jirajitsu validate

Validation and verification commands.

#### validate config

Test all configuration and connections:

```bash
jirajitsu validate config
```

Checks:
- JIRA connection
- JitBit connection
- Directory existence
- Category ID validity
- Filter ID validity

#### validate users

Check user mappings between JIRA and JitBit:

```bash
jirajitsu validate users                     # Show report
jirajitsu validate users --create-missing    # Create missing users
jirajitsu validate users --output report.csv # Save to CSV
```

#### validate filter

Preview issues that would be migrated:

```bash
jirajitsu validate filter                           # Default filter
jirajitsu validate filter --filter-id 10001         # Specific filter
jirajitsu validate filter --jql "project = RFM"     # Custom JQL
jirajitsu validate filter --project RFM --range 100:200  # Range
```

### jirajitsu users

User management commands.

#### users sync

Sync all JIRA users to JitBit:

```bash
jirajitsu users sync                        # Create all missing users
jirajitsu users sync --dry-run              # Preview without creating
jirajitsu users sync --technician           # Create as technicians
```

#### users validate

Validate user mappings:

```bash
jirajitsu users validate
jirajitsu users validate --output users-report.csv
```

#### users create

Create a single user manually:

```bash
jirajitsu users create \
  --email john.doe@example.com \
  --first-name John \
  --last-name Doe \
  --technician
```

### jirajitsu migrate

Perform issue migration.

```bash
# Basic migration with default filter
jirajitsu migrate

# Preview before migrating
jirajitsu migrate --dry-run

# Use specific filter
jirajitsu migrate --filter-id 10001

# Use custom JQL query
jirajitsu migrate --jql "project = RFM AND status = Done"

# Migrate specific project
jirajitsu migrate --project RFM

# Migrate project with range
jirajitsu migrate --project RFM --range 100:200

# Migrate specific issues
jirajitsu migrate --issues RFM-1,RFM-2,RFM-3

# Override destination category
jirajitsu migrate --category-id 12345

# Auto-create missing users
jirajitsu migrate --create-missing-users
```

### jirajitsu test

Test single issue migration.

```bash
jirajitsu test --issue RFM-123
jirajitsu test --issue RFM-123 --verbose  # Detailed output
```

## Common Workflows

### Workflow 1: First-Time Migration Setup

```bash
# 1. Run setup wizard
jirajitsu setup

# 2. List available projects
jirajitsu list projects

# 3. Validate users and create missing ones
jirajitsu validate users --create-missing

# 4. Preview migration
jirajitsu validate filter

# 5. Test with single issue
jirajitsu test --issue PROJECT-123

# 6. Run full migration
jirajitsu migrate
```

### Workflow 2: Migrating Specific Project Range

```bash
# 1. View project issues count
jirajitsu list projects

# 2. Preview the range
jirajitsu validate filter --project RFM --range 100:200

# 3. Dry run
jirajitsu migrate --project RFM --range 100:200 --dry-run

# 4. Execute migration
jirajitsu migrate --project RFM --range 100:200
```

### Workflow 3: User Management

```bash
# 1. Check current user mappings
jirajitsu validate users --output user-report.csv

# 2. Review CSV file to identify missing users

# 3. Sync users (dry run first)
jirajitsu users sync --dry-run

# 4. Actually create users
jirajitsu users sync

# 5. Verify sync
jirajitsu validate users
```

### Workflow 4: Testing and Validation

```bash
# 1. Validate configuration
jirajitsu validate config

# 2. Test connections
jirajitsu config test-connection

# 3. Check a specific filter
jirajitsu validate filter --filter-id 10001

# 4. Test single issue
jirajitsu test --issue RFM-1

# 5. Preview full migration
jirajitsu migrate --dry-run
```

## Examples

### Example 1: Complete Setup and Migration

```bash
# Interactive setup
jirajitsu setup

# Verify everything is configured
jirajitsu validate config

# See what's available
jirajitsu list projects
jirajitsu list jitbit-categories

# Check and create users
jirajitsu validate users --create-missing

# Test one issue first
jirajitsu test --issue RFM-1

# Preview full migration
jirajitsu migrate --dry-run

# Execute migration
jirajitsu migrate
```

### Example 2: Migrate Completed Issues Only

```bash
# Use custom JQL
jirajitsu migrate --jql "project = RFM AND status = Done"
```

### Example 3: Migrate by Date Range

```bash
# Custom JQL with date filter
jirajitsu migrate --jql "created >= 2024-01-01 AND created <= 2024-03-31"
```

### Example 4: Export Configuration for Documentation

```bash
# Export current config
jirajitsu config export --output production-config.txt

# View current settings
jirajitsu config view
```

### Example 5: Batch User Creation

```bash
# Sync all users
jirajitsu users sync

# Create individual user
jirajitsu users create \
  --email admin@company.com \
  --first-name Admin \
  --last-name User \
  --technician
```

## Output Formats

Most list commands support multiple output formats:

### Table Format (Default)

```bash
jirajitsu list projects
```

Pretty-printed tables with colors.

### JSON Format

```bash
jirajitsu list projects --format json
```

Machine-readable JSON output for scripting.

### CSV Format

```bash
jirajitsu list projects --format csv > projects.csv
```

CSV output suitable for Excel or data analysis.

## Logging

Control logging verbosity:

```bash
# Minimal output
jirajitsu migrate --quiet

# Detailed output
jirajitsu migrate --verbose

# Specific log level
jirajitsu migrate --log-level DEBUG
```

## Exit Codes

- `0` - Success
- `1` - Error or validation failure

Use exit codes in scripts:

```bash
if jirajitsu validate config; then
    echo "Config valid, proceeding..."
    jirajitsu migrate
else
    echo "Config invalid, aborting"
    exit 1
fi
```

## Environment Variables

JiraJitsu reads secrets from `.env` file:

```bash
JIRA_API_URL=https://jira.example.com/rest/api/2
JIRA_USER=username
JIRA_PWD=password
JITBIT_API_URL=https://company.jitbit.com/helpdesk/api
JITBIT_USER=username
JITBIT_PWD=password
```

## Tips and Best Practices

1. **Always use --dry-run first** for migrations
2. **Test with single issue** before full migration
3. **Validate users** before migrating to avoid assignment issues
4. **Export configuration** before making changes
5. **Use filters or JQL** for selective migration
6. **Check exit codes** in automated scripts
7. **Save reports to CSV** for documentation

## Troubleshooting

### Command Not Found

```bash
# Reinstall package
pip install -e .
```

### Import Errors

```bash
# Make sure you're in the correct directory
cd /path/to/jirajitsu

# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration Errors

```bash
# Run setup again
jirajitsu setup

# Or validate to see specific issues
jirajitsu validate config
```

### Connection Failures

```bash
# Test individual connections
jirajitsu config test-connection --system jira
jirajitsu config test-connection --system jitbit

# Check configuration
jirajitsu config view
```

## Getting Help

```bash
# General help
jirajitsu --help

# Command-specific help
jirajitsu migrate --help
jirajitsu list --help
jirajitsu validate --help

# Subcommand help
jirajitsu list projects --help
jirajitsu users sync --help
```
