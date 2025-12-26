# Contributing to pytrends-modern

Thank you for your interest in contributing to pytrends-modern! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Relevant code snippets or error messages

### Suggesting Features

Feature suggestions are welcome! Please open an issue with:
- Clear description of the feature
- Use case and benefits
- Example API if applicable

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yiromo/pytrends-modern.git
   cd pytrends-modern
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,all]"
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

5. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style
   - Add type hints
   - Update tests

6. **Run tests**
   ```bash
   pytest
   pytest --cov=pytrends_modern  # With coverage
   ```

7. **Run linting**
   ```bash
   black pytrends_modern/
   ruff check pytrends_modern/
   mypy pytrends_modern/
   ```

8. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

9. **Push and create PR**
   ```bash
   git push origin feature/my-new-feature
   ```
   Then open a Pull Request on GitHub.

## Development Guidelines

### Code Style

- Follow PEP 8
- Use Black for formatting (line length 100)
- Use type hints throughout
- Write docstrings for all public functions/classes
- Keep functions focused and small

### Type Hints

All code should include type hints:

```python
def get_trends(
    keywords: List[str],
    timeframe: str = 'today 12-m',
    geo: str = ''
) -> pd.DataFrame:
    """
    Get trend data for keywords
    
    Args:
        keywords: List of keywords to query
        timeframe: Time range for data
        geo: Geographic location
        
    Returns:
        DataFrame with trend data
    """
    pass
```

### Documentation

- Use Google-style docstrings
- Include examples in docstrings
- Update README for user-facing changes
- Update CHANGELOG.md

Example docstring:
```python
def my_function(param1: str, param2: int = 10) -> bool:
    """
    Short description of function
    
    Longer description if needed, explaining behavior,
    edge cases, etc.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with default
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
        
    Example:
        >>> result = my_function("test", param2=20)
        >>> print(result)
        True
    """
    pass
```

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Use pytest fixtures for reusable test data
- Mark integration tests with `@pytest.mark.integration`

Example test:
```python
def test_my_feature():
    """Test description"""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result is True
```

### Error Handling

- Use custom exceptions from `exceptions.py`
- Provide helpful error messages
- Log warnings when appropriate
- Handle edge cases gracefully

Example:
```python
from pytrends_modern.exceptions import InvalidParameterError

def validate_input(value: str) -> str:
    if not value:
        raise InvalidParameterError(
            "Value cannot be empty. Please provide a valid string."
        )
    return value.upper()
```

## Project Structure

```
pytrends-modern/
├── pytrends_modern/          # Main package
│   ├── __init__.py         # Package exports
│   ├── request.py          # Core API client
│   ├── rss.py              # RSS feed support
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration constants
│   ├── exceptions.py       # Custom exceptions
│   └── utils.py            # Utility functions
├── examples/               # Usage examples
├── tests/                  # Test suite
├── README.md              # User documentation
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # This file
└── pyproject.toml         # Project metadata
```

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. Build package: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for contributing to pytrends-modern! 🎉
