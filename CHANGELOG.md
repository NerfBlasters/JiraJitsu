# Changelog

All notable changes to JiraJitsu will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
