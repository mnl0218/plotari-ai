# Chatbot Services Module

This module contains all specialized services for the Plotari chatbot operation, organized in a modular way with clear responsibilities.

## Module Structure

```
src/services/chatbot/
├── __init__.py                      # Module exports
├── interfaces.py                    # Contracts/Protocols for all services
├── chatbot_service.py              # Main service (Orchestrator)
├── intent_extractor_service.py     # Search intent extraction
├── property_search_service.py      # Property searches and operations
├── poi_search_service.py           # POI searches (Points of Interest)
├── response_generator_service.py   # Contextual response generation
├── conversation_manager_service.py # Conversation and context management
└── cache_manager_service.py        # Cache management (memory and JSON)
```

## Specialized Services

### 1. **ChatbotService** (Main Orchestrator)
- **Responsibility**: Coordinate all specialized services
- **Main functions**:
  - `process_message()`: Processes user messages
  - `get_conversation_history()`: Gets conversation history
  - `get_service_status()`: Status of all services

### 2. **IntentExtractorService**
- **Responsibility**: Extract and validate search intents
- **Methods**:
  - `extract_search_intent()`: Extracts intent using OpenAI or fallback
  - `_validate_search_intent()`: Validates intent structure
  - `_extract_*_intent()`: Specific methods by intent type

### 3. **PropertySearchService**
- **Responsibility**: Property searches and related operations
- **Methods**:
  - `search_properties()`: Basic property search
  - `search_properties_near_pois()`: Search near POIs
  - `get_property_detail()`: Specific property detail
  - `compare_properties()`: Property comparison

### 4. **POISearchService**
- **Responsibility**: POI searches (Points of Interest)
- **Methods**:
  - `search_pois()`: Searches POIs near a property

### 5. **ResponseGeneratorService**
- **Responsibility**: Contextual response generation
- **Methods**:
  - `generate_response()`: Generates responses using OpenAI or fallback
  - `_get_fallback_response()`: Rule-based fallback responses

### 6. **ConversationManagerService**
- **Responsibility**: Conversation and context management
- **Methods**:
  - `get_or_create_conversation()`: Gets or creates conversation
  - `build_context_from_conversation()`: Builds context from conversation
  - `update_conversation_context()`: Updates conversation context
  - `get_conversation_history()`: Gets conversation history
  - `clear_conversation()`: Clears specific conversation

### 7. **CacheManagerService**
- **Responsibility**: Cache management (memory and JSON)
- **Methods**:
  - `add_to_memory_cache()`: Adds to memory cache
  - `save_conversation_to_cache()`: Saves to JSON cache
  - `cleanup_old_conversations()`: Cleans old conversations
  - `get_cache_info()`: Gets cache information
  - `clear_all_cache()`: Clears all cache

## Service Flow

```
User Message
     ↓
ChatbotService.process_message()
     ↓
IntentExtractorService.extract_search_intent()
     ↓
PropertySearchService.search_properties() OR
POISearchService.search_pois()
     ↓
ResponseGeneratorService.generate_response()
     ↓
ConversationManagerService.update_conversation_context()
     ↓
CacheManagerService.save_conversation_to_cache()
     ↓
Response to User
```

## Architecture Principles

### 1. **Single Responsibility**
Each service has a single, well-defined responsibility.

### 2. **Dependency Injection**
Services receive their dependencies through constructors.

### 3. **Interface Segregation**
Each service implements specific interfaces.

### 4. **Open/Closed Principle**
Services are open for extension but closed for modification.

### 5. **Dependency Inversion**
Services depend on abstractions, not concrete implementations.

## Configuration

### Environment Variables
- `CACHE_DIR`: Cache directory (default: "cache/conversations")
- `CACHE_MAX_AGE_HOURS`: Maximum cache age in hours (default: 24)
- `CACHE_MAX_SIZE`: Maximum memory cache size (default: 100)

### Dependencies
- `src.services.weaviate`: Weaviate service for database operations
- `src.services.openai`: OpenAI service for AI operations
- `src.utils.json_cache`: JSON cache utility
- `src.models.property`: Data models

## Testing

### Unit Tests
Each service can be tested independently by mocking its dependencies.

### Integration Tests
Test the complete flow from user message to response.

### Example Test
```python
def test_chatbot_service():
    # Mock dependencies
    mock_weaviate = Mock()
    mock_openai = Mock()
    
    # Create service
    chatbot = ChatbotService()
    chatbot.weaviate_service = mock_weaviate
    chatbot.openai_service = mock_openai
    
    # Test message processing
    request = ChatRequest(message="Find houses in Miami")
    response = chatbot.process_message(request)
    
    assert response.message is not None
    assert response.properties_found is not None
```

## Performance Considerations

### 1. **Memory Cache**
- Fast access to recent conversations
- Limited size to prevent memory issues
- Automatic cleanup of old conversations

### 2. **JSON Cache**
- Persistent storage for conversations
- Automatic cleanup based on age
- Efficient file-based storage

### 3. **Service Initialization**
- Lazy loading of external services
- Connection pooling where possible
- Error handling and reconnection

## Usage Examples

### Basic Usage
```python
from src.services.chatbot import ChatbotService

# Create service
chatbot = ChatbotService()

# Process message
request = ChatRequest(message="Find houses near schools")
response = chatbot.process_message(request)

print(response.message)
```

### Advanced Usage
```python
# Get conversation history
history = chatbot.get_conversation_history("session_123", limit=10)

# Get service status
status = chatbot.get_service_status()

# Clear conversation
chatbot.clear_conversation("session_123")
```

## Troubleshooting

### Common Issues

1. **Service Initialization Errors**
   - Check environment variables
   - Verify external service connections
   - Check logs for specific error messages

2. **Cache Issues**
   - Verify cache directory permissions
   - Check disk space
   - Clear cache if corrupted

3. **Intent Extraction Issues**
   - Check OpenAI API key
   - Verify message format
   - Check fallback mechanisms

### Debug Mode
Enable debug logging to see detailed service operations:
```python
import logging
logging.getLogger("src.services.chatbot").setLevel(logging.DEBUG)
```

## Related Documentation

- [Weaviate Services](../weaviate/README.md)
- [OpenAI Services](../openai/README.md)
- [API Endpoints](../../api/endpoints.py)
- [Data Models](../../models/property.py)

---

**Note**: This module is designed to be highly modular and testable. Each service can be used independently or as part of the complete chatbot system.