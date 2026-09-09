# Contributing Guide

Thank you for your interest in contributing! Here's how you can help.

## Development Setup

```bash
git clone https://github.com/uzairaalizai/voiceover-to-video-matcher.git
cd voiceover-to-video-matcher
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

## Code Style

We follow PEP 8 standards with some modifications.

```bash
# Format code
black . --line-length 100

# Check code style
flake8 . --max-line-length 100
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_matcher.py::TestEmbedder -v
```

## Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Add/update tests:**
   ```bash
   # Add tests in tests/ directory
   pytest tests/
   ```

4. **Update documentation:**
   - Update relevant sections in README.md, API.md, or EXAMPLES.md
   - Add docstrings to new functions

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- Include a clear description of changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep commits focused and logical

## Areas for Contribution

### High Priority
- [ ] Improve vision analysis accuracy
- [ ] Add support for more audio formats
- [ ] Performance optimization for large files
- [ ] Better error messages and logging

### Medium Priority
- [ ] Add batch processing features
- [ ] Implement caching for embeddings
- [ ] Add progress bars for long operations
- [ ] Support for different embedding models

### Nice to Have
- [ ] Web interface
- [ ] Docker support
- [ ] Additional language support
- [ ] Export to different formats (XML, CSV, etc.)

## Reporting Issues

When reporting bugs, include:
- Python version
- OS/Platform
- Steps to reproduce
- Error messages and traceback
- Expected vs actual behavior

## Questions?

Feel free to open an issue or discussion for questions!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
