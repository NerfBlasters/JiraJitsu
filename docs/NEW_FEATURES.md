# New Features in JiraJitsu

This document describes the enhancements and new features added to JiraJitsu compared to the original sandpiper project.

## Table of Contents

- [Version 1.2 Features](#version-12-features)
- [Version 1.1 Features](#version-11-features)
- [Version 1.0 Features](#version-10-features)
- [Migration from Sandpiper](#migration-from-sandpiper)

---

## Version 1.2 Features

Released: January 2025

### Content Management

#### HTML Rendering Option

Cleaner content formatting with the new `--html` flag:

```bash
jirajitsu migrate --html
```

**Features:**
- Uses JIRA's HTML-rendered content instead of raw wiki markup
- Automatically strips internal images (192.168.x.x URLs) that won't be accessible
- Better formatting preservation
- Cleaner, more readable content in JitBit
- Falls back to wiki markup if HTML not available

#### JIRA Wiki Markup Cleaning

Automatic removal of JIRA formatting tags:

- Removes all `{color:...}` and `{color}` tags from content
- Applied to both ticket descriptions and comments
- Makes migrated content much more readable
- Preserves actual content while removing visual markup

**Example:**
```
Before: {color:black}Important message{color}
After:  Important message
```

### Large-Scale Migration Support

#### Filter Pagination

Handles JIRA filters with thousands of issues:

- Automatic pagination for filter results
- JIRA API limits results to 1000 per request
- Now fetches all pages automatically up to 10,000 total issues
- Transparent to the user - just works

**Before (v1.1):**
- Filters with >1000 issues only returned first 1000

**After (v1.2):**
- Fetches all issues automatically with pagination

#### Duplicate Detection

Prevents recreating already-migrated tickets:

- Checks JitBit for existing tickets before migration
- Searches by JIRA key in ticket subject
- Reports as "updated" instead of creating duplicates
- Also prevents duplicate comments using timestamp comparison

**Benefits:**
- Safe to re-run migrations
- Can migrate incrementally
- No manual cleanup of duplicates needed

### User Management Enhancements

#### Auto-Create Users by Default

**Breaking Change:** User creation behavior changed in v1.2

**v1.1 and earlier:**
```bash
# Had to explicitly enable user creation
jirajitsu migrate --create-missing-users
```

**v1.2:**
```bash
# Auto-creates users by default
jirajitsu migrate

# Disable with flag
jirajitsu migrate --ignore-missing-users
```

**Features:**
- Automatically creates missing JitBit users during migration
- Grants technician permissions for assigned categories automatically
- Tracks created users in migration summary
- More intuitive default behavior

#### Technician Permission Auto-Grant

Automatic technician status assignment:

- JitBit `create_user()` API ignores `isTechie` parameter
- Now automatically calls `AddCategoryTechPermission` after user creation
- Users get proper technician permissions for the migration category
- No manual permission granting needed

### Migration Statistics

Beautiful summary table after migration:

```
┌─────────────────────────────┬───────┐
│ Metric                      │ Count │
├─────────────────────────────┼───────┤
│ Total Tickets Processed     │   150 │
│ Tickets Created             │   142 │
│ Tickets Updated (existing)  │     8 │
│ Comments Added              │   450 │
│ Comments Skipped (duplicate)│    12 │
│ Attachments Added           │    89 │
│ Users Created               │    23 │
│ Technicians (cached)        │    45 │
│ Failed Tickets              │     0 │
│ Execution Time              │  15m 23s │
└─────────────────────────────┴───────┘
```

**Tracks:**
- Total tickets processed
- Tickets created vs. updated
- Comments added and skipped (duplicates)
- Attachments added
- Users created and cached technicians
- Execution time

### API Improvements

#### Custom User-Agent

Identifies JiraJitsu traffic in server logs:

- Sets `User-Agent: JiraJitsu/{version}` for all API requests
- Applied to both JIRA and JitBit API clients
- Helps with traffic monitoring and debugging
- Better than default `python-requests/x.x.x`

#### Enhanced jitapi Command

Improved manual API testing tool:

**Old syntax:**
```bash
jirajitsu jitapi --endpoint UserByEmail -p email user@example.com
```

**New syntax:**
```bash
jirajitsu jitapi UserByEmail --email user@example.com
```

**Features:**
- Dynamic parameter support (no predefined flags)
- Cleaner, more intuitive interface
- Better error messages
- Pretty-printed JSON responses

### Bug Fixes

#### Critical Fixes

- **Filter Pagination**: Fixed filters with >1000 issues returning only first 1000
- **Query Options**: Fixed --issues, --jql, --project options being ignored
- **Comment Reopening**: Fixed tickets being reopened when comments added
- **Close Date**: Fixed historical close dates showing current date instead
- **Comment Deduplication**: Fixed edge case with different line break formats

#### Migration Flow Improvements

**Old flow (caused issues):**
1. Create ticket
2. Update ticket status (close)
3. Add comments (reopens ticket!)

**New flow (correct):**
1. Create ticket
2. Add comments
3. Add attachments
4. Update ticket status (stays closed)

#### Close Date Preservation

**Problem:** JitBit API ignores closeDate when sent with statusId

**Solution:**
- First API call: Set ticket status
- Second API call: Set close date
- Historical dates now preserved correctly

---

## Version 1.1 Features

Released: November 2024

### Token Authentication Support

Modern authentication methods for both JIRA and JitBit:

#### JIRA Authentication

**JIRA Cloud:**
```ini
JIRA_AUTH_METHOD=token
JIRA_USER=your.email@company.com
JIRA_TOKEN=your_api_token
```

**JIRA Server/DC:**
```ini
JIRA_AUTH_METHOD=token
JIRA_TOKEN=your_personal_access_token
# Note: Do not set JIRA_USER for PAT
```

**Legacy Basic Auth:**
```ini
JIRA_AUTH_METHOD=basic
JIRA_USER=username
JIRA_PWD=password
```

#### JitBit Authentication

**Token (Recommended):**
```ini
JITBIT_AUTH_METHOD=token
JITBIT_TOKEN=your_api_token
```

**Basic Auth:**
```ini
JITBIT_AUTH_METHOD=basic
JITBIT_USER=username
JITBIT_PWD=password
```

### Interactive Setup Wizard

Guided configuration with the `jirajitsu setup` command:

**Features:**
- Loads existing configuration as defaults
- Shows current values when updating
- Smart password/token handling
- Detects auth method switching
- URL normalization
- Connection validation
- Automatic configuration backups
- Interactive defaults from API (categories, filters, etc.)

**Benefits:**
- No need to manually edit config files
- Catches configuration errors early
- Validates API connections before migration
- Safe updates with automatic backups

### Enhanced Validation

Better pre-migration checks:

```bash
# Validate user mappings
jirajitsu validate users

# Create missing users during validation
jirajitsu validate users --create-missing

# Validate configuration
jirajitsu validate config

# Preview filter results
jirajitsu validate filter
```

**Improvements:**
- Shows unique email counts
- Clearer messaging
- Better permission error messages
- Limit options for large datasets

### Critical API Fixes

Fixed several JitBit API bugs:

1. **Authorization endpoint**: Changed GET → POST (per API docs)
2. **AttachFile endpoint**: Fixed parameter name `file` → `uploadFile`
3. **User endpoint**: Fixed parameter name `id` → `userId`
4. **User endpoint**: Fixed response field `IsTechie` → `IsTech`
5. **URL normalization**: Fixed duplicate protocol prefix handling

**Impact:**
- File attachments now work correctly
- Technician status detection works
- Authentication is more reliable

---

## Version 1.0 Features

Initial release: November 2024

### Python 3.10+ Compatibility

**Complete modern Python rewrite:**
- Type hints throughout codebase
- Modern string formatting (f-strings)
- Proper exception handling
- Async-ready architecture
- No Python 2 legacy code

### Security Enhancements

#### Hybrid Configuration System

Separated sensitive and non-sensitive data:

- **`.env` file**: API credentials, passwords, tokens
- **`config.yml` file**: Settings, IDs, paths, options
- **No hardcoded credentials**: All sensitive data in environment variables
- **python-dotenv integration**: Secure credential loading

### Enhanced User Management

#### Comment Author Tracking

Preserves original comment authors:

```python
# Looks up JIRA comment author in JitBit
comment_author = comment['updateAuthor']['emailAddress']
comment_author_id = self.jitbit_api.get_user_id_by_email(comment_author)
```

**Benefits:**
- Comments show who actually wrote them
- Email-based user lookup from JIRA to JitBit
- Falls back to default user for anonymous comments

#### Comment Timestamps

Comments include original posting dates:

```
(Originally posted on: 2024-01-15 14:30:00)

[Original comment text here]
```

#### Technician Flag Validation

Validates user permissions before assignment:

```python
is_technician = self.jitbit_api.get_user_is_technician(assign_to_id)
if not is_technician:
    assign_to_id = self.default_assign_id  # Fallback
```

**Benefits:**
- Prevents assignment to non-technician users
- Automatic fallback to default technician
- Reduces ticket routing errors

### Metadata Preservation

#### Assignee Name Preservation

Original JIRA assignee stored in ticket body:

```
[Original ticket description]

(Originally assigned to: John Doe)
(Original Resolution date: 2024-01-15)
```

**Note:** Starting in v1.2, also stored in custom field for better tracking

#### Timestamp Preservation

Original timestamps maintained:

- **Creation date**: Preserved from JIRA
- **Resolution date**: Preserved from JIRA
- **Comment timestamps**: All preserved with "(Originally posted on: ...)" prefix

### API Improvements

#### Universal Update Method

New `post_update_ticket()` method:

```python
# Update any ticket field(s) with kwargs
self.jitbit_api.post_update_ticket(
    key, ticket_id,
    assignedUserId=user_id,
    date=created_date,
    statusId=status_id
)
```

**Benefits:**
- Single method for all updates
- Reduces code duplication
- Type-safe with kwargs
- Extensible for future fields

#### Better Error Handling

Comprehensive error handling:

- Individual ticket failures don't stop migration
- Failed tickets moved to "deleted" category
- All errors logged with full details
- Progress bar shows migration status

### Logging Enhancements

Better debugging and monitoring:

- **Rotating file handlers**: Automatic log rotation
- **Configurable log levels**: DEBUG, INFO, WARNING, ERROR
- **Detailed API logging**: All API calls logged with parameters
- **Progress tracking**: Real-time progress bars
- **Rich console output**: Colored, formatted console output

### Testing Infrastructure

Comprehensive test suite:

- pytest-based testing
- Code coverage tracking
- Type checking with mypy
- Fixtures for API mocking
- Integration tests

---

## Migration from Sandpiper

### Breaking Changes

1. **Package name**: `sandpiper` → `jirajitsu`
2. **Log alias**: `sandpiper_log` → `jirajitsu_log`
3. **Configuration**: Credentials must be in `.env` file (not `config.yml`)
4. **Python version**: Requires Python 3.10+ (Python 2 not supported)
5. **Invocation**: Script-based → CLI commands
   - Old: `python -m jirajitsu.process_data`
   - New: `jirajitsu migrate`

### Migration Steps

1. **Update Python**: Ensure Python 3.10+ is installed
2. **Install JiraJitsu**: `pip install -e .`
3. **Run setup wizard**: `jirajitsu setup`
4. **Migrate configuration**:
   - Move credentials from `config.yml` to `.env`
   - Update config file structure
5. **Test connection**: `jirajitsu config test-connection`
6. **Validate setup**: `jirajitsu validate users`
7. **Run migration**: `jirajitsu migrate`

### Feature Comparison

| Feature | Sandpiper | JiraJitsu v1.0 | JiraJitsu v1.2 |
|---------|-----------|----------------|----------------|
| Python Version | 2.7 | 3.10+ | 3.10+ |
| Configuration | YAML only | .env + YAML | .env + YAML |
| Authentication | Basic only | Basic + Token | Basic + Token |
| User Interface | Script | CLI | CLI |
| Setup | Manual editing | Manual/Wizard | Interactive Wizard |
| User Creation | Manual | Manual | Automatic |
| Duplicate Detection | No | No | Yes |
| Filter Pagination | No | No | Yes |
| HTML Rendering | No | No | Yes |
| Migration Stats | No | No | Yes |
| Comment Timestamps | No | Yes | Yes |
| Technician Validation | No | Yes | Yes |
| Testing | None | pytest | pytest |
| Type Hints | No | Yes | Yes |

### Why Upgrade?

**From Sandpiper to JiraJitsu 1.2:**
- Modern Python with type safety
- Secure credential management
- Token authentication support
- Interactive setup wizard
- Automatic user creation
- Duplicate detection
- Large filter support (>1000 issues)
- HTML content rendering
- Migration statistics
- Better error handling
- Comprehensive logging
- Active maintenance

**Bottom line:** JiraJitsu 1.2 is production-ready, secure, and feature-rich compared to the original sandpiper project.

---

## Future Enhancements

Potential features for future versions:

- **Incremental sync**: Continuous synchronization mode
- **Custom field mapping**: Configure which JIRA fields map to JitBit
- **Webhook support**: Real-time migration triggers
- **Rollback capability**: Undo migrations
- **Multi-project migrations**: Migrate multiple projects in one run
- **Advanced filtering**: More complex JQL query building
- **Export/import**: Migration templates and configurations
- **Audit trail**: Detailed migration history tracking

---

## Contributing

Want to add a feature? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

Found a bug? Open an issue on the project repository.

Need help? Check the [README.md](../README.md) or [CLI_USAGE_GUIDE.md](../CLI_USAGE_GUIDE.md).
