"""
Health check endpoint
"""
from fastapi import APIRouter, Depends
import logging
from src.services.chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """Application health endpoint"""
    try:
        status_info = chatbot_service.get_service_status()
        
        is_healthy = (
            status_info.get("weaviate_available", False) and 
            status_info.get("openai_available", False)
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "weaviate_connected": status_info.get("weaviate_available", False),
            "openai_connected": status_info.get("openai_available", False),
            "conversations": status_info.get("conversations", {}),
            "service": "chatbot-backend",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "weaviate_connected": False,
            "openai_connected": False,
            "service": "chatbot-backend",
            "error": str(e)
        }

