"""
Service for cache management (Supabase database)
Handles conversation storage using Supabase database
"""
from typing import List, Dict, Any, Optional
from .interfaces import CacheManagerInterface
from src.services.supabase.conversation_service import SupabaseConversationService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheManagerService(CacheManagerInterface):
    """Service for cache management using Supabase database"""
    
    def __init__(self, cache_dir: str = "cache/conversations", cache_max_age_hours: int = 24, cache_max_size: int = 100):
        # Initialize Supabase conversation service
        self.supabase_service = SupabaseConversationService()
        # Keep cache in memory for fast access (optional)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = cache_max_size
    
    def add_to_memory_cache(self, session_id: str, conversation: Dict[str, Any]) -> None:
        """Adds conversation to memory cache with size limit"""
        # If cache is full, remove oldest conversation
        if len(self._memory_cache) >= self._cache_max_size:
            oldest_session = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].get("last_activity", "")
            )
            del self._memory_cache[oldest_session]
        
        self._memory_cache[session_id] = conversation
    
    def save_conversation_to_cache(self, user_id: str, session_id: str, conversation: Dict[str, Any]) -> None:
        """Saves conversation to Supabase database"""
        try:
            success = self.supabase_service.save_conversation(user_id, session_id, conversation)
            if not success:
                logger.warning(f"Could not save conversation {user_id}/{session_id} to Supabase database")
        except Exception as e:
            logger.error(f"Error saving conversation {user_id}/{session_id}: {e}")
    
    def cleanup_old_conversations(self) -> None:
        """Cleans old conversations using Supabase database"""
        try:
            # Clean Supabase database
            deleted_count = self.supabase_service.cleanup_expired_conversations()
            
            # Clean memory cache based on time
            cutoff_time = datetime.now() - timedelta(hours=1)
            sessions_to_remove = []
            
            for session_id, conversation in self._memory_cache.items():
                try:
                    last_activity = datetime.fromisoformat(conversation.get("last_activity", ""))
                    if last_activity < cutoff_time:
                        sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    # If there is error parsing date, remove
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._memory_cache[session_id]
                logger.debug(f"Conversation {session_id} removed from memory cache")
            
            if deleted_count > 0 or sessions_to_remove:
                logger.info(f"Cleanup completed: {deleted_count} Supabase conversations, {len(sessions_to_remove)} memory cache")
                
        except Exception as e:
            logger.error(f"Error in conversation cleanup: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Gets detailed cache information"""
        return {
            "supabase_database": self.supabase_service.get_cache_info(),
            "memory_cache": {
                "conversations": len(self._memory_cache),
                "max_size": self._cache_max_size,
                "usage_percentage": (len(self._memory_cache) / self._cache_max_size) * 100
            }
        }
    
    def clear_all_cache(self) -> Dict[str, Any]:
        """Clears all cache (memory and Supabase database)"""
        # Clear memory cache
        memory_cleared = len(self._memory_cache)
        self._memory_cache.clear()
        
        # Clear Supabase database
        supabase_result = self.supabase_service.clear_all_cache()
        supabase_cleared = supabase_result.get("conversations_cleared", 0)
        
        return {
            "memory_conversations_cleared": memory_cleared,
            "supabase_conversations_cleared": supabase_cleared,
            "total_cleared": memory_cleared + supabase_cleared,
            "storage_type": "supabase_database"
        }
