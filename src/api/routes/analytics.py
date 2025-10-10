"""
Search analytics endpoints
"""
from fastapi import APIRouter, Depends
from typing import Optional
import logging
from datetime import datetime
from src.services.chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/search-logs")
async def get_search_logs(
    conversation_id: Optional[str] = None,
    search_type: Optional[str] = None,
    limit: int = 100,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    Get search logs with optional filtering
    
    Args:
        conversation_id: Filter by conversation ID
        search_type: Filter by search type (property_search, poi_search, general_inquiry)
        limit: Maximum number of logs to return
    """
    try:
        logs = chatbot_service.search_log_service.get_search_logs(
            conversation_id=conversation_id,
            search_type=search_type,
            limit=limit
        )
        
        return {
            "success": True,
            "logs": logs,
            "count": len(logs),
            "filters": {
                "conversation_id": conversation_id,
                "search_type": search_type,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting search logs: {e}")
        return {
            "success": False,
            "error": str(e),
            "logs": []
        }

@router.get("/search-stats")
async def get_search_analytics(
    days: int = 7,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    Get search analytics for the specified period
    
    Args:
        days: Number of days to analyze (default: 7)
    """
    try:
        analytics = chatbot_service.search_log_service.get_search_analytics(days=days)
        
        return {
            "success": True,
            "analytics": analytics,
            "period_days": days,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        return {
            "success": False,
            "error": str(e),
            "analytics": {}
        }

@router.delete("/search-logs/cleanup")
async def cleanup_search_logs(
    days: int = 30,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    Clean up old search logs
    
    Args:
        days: Number of days to keep logs (default: 30)
    """
    try:
        deleted_count = chatbot_service.search_log_service.cleanup_old_logs(days=days)
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "retention_days": days,
            "cleaned_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up search logs: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }

