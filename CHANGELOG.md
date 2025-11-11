# Changelog

All notable changes to JiraJitsu will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-10

### Added

#### Content Rendering
- **HTML Rendering Option** - New `--html` flag for migrate command
  - Uses JIRA's HTML-rendered content instead of raw wiki markup
  - Automatically strips internal images (192.168.x.x URLs) that won't be accessible
  - Cleaner formatting and structure in migrated tickets
  - Optional - defaults to wiki markup mode for compatibility

#### Content Cleaning
- **JIRA Wiki Markup Cleaning** - Automatic removal of formatting tags
  - Removes all `{color:...}` and `{color}` tags from content
  - Applied to both ticket descriptions and comments
  - Makes migrated content much more readable in JitBit
  - New `clean_jira_wiki_markup()` function in process_data.py

#### Filter Pagination
- **Large Filter Support** - Handles JIRA filters with >1000 issues
  - Automatic pagination for filter results
  - JIRA API limits results to 1000 per request
  - Now fetches all pages automatically up to 10,000 total issues
  - Fixed `get_filter()` method with pagination logic

#### Migration Features
- **Duplicate Detection** - Prevents recreating existing tickets
  - Checks JitBit for existing tickets before migration
  - Searches by JIRA key in ticket subject
  - Reports as "updated" instead of creating duplicates
  - Also prevents duplicate comments using timestamp comparison

- **Migration Statistics** - Detailed summary table after migration
  - Shows total tickets processed
  - Counts tickets created vs. updated
  - Tracks comments added and skipped (duplicates)
  - Shows attachments added
  - Displays users created and cached technicians
  - Reports execution time
  - Beautiful table formatting using Rich library

- **Auto-Create Users by Default** - Changed default behavior
  - Now automatically creates missing JitBit users during migration
  - New `--ignore-missing-users` flag to disable auto-creation
  - Removed old `--create-missing-users` flag (behavior is now default)
  - Automatically grants technician permissions for assigned categories
  - Tracks created users in migration summary

#### API Improvements
- **Custom User-Agent** - Identifies JiraJitsu traffic in server logs
  - Sets `User-Agent: JiraJitsu/{version}` for all API requests
  - Applied to both JIRA and JitBit API clients
  - Helps with traffic monitoring and debugging

- **jitapi Command Enhancement** - Improved manual API testing
  - New syntax: `jirajitsu jitapi <endpoint> --param value`
  - Dynamic parameter support (no predefined --param flags)
  - Cleaner, more intuitive interface
  - Better error messages and help text

#### CLI Enhancements
- **Enhanced Validation** - More detailed reporting
  - Added `--limit` option to validation commands
  - Better formatting of validation reports
  - More helpful error messages

- **Query Options Fix** - Fixed --issues, --jql, --project flags
  - These options were being ignored (always used default filter)
  - Now properly passes custom query to migration
  - ProcessData.start() accepts optional issues_list parameter

### Fixed

#### Critical Bugs
- **Filter Pagination** - Fixed filters with >1000 issues returning only first 1000
- **Query Options** - Fixed --issues, --jql, --project options being ignored
- **Hardcoded Project References** - Removed hardcoded project checks
  - Changed JIRA auth check from `/issue/PROJ-1` to `/myself` endpoint
  - More generic and works with any project structure

#### Migration Flow
- **Comment Reopening Tickets** - Fixed tickets being reopened after closure
  - Reordered flow: post_ticket → add_comments → add_attachments → update_ticket
  - Comments no longer reopen closed tickets

- **Historical Close Date** - Fixed close dates showing current date
  - JitBit API ignores closeDate when sent with statusId
  - Split into two UpdateTicket calls: first sets status, second sets closeDate
  - Historical dates now preserved correctly

- **Comment Deduplication** - Fixed edge case with different formats
  - JitBit stores comments with both `)<br><br>` and `)\n\n` separators
  - Updated regex to handle both formats
  - Prevents duplicate comment detection failures

#### User Management
- **Technician Permissions** - Auto-grant technician status
  - JitBit `create_user()` API ignores `isTechie` parameter
  - Now calls `AddCategoryTechPermission` after user creation
  - Users are properly assigned as technicians for the migration category

### Changed

- **Default Migration Behavior** - Auto-create users is now default
  - Breaking change: `--create-missing-users` flag removed
  - New flag: `--ignore-missing-users` to disable auto-creation
  - More intuitive - most users want missing users created

- **Setup Wizard** - Enhanced interactive defaults
  - Smarter messaging and permission checks
  - Automatic configuration backups
  - Better validation and error handling

- **Logging** - Improved debug output
  - More detailed logging for cache hits/misses
  - Better error context in API failures
  - Enhanced progress reporting

### Performance

- **User Cache Pre-loading** - Reduced API calls
  - Loads all JitBit users and technicians at start
  - Minimizes repeated API lookups during migration
  - Significant performance improvement for large migrations

- **Rate Limiting** - Better API throttling
  - Configurable rate limits in config.yml
  - Automatic retry on rate limit errors
  - Prevents API overload

### Documentation

- **Updated README.md** - Comprehensive CLI documentation
  - Replaced script-based examples with CLI commands
  - Added all new features
  - Better troubleshooting section
  - Token authentication examples

- **Updated INSTALLATION.md** - Modern installation guide
  - Interactive setup wizard instructions
  - Token authentication setup
  - Updated verification steps

- **Updated CLI_USAGE_GUIDE.md** - Corrected and expanded
  - Fixed incorrect `--create-missing-users` flag references
  - Added `--html` and `--limit` flags
  - Added comprehensive `jitapi` command documentation
  - Better examples and workflows

### Testing

- Tested filter pagination with 1257-issue filter
- Verified HTML rendering with internal image stripping
- Confirmed duplicate detection prevents recreating tickets
- Validated auto-create users with technician permissions
- Tested wiki markup cleaning removes color tags correctly

## [1.1.0] - 2024-11-05

### Added

#### Authentication
- **Token/API Key Authentication Support** for both JIRA and JitBit
  - JIRA Cloud: Email + API token authentication
  - JIRA Server/DC: Personal Access Token (PAT) authentication
  - JitBit: Bearer token authentication
  - Configurable via `JIRA_AUTH_METHOD` and `JITBIT_AUTH_METHOD` in `.env`
  - New `_get_auth_config()` and `_make_request()` helper methods in both API classes

#### Setup Improvements
- **Enhanced Setup Wizard** now loads existing configuration as defaults
  - Shows current values when updating configuration
  - Smart password/token handling - only prompts when credentials changed
  - Detects auth method switching and clears inappropriate defaults
  - Added helpful tips for switching from basic to token auth
  - URL normalization with duplicate protocol detection
- New configuration loading functions: `load_env_config()` and `load_yaml_config()`

#### Validation
- Improved user validation output clarity
  - Shows unique email count for JitBit users
  - Clearer messaging: "JIRA users with JitBit accounts" vs "Existing in JitBit"
  - Better permission error messages for restricted JIRA projects

### Fixed

#### Critical JitBit API Bugs
- **Authorization endpoint**: Fixed HTTP method from GET to POST (per API documentation)
- **AttachFile endpoint**: Fixed parameter name from `file` to `uploadFile` (files now attach correctly)
- **User endpoint**: Fixed parameter name from `id` to `userId` (technician check now works)
- **User endpoint**: Fixed response field from `IsTechie` to `IsTech` (correct technician detection)
- **URL normalization**: Fixed duplicate protocol prefix handling (e.g., `http://http://` → `http://`)

#### Setup Wizard Issues
- Fixed setup prompting for overwrite with default=False (now default=True for updates)
- Fixed username defaults when switching from basic to token authentication
- Fixed empty username handling for PAT/token-only authentication

### Changed
- Improved error messages with status codes in API responses
- Updated `.env.example` with comprehensive authentication examples
- Enhanced logging for authentication method selection

### Known Issues
- `create_user()` method's `isTechie` parameter is ignored by JitBit API
  - JitBit requires separate `AddCategoryTechPermission` API call to grant technician status
  - Users created with `is_technician=True` will NOT have technician permissions
  - Documented for future enhancement

### Testing
- Verified token authentication for both JIRA and JitBit
- Tested file attachment with README.md (Ticket #92214445)
- Confirmed technician status detection working correctly
- Validated setup wizard with existing configurations

## [1.0.0] - 2024-11-03

### Added

#### Security
- Environment-based configuration with python-dotenv
- Hybrid config system: `.env` for secrets, `config.yml` for settings
- Removed all hardcoded credentials from source code

#### User Management
- `get_user_is_technician()` method to validate user permissions
- Technician flag checking before ticket assignment
- Automatic fallback to default user for invalid assignments
- Comment author tracking with email-based lookup
- Comment timestamp preservation in format "(Originally posted on: YYYY-MM-DD)"
- Default user fallback for anonymous or invalid comment authors

#### Metadata Preservation
- Original assignee name added to ticket body
- Original resolution date preserved in ticket body
- Created timestamp passed to JitBit UpdateTicket API
- Historical accuracy maintained throughout migration

#### API Improvements
- Universal `post_update_ticket()` method supporting all UpdateTicket parameters
- Legacy methods (`post_set_assignee`, `post_change_catetory`) maintained for compatibility
- Better error messages using f-string formatting
- Type hints added to all function signatures

#### Testing
- Pytest framework integration
- Unit tests for configuration loading
- Unit tests for JIRA API methods
- Unit tests for JitBit API methods
- Mock-based testing (no live API calls required)
- Test fixtures for common scenarios

#### Documentation
- Comprehensive README.md with installation and usage instructions
- NEW_FEATURES.md documenting enhancements
- CONTRIBUTING.md with contribution guidelines
- Example configuration files (`.env.example`, `config.yml.example`)
- Inline code documentation with type hints

#### Development
- Python 3.10+ type hints throughout codebase
- GitHub Actions CI workflow for automated testing
- requirements.txt for dependency management
- setup.py for package installation
- Comprehensive .gitignore

### Changed

#### Breaking Changes
- **Package renamed**: `sandpiper` → `jirajitsu`
- **Python version**: Now requires Python 3.10+
- **Configuration**: Credentials must be in `.env` file instead of `config.yml`
- **Log alias**: Changed from `sandpiper_log` to `jirajitsu_log`
- **Log files**: Now named `jirajitsu_<pid>.log` instead of `sandpiper_<pid>.log`

#### Code Improvements
- All exception handling updated: `e.message` → `str(e)`
- All string formatting converted to f-strings
- Removed Python 2 compatibility code
- Cleaned up unused imports (urllib.request, urllib.error)
- Removed commented urllib2 methods
- Improved variable naming and code clarity

#### Configuration
- Split configuration into two files:
  - `.env`: API URLs, usernames, passwords (not committed)
  - `config.yml`: Category IDs, filter IDs, paths (can be committed)
- Better assertion error messages for missing config
- Defaults for optional parameters

#### API Methods
- `post_tag()` uncommented and working (was commented out)
- `post_update_ticket()` now handles both `categoryId` and `newCategoryId`
- Better parameter validation
- Improved logging throughout

### Fixed
- Python 2/3 compatibility issues
- Hardcoded default email removed
- Invalid email type checking improved
- Comment author lookup with proper fallback
- Assignee email validation with None checks
- Exception handling throughout codebase
- Missing return statements

### Removed
- Python 2 support
- `get_tickets()` method (unused urllib2 code)
- `_add_basic_auth()` method (unused urllib2 code)
- Hardcoded passwords and API keys
- Unused import statements
- Legacy code comments

## Migration Guide from Sandpiper

### For Users

1. **Upgrade Python**
   ```bash
   python --version  # Must be 3.10 or higher
   ```

2. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env and add your credentials
   ```

3. **Update config.yml**
   - Remove `jitbit_user`, `jitbit_pwd`, `jitbit_api_url`
   - Remove `jira_user`, `jira_pwd`, `jira_api_url`
   - Keep everything else

4. **Install new dependencies**
   ```bash
   pip install python-dotenv
   ```

5. **Update any scripts**
   - Replace `import sandpiper` with `import jirajitsu`
   - Update log file names in any scripts

### For Developers

1. **Update imports**
   ```python
   # Old
   from sandpiper import config
   from sandpiper.jira_api import JiraApi

   # New
   from jirajitsu import config
   from jirajitsu.jira_api import JiraApi
   ```

2. **Update exception handling**
   ```python
   # Old
   except Exception as e:
       logger.error(e.message)

   # New
   except Exception as e:
       logger.error(str(e))
   ```

3. **Add type hints**
   ```python
   # Old
   def get_user_id_by_email(self, email):

   # New
   def get_user_id_by_email(self, email: str) -> int:
   ```

4. **Update configuration loading**
   - Ensure `.env` file exists in project root
   - Use `os.getenv()` for any new environment variables

## [0.5.1] - 2023-11-16 (Sandpiper Fork)

### Changed
- Updated from Python 2.7 to Python 3 (partial)
- Added comment author tracking
- Added comment timestamps
- Improved assignee handling with creation date preservation

### Fixed
- Some Python 3 compatibility issues

## [0.5.0] - 2016-02-07 (Original Sandpiper)

### Added
- Initial JIRA to JitBit migration tool
- Basic ticket migration
- Attachment support
- Comment migration
- Progress bar
- Logging infrastructure

---

## Version History

- **1.0.0** (2024-11-03): JiraJitsu - Complete rewrite for Python 3.10+, security improvements, enhanced features
- **0.5.1** (2023-11-16): Sandpiper fork - Python 3 updates, improved user tracking
- **0.5.0** (2016-02-07): Original Sandpiper - Initial release

## Links

- [Original Sandpiper Repository](https://github.com/ajegam/sandpiper)
- [JiraJitsu Repository](TBD)

## Credits

- **Original Author**: ajegam (sandpiper)
- **Fork**: andy@clownshoemotorsports.com (2023)
- **JiraJitsu**: Complete rewrite and rebranding (2024)
