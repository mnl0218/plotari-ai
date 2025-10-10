"""
Chat endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
import json
import logging
from src.models.property import ChatRequest, ChatResponse
from src.services.chatbot import ChatbotService
from src.api.dependencies import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
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

@router.post("/message")
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

