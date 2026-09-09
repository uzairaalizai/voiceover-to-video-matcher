# Tests directory

This directory contains unit tests and integration tests for the voiceover matcher.

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_matcher.py -v

# Run specific test
pytest tests/test_matcher.py::TestEmbedder::test_embedder_initialization -v
```

## Test Structure

- `test_matcher.py` - Unit tests for core components
- `test_integration.py` - Integration tests

## Mocking Media Files

For testing without actual media files, create dummy files:

```python
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    # Create test files
    pass
```
