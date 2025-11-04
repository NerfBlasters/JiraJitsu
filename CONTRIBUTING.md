# Contributing to JiraJitsu

Thank you for your interest in contributing to JiraJitsu! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A JIRA and JitBit test environment (recommended)
- Familiarity with REST APIs

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/jirajitsu.git
   cd jirajitsu
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

5. Set up configuration files:
   ```bash
   cp .env.example .env
   cp config/config.yml.example config/config.yml
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 2. Make Changes

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Use f-strings for string formatting
- Write descriptive commit messages

### 3. Add Tests

All new features and bug fixes should include tests:

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=jirajitsu tests/

# Run specific test file
pytest tests/test_jira_api.py
```

### 4. Update Documentation

- Update README.md if adding user-facing features
- Add docstrings to new functions
- Update NEW_FEATURES.md for significant enhancements
- Update CHANGELOG.md

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Commit message format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints (Python 3.10+ style)
- Maximum line length: 120 characters
- Use docstrings for all public methods

### Type Hints Example

```python
def get_user_id_by_email(self, email: str) -> int:
    """
    Get JitBit user ID from email address.

    Args:
        email: User's email address

    Returns:
        User ID if found, or default user ID

    Raises:
        Exception: If API call fails
    """
    ...
```

### Logging

Use the logger throughout:

```python
import logging
from . import config

logger = logging.getLogger(config.LOG_ALIAS)

logger.debug(f'Debug message with {variable}')
logger.info(f'Info message')
logger.warning(f'Warning message')
logger.error(f'Error message')
logger.critical(f'Critical message')
```

### Error Handling

```python
try:
    # Code that might fail
    result = api_call()
except Exception as e:
    logger.error(f'Operation failed: {str(e)}')
    raise
```

Never use `e.message` (Python 2 style).

## Testing Guidelines

### Test Structure

```python
def test_feature_name():
    """Test description"""
    # Arrange
    setup_test_data()

    # Act
    result = function_to_test()

    # Assert
    assert result == expected_value
```

### Use Fixtures

```python
@pytest.fixture
def mock_api():
    """Create mock API for testing"""
    with patch('module.api_call') as mock:
        mock.return_value = {'status': 'success'}
        yield mock

def test_with_fixture(mock_api):
    """Test using fixture"""
    result = function_that_uses_api()
    assert result is not None
    mock_api.assert_called_once()
```

### Mock External APIs

Never make real API calls in tests:

```python
@patch('jirajitsu.jira_api.requests.get')
def test_api_call(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'key': 'value'}
    mock_get.return_value = mock_response

    # Test code here
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No secrets or credentials in code
- [ ] Commit messages are clear

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added
- [ ] No hardcoded secrets
```

### Review Process

1. Automated tests run on PR
2. Code review by maintainer(s)
3. Address feedback
4. Approval and merge

## Areas for Contribution

### High Priority

- Additional unit tests
- Integration tests
- Performance optimizations
- Better error messages
- Documentation improvements

### Feature Ideas

- Bulk API operations
- Resume capability for interrupted migrations
- Dry-run mode
- Custom field mapping configuration
- Parallel processing
- Progress reporting webhooks
- CLI improvements (--verbose, --quiet, etc.)
- Support for other issue trackers

### Bug Fixes

Check the issue tracker for bugs labeled "good first issue" or "help wanted".

## Security

### Reporting Vulnerabilities

**Do not open public issues for security vulnerabilities.**

Email security concerns to [security contact email] with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Best Practices

- Never commit secrets or credentials
- Always use environment variables for sensitive data
- Validate all user inputs
- Use parameterized queries
- Follow OWASP guidelines

## Questions?

- Open an issue with the "question" label
- Check existing documentation
- Review closed issues for similar questions

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## Acknowledgments

Thank you for contributing to JiraJitsu! Your efforts help make this tool better for everyone.
