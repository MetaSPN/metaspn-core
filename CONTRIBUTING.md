# Contributing to MetaSPN

Thank you for your interest in contributing to MetaSPN! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or another package manager
- Git

### Installation

1. Clone the repository:

```bash
git clone https://github.com/metaspn/metaspn.git
cd metaspn
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:

```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:

```bash
pre-commit install
```

This ensures all code is properly formatted and linted before each commit.
Commits will be blocked if linting fails.

5. Verify installation:

```bash
metaspn --version
pytest
```

## Code Style

We use the following tools to maintain code quality:

### Formatting

We use Black for code formatting:

```bash
black .
```

Configuration is in `pyproject.toml`:
- Line length: 100 characters
- Target Python versions: 3.9, 3.10, 3.11, 3.12

### Linting

We use Ruff for linting:

```bash
ruff check .
ruff check . --fix  # Auto-fix issues
```

### Type Checking

We use mypy for type checking:

```bash
mypy metaspn
```

All public functions should have type hints.

### Pre-commit Hooks

We use pre-commit to run all checks automatically before each commit:

```bash
# Run all hooks manually
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

The following hooks run automatically:
- **Black** - code formatting
- **Ruff** - linting
- **MyPy** - type checking
- **Bandit** - security checks
- **General hooks** - trailing whitespace, file endings, YAML/JSON validation

If a commit is blocked, fix the issues and try again. Most formatting issues
are auto-fixed by the hooks.

## Testing

### Running Tests

Run the full test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=metaspn --cov-report=html
```

Run specific tests:

```bash
pytest tests/test_core/test_profile.py
pytest -k "test_compute"  # Run tests matching pattern
```

### Test Coverage

We aim for >85% test coverage. New features should include tests.

### Writing Tests

- Place tests in the appropriate `tests/` subdirectory
- Use fixtures from `conftest.py` when possible
- Follow the existing test patterns
- Use descriptive test names

Example test:

```python
def test_activity_serialization(self, sample_activity: Activity):
    """Test that Activity can be serialized and deserialized."""
    data = sample_activity.to_dict()
    restored = Activity.from_dict(data)

    assert restored.platform == sample_activity.platform
    assert restored.title == sample_activity.title
```

## Pull Request Process

### Before Submitting

1. Create a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:

```bash
git add .
git commit -m "Add your descriptive commit message"
```

3. Ensure all tests pass:

```bash
pytest
```

4. Format and lint your code:

```bash
black .
ruff check .
mypy metaspn
```

5. Push to your fork:

```bash
git push origin feature/your-feature-name
```

### Submitting a PR

1. Open a pull request against the `main` branch
2. Fill out the PR template
3. Link any related issues
4. Wait for CI checks to pass
5. Request review from maintainers

### PR Guidelines

- Keep PRs focused on a single change
- Write clear commit messages
- Update documentation if needed
- Add tests for new features
- Follow existing code patterns

## Project Structure

```
metaspn/
├── core/           # Core data structures and computation
├── platforms/      # Platform-specific integrations
├── analyzers/      # Metrics analyzers
├── repo/           # Repository management
├── utils/          # Utility functions
├── cli/            # Command-line interface
└── api/            # REST API server

tests/
├── test_core/      # Tests for core module
├── test_platforms/ # Tests for platforms
├── test_analyzers/ # Tests for analyzers
├── test_repo/      # Tests for repo module
└── fixtures/       # Test fixtures and sample data
```

## Adding New Features

### Adding a New Platform

1. Create a new file in `metaspn/platforms/`
2. Inherit from `BasePlatform`
3. Implement required methods:
   - `get_platform_name()`
   - `ingest(data)`
   - `compute_metrics(activities)`
4. Add tests in `tests/test_platforms/`
5. Register in `metaspn/platforms/__init__.py`

### Adding a New Analyzer

1. Create a new file in `metaspn/analyzers/`
2. Create a class with a `compute()` method
3. Add tests in `tests/test_analyzers/`
4. Export in `metaspn/analyzers/__init__.py`

### Adding a New CLI Command

1. Add command in `metaspn/cli/commands.py`
2. Use the `@cli.command()` decorator
3. Add appropriate options and arguments
4. Update documentation

## Documentation

### Docstrings

All public functions, classes, and methods should have docstrings:

```python
def compute_profile(
    repo_path: str,
    force_recompute: bool = False,
) -> UserProfile:
    """Compute complete user profile from repository.

    Args:
        repo_path: Path to MetaSPN content repository
        force_recompute: If True, ignore cached results

    Returns:
        Complete UserProfile object with all computed metrics

    Raises:
        ValueError: If repo_path is invalid or repo is malformed

    Example:
        >>> profile = compute_profile("./my-content")
        >>> print(f"Level: {profile.cards.level}")
        Level: 8
    """
```

### README Updates

Update README.md when adding:
- New features
- New CLI commands
- API changes
- Configuration options

## Getting Help

- Open an issue for bugs or feature requests
- Join our Discord community for discussions
- Check existing issues before creating new ones

## Code of Conduct

Be respectful and inclusive. We welcome contributors from all backgrounds.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
