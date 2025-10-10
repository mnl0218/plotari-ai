"""
Main chatbot backend application
Minimal REST design with 5 main endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
import os

from src.config.settings import settings
from src.api.routes import (
    chat_router,
    properties_router,
    conversations_router,
    analytics_router,
    sync_router,
    cache_router,
    health_router,
    deletion_router,
    enrichment_router
)

# Configure logging
def setup_logging():
    """Configures the logging system"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("chatbot.log") if os.getenv("LOG_TO_FILE", "false").lower() == "true" else logging.NullHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# Validate configuration at startup
def validate_configuration():
    """Validates the application configuration"""
    try:
        settings.validate()
        logger.info("Configuration validated successfully")
        return True
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return False

if not validate_configuration():
    raise RuntimeError("Invalid configuration. Check environment variables.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("🚀 Starting Plotari Chatbot API...")
    logger.info(f"📊 Configuration: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    try:
        # Check external services
        from src.services.weaviate import WeaviateService
        from src.services.openai import OpenAIService
        
        with WeaviateService() as weaviate:
            if weaviate.is_connected():
                logger.info("✅ Weaviate connected successfully")
            else:
                logger.warning("⚠️ Weaviate not available")
        
        with OpenAIService() as openai:
            if openai.is_available():
                logger.info("✅ OpenAI connected successfully")
            else:
                logger.warning("⚠️ OpenAI not available")
        
        logger.info("🎉 Application started successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    logger.info("👋 Application closed successfully")

# Create FastAPI application
app = FastAPI(
    title="Plotari Chatbot API",
    description="Modular REST API for Plotari chatbot with Weaviate and OpenAI. Organized by service: Chat, Properties, Conversations, Analytics, Sync, Cache, and Health.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers - Modular design
app.include_router(chat_router, prefix="/api")
app.include_router(properties_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
app.include_router(deletion_router, prefix="/api")
app.include_router(cache_router, prefix="/api")
app.include_router(enrichment_router, prefix="/api")
app.include_router(health_router, prefix="/api")

# Global exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "Internal error"
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Plotari Chatbot API - Modular REST Design",
        "version": "2.0.0",
        "status": "running",
        "services": {
            "chat": {
                "endpoints": ["POST /api/chat", "POST /api/chat/message"],
                "description": "Chat with intent detection and SSE streaming"
            },
            "properties": {
                "endpoints": ["POST /api/search", "GET /api/property/{id}", "GET /api/property/{id}/pois", "POST /api/compare"],
                "description": "Property search, details, POIs, and comparison"
            },
            "conversations": {
                "endpoints": ["GET /api/conversation/{user_id}/{session_id}/history", "DELETE /api/conversation/{user_id}/{session_id}", "GET /api/user/{user_id}/conversations"],
                "description": "Conversation history and management"
            },
            "analytics": {
                "endpoints": ["GET /api/analytics/search-logs", "GET /api/analytics/search-stats", "DELETE /api/analytics/search-logs/cleanup"],
                "description": "Search analytics and logs"
            },
            "sync": {
                "endpoints": ["POST /api/sync/properties/full", "POST /api/sync/properties/incremental", "GET /api/sync/properties/status"],
                "description": "Property synchronization between Supabase and Weaviate"
            },
            "deletion": {
                "endpoints": ["DELETE /api/delete/properties/all", "DELETE /api/delete/properties/by-date", "DELETE /api/delete/properties/{zpid}", "DELETE /api/delete/properties/bulk", "GET /api/delete/properties/status"],
                "description": "Weaviate data deletion operations"
            },
            "cache": {
                "endpoints": ["GET /api/cache/info", "DELETE /api/cache/clear"],
                "description": "Cache management and information"
            },
            "health": {
                "endpoints": ["GET /api/health"],
                "description": "Service health status"
            },
            "enrichment": {
                "endpoints": ["POST /api/enrich-pois"],
                "description": "Enrich properties with POIs from OpenStreetMap"
            }
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/info")
async def get_info():
    """Detailed API information"""
    return {
        "service": "Plotari Chatbot API",
        "version": "2.0.0",
        "description": "Modular REST API for Plotari chatbot with Weaviate and OpenAI",
        "design": "Modular REST design organized by service domains",
        "architecture": {
            "chat_service": "Real-time chat with SSE streaming and intent detection",
            "property_service": "Property search, details, POIs, and comparison",
            "conversation_service": "User conversation history and session management",
            "analytics_service": "Search analytics and activity logs",
            "sync_service": "Data synchronization between Supabase and Weaviate",
            "deletion_service": "Weaviate data deletion operations",
            "cache_service": "Cache management and optimization",
            "health_service": "System health monitoring"
        },
        "total_endpoints": 23,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    # Uvicorn configuration
    uvicorn_config = {
        "app": "src.main:app",
        "host": settings.HOST,
        "port": settings.PORT,
        "reload": settings.DEBUG,
        "log_level": "info" if not settings.DEBUG else "debug",
        "access_log": True
    }
    
    logger.info(f"🚀 Starting server at {settings.HOST}:{settings.PORT}")
    logger.info(f"📚 Documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(**uvicorn_config)