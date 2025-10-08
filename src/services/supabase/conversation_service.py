"""
Supabase conversation service
Orchestrates conversation operations using specialized services
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from .conversation_repository import SupabaseConversationRepository
from .conversation_analytics_service import ConversationAnalyticsService
from .conversation_cleanup_service import ConversationCleanupService

logger = logging.getLogger(__name__)


class SupabaseConversationService:
    """Orchestrator service for managing conversations in Supabase database"""
    
    def __init__(self):
        """Initialize specialized services"""
        try:
            self.repository = SupabaseConversationRepository()
            self.analytics = ConversationAnalyticsService()
            self.cleanup = ConversationCleanupService()
            logger.info("Supabase conversation service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase conversation service: {e}")
            raise
    
    def get_conversation(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets an existing conversation without creating a new one
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict with conversation data or None if not found
        """
        try:
            # Try to get existing conversation
            existing_conversation = self.repository.get_conversation(user_id, session_id)
            
            if existing_conversation:
                # Update last_activity
                self.repository.update_last_activity(existing_conversation["id"])
                
                # Return conversation data with ID
                conversation_data = existing_conversation["conversation_data"]
                conversation_data["id"] = existing_conversation["id"]
                return conversation_data
            else:
                return None
                    
        except Exception as e:
            logger.error(f"Error getting conversation {user_id}/{session_id}: {e}")
            return None

    def get_or_create_conversation(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Gets or creates a conversation for the user session
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict with conversation data
        """
        try:
            # Try to get existing conversation first
            existing_conversation = self.get_conversation(user_id, session_id)
            
            if existing_conversation:
                return existing_conversation
            else:
                # Create new conversation
                new_conversation = {
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
                
                # Save to database (without chat_summary initially)
                created_conversation = self.repository.create_conversation(user_id, session_id, new_conversation)
                
                if created_conversation:
                    logger.info(f"New conversation created in Supabase: {user_id}/{session_id}")
                    # Add the ID to the conversation data
                    new_conversation["id"] = created_conversation["id"]
                    return new_conversation
                else:
                    raise Exception("Failed to create conversation in database")
                    
        except Exception as e:
            logger.error(f"Error getting/creating conversation {user_id}/{session_id}: {e}")
            raise
    
    def save_conversation(self, user_id: str, session_id: str, conversation_data: Dict[str, Any], chat_summary: Optional[str] = None) -> bool:
        """
        Saves conversation to database
        
        Args:
            user_id: User ID
            session_id: Session ID
            conversation_data: Conversation data
            chat_summary: Optional chat summary to update
            
        Returns:
            bool: True if saved successfully
        """
        try:
            return self.repository.update_conversation(user_id, session_id, conversation_data, chat_summary)
                
        except Exception as e:
            logger.error(f"Error saving conversation {user_id}/{session_id}: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gets conversation history for a user session
        
        Args:
            user_id: User ID
            session_id: Session ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        try:
            conversation = self.repository.get_conversation(user_id, session_id)
            
            if conversation:
                conversation_data = conversation["conversation_data"]
                messages = conversation_data.get("messages", [])
                
                # Return last N messages
                return messages[-limit:] if limit else messages
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting conversation history {user_id}/{session_id}: {e}")
            return []
    
    def clear_conversation(self, user_id: str, session_id: str) -> bool:
        """
        Clears a specific conversation (marks as inactive)
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            bool: True if cleared successfully
        """
        try:
            return self.repository.delete_conversation(user_id, session_id)
                
        except Exception as e:
            logger.error(f"Error clearing conversation {user_id}/{session_id}: {e}")
            return False
    
    def cleanup_expired_conversations(self) -> int:
        """
        Cleans up expired conversations
        
        Returns:
            int: Number of conversations cleaned up
        """
        try:
            return self.cleanup.cleanup_expired_conversations()
            
        except Exception as e:
            logger.error(f"Error cleaning up expired conversations: {e}")
            return 0
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Gets conversation statistics
        
        Returns:
            Dict with statistics
        """
        try:
            return self.analytics.get_conversation_stats()
            
        except Exception as e:
            logger.error(f"Error getting conversation statistics: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "active_sessions": 0,
                "oldest_conversation": None,
                "newest_conversation": None,
                "storage_type": "supabase_database",
                "error": str(e)
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Gets cache information (for compatibility with existing interface)
        
        Returns:
            Dict with cache information
        """
        try:
            stats = self.get_conversation_stats()
            
            return {
                "supabase_database": stats,
                "storage_type": "supabase_database",
                "conversations_list": self.repository.list_conversations()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {
                "supabase_database": {},
                "storage_type": "supabase_database",
                "conversations_list": [],
                "error": str(e)
            }
    
    def clear_all_cache(self) -> Dict[str, Any]:
        """
        Clears all conversations (marks as inactive)
        
        Returns:
            Dict with cleanup results
        """
        try:
            cleared_count = self.cleanup.clear_all_conversations()
            
            return {
                "conversations_cleared": cleared_count,
                "storage_type": "supabase_database"
            }
            
        except Exception as e:
            logger.error(f"Error clearing all conversations: {e}")
            return {
                "conversations_cleared": 0,
                "storage_type": "supabase_database",
                "error": str(e)
            }
    
    def list_conversations(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lists conversations with optional filters
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of conversations
        """
        try:
            return self.repository.list_conversations(filters)
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []
    
    # Additional methods for enhanced functionality
    
    def get_user_activity_stats(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Gets user activity statistics
        
        Args:
            user_id: Optional user ID to filter by
            days: Number of days to look back
            
        Returns:
            Dict with user activity statistics
        """
        try:
            return self.analytics.get_user_activity_stats(user_id, days)
        except Exception as e:
            logger.error(f"Error getting user activity stats: {e}")
            return {"error": str(e)}
    
    def get_conversation_metrics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets detailed conversation metrics
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Dict with conversation metrics
        """
        try:
            return self.analytics.get_conversation_metrics(user_id)
        except Exception as e:
            logger.error(f"Error getting conversation metrics: {e}")
            return {"error": str(e)}
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Gets statistics about conversations that could be cleaned up
        
        Returns:
            Dict with cleanup statistics
        """
        try:
            return self.cleanup.get_cleanup_stats()
        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}")
            return {"error": str(e)}
    
    def schedule_cleanup(self, cleanup_type: str = "all") -> Dict[str, Any]:
        """
        Schedules cleanup operations
        
        Args:
            cleanup_type: Type of cleanup to perform ("expired", "inactive", "archive", "all")
            
        Returns:
            Dict with cleanup results
        """
        try:
            return self.cleanup.schedule_cleanup(cleanup_type)
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}")
            return {"error": str(e)}
