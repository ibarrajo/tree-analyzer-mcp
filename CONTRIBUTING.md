# Contributing to Tree Analyzer MCP

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Prerequisites**
   - Python 3.11 or higher
   - pip or uv
   - Git

2. **Clone and Install**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tree-analyzer-mcp
   cd tree-analyzer-mcp

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode with dev dependencies
   pip install -e ".[dev]"
   ```

3. **Development Workflow**
   ```bash
   # Run tests
   pytest

   # Run tests with coverage
   pytest --cov=src --cov-report=html --cov-report=term

   # Open coverage report
   open htmlcov/index.html  # On macOS

   # Lint code
   ruff check src
   black --check src
   mypy src

   # Auto-fix linting issues
   ruff check --fix src
   black src

   # Run all checks at once
   pytest && ruff check src && black --check src && mypy src
   ```

## Code Standards

### Python

- Python 3.11+ with type hints
- Follow PEP 8 style guide (enforced by Black and Ruff)
- Use type hints for all function signatures
- Add docstrings for all public functions (Google style)
- Maximum line length: 100 characters

Example:
```python
def analyze_person(person_id: str, depth: int = 3) -> dict[str, Any]:
    """Analyze a person and their relationships.

    Args:
        person_id: FamilySearch person ID
        depth: Number of relationship levels to analyze

    Returns:
        Dictionary containing analysis results with keys:
        - name: Person's display name
        - issues: List of detected issues
        - score: Overall data quality score (0-1)

    Raises:
        ValueError: If person_id is invalid
    """
    # Implementation
```

### Testing

- Write tests for all new features
- Maintain 70%+ code coverage
- Test both success and error cases
- Use descriptive test names: `test_<function>_<condition>_<expected_result>`

Example:
```python
def test_detect_duplicates_finds_similar_names():
    """Test that duplicate detection finds persons with similar names."""
    # Arrange
    db = create_test_db_with_duplicates()

    # Act
    duplicates = detect_name_duplicates(db, threshold=0.8)

    # Assert
    assert len(duplicates) > 0
    assert duplicates[0]["similarity"] >= 0.8
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Build process or tooling changes

Examples:
```
feat: add Metaphone algorithm for name matching
fix: handle missing birth dates in timeline validation
docs: update README with installation instructions
test: add integration tests for report generation
```

## Adding New Analysis Tools

To add a new analysis tool:

1. **Create analysis module** in `src/analysis/`:
   ```python
   # src/analysis/new_analyzer.py
   from typing import Any

   def analyze_new_feature(db, person_id: str) -> dict[str, Any]:
       """Analyze a specific genealogy feature.

       Args:
           db: Database connection
           person_id: Person to analyze

       Returns:
           Analysis results dictionary
       """
       # Implementation
   ```

2. **Add tool handler** in `src/tools/`:
   ```python
   # src/tools/analysis_tools.py
   from mcp.server import Server
   from ..analysis.new_analyzer import analyze_new_feature

   @server.tool()
   async def analyze_feature(person_id: str) -> str:
       """MCP tool for feature analysis."""
       db = get_db()
       results = analyze_new_feature(db, person_id)
       return format_results(results)
   ```

3. **Write tests** in `tests/`:
   ```python
   # tests/test_new_analyzer.py
   import pytest
   from src.analysis.new_analyzer import analyze_new_feature

   def test_analyze_feature_basic():
       """Test basic feature analysis."""
       # Test implementation
   ```

4. **Update documentation**:
   - Add to README.md "Tools Available" table
   - Add usage example
   - Update CHANGELOG.md

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
def test_normalize_spanish_name():
    """Test normalization of Spanish names with accents."""
    assert normalize_name("José María") == "jose maria"
    assert normalize_name("Martínez de la Cruz") == "martinez cruz"
```

### Integration Tests

Test analysis workflows end-to-end:

```python
def test_full_audit_report_generation(test_db):
    """Test generating complete audit report."""
    report = generate_audit_report(
        db=test_db,
        root_person_id="I1",
        generations=5
    )
    assert "Executive Summary" in report
    assert "FamilySearch" in report
```

### Fixtures

Use pytest fixtures for test data:

```python
@pytest.fixture
def test_db():
    """Create test database with sample genealogy data."""
    db = create_in_memory_db()
    populate_test_data(db)
    return db
```

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feat/add-new-analyzer
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test thoroughly**
   ```bash
   pytest
   ruff check src
   black --check src
   mypy src
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new genealogy analyzer"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/add-new-analyzer
   ```

6. **PR Requirements**
   - All tests pass
   - No linting errors
   - Code coverage maintained or improved
   - Documentation updated
   - Meaningful commit messages

## Code Review

All contributions require code review. Reviewers will check:

- Code quality and style
- Test coverage
- Documentation completeness
- Performance implications
- Algorithm correctness (especially for name matching)

## Bug Reports

When reporting bugs, include:

1. **Environment**
   - Python version
   - Operating system
   - MCP client (Claude Desktop, etc.)

2. **Steps to reproduce**
   - Exact commands or tool calls
   - Input parameters
   - Expected vs actual behavior

3. **Data context**
   - Database size (number of persons)
   - Specific person IDs if relevant
   - Error messages and stack traces

## Feature Requests

For new features:

1. **Use case**: Describe the genealogy problem you're trying to solve
2. **Proposed solution**: How should the analysis work?
3. **Alternatives**: What alternatives have you considered?
4. **Data requirements**: What data from the tree is needed?

## Questions?

- Open an issue for questions
- Join discussions on GitHub Discussions
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
