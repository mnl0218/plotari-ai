### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd chatbot-backend


# Create environment file
cp .env.example .env

# configure .env
```env
# Weaviate Configuration
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your_weaviate_api_key


# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key

# Application Configuration
APP_NAME=Chatbot API
APP_VERSION=1.0.0
DEBUG=True

# Configuración del modelo
DEFAULT_MODEL=gpt-5-nano
EMBEDDING_MODEL=text-embedding-ada-002

# Configuración de límites
MAX_TOKENS=1000
```

# Build and start with Docker Compose
docker-compose up --build

### 2. API Endpoints

### 💬 Chat
- `POST /api/chat` - Process chat message
- `GET /api/conversation/{conversation_id}` - Get conversation history
- `DELETE /api/conversation/{conversation_id}` - Clear specific conversation


### 🔍 Property Search
- `POST /api/search` - Hybrid search (recommended)
- `GET /api/property/{zpid}` - Get specific property by ID

### 3. API Usage Examples

#### 💬 Chat Endpoints

**POST /api/chat - Process chat message**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am looking for a 3 bedroom house in Crescent City with a backyard",
    "conversation_id": "session_123",
    "user_id": "user_456"
  }'
```


**GET /api/conversation/{conversation_id} - Get conversation history**
```bash
curl -X GET "http://localhost:8000/api/conversation/session_123"
```


**DELETE /api/conversation/{conversation_id} - Clear specific conversation**
```bash
curl -X DELETE "http://localhost:8000/api/conversation/session_123"
```


#### 🔍 Property Search Endpoints

**POST /api/search - Hybrid search (recommended)**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2 bedroom condo in Crescent City with ocean view",
    "filters": {
      "bedrooms": 2,
      "city": "Crescent City",
      "price_min": 200000,
      "price_max": 500000
    },
    "limit": 10
  }'
```


**GET /api/property/{zpid} - Get specific property by ID**
```bash
curl -X GET "http://localhost:8000/api/property/18562768"
```