# New Features in JiraJitsu

This document describes the enhancements and new features added to JiraJitsu compared to the original sandpiper project.

## Python 3.10+ Compatibility

- **Complete Python 3 rewrite**: All code updated to use modern Python 3.10+ features
- **Type hints**: Full type annotations added to all function signatures for better IDE support and type checking
- **Modern string formatting**: Converted all string formatting to f-strings
- **Fixed exception handling**: Replaced deprecated `e.message` with `str(e)`
- **Removed Python 2 code**: Cleaned up all urllib2 and legacy Python 2 constructs

## Security Enhancements

### Hybrid Configuration System

- **Environment-based secrets**: API credentials now loaded from `.env` file using python-dotenv
- **Separated concerns**:
  - Sensitive data (passwords, API keys) → `.env` file
  - Non-sensitive settings (IDs, paths) → `config.yml` file
- **No hardcoded credentials**: Removed all hardcoded passwords and API keys from source code
- **Default user handling**: Hardcoded default email removed, now configurable

## Enhanced User Management

### Comment Author Tracking

JiraJitsu preserves the original comment author information:

```python
# Old (sandpiper):
comment_author = 'Unknown'

# New (JiraJitsu):
comment_author = comment['updateAuthor']['emailAddress']
comment_author_id = self.jitbit_api.get_user_id_by_email(comment_author)
```

**Benefits:**
- Comments show who actually wrote them
- Email-based user lookup from JIRA to JitBit
- Falls back to default user for anonymous comments

### Comment Timestamps

Comments now include original posting date:

```
(Originally posted on: 2024-01-15)

[Original comment text here]
```

### Technician Flag Validation

New `get_user_is_technician()` method validates user permissions:

```python
is_technician = self.jitbit_api.get_user_is_technician(assign_to_id)
if not is_technician:
    logger.warning(f'User {assign_to_id} is not a technician, using default')
    assign_to_id = self.default_assign_id
```

**Benefits:**
- Prevents assignment to non-technician users
- Automatic fallback to default technician
- Reduces ticket routing errors

### Default Author ID Logic

Improved handling of missing/invalid comment authors:

```python
# Comments now properly fall back to default user
if comment_author_id <= 0:
    comment_author_id = self.default_assign_id
```

## Metadata Preservation

### Assignee Name Preservation

Original JIRA assignee name added to ticket body:

```
[Original ticket description]

(Originally assigned to: John Doe)
(Original Resolution date: 2024-01-15)
```

### Timestamp Preservation

Original creation date now passed to JitBit:

```python
date_created = issue_info['fields']['created']
self.jitbit_api.post_update_ticket(key, ticket_id,
                                    assignedUserId=assign_to_id,
                                    date=date_created)
```

**Benefits:**
- Historical accuracy maintained
- Proper aging reports in JitBit
- Audit trail preservation

## API Improvements

### Universal Update Method

New `post_update_ticket()` method consolidates ticket updates:

```python
def post_update_ticket(self, key: str, ticket_id: int, **kwargs) -> bool:
    """
    Universal method to update any ticket parameters.
    Accepts any valid UpdateTicket API parameters as kwargs.
    """
```

**Supported parameters:**
- `assignedUserId`: Assign to user
- `date`: Created date
- `categoryId` / `newCategoryId`: Category
- `priorityId`: Priority
- `statusId`: Status
- `dueDate`: Due date
- `tags`: Tags
- `subject`: Subject
- `body`: Body
- `timeSpentInSeconds`: Time spent

**Benefits:**
- Single method for all updates
- Reduces code duplication
- Easier to extend with new parameters
- Backward compatible (legacy methods still work)

### Enhanced Error Messages

All error messages now use f-strings for clarity:

```python
# Old:
logger.critical('[{key}] ERROR: Unable to connect to URL: {url}'.format(key=key, url=url))

# New:
logger.critical(f'[{key}] ERROR: Unable to connect to URL: {url}')
```

## Testing Infrastructure

### Pytest Framework

- Comprehensive test suite with pytest
- Test fixtures for common scenarios
- Mock-based testing (no live API calls needed)
- Tests for all major components:
  - Configuration loading
  - JIRA API methods
  - JitBit API methods

### Test Coverage

```bash
pytest --cov=jirajitsu tests/
```

Example tests:
- Config loading with environment variables
- API authentication
- User lookup and validation
- Ticket creation and updates
- Error handling

## Code Quality Improvements

### Type Hints

All functions now have type annotations:

```python
def get_user_id_by_email(self, email: str) -> int:
    """Get JitBit user ID from email address."""
    ...

def get_issue_info(self, key: str) -> tuple[bool, dict | None]:
    """Get detailed issue information from JIRA."""
    ...
```

### Removed Dead Code

- Deleted commented urllib2 methods
- Removed unused imports (urllib.request, urllib.error)
- Cleaned up experimental code

### Improved Logging

- All logs use f-strings
- Consistent log format throughout
- Debug logs for troubleshooting user lookups
- Warning logs for fallback scenarios

## Attachment Handling Improvements

### Smart File Filtering

Automatically skips small files (< 5KB):

```python
if os.path.getsize(file_dir) > 5120:
    self.jitbit_api.post_attach_file(key, ticket_id, file_dir)
else:
    logger.info(f'[{key}] File size is < 5K. Ignoring. {file_dir}')
```

### Better Logging

Detailed logging for attachment operations:
- Download progress
- File size information
- Skip reasons

## Configuration Improvements

### Better Error Messages

Clearer assertion messages for missing config:

```python
assert JITBIT_API_URL is not None, 'JITBIT_API_URL must be set in .env file'
assert JITBIT_USER is not None, 'JITBIT_USER must be set in .env file'
```

### Flexible Defaults

Optional configuration parameters with sensible defaults:

```python
LOG_DIR = data.get('log_dir', base_dir_name + os.sep + '..' + os.sep + 'logs')
LOG_MAX_BYTES = data.get('log_max_bytes', 10485760)  # 10MB
LOG_BACKUP_COUNT = data.get('log_backup_count', 5)
```

## Migration Path from Sandpiper

See [CHANGELOG.md](../CHANGELOG.md) for detailed migration instructions.

### Quick Summary:

1. Rename package references from `sandpiper` to `jirajitsu`
2. Move credentials from `config.yml` to `.env`
3. Update Python to 3.10+
4. Update any custom code using the API

## Future Enhancements

Potential areas for future development:

1. **Bulk Operations**: Batch API calls for better performance
2. **Resume Capability**: Save progress and resume interrupted migrations
3. **Dry Run Mode**: Preview changes without actually migrating
4. **Custom Field Mapping**: Configurable field mappings between JIRA and JitBit
5. **Parallel Processing**: Migrate multiple tickets concurrently
6. **Web UI**: Optional web interface for monitoring migrations
7. **Webhook Support**: Real-time synchronization between systems

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for information on contributing new features.
