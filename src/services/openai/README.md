# OpenAI Services Module

This module contains all specialized services for OpenAI operations, organized in a modular way with clear responsibilities.

## Module Structure

```
src/services/openai/
├── __init__.py                    # Module exports
├── interfaces.py                  # Contracts/Protocols for all services
├── openai_service.py             # Main service (Orchestrator)
├── connection_service.py         # Connection management
├── embedding_service.py          # Embedding operations
├── chat_service.py               # Chat completion
├── intent_extraction_service.py  # Intent extraction
├── property_response_service.py  # Property responses
├── model_service.py              # Model management
└── README.md                     # This documentation
```

## Specialized Services

### 1. **OpenAIService** (Main Orchestrator)
- **Responsibility**: Coordinate all specialized services
- **Main functions**:
  - `generate_embeddings()`: Generate text embeddings
  - `generate_chat_completion()`: Generate chat responses
  - `extract_search_intent()`: Extract search intent from messages
  - `generate_property_response()`: Generate property-specific responses
  - `is_available()`: Check service availability
  - `get_available_models()`: Get list of available models

### 2. **OpenAIConnectionService**
- **Responsibility**: Connection management and API key validation
- **Methods**:
  - `get_client()`: Gets the OpenAI client instance
  - `is_connected()`: Checks if service is properly connected
  - `_validate_api_key()`: Validates the API key
  - `_initialize_client()`: Initializes the OpenAI client

### 3. **OpenAIEmbeddingService**
- **Responsibility**: Embedding generation and management
- **Methods**:
  - `generate_embeddings()`: Generates embeddings for given text
  - `_validate_text_input()`: Validates text input
  - `_call_embedding_api()`: Internal API call method

### 4. **OpenAIChatService**
- **Responsibility**: Chat completion and conversation management
- **Methods**:
  - `generate_chat_completion()`: Generates chat response using OpenAI
  - `_validate_messages()`: Validates message structure
  - `_call_chat_completion_api()`: Internal API call method

### 5. **OpenAIIntentExtractionService**
- **Responsibility**: Intent extraction and analysis
- **Methods**:
  - `extract_search_intent()`: Extracts search intent from user message
  - `_build_intent_prompt()`: Builds the intent extraction prompt
  - `_validate_and_complete_intent()`: Validates and completes intent structure
  - `_get_default_search_intent()`: Returns default search intent

### 6. **OpenAIPropertyResponseService**
- **Responsibility**: Property-specific response generation
- **Methods**:
  - `generate_property_response()`: Generates contextual response about properties
  - `_build_response_context()`: Builds context of properties and POIs
  - `_get_fallback_response()`: Returns fallback response on errors

### 7. **OpenAIModelService**
- **Responsibility**: Model management and availability checks
- **Methods**:
  - `is_available()`: Checks if OpenAI service is available
  - `get_available_models()`: Returns list of available models
  - `_check_api_connection()`: Internal connection check
  - `_filter_relevant_models()`: Filters models to relevant ones
  - `get_model_info()`: Gets detailed information about a model

## Interfaces/Contracts

All interfaces are defined in `interfaces.py`:
- `OpenAIConnectionInterface`
- `OpenAIEmbeddingInterface`
- `OpenAIChatInterface`
- `OpenAIIntentExtractionInterface`
- `OpenAIPropertyResponseInterface`
- `OpenAIModelInterface`

## Usage

### Simple Import
```python
from src.services.openai import OpenAIService

# Create instance
openai_service = OpenAIService()

# Generate embeddings
embeddings = openai_service.generate_embeddings("text to embed")

# Generate chat completion
response = openai_service.generate_chat_completion([
    {"role": "user", "content": "Hello"}
])
```

### Individual Service Import
```python
from src.services.openai import (
    OpenAIConnectionService,
    OpenAIEmbeddingService,
    OpenAIChatService
)

# Use individual services
connection = OpenAIConnectionService()
embedding = OpenAIEmbeddingService(connection)
chat = OpenAIChatService(connection)
```

## Workflow

```
OpenAIService.generate_property_response()
    ↓
OpenAIConnectionService.get_client()
    ↓
OpenAIChatService.generate_chat_completion()
    ↓
OpenAIPropertyResponseService._build_response_context()
```

## Advantages of the Organization

1. **Single Responsibility**: Each service has a clear, well-defined responsibility
2. **Maintainability**: Changes in one functionality don't affect others
3. **Testability**: Each service can be tested independently
4. **Reusability**: Services can be reused in other contexts
5. **Scalability**: Easy to add new functionalities without modifying existing code
6. **Dependency Injection**: Easy to mock services for testing

## Testing

The module includes interfaces that facilitate testing:
- Mock individual services
- Test contracts
- Integration verification

## Development Notes

- All services implement their respective interfaces
- Imports are optimized for the new directory structure
- The main service maintains the same public API
- Compatible with the previous project structure
- All code is in English as requested

## Backward Compatibility

The original `OpenAIService` is still available through:
- Direct import: `from src.services.openai_service import OpenAIService`
- New import: `from src.services.openai import OpenAIService`

Both imports point to the same refactored service, ensuring full backward compatibility.

## Key Features

- **Embedding Generation**: High-quality text embeddings using OpenAI's latest models
- **Chat Completion**: Advanced conversation capabilities with GPT models
- **Intent Extraction**: Smart extraction of search intents from natural language
- **Property Responses**: Contextual responses about Plotari properties
- **Model Management**: Comprehensive model availability and information
- **Error Handling**: Robust error handling with fallback responses
- **Validation**: Input validation and sanitization throughout