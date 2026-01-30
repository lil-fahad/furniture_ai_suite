# Contributing to Interior Design AI Suite

Thank you for your interest in contributing to the Professional Interior Design AI Suite! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Code Standards](#code-standards)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Ways to Contribute

- **Bug Reports**: Report bugs via GitHub Issues
- **Feature Requests**: Suggest new features or improvements
- **Documentation**: Improve or translate documentation
- **Code**: Submit bug fixes or new features
- **Reviews**: Review pull requests from other contributors

### Before You Start

1. Check existing issues and pull requests to avoid duplicates
2. For major changes, open an issue first to discuss your approach
3. Ensure your development environment is set up correctly

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)
- (Optional) CUDA-capable GPU for training

### Setup Steps

1. **Fork the repository**
   ```bash
   # Click 'Fork' on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/furniture_ai_suite.git
   cd furniture_ai_suite
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/lil-fahad/furniture_ai_suite.git
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

5. **Install pre-commit hooks (optional)**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## How to Contribute

### Reporting Bugs

When filing a bug report, include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Minimal steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, relevant package versions
- **Logs**: Any relevant error messages or logs

**Template:**
```markdown
## Bug Description
[Clear description]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.10.0]
- Package versions: [relevant versions]

## Logs/Screenshots
[Any relevant logs or screenshots]
```

### Suggesting Features

For feature requests, include:

- **Problem Statement**: What problem does this solve?
- **Proposed Solution**: Your suggested implementation
- **Alternatives**: Other solutions you've considered
- **Additional Context**: Any other relevant information

### Contributing Code

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow the code standards (see below)
   - Add tests for new functionality

3. **Test your changes**
   ```bash
   # Run tests (when test suite is available)
   pytest
   
   # Check code style
   flake8 .
   black --check .
   
   # Type checking
   mypy .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```
   
   **Commit Message Format:**
   ```
   type(scope): subject
   
   body (optional)
   
   footer (optional)
   ```
   
   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   
   Example:
   ```
   feat(api): add batch prediction endpoint
   
   - Implemented batch processing for multiple images
   - Added validation for batch size limits
   - Updated API documentation
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Fill in the PR template

## Code Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters maximum (not 79)
- **Imports**: Group standard library, third-party, and local imports
- **Docstrings**: Google style docstrings for all public functions/classes

### Type Hints

Use type hints for all function signatures:

```python
from typing import List, Dict, Optional

def process_images(
    image_paths: List[str],
    output_dir: str,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Process a batch of images.
    
    Args:
        image_paths: List of paths to input images
        output_dir: Directory for processed images
        config: Optional configuration dictionary
        
    Returns:
        List of dictionaries with processing results
        
    Raises:
        ValueError: If image_paths is empty
        FileNotFoundError: If output_dir doesn't exist
    """
    pass
```

### Documentation

#### Module Docstrings

Every module should have a docstring:

```python
"""Module for handling data preparation.

This module provides functions for scanning, validating, and preparing
image datasets for model training.
"""
```

#### Function Docstrings

Use Google style:

```python
def train_model(config: Dict[str, Any]) -> Dict[str, float]:
    """Train a deep learning model.
    
    Args:
        config: Configuration dictionary with training parameters.
            Must include 'model_name', 'epochs', and 'learning_rate'.
    
    Returns:
        Dictionary with training metrics including 'accuracy' and 'loss'.
        
    Raises:
        ValueError: If required config keys are missing.
        RuntimeError: If training fails.
        
    Example:
        >>> config = {'model_name': 'efficientnet_b0', 'epochs': 10}
        >>> results = train_model(config)
        >>> print(results['accuracy'])
        0.95
    """
    pass
```

#### Class Docstrings

```python
class ImageProcessor:
    """Process and augment images for training.
    
    This class handles image loading, validation, augmentation,
    and preprocessing for deep learning models.
    
    Attributes:
        target_size: Target image dimensions (width, height)
        augmentation: Whether to apply data augmentation
        
    Example:
        >>> processor = ImageProcessor(target_size=(256, 256))
        >>> img = processor.process('path/to/image.jpg')
    """
    
    def __init__(self, target_size: Tuple[int, int]):
        """Initialize the image processor.
        
        Args:
            target_size: Target dimensions for processed images
        """
        pass
```

### Code Organization

```python
# 1. Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 2. Third-party imports
import numpy as np
import torch
from fastapi import FastAPI

# 3. Local imports
from utils import helper_function
from models import ModelClass
```

### Error Handling

Use specific exception types:

```python
# Good
if not image_path.exists():
    raise FileNotFoundError(f"Image not found: {image_path}")

# Bad
if not image_path.exists():
    raise Exception("Image not found")
```

### Logging

Use the logging module:

```python
import logging

logger = logging.getLogger(__name__)

def process_data():
    logger.info("Starting data processing")
    try:
        # Process data
        logger.debug("Processing step 1 complete")
    except Exception as e:
        logger.error(f"Data processing failed: {str(e)}")
        raise
```

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names

```python
# tests/test_data_processing.py

import pytest
from prepare_data import scan_images, unify_and_clean

def test_scan_images_finds_valid_images():
    """Test that scan_images correctly identifies image files."""
    result = scan_images("test_data/", "test_source")
    assert len(result) > 0
    assert all('filepath' in r for r in result)

def test_scan_images_ignores_non_images():
    """Test that scan_images ignores non-image files."""
    result = scan_images("test_data/", "test_source")
    assert not any(r['filepath'].endswith('.txt') for r in result)

def test_unify_and_clean_removes_duplicates():
    """Test that duplicate images are removed."""
    # Test implementation
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_data_processing.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Pull Request Process

### PR Checklist

Before submitting, ensure:

- [ ] Code follows the style guide
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated (README, API_EXAMPLES, etc.)
- [ ] Docstrings added/updated
- [ ] Type hints included
- [ ] No merge conflicts with main branch
- [ ] Commit messages are clear and descriptive

### PR Template

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
[How was this tested?]

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Closes #[issue number]
```

### Review Process

1. Automated checks run (linting, tests)
2. Maintainers review code
3. Address feedback and make changes
4. Once approved, maintainer merges PR

## Questions?

- Open an issue for questions
- Join our community discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing! 🎉
