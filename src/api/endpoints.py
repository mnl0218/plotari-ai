"""
API Endpoints - Minimal REST design
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import uuid
from src.models.property import (
    ChatRequest, ChatResponse,
    PropertySearchRequest, PropertySearchResponse,
    PropertyDetailResponse,
    POISearchRequest, POISearchResponse,
    PropertyCompareRequest, PropertyCompareResponse,
    Property, POI, Neighborhood
)
from src.services.chatbot import ChatbotService
from src.services.weaviate import WeaviateService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Singleton instance of the chatbot service
_chatbot_service_instance = None

def get_chatbot_service() -> ChatbotService:
    """Dependency to get the chatbot service (singleton)"""
    global _chatbot_service_instance
    try:
        if _chatbot_service_instance is None:
            _chatbot_service_instance = ChatbotService()
            logger.info("ChatbotService singleton initialized")
        return _chatbot_service_instance
    except Exception as e:
        logger.error(f"Error initializing ChatbotService: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )

# Dependency to get the Weaviate service
def get_weaviate_service() -> WeaviateService:
    """Dependency to get the Weaviate service"""
    try:
        return WeaviateService()
    except Exception as e:
        logger.error(f"Error initializing WeaviateService: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    POST /chat
    Input: { "user_id": "...", "message": "...", "context": { "propertyId"?: "...", "city"?: "..."} }
    Logic: detects intent → routes to /search, /pois, /property internally and composes response in natural language
    """
    try:
        response = chatbot_service.process_message(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/chat/message")
async def chat_message_sse(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    POST /chat/message - SSE endpoint for real-time chat
    Input: { "user_id": "...", "sessionId": "...", "message": "...", "metadata": {...} }
    Output: SSE event stream with chatbot responses
    """
    try:
        # Log the received request
        logger.info(f"Request received - user_id: {request.user_id}, session_id: {request.session_id}, message: {request.message[:50]}...")
        
        async def generate_sse_events():
            try:
                user_id = request.user_id
                session_id = request.session_id
                logger.info(f"Using user_id: {user_id}, session_id: {session_id}")
                
                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'userId': user_id, 'sessionId': session_id})}\n\n"
                
                # Process message with chatbot service
                response = chatbot_service.process_message(request)
                
                # Send complete response event
                yield f"data: {json.dumps({'type': 'response', 'data': response.model_dump(), 'userId': user_id, 'sessionId': session_id})}\n\n"
                
                # Send end event
                yield f"data: {json.dumps({'type': 'end', 'userId': user_id, 'sessionId': session_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                error_response = {
                    "type": "error",
                    "message": "Error processing message",
                    "userId": user_id,
                    "sessionId": session_id
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        
        return StreamingResponse(
            generate_sse_events(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat SSE endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/search", response_model=PropertySearchResponse)
async def search_properties(
    request: PropertySearchRequest,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    POST /search
    Input: text + filters (price, beds, baths, radius, lat/lon)
    Output: list of properties + metadata
    """
    try:
        search_response = weaviate_service.search_properties(request)
        return search_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in property search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search error"
        )

@router.get("/property/{property_id}", response_model=PropertyDetailResponse)
async def get_property_detail(
    property_id: str,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    GET /property/{id}
    Detail + similar recommendations (vector query nearObject or more_like_this via hybrid)
    """
    try:
        if not property_id or not property_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid property ID"
            )
        
        property_detail = weaviate_service.get_property_detail(property_id.strip())
        if not property_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        return property_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property detail {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/property/{property_id}/pois", response_model=POISearchResponse)
async def get_property_pois(
    property_id: str,
    category: Optional[str] = None,
    radius: int = 1500,
    limit: int = 10,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    GET /property/{id}/pois?category=school&radius=1500
    Calls Weaviate(POI). Returns top N by distance.
    """
    try:
        if not property_id or not property_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid property ID"
            )
        
        if not 1 <= radius <= 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Radius must be between 1 and 10000 meters"
            )
        
        if not 1 <= limit <= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )
        
        poi_request = POISearchRequest(
            property_id=property_id.strip(),
            category=category,
            radius=radius,
            limit=limit
        )
        
        pois_response = weaviate_service.search_pois(poi_request)
        return pois_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting POIs for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/compare", response_model=PropertyCompareResponse)
async def compare_properties(
    request: PropertyCompareRequest,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    POST /compare
    Input: list of IDs, returns aligned comparison (table) and generated pros/cons
    """
    try:
        comparison_response = weaviate_service.compare_properties(request)
        return comparison_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comparison error"
        )

@router.get("/conversation/{user_id}/{session_id}/history")
async def get_conversation_history(
    user_id: str,
    session_id: str,
    limit: int = 10,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /conversation/{user_id}/{session_id}/history?limit=10
    Gets conversation history for a user session
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID"
            )
        
        if not 1 <= limit <= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )
        
        history = chatbot_service.get_conversation_history(user_id.strip(), session_id.strip(), limit)
        
        return {
            "user_id": user_id.strip(),
            "session_id": session_id.strip(),
            "messages": history,
            "total_messages": len(history),
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history {user_id}/{session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/conversation/{user_id}/{session_id}")
async def clear_conversation(
    user_id: str,
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    DELETE /conversation/{user_id}/{session_id}
    Clears a specific conversation for a user
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID"
            )
        
        success = chatbot_service.clear_conversation(user_id.strip(), session_id.strip())
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "message": "Conversation deleted successfully",
            "user_id": user_id.strip(),
            "session_id": session_id.strip()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation {user_id}/{session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/conversations/stats")
async def get_conversation_stats(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /conversations/stats
    Gets statistics of active conversations
    """
    try:
        stats = chatbot_service.get_conversation_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting conversation statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/user/{user_id}/conversations")
async def get_user_conversations(
    user_id: str,
    limit: int = 10,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /user/{user_id}/conversations?limit=10
    Gets all conversations for a specific user
    """
    try:
        logger.info(f"API: Getting conversations for user: {user_id}")
        
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        if not 1 <= limit <= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )
        
        conversations = chatbot_service.get_user_conversations(user_id.strip(), limit)
        logger.info(f"API: Retrieved {len(conversations)} conversations for user {user_id}")
        
        result = {
            "user_id": user_id.strip(),
            "conversations": conversations,
            "total_conversations": len(conversations),
            "limit": limit
        }
        
        logger.info(f"API: Returning result: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Error getting user conversations {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/user/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /user/{user_id}/stats
    Gets statistics for a specific user
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        stats = chatbot_service.get_user_stats(user_id.strip())
        
        return {
            "user_id": user_id.strip(),
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/debug/conversations")
async def debug_conversations(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """
    GET /debug/conversations
    Debug endpoint to check all conversations in the database
    """
    try:
        # Get all conversations without filters
        all_conversations = chatbot_service.conversation_manager.cache_manager_service.supabase_service.list_conversations()
        
        return {
            "total_conversations": len(all_conversations),
            "conversations": all_conversations
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {
            "error": str(e),
            "total_conversations": 0,
            "conversations": []
        }

@router.get("/cache/info")
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

@router.delete("/cache/clear")
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


# =====================================================
# SEARCH ANALYTICS ENDPOINTS
# =====================================================

@router.get("/analytics/search-logs")
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


@router.get("/analytics/search-stats")
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


@router.delete("/analytics/search-logs/cleanup")
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
