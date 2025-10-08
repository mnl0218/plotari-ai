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
from src.api.endpoints import router

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
    description="Minimal REST API for Plotari chatbot with Weaviate and OpenAI. Endpoints: POST /chat, POST /search, GET /property/{id}, GET /property/{id}/pois, POST /compare",
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

# Include routers
app.include_router(router, prefix="/api")

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
        "message": "Plotari Chatbot API - Minimal REST Design",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /api/chat - Chat with intent detection",
            "search": "POST /api/search - Property search with filters",
            "property": "GET /api/property/{id} - Detail + recommendations",
            "pois": "GET /api/property/{id}/pois - POIs near property",
            "compare": "POST /api/compare - Property comparison",
            "health": "GET /api/health - Service status"
        },
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/info")
async def get_info():
    """Detailed API information"""
    return {
        "service": "Plotari Chatbot API",
        "version": "2.0.0",
        "description": "Minimal REST API for Plotari chatbot with Weaviate and OpenAI",
        "design": "Minimal REST with 5 main endpoints",
        "endpoints": {
            "POST /chat": "Chat with intent detection → routes to /search, /pois, /property internally",
            "POST /search": "Property search with filters (price, beds, baths, radius, lat/lon)",
            "GET /property/{id}": "Property detail + similar recommendations",
            "GET /property/{id}/pois": "POIs near property (category, radius)",
            "POST /compare": "Property comparison with table and pros/cons",
            "GET /health": "Service status"
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