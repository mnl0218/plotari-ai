# Weaviate Services Module

This module contains all specialized services for Weaviate operations, organized in a modular way with clear responsibilities.

## Module Structure

```
src/services/weaviate/
├── __init__.py                    # Module exports
├── interfaces.py                  # Contracts/Protocols for all services
├── weaviate_service.py           # Main service (Orchestrator)
├── connection_service.py         # Connection management
├── embedding_service.py          # AI/Embedding operations
├── data_converter_service.py     # Data transformation
├── search_service.py             # Core search operations
├── property_service.py           # Property-specific operations
├── poi_service.py                # POI operations
├── comparison_service.py         # Property comparison
└── README.md                     # This documentation
```

## Specialized Services

### 1. **WeaviateService** (Main Orchestrator)
- **Responsibility**: Coordinate all specialized services
- **Main functions**:
  - `search_properties()`: Search properties with filters
  - `get_property_detail()`: Get property details with recommendations
  - `search_pois()`: Search POIs near properties
  - `compare_properties()`: Compare properties with AI analysis

### 2. **WeaviateConnectionService**
- **Responsibility**: Connection management and health checks
- **Methods**:
  - `connect()`: Establishes connection with Weaviate
  - `ensure_connection()`: Ensures connection is active
  - `is_connected()`: Checks connection status
  - `close()`: Closes the connection

### 3. **WeaviateEmbeddingService**
- **Responsibility**: Embedding generation and AI operations
- **Methods**:
  - `generate_embedding()`: Generates embeddings using OpenAI
  - `generate_pros_cons_with_ai()`: Generates pros/cons using AI
  - `_call_openai_embedding()`: Internal OpenAI embedding calls
  - `_call_openai_completion()`: Internal OpenAI completion calls

### 4. **WeaviateDataConverterService**
- **Responsibility**: Data conversion and transformation
- **Methods**:
  - `convert_geo_coordinate()`: Converts geo data to GeoCoordinate
  - `convert_property_from_weaviate()`: Converts to Property object
  - `convert_poi_from_weaviate()`: Converts to POI object
  - `convert_neighborhood_from_weaviate()`: Converts to Neighborhood object

### 5. **WeaviateSearchService**
- **Responsibility**: Core search operations and query building
- **Methods**:
  - `search_properties()`: Searches properties with hybrid search
  - `_build_filters()`: Builds search filters
  - `_execute_hybrid_search()`: Executes hybrid search
  - `_execute_bm25_search()`: Executes BM25 search

### 6. **WeaviatePropertyService**
- **Responsibility**: Property-specific operations
- **Methods**:
  - `get_property_detail()`: Gets property details with recommendations
  - `find_similar_properties()`: Finds similar properties using vector search
  - `get_neighborhood_info()`: Gets neighborhood information

### 7. **WeaviatePOIService**
- **Responsibility**: POI-related operations
- **Methods**:
  - `search_pois()`: Searches POIs near a property
  - `get_pois_by_category()`: Gets POIs by category
  - `_convert_poi_data()`: Converts POI data

### 8. **WeaviateComparisonService**
- **Responsibility**: Property comparison operations
- **Methods**:
  - `compare_properties()`: Compares properties with AI analysis
  - `_build_comparison_table()`: Builds comparison table
  - `_generate_pros_cons()`: Generates pros/cons using AI

## Interfaces/Contracts

All interfaces are defined in `interfaces.py`:
- `WeaviateConnectionInterface`
- `WeaviateSearchInterface`
- `WeaviatePropertyInterface`
- `WeaviatePOIInterface`
- `WeaviateComparisonInterface`
- `WeaviateEmbeddingInterface`
- `WeaviateDataConverterInterface`

## Usage

### Simple Import
```python
from src.services.weaviate import WeaviateService

# Create instance
weaviate = WeaviateService()

# Search properties
response = weaviate.search_properties(search_request)
```

### Individual Service Import
```python
from src.services.weaviate import (
    WeaviateConnectionService,
    WeaviateEmbeddingService,
    WeaviateDataConverterService
)

# Use individual services
connection = WeaviateConnectionService()
embedding = WeaviateEmbeddingService()
converter = WeaviateDataConverterService()
```

## Workflow

```
WeaviateService.search_properties()
    ↓
WeaviateConnectionService.ensure_connection()
    ↓
WeaviateSearchService.search_properties()
    ↓
WeaviateEmbeddingService.generate_embedding()
    ↓
WeaviateDataConverterService.convert_property_from_weaviate()
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

The original `WeaviateService` is still available through:
- Direct import: `from src.services.weaviate_service import WeaviateService`
- New import: `from src.services.weaviate import WeaviateService`

Both imports point to the same refactored service, ensuring full backward compatibility.