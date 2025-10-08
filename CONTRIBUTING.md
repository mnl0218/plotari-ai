# Contributing to Plotari Chatbot

Thank you for your interest in contributing to the Plotari Chatbot project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project follows a code of conduct that we expect all contributors to follow. Please be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Docker (optional, for containerized development)
- Weaviate Cloud Services account
- OpenAI API key
- Supabase account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/plotari-ai.git
   cd plotari-ai
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/original-owner/plotari-ai.git
   ```

## Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Weaviate Configuration
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your_weaviate_api_key
WEAVIATE_COLLECTION=Plotarichatbot

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
LOG_TO_FILE=false
ENVIRONMENT=development
```

### 3. Database Setup

```bash
# Run the RLS policy fix script
python fix_supabase_rls.py
```

### 4. Verify Installation

```bash
# Test the installation
python run.py
```

## Making Changes

### 1. Create a Feature Branch

```bash
# Always start from the latest dev branch
git checkout dev
git pull upstream dev

# Create a new feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and focused

### 3. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication system

- Implement JWT token generation
- Add login/logout endpoints
- Update API documentation
- Add unit tests for auth service

Fixes #123"
```

### 4. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Branch is up to date with target branch

### PR Requirements

1. **Clear Description**: Explain what, why, and how
2. **Link Issues**: Reference related issues
3. **Screenshots**: Include for UI changes
4. **Testing**: Describe how changes were tested
5. **Breaking Changes**: Document any breaking changes

### Review Process

1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one approval required
3. **Testing**: All tests must pass
4. **Documentation**: Must be updated if needed

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

```python
# Use type hints
def process_message(self, request: ChatRequest) -> ChatResponse:
    """Process a user message and generate response."""
    pass

# Use descriptive variable names
user_conversation_history = get_conversation_history(user_id)

# Keep functions small and focused (max 30 lines)
def validate_search_intent(intent: Dict[str, Any]) -> bool:
    """Validate search intent structure."""
    return all(key in intent for key in REQUIRED_KEYS)
```

### Code Organization

- **Single Responsibility**: Each function/class has one purpose
- **DRY Principle**: Don't repeat yourself
- **Clear Naming**: Use descriptive names
- **Comments**: Explain why, not what
- **Error Handling**: Always handle errors gracefully

### File Structure

```
src/
├── api/           # API endpoints
├── config/        # Configuration
├── models/        # Data models
├── services/      # Business logic
└── utils/         # Utilities
```

## Testing Guidelines

### Unit Tests

```python
def test_chatbot_service_process_message():
    """Test message processing functionality."""
    # Arrange
    chatbot = ChatbotService()
    request = ChatRequest(message="Find houses in Miami")
    
    # Act
    response = chatbot.process_message(request)
    
    # Assert
    assert response.message is not None
    assert response.properties_found is not None
```

### Integration Tests

```python
def test_property_search_integration():
    """Test property search with real services."""
    # Test with actual Weaviate connection
    pass
```

### Test Requirements

- **Coverage**: Aim for 80%+ code coverage
- **Naming**: Use descriptive test names
- **Isolation**: Tests should be independent
- **Speed**: Keep tests fast
- **Reliability**: Tests should be deterministic

## Documentation

### Code Documentation

```python
def search_properties(self, request: PropertySearchRequest) -> PropertySearchResponse:
    """
    Search for properties using hybrid search (vector + BM25).
    
    Args:
        request: Search parameters including query, filters, and location
        
    Returns:
        Search results with properties and metadata
        
    Raises:
        WeaviateConnectionError: If unable to connect to Weaviate
        ValidationError: If request parameters are invalid
    """
```

### API Documentation

- Update OpenAPI/Swagger documentation
- Include request/response examples
- Document error codes and messages

### README Updates

- Update installation instructions
- Add new features to feature list
- Update API endpoint documentation

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Create Release Branch**: `release/v2.2.0`
2. **Update Version**: Update version in `__init__.py`
3. **Update Changelog**: Document all changes
4. **Merge to Main**: After testing and approval
5. **Create Tag**: Tag the release
6. **Deploy**: Deploy to production

## Getting Help

### Questions and Support

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Code Review**: Ask for help in PR comments

### Resources

- [Python Style Guide](https://pep8.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Plotari Chatbot! 🚀
