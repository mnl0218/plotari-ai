# Plotari AI Backend

A robust and scalable backend for the Plotari AI real estate chatbot that uses **Weaviate** as a vector database, **OpenAI** for natural language processing, **Supabase** for data persistence, and **OpenStreetMap** for POI enrichment. The system enables intelligent property searches through natural conversation with a **comprehensive REST API** featuring multiple specialized endpoints.

## Key Features

- **Conversational Chatbot**: Natural chat interface with intent detection and conversation persistence
- **Hybrid Search**: Combines semantic (vector) and textual (BM25) search in Weaviate
- **Vector Database**: Weaviate for intelligent property and POI searches
- **Advanced AI**: OpenAI GPT for natural language processing and response generation
- **Persistent Storage**: Supabase for conversation, analytics, and property data
- **Real-time Chat**: Server-Sent Events (SSE) support for streaming responses
- **POI Enrichment**: OpenStreetMap integration for location-based services
- **Data Synchronization**: Automated sync between Supabase and Weaviate
- **Deletion Operations**: Comprehensive data deletion capabilities
- **Scalable**: Modular service-oriented architecture with dependency injection
- **Analytics**: Search logging and conversation analytics
- **Robust**: Comprehensive error handling, validations, and structured logging

## Project Architecture

```
plotari-ai/
├── src/
│   ├── config/              # Centralized configuration
│   │   ├── __init__.py
│   │   └── settings.py         # Environment variables and configuration
│   ├── models/              # Data models (Pydantic)
│   │   ├── __init__.py
│   │   └── property.py         # Plotari property models
│   ├── services/            # Business logic (modular services)
│   │   ├── chatbot/         # Chatbot specialized services
│   │   │   ├── chatbot_service.py              # Main orchestrator
│   │   │   ├── intent_extractor_service.py     # Intent extraction
│   │   │   ├── property_search_service.py      # Property searches
│   │   │   ├── poi_search_service.py           # POI searches
│   │   │   ├── response_generator_service.py   # Response generation
│   │   │   ├── conversation_manager_service.py # Conversation management
│   │   │   └── cache_manager_service.py        # Cache management
│   │   ├── openai/          # OpenAI specialized services
│   │   │   ├── openai_service.py              # Main orchestrator
│   │   │   ├── connection_service.py          # Connection management
│   │   │   ├── embedding_service.py           # Embedding operations
│   │   │   ├── chat_service.py                # Chat completion
│   │   │   ├── intent_extraction_service.py   # Intent extraction
│   │   │   ├── property_response_service.py   # Property responses
│   │   │   ├── summary_service.py             # Summary generation
│   │   │   └── model_service.py               # Model management
│   │   ├── weaviate/        # Weaviate specialized services
│   │   │   ├── weaviate_service.py           # Main orchestrator
│   │   │   ├── connection_service.py         # Connection management
│   │   │   ├── embedding_service.py          # AI/Embedding operations
│   │   │   ├── data_converter_service.py     # Data transformation
│   │   │   ├── search_service.py             # Core search operations
│   │   │   ├── property_service.py           # Property operations
│   │   │   ├── poi_service.py                # POI operations
│   │   │   ├── deletion_service.py           # Deletion operations
│   │   │   └── comparison_service.py         # Property comparison
│   │   ├── supabase/        # Supabase specialized services
│   │   │   ├── conversation_service.py       # Conversation persistence
│   │   │   ├── conversation_repository.py    # Data access layer
│   │   │   ├── conversation_analytics_service.py # Analytics
│   │   │   ├── conversation_cleanup_service.py   # Cleanup operations
│   │   │   ├── property_service.py           # Property operations
│   │   │   └── search_log_service.py         # Search logging
│   │   ├── osm/             # OpenStreetMap services
│   │   │   ├── osm_service.py                # Main orchestrator
│   │   │   ├── connection_service.py         # Connection management
│   │   │   └── poi_service.py                # POI search operations
│   │   ├── enrichment/      # Enrichment services
│   │   │   └── poi_enrichment_service.py     # POI enrichment
│   │   └── sync/            # Synchronization services
│   │       └── property_sync_service.py      # Property sync
│   ├── api/                 # API endpoints
│   │   ├── routes/          # Route modules
│   │   │   ├── analytics.py    # Analytics endpoints
│   │   │   ├── cache.py        # Cache endpoints
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── conversations.py # Conversation endpoints
│   │   │   ├── deletion.py     # Deletion endpoints
│   │   │   ├── enrichment.py   # Enrichment endpoints
│   │   │   ├── health.py       # Health check endpoints
│   │   │   ├── properties.py   # Property endpoints
│   │   │   └── sync.py         # Sync endpoints
│   │   └── dependencies.py  # Shared dependencies
│   ├── utils/               # Common utilities
│   │   ├── __init__.py
│   │   ├── helpers.py          # Helper functions and validators
│   │   └── json_cache.py       # JSON cache utilities
│   └── main.py                 # Main FastAPI application
├── tests/                   # Test files and SQL schemas
├── docs/                    # Documentation
├── backup/                  # Service backups
├── scripts/                 # Utility scripts
├── requirements.txt         # Project dependencies
├── run.py                   # Quick start script
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── Makefile                 # Build automation
├── CONTRIBUTING.md          # Contribution guidelines
├── QUICK_INSTALLATION.md    # Quick setup guide
└── README.md               # This file
```

## Installation and Setup

### 1. Prerequisites

- Python 3.8+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- Weaviate Cloud Services (WCS) account
- OpenAI API Key
- Supabase account and project
- Git

### 2. Installation

#### Option A: Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd chatbot-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Docker Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd chatbot-backend

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Build and start with Docker Compose
docker-compose up --build

# Or build Docker image manually
docker build -t chatbot-backend .
```

### 3. Configuration

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

# CORS Configuration (optional)
CORS_ORIGINS=*
```

### 4. Supabase Setup

Before running the application, you need to set up the Supabase database:

```bash
# Run the RLS policy fix script
python fix_supabase_rls.py

# Or manually create the tables using the SQL files in tests/
```

### 5. Verification

```bash
# Use the startup script that includes checks
python run.py

# Or start directly
python -m src.main
```

## API Endpoints

### General Information
- `GET /` - Basic API information and endpoint overview
- `GET /info` - Detailed system information and design description
- `GET /docs` - Interactive documentation (Swagger UI)
- `GET /redoc` - Alternative documentation (ReDoc)

### Chat (Core Endpoints)
- `POST /api/chat` - Process chat message with intent detection and natural language response
- `POST /api/chat/message` - **SSE endpoint** for real-time streaming chat responses

### Property Search
- `POST /api/search` - Hybrid property search with filters (price, beds, baths, location)
- `GET /api/property/{property_id}` - Get property detail with similar recommendations
- `GET /api/property/{property_id}/pois` - Get POIs near property (schools, restaurants, etc.)
- `POST /api/compare` - Compare multiple properties with AI-generated pros/cons

### Conversation Management
- `GET /api/conversation/{user_id}/{session_id}/history` - Get conversation history
- `DELETE /api/conversation/{user_id}/{session_id}` - Clear specific conversation
- `GET /api/user/{user_id}/conversations` - Get all conversations for a user
- `GET /api/user/{user_id}/stats` - Get user statistics
- `GET /api/conversations/stats` - Get conversation statistics

### Analytics & Monitoring
- `GET /api/analytics/search-logs` - Get search logs with filtering
- `GET /api/analytics/search-stats` - Get search analytics for specified period
- `DELETE /api/analytics/search-logs/cleanup` - Clean up old search logs
- `GET /api/health` - System health status and service availability
- `GET /api/cache/info` - Detailed cache information
- `DELETE /api/cache/clear` - Clear all cache

### Synchronization
- `POST /api/sync/properties/full` - Full synchronization of properties from Supabase to Weaviate
- `POST /api/sync/properties/incremental` - Incremental synchronization of recent properties
- `GET /api/sync/properties/status` - Get synchronization status and statistics

### Deletion Operations
- `DELETE /api/delete/properties/all` - Delete all properties from Weaviate
- `DELETE /api/delete/properties/by-date` - Delete properties before a specific date
- `DELETE /api/delete/properties/{zpid}` - Delete a specific property by ID
- `DELETE /api/delete/properties/bulk` - Bulk delete properties by IDs
- `GET /api/delete/properties/status` - Get deletion operation status

### Enrichment
- `POST /api/enrich-pois` - Enrich properties with POIs from OpenStreetMap

> 📖 **For detailed documentation on Synchronization and POI Enrichment endpoints**, see [Sync and Enrichment Endpoints Guide](docs/sync-and-enrichment-endpoints.md)

## Services and Functionality

The system is built with a **modular architecture** where each service has a single, well-defined responsibility. Services are organized into seven main modules:

### Chatbot Services (`src/services/chatbot/`)

**Main orchestrator and specialized chatbot services**

```python
from src.services.chatbot import ChatbotService

# Main service that coordinates all components
with ChatbotService() as chatbot:
    # Process message with intent detection
    response = chatbot.process_message(chat_request)
    
    # Get conversation history with enriched properties
    history = chatbot.get_conversation_history("user_123", "session_456")
    
    # Get conversation statistics
    stats = chatbot.get_conversation_stats()
    
    # Get cache information
    cache_info = chatbot.get_cache_info()
    
    # System status
    status = chatbot.get_service_status()
```

**Specialized Services:**
- **`IntentExtractorService`**: Extracts and validates search intents
- **`PropertySearchService`**: Property searches and operations
- **`POISearchService`**: POI searches (Points of Interest)
- **`ResponseGeneratorService`**: Contextual response generation
- **`ConversationManagerService`**: Conversation and context management
- **`CacheManagerService`**: Cache management (memory and JSON)

### OpenAI Services (`src/services/openai/`)

**OpenAI integration with specialized services**

```python
from src.services.openai import OpenAIService

# Main service that coordinates all OpenAI operations
with OpenAIService() as openai:
    # Generate embeddings
    embedding = openai.generate_embeddings("3 bedroom house")
    
    # Extract search intent
    intent = openai.extract_search_intent("Looking for a house in Miami")
    
    # Generate contextual response
    response = openai.generate_property_response(
        user_message, properties, search_intent
    )
    
    # Check availability
    is_available = openai.is_available()
```

### Weaviate Services (`src/services/weaviate/`)

**Weaviate vector database operations with specialized services**

```python
from src.services.weaviate import WeaviateService
from src.models.property import PropertySearchRequest, POISearchRequest, PropertyCompareRequest

# Main service that coordinates all Weaviate operations
with WeaviateService() as weaviate:
    # Search properties with filters
    search_request = PropertySearchRequest(
        query="3 bedroom house Miami",
        min_price=300000,
        max_price=800000,
        latitude=25.7617,
        longitude=-80.1918,
        radius=5000
    )
    results = weaviate.search_properties(search_request)
    
    # Get property details with similar recommendations
    property_detail = weaviate.get_property_detail("12345")
    
    # Search POIs near properties
    poi_request = POISearchRequest(
        property_id="12345",
        category="school",
        radius=1500,
        limit=10
    )
    pois = weaviate.search_pois(poi_request)
    
    # Compare properties with AI analysis
    compare_request = PropertyCompareRequest(property_ids=["prop1", "prop2", "prop3"])
    comparison = weaviate.compare_properties(compare_request)
```

### Supabase Services (`src/services/supabase/`)

**Supabase database operations for conversation persistence and analytics**

```python
from src.services.supabase import SearchLogService, SupabaseConversationService, SupabasePropertyService

# Search logging
search_log_service = SearchLogService()
search_log_service.log_search("conversation_123", "property_search", {"query": "3 bedroom house"})

# Conversation management
conversation_service = SupabaseConversationService()
conversations = conversation_service.list_conversations(user_id="user_123")

# Property management
property_service = SupabasePropertyService()
properties = property_service.get_all_properties(limit=100)
```

**Specialized Services:**
- **`SupabaseConversationService`**: Conversation persistence and management
- **`SupabaseConversationRepository`**: Data access layer for conversations
- **`ConversationAnalyticsService`**: Conversation analytics and insights
- **`ConversationCleanupService`**: Cleanup operations for old conversations
- **`SearchLogService`**: Search logging and analytics
- **`SupabasePropertyService`**: Property data operations

### OpenStreetMap Services (`src/services/osm/`)

**OpenStreetMap integration for POI enrichment**

```python
from src.services.osm import OSMService

# Main service for OpenStreetMap operations
with OSMService() as osm:
    # Search for POIs near coordinates
    pois = osm.search_pois_nearby(
        latitude=25.7617,
        longitude=-80.1918,
        radius=1500,
        category="restaurant"
    )
    
    # Check availability
    is_available = osm.is_available()
```

**Specialized Services:**
- **`OSMService`**: Main orchestrator for OpenStreetMap operations
- **`OSMConnectionService`**: Connection management
- **`OSMPOIService`**: POI search and retrieval operations

### Enrichment Services (`src/services/enrichment/`)

**POI enrichment for properties**

```python
from src.services.enrichment import POIEnrichmentService

# Enrich properties with POIs
enrichment_service = POIEnrichmentService()
result = enrichment_service.enrich_properties_with_pois(
    property_ids=["prop1", "prop2"],
    categories=["restaurant", "school", "park"],
    radius=1500
)
```

**Specialized Services:**
- **`POIEnrichmentService`**: Property enrichment with POI data

### Synchronization Services (`src/services/sync/`)

**Data synchronization between Supabase and Weaviate**

```python
from src.services.sync import PropertySyncService

# Synchronize properties
sync_service = PropertySyncService()

# Full synchronization
result = sync_service.sync_all_properties()

# Incremental synchronization
result = sync_service.sync_incremental(days=7)
```

**Specialized Services:**
- **`PropertySyncService`**: Property data synchronization

## Architecture Benefits

### Service-Oriented Architecture (SOA)
The system follows a **Service-Oriented Architecture** with clear separation of concerns:

- **Single Responsibility**: Each service has one well-defined purpose
- **Loose Coupling**: Services communicate through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together
- **Dependency Injection**: Services receive dependencies through constructors
- **Interface Segregation**: Clean contracts for all service interactions

### Service Organization

```
src/services/
├── chatbot/          # Chatbot business logic
├── openai/           # AI/ML operations
├── weaviate/         # Vector database operations
├── supabase/         # Persistence and analytics
├── osm/              # OpenStreetMap integration
├── enrichment/       # Data enrichment operations
└── sync/             # Data synchronization
```

Each module contains:
- **Main Service**: Orchestrates specialized services
- **Specialized Services**: Handle specific responsibilities
- **Interfaces**: Define contracts and protocols
- **README**: Detailed documentation for each module

## Data Models

### Property
```python
class Property(BaseModel):
    zpid: str = Field(..., description="Unique property ID")
    address: str = Field(..., max_length=500)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=50)
    zipcode: str = Field(..., max_length=10)
    price: Optional[float] = Field(None, ge=0)
    bedrooms: Optional[float] = Field(None, ge=0, le=20)
    bathrooms: Optional[float] = Field(None, ge=0, le=20)
    living_area: Optional[float] = Field(None, ge=0)
    year_built: Optional[float] = Field(None, ge=1800, le=2030)
    geo: GeoCoordinate = Field(..., description="Geographic location")
    # ... more fields with comprehensive validations
```

### Chat
```python
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = Field(default=None)

class ChatResponse(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    properties_found: Optional[List[Property]] = Field(default=None)
    pois_found: Optional[List[POI]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
```

## Execution

### Development

#### Local Development
```bash
# Option 1: Startup script (recommended)
python run.py

# Option 2: Direct with uvicorn
python -m src.main
# or
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Docker Development
```bash
# Start with Docker Compose (recommended)
docker-compose up --build

# Or run Docker container directly
docker run -p 8000:8000 --env-file .env chatbot-backend
```

### Production

#### Local Production
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Docker Production
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using Docker directly
docker run -d -p 8000:8000 --env-file .env --name chatbot-backend chatbot-backend
```

## Quick Start Script

The project includes a `run.py` script that facilitates startup:

### Script Features
- **Automatic verification** of installed dependencies
- **Validation** of `.env` file
- **Optional connection tests**
- **Automatic startup** of the server

### Usage
```bash
python run.py
```

## Testing

### Quick Start Script
```bash
# Use the startup script that includes checks
python run.py
```

### Manual Testing
```bash
# Test individual components
python -c "from src.services.weaviate import WeaviateService; print('Weaviate OK')"
python -c "from src.services.openai import OpenAIService; print('OpenAI OK')"
python -c "from src.services.supabase import SearchLogService; print('Supabase OK')"

# Start server directly
python -m src.main
```

## Advanced Configuration

### Environment Variables

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `WEAVIATE_URL` | Weaviate cluster URL | - | ✅ |
| `WEAVIATE_API_KEY` | Weaviate API Key | - | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key | - | ✅ |
| `SUPABASE_URL` | Supabase project URL | - | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | - | ✅ |
| `DEBUG` | Debug mode | `False` | ❌ |
| `HOST` | Server host | `0.0.0.0` | ❌ |
| `PORT` | Server port | `8000` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `LOG_TO_FILE` | Write logs to file | `false` | ❌ |
| `ENVIRONMENT` | Runtime environment | `development` | ❌ |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | ❌ |

## Deployment

### Docker

#### Dockerfile
```dockerfile
# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/cache/conversations && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring and Metrics

### Health Check
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "weaviate_connected": true,
  "openai_connected": true,
  "conversations": {
    "total": 5,
    "active": 3
  },
  "service": "chatbot-backend",
  "version": "1.0.0"
}
```

## Security

### Implemented Best Practices
- Input validation on all endpoints
- User data sanitization
- Secure environment variable handling
- Security logging
- Supabase RLS policies for data protection

### CORS Configuration
```env
# Allow only specific domains in production
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
```

## Troubleshooting

### Common Issues

#### 1. Weaviate Connection Error
```bash
# Check environment variables
echo $WEAVIATE_URL
echo $WEAVIATE_API_KEY

# Use the startup script that checks connections
python run.py
```

#### 2. OpenAI Error
```bash
# Check API Key
echo $OPENAI_API_KEY

# Test with curl
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/models
```

#### 3. Supabase Connection Error
```bash
# Check Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Run RLS policy fix
python fix_supabase_rls.py
```

#### 4. Port in Use
```bash
# Change port
PORT=8001 uvicorn src.main:app --reload

# Or kill process
lsof -ti:8000 | xargs kill -9
```

## Project Structure

### Core Directories

- **`/src/`** - Core application code
  - `/api/` - API routes and endpoints
  - `/config/` - Configuration management
  - `/models/` - Data models (Pydantic)
  - `/services/` - Business logic services
  - `/utils/` - Utility functions
- **`/tests/`** - Test files and SQL schemas
- **`/docs/`** - Documentation files
- **`/scripts/`** - Utility scripts
- **`/backup/`** - Service backups

### Configuration Files

- **`requirements.txt`** - Python dependencies
- **`run.py`** - Quick start script
- **`Dockerfile`** - Docker configuration
- **`docker-compose.yml`** - Docker Compose configuration
- **`Makefile`** - Build automation
- **`.env`** - Environment variables (not in repo)
- **`.gitignore`** - Git ignore rules
- **`.dockerignore`** - Docker ignore rules

## Support

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Weaviate Docs](https://weaviate.io/developers/weaviate)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Supabase Docs](https://supabase.com/docs)

### Issues
To report bugs or request features, create an issue in the repository.

## License

This project is under the MIT License. See the `LICENSE` file for more details.

---

## Current Version

**Version 2.0.0** - Modular REST API with Full Integration Suite

### What's New in v2.0.0
- **Seven Service Modules** - chatbot, openai, weaviate, supabase, osm, enrichment, sync
- **OpenStreetMap Integration** - POI enrichment from OSM data
- **Data Synchronization** - Automated sync between Supabase and Weaviate
- **Deletion Operations** - Comprehensive data deletion capabilities
- **POI Enrichment** - Automated property enrichment with nearby POIs
- **Modular Routing** - Organized API routes by service domain
- **23+ Endpoints** - Comprehensive API coverage
- **Enhanced Analytics** - Advanced search logging and conversation analytics
- **Better Monitoring** - Comprehensive health checks and status endpoints
- **Code Quality** - All Spanish comments removed, English-only codebase

---

## GitHub Workflow & Development Guidelines

This project follows a structured Git workflow to ensure code quality, collaboration, and smooth deployments. All developers must follow these guidelines when contributing to the codebase.

### Branch Strategy

The project uses a **three-tier branching strategy** with the following branches:

#### Production Branches
- **`main`** - Production-ready code, always stable and deployable
- **`staging`** - Pre-production testing environment, stable code ready for final testing

#### Development Branches
- **`dev`** - Integration branch for ongoing development, where feature branches are merged
- **`feature/*`** - Individual feature development branches

### Branch Naming Conventions

#### Feature Branches
```
feature/description-of-feature
feature/add-user-authentication
feature/improve-search-performance
feature/fix-conversation-bug
```

#### Hotfix Branches
```
hotfix/critical-security-fix
hotfix/urgent-production-bug
```

#### Release Branches
```
release/v2.2.0
release/v2.1.1
```

### Development Workflow

#### 1. Starting New Work

```bash
# Always start from the latest dev branch
git checkout dev
git pull origin dev

# Create a new feature branch
git checkout -b feature/your-feature-name

# Push the new branch to remote
git push -u origin feature/your-feature-name
```

#### 2. Development Process

```bash
# Make your changes
# ... code changes ...

# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication system

- Implement JWT token generation
- Add login/logout endpoints
- Update API documentation
- Add unit tests for auth service

Fixes #123"

# Push changes to your feature branch
git push origin feature/your-feature-name
```

#### 3. Creating Pull Requests

**Always create Pull Requests (PRs) for code review:**

1. **Feature → Dev**: For new features and improvements
2. **Dev → Staging**: For pre-production testing
3. **Staging → Main**: For production releases
4. **Hotfix → Main**: For critical production fixes

#### PR Template
```markdown
## What
Brief description of changes

## Why
Link to issue/requirement

## How
Technical approach taken

## Testing
How to verify changes

## Screenshots
If UI changes

## Performance Impact
Benchmarks if relevant

## Rollback Plan
How to undo if issues arise
```

### Commit Message Guidelines

Follow the **Conventional Commits** specification:

```
type(scope): subject

body explaining why, not what

Fixes #123
```

#### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples:
```bash
feat(auth): add JWT token validation
fix(api): resolve memory leak in conversation service
docs(readme): update installation instructions
refactor(chatbot): improve response generation logic
test(weaviate): add integration tests for search
```

### Code Review Process

#### For Reviewers:
1. **Review within 24 hours** during business days
2. **Check for**:
   - Code quality and readability
   - Test coverage
   - Security implications
   - Performance impact
   - Documentation updates
3. **Provide constructive feedback**
4. **Approve only when ready for production**

#### For Authors:
1. **Self-review first** before requesting review
2. **Keep PRs focused** (max 400 lines of changes)
3. **Respond to feedback** within 24 hours
4. **Update based on feedback** or explain why not

### Deployment Strategy

#### Staging Deployment
- **Trigger**: Merge to `staging` branch
- **Environment**: Staging environment
- **Purpose**: Integration testing and QA validation

#### Production Deployment
- **Trigger**: Merge to `main` branch
- **Environment**: Production environment
- **Requirements**: 
  - All tests passing
  - Staging validation complete
  - Code review approved
  - Documentation updated

### Emergency Procedures

#### Hotfix Process
```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue

# Make minimal fix
# ... emergency fix ...

# Commit and push
git commit -m "hotfix: resolve critical security vulnerability"
git push origin hotfix/critical-issue

# Create PR: hotfix → main
# After merge, also merge main → dev and main → staging
```

### Branch Protection Rules

#### Main Branch
- Require pull request reviews (2 reviewers)
- Require status checks to pass
- Require branches to be up to date
- Restrict pushes to main
- Require linear history

#### Staging Branch
- Require pull request reviews (1 reviewer)
- Require status checks to pass
- Restrict pushes to staging

#### Dev Branch
- Require pull request reviews (1 reviewer)
- Allow force pushes (for rebasing)

### Getting Help

#### When Stuck:
1. **Check existing issues** in the repository
2. **Ask in team chat** for quick questions
3. **Create detailed issue** for complex problems
4. **Request pair programming** for complex features

#### Resources:
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Code Review Best Practices](https://google.github.io/eng-practices/review/)

---

**Developed to facilitate Plotari property searches!**