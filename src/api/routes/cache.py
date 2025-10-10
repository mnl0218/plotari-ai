"""
Cache management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
import logging
from datetime import datetime
from src.services.chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Cache"])

@router.get("/info")
async def get_cache_info(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /cache/info
    Gets detailed information about JSON cache and memory
    """
    try:
        cache_info = chatbot_service.get_cache_info()
        
        return {
            "message": "Cache information retrieved successfully",
            "cache_info": cache_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache information: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/clear")
async def clear_all_cache(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    DELETE /cache/clear
    Clears all cache (memory and JSON files)
    """
    try:
        result = chatbot_service.clear_all_cache()
        
        return {
            "message": "Cache cleared successfully",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

