"""
Conversation management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
import logging
from src.services.chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Conversations"])

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

