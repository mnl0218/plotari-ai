"""
Service for conversation and context management
Handles creation, updating and querying of conversations
"""
from typing import List, Dict, Any, Optional
from .interfaces import ConversationManagerInterface
from src.models.property import Property
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationManagerService(ConversationManagerInterface):
    """Service for conversation and context management"""
    
    def __init__(self, cache_manager_service: Optional[Any] = None):
        self.cache_manager_service = cache_manager_service
    
    def get_conversation(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Gets an existing conversation without creating a new one"""
        # Create a unique key for memory cache
        cache_key = f"{user_id}:{session_id}"
        
        # First check memory cache
        if self.cache_manager_service and hasattr(self.cache_manager_service, '_memory_cache'):
            if cache_key in self.cache_manager_service._memory_cache:
                conversation = self.cache_manager_service._memory_cache[cache_key]
                conversation["last_activity"] = datetime.now().isoformat()
                return conversation
        
        # Try to load from Supabase database (without creating)
        conversation = None
        if self.cache_manager_service and hasattr(self.cache_manager_service, 'supabase_service'):
            conversation = self.cache_manager_service.supabase_service.get_conversation(user_id, session_id)
        
        if conversation:
            # Update last activity
            conversation["last_activity"] = datetime.now().isoformat()
            logger.debug(f"Conversation loaded from database: {user_id}/{session_id}")
            
            # Add to memory cache
            if self.cache_manager_service:
                self.cache_manager_service.add_to_memory_cache(cache_key, conversation)
        
        return conversation

    def get_or_create_conversation(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Gets or creates a conversation for the user session using JSON cache"""
        # First try to get existing conversation
        existing_conversation = self.get_conversation(user_id, session_id)
        
        if existing_conversation:
            return existing_conversation
        
        # Create new conversation
        conversation = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "messages": [],
            "context": {
                "last_search_intent": None,
                "last_properties": [],
                "last_pois": [],
                "user_preferences": {},
                "current_location": None,
                "current_property": None
            }
        }
        logger.info(f"New conversation created in memory: {user_id}/{session_id}")
        
        # Add to memory cache
        cache_key = f"{user_id}:{session_id}"
        if self.cache_manager_service:
            self.cache_manager_service.add_to_memory_cache(cache_key, conversation)
        
        return conversation
    
    def build_context_from_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Builds context from conversation"""
        context = conversation.get("context", {})
        
        # Add information from last message if relevant
        messages = conversation.get("messages", [])
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                # Extract information from last user message
                content = last_message.get("content", "").lower()
                
                # Detect mentioned location
                if any(word in content for word in ["crescent city", "california", "ca"]):
                    context["current_location"] = "Crescent City, CA"
                
                # Detect mentioned property type
                if any(word in content for word in ["casa", "house", "home"]):
                    context["user_preferences"]["property_type"] = "house"
                elif any(word in content for word in ["apartamento", "apartment", "condo"]):
                    context["user_preferences"]["property_type"] = "apartment"
        
        return context
    
    def update_conversation_context(self, conversation: Dict[str, Any], search_intent: Dict[str, Any], 
                                   properties_found: List[Property]) -> None:
        """Updates conversation context"""
        context = conversation.get("context", {})
        
        # Update last search intent
        context["last_search_intent"] = search_intent
        
        # Update last properties found
        if properties_found:
            context["last_properties"] = [
                {
                    "zpid": prop.zpid,
                    "address": prop.address,
                    "price": prop.price,
                    "city": prop.city
                }
                for prop in properties_found[:3]  # Only the first 3
            ]
        
        # Update user preferences based on searches
        filters = search_intent.get("filters", {})
        if filters.get("city"):
            context["user_preferences"]["preferred_city"] = filters["city"]
        if filters.get("min_bedrooms"):
            context["user_preferences"]["min_bedrooms"] = filters["min_bedrooms"]
        if filters.get("max_price"):
            context["user_preferences"]["max_price"] = filters["max_price"]
    
    def get_conversation_history(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets conversation history for a user session with enriched properties"""
        # Try to get existing conversation (without creating)
        conversation = self.get_conversation(user_id, session_id)
        
        if conversation is None:
            return []
        
        messages = conversation.get("messages", [])
        enriched_messages = self._enrich_messages_with_properties(messages, conversation)
        return enriched_messages[-limit:] if limit else enriched_messages
    
    def _enrich_messages_with_properties(self, messages: List[Dict[str, Any]], conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Messages already include complete properties from new implementation"""
        # Messages already come enriched from process_message, just return as they are
        logger.info(f"Returning {len(messages)} messages (already enriched)")
        return messages
    
    def clear_conversation(self, user_id: str, session_id: str) -> bool:
        """Clears a specific conversation"""
        success = False
        
        # Create a unique key for memory cache
        cache_key = f"{user_id}:{session_id}"
        
        # Remove from memory cache
        if self.cache_manager_service and hasattr(self.cache_manager_service, '_memory_cache'):
            if cache_key in self.cache_manager_service._memory_cache:
                del self.cache_manager_service._memory_cache[cache_key]
                success = True
        
        # Remove from Supabase database
        if self.cache_manager_service and hasattr(self.cache_manager_service, 'supabase_service'):
            if self.cache_manager_service.supabase_service.clear_conversation(user_id, session_id):
                success = True
        
        return success
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Gets conversation statistics"""
        if not self.cache_manager_service:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "active_sessions": 0,
                "memory_cache_conversations": 0,
                "memory_cache_messages": 0,
                "json_cache_size_mb": 0,
                "memory_usage_mb": 0,
                "cache_directory": "",
                "oldest_conversation": None,
                "newest_conversation": None
            }
        
        # Supabase database statistics
        supabase_stats = {}
        if hasattr(self.cache_manager_service, 'supabase_service'):
            supabase_stats = self.cache_manager_service.supabase_service.get_conversation_stats()
        
        # Memory cache statistics
        memory_conversations = 0
        memory_messages = 0
        if hasattr(self.cache_manager_service, '_memory_cache'):
            memory_conversations = len(self.cache_manager_service._memory_cache)
            memory_messages = sum(len(conv.get("messages", [])) for conv in self.cache_manager_service._memory_cache.values())
        
        return {
            "total_conversations": supabase_stats.get("total_conversations", 0),
            "total_messages": supabase_stats.get("total_messages", 0),
            "active_sessions": supabase_stats.get("active_sessions", 0),
            "memory_cache_conversations": memory_conversations,
            "memory_cache_messages": memory_messages,
            "storage_type": supabase_stats.get("storage_type", "supabase_database"),
            "memory_usage_mb": len(str(self.cache_manager_service._memory_cache)) / 1024 / 1024 if hasattr(self.cache_manager_service, '_memory_cache') else 0,
            "oldest_conversation": supabase_stats.get("oldest_conversation"),
            "newest_conversation": supabase_stats.get("newest_conversation")
        }
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets all conversations for a specific user"""
        logger.info(f"Getting conversations for user: {user_id}")
        
        if not self.cache_manager_service:
            logger.warning("No cache_manager_service available")
            return []
        
        try:
            # Get conversations from Supabase
            if hasattr(self.cache_manager_service, 'supabase_service'):
                logger.info(f"Calling supabase_service.list_conversations for user: {user_id}")
                conversations = self.cache_manager_service.supabase_service.list_conversations({
                    "user_id": user_id,
                    "limit": limit,
                    "order_by": "last_activity",
                    "order_desc": True
                })
                
                logger.info(f"Raw conversations from Supabase: {len(conversations)} found")
                logger.info(f"Raw conversations data: {conversations}")
                
                # Add summaries and message counts
                enriched_conversations = []
                for conv in conversations:
                    enriched_conv = {
                        "session_id": conv["session_id"],
                        "created_at": conv["created_at"],
                        "last_activity": conv["last_activity"],
                        "message_count": conv["message_count"],
                        "summary": self._generate_conversation_summary(conv["session_id"], user_id)
                    }
                    enriched_conversations.append(enriched_conv)
                
                logger.info(f"Returning {len(enriched_conversations)} enriched conversations")
                return enriched_conversations
            else:
                logger.warning("No supabase_service available")
            
            return []
        except Exception as e:
            logger.error(f"Error getting user conversations for {user_id}: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Gets statistics for a specific user"""
        if not self.cache_manager_service:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "active_sessions": 0
            }
        
        try:
            # Get user activity stats from Supabase
            if hasattr(self.cache_manager_service, 'supabase_service'):
                user_stats = self.cache_manager_service.supabase_service.get_user_activity_stats(user_id, 30)
                
                return {
                    "total_conversations": user_stats.get("total_conversations", 0),
                    "total_messages": user_stats.get("total_messages", 0),
                    "active_sessions": user_stats.get("active_sessions", 0),
                    "avg_messages_per_conversation": user_stats.get("avg_messages_per_conversation", 0)
                }
            
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "active_sessions": 0,
                "avg_messages_per_conversation": 0
            }
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "active_sessions": 0,
                "avg_messages_per_conversation": 0
            }
    
    def _generate_conversation_summary(self, session_id: str, user_id: str) -> str:
        """Generates a summary for a conversation"""
        try:
            # Get conversation history
            history = self.get_conversation_history(user_id, session_id, 5)
            
            if not history:
                return "No conversation data"
            
            # Get the first user message to create a summary
            user_messages = [msg for msg in history if msg.get("role") == "user"]
            if user_messages:
                first_message = user_messages[0].get("content", "")
                # Truncate and create summary
                if len(first_message) > 100:
                    return first_message[:97] + "..."
                return first_message
            
            return "Conversation started"
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return "Summary unavailable"