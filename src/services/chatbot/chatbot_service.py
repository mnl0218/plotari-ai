"""
Main chatbot service - Refactored
Orchestrates all specialized services to process messages
"""
from typing import List, Dict, Any, Optional
from src.services.weaviate import WeaviateService
from src.services.openai import OpenAIService
from .intent_extractor_service import IntentExtractorService
from .property_search_service import PropertySearchService
from .poi_search_service import POISearchService
from .response_generator_service import ResponseGeneratorService
from .conversation_manager_service import ConversationManagerService
from .cache_manager_service import CacheManagerService
from src.services.supabase import SearchLogService
from src.models.property import (
    ChatRequest, ChatResponse, Property, POI
)
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ChatbotService:
    """Main Plotari chatbot service - Refactored"""
    
    def __init__(self, cache_dir: str = "cache/conversations", cache_max_age_hours: int = 24):
        # Initialize external services
        self.weaviate_service = None
        self.openai_service = None
        self._initialize_external_services()
        
        # Initialize internal services
        self.cache_manager = CacheManagerService(cache_dir, cache_max_age_hours)
        self.conversation_manager = ConversationManagerService(self.cache_manager)
        self.intent_extractor = IntentExtractorService(self.openai_service)
        self.property_search = PropertySearchService(self.weaviate_service)
        self.poi_search = POISearchService(self.weaviate_service)
        self.response_generator = ResponseGeneratorService(self.openai_service)
        self.search_log_service = SearchLogService()
        
        logger.info("Refactored ChatbotService initialized successfully")
    
    def _initialize_external_services(self) -> None:
        """Initializes external services (Weaviate, OpenAI)"""
        try:
            self.weaviate_service = WeaviateService()
            self.openai_service = OpenAIService()
            logger.info("External services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing external services: {e}")
            raise
    
    def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a user message and generates a response
        Detects intent -> routes to /search, /pois, /property internally and composes response in natural language
        """
        try:
            # Validate input
            if not request.message or not request.message.strip():
                return self._create_error_response(
                    "Please provide a valid message."
                )
            
            # Get or create conversation session
            user_id = request.user_id
            session_id = request.session_id
            
            # First try to get existing conversation
            conversation = self.conversation_manager.get_conversation(user_id, session_id)
            
            # If no conversation exists, create one (this will only be in memory initially)
            if conversation is None:
                conversation = self.conversation_manager.get_or_create_conversation(user_id, session_id)
                logger.info(f"New conversation created in memory for first message: {user_id}/{session_id}")
            else:
                logger.debug(f"Using existing conversation: {user_id}/{session_id}")
            
            # Add user message to history
            conversation["messages"].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate chat summary if this is the first message in the conversation
            chat_summary = None
            if len(conversation["messages"]) == 1:  # Only the user message we just added
                try:
                    if self.openai_service:
                        chat_summary = self.openai_service.generate_chat_summary(
                            request.message, 
                            conversation.get("context", {})
                        )
                        logger.info(f"Generated chat summary: {chat_summary}")
                    else:
                        logger.warning("OpenAI service not available for chat summary generation")
                except Exception as e:
                    logger.error(f"Error generating chat summary: {e}")
                    # Continue without summary if generation fails
            
            # Extract search intent with conversation context
            search_intent = self.intent_extractor.extract_search_intent(
                request.message, 
                self.conversation_manager.build_context_from_conversation(conversation)
            )
            logger.info(f"Search intent extracted: {search_intent}")
            
            # Process according to detected intent
            properties_found = []
            pois_found = []
            search_start_time = time.time()
            
            if search_intent["type"] == "property_search":
                properties_found = self.property_search.search_properties(search_intent)
            elif search_intent["type"] == "property_detail":
                property_detail = self.property_search.get_property_detail(search_intent)
                if property_detail:
                    properties_found = [property_detail.property]
            elif search_intent["type"] == "poi_search":
                pois_found = self.poi_search.search_pois(search_intent)
            elif search_intent["type"] == "property_compare":
                properties_found = self.property_search.compare_properties(search_intent)
            
            # Calculate search response time
            search_response_time = int((time.time() - search_start_time) * 1000)
            
            # Log search operation if it's a search type
            if search_intent["type"] in ["property_search", "property_detail", "poi_search", "property_compare"]:
                try:
                    # Get conversation ID from the conversation data
                    conversation_id = conversation.get("id")
                    if conversation_id:
                        # Determine search type for logging
                        log_search_type = search_intent["type"]
                        if log_search_type == "property_detail":
                            log_search_type = "property_search"  # Map to valid enum value
                        
                        # Count results
                        results_count = len(properties_found) if properties_found else len(pois_found) if pois_found else 0
                        
                        # Log the search
                        self.search_log_service.log_search(
                            conversation_id=conversation_id,
                            search_type=log_search_type,
                            query=request.message,
                            filters=search_intent.get("filters", {}),
                            results_count=results_count,
                            response_time_ms=search_response_time,
                            metadata={
                                "user_id": user_id,
                                "session_id": session_id,
                                "search_intent": search_intent,
                                "properties_found": len(properties_found) if properties_found else 0,
                                "pois_found": len(pois_found) if pois_found else 0
                            }
                        )
                        logger.info(f"Search logged: {log_search_type} - {results_count} results in {search_response_time}ms")
                except Exception as e:
                    logger.error(f"Error logging search: {e}")
            
            # Generate contextual response with history
            response_text = self.response_generator.generate_response(
                request.message, 
                properties_found, 
                pois_found, 
                search_intent,
                conversation
            )
            
            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
                "search_intent": search_intent,
                "properties_found": len(properties_found),
                "pois_found": len(pois_found)
            }
            
            # Include complete properties if any
            if properties_found:
                assistant_message["properties"] = [prop.model_dump() for prop in properties_found]
                logger.info(f"Saving {len(properties_found)} complete properties in message")
            
            # Include complete POIs if any
            if pois_found:
                assistant_message["pois"] = [poi.model_dump() for poi in pois_found]
                logger.info(f"Saving {len(pois_found)} complete POIs in message")
            
            conversation["messages"].append(assistant_message)
            
            # Update conversation context
            self.conversation_manager.update_conversation_context(conversation, search_intent, properties_found)
            
            # Save conversation to JSON cache
            self.cache_manager.save_conversation_to_cache(user_id, session_id, conversation)
            
            # Save to Supabase database only if this is a real conversation (has messages)
            if len(conversation["messages"]) > 0:
                # Check if conversation exists in Supabase, if not create it
                if not conversation.get("id"):
                    # This is the first message, create conversation in Supabase with current data
                    if self.cache_manager.supabase_service:
                        try:
                            # Create conversation directly with the current conversation data and chat summary
                            created_conversation = self.cache_manager.supabase_service.repository.create_conversation(
                                user_id, session_id, conversation, chat_summary
                            )
                            if created_conversation and created_conversation.get("id"):
                                conversation["id"] = created_conversation["id"]
                                logger.info(f"Conversation created in Supabase after first message: {user_id}/{session_id}")
                                if chat_summary:
                                    logger.info(f"Chat summary saved: {chat_summary}")
                        except Exception as e:
                            logger.error(f"Error creating conversation in Supabase: {e}")
                else:
                    # Update existing conversation in Supabase
                    if self.cache_manager.supabase_service:
                        try:
                            # Only update chat_summary if it was generated (first message)
                            self.cache_manager.supabase_service.save_conversation(
                                user_id, session_id, conversation, chat_summary
                            )
                            logger.debug(f"Conversation updated in Supabase: {user_id}/{session_id}")
                            if chat_summary:
                                logger.info(f"Chat summary updated: {chat_summary}")
                        except Exception as e:
                            logger.error(f"Error updating conversation in Supabase: {e}")
            
            # Clean up old conversations
            self.cache_manager.cleanup_old_conversations()
            
            # Create response
            response = ChatResponse(
                message=response_text,
                properties_found=properties_found[:5] if properties_found else None,
                pois_found=pois_found[:5] if pois_found else None,
                metadata={
                    "search_intent": search_intent,
                    "total_properties_found": len(properties_found),
                    "total_pois_found": len(pois_found),
                    "user_id": user_id,
                    "session_id": session_id,
                    "conversation_length": len(conversation["messages"])
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(
                "Sorry, an error occurred while processing your query. Please try again.",
                str(e)
            )
    
    def get_conversation_history(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets conversation history for a user session with enriched properties"""
        return self.conversation_manager.get_conversation_history(user_id, session_id, limit)
    
    def clear_conversation(self, user_id: str, session_id: str) -> bool:
        """Clears a specific conversation"""
        return self.conversation_manager.clear_conversation(user_id, session_id)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Gets detailed cache information"""
        return self.cache_manager.get_cache_info()
    
    def clear_all_cache(self) -> Dict[str, Any]:
        """Clears all cache (memory and JSON)"""
        return self.cache_manager.clear_all_cache()
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Gets conversation statistics"""
        return self.conversation_manager.get_conversation_stats()
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets all conversations for a specific user"""
        return self.conversation_manager.get_user_conversations(user_id, limit)
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Gets statistics for a specific user"""
        return self.conversation_manager.get_user_stats(user_id)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Gets the status of services"""
        status = {
            "weaviate_available": False,
            "openai_available": False,
            "conversations": self.get_conversation_stats()
        }
        
        try:
            if self.weaviate_service:
                status["weaviate_available"] = self.weaviate_service.is_connected()
        except Exception as e:
            logger.warning(f"Error checking Weaviate: {e}")
        
        try:
            if self.openai_service:
                status["openai_available"] = self.openai_service.is_available()
        except Exception as e:
            logger.warning(f"Error checking OpenAI: {e}")
        
        return status
    
    def _create_error_response(self, message: str, error: Optional[str] = None) -> ChatResponse:
        """Creates an error response"""
        return ChatResponse(
            message=message,
            metadata={"error": error} if error else {}
        )
    
    def close(self) -> None:
        """Closes connections"""
        try:
            if self.weaviate_service:
                self.weaviate_service.close()
            logger.info("ChatbotService closed successfully")
        except Exception as e:
            logger.error(f"Error closing ChatbotService: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()