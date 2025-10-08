"""
Supabase conversation repository
Handles conversation persistence operations using Supabase database
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from src.config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseConversationRepository:
    """Repository for conversation persistence operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            logger.info("Supabase conversation repository initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    def get_conversation(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets an existing conversation
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Conversation data or None if not found
        """
        try:
            response = self.supabase.table("chatbot_conversations").select("*").eq("user_id", user_id).eq("session_id", session_id).eq("is_active", True).execute()
            
            if response.data:
                return response.data[0]
            return None
                
        except Exception as e:
            logger.error(f"Error getting conversation {user_id}/{session_id}: {e}")
            return None
    
    def create_conversation(self, user_id: str, session_id: str, conversation_data: Dict[str, Any], chat_summary: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Creates a new conversation
        
        Args:
            user_id: User ID
            session_id: Session ID
            conversation_data: Conversation data
            chat_summary: Optional chat summary
            
        Returns:
            Created conversation data or None if failed
        """
        try:
            insert_data = {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_data": conversation_data,
                "context": conversation_data.get("context", {}),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            # Add chat_summary if provided
            if chat_summary:
                insert_data["chat_summary"] = chat_summary
            
            response = self.supabase.table("chatbot_conversations").insert(insert_data).execute()
            
            if response.data:
                logger.info(f"New conversation created in Supabase: {user_id}/{session_id}")
                return response.data[0]
            return None
                
        except Exception as e:
            logger.error(f"Error creating conversation {user_id}/{session_id}: {e}")
            return None
    
    def update_conversation(self, user_id: str, session_id: str, conversation_data: Dict[str, Any], chat_summary: Optional[str] = None) -> bool:
        """
        Updates an existing conversation
        
        Args:
            user_id: User ID
            session_id: Session ID
            conversation_data: Updated conversation data
            chat_summary: Optional chat summary to update
            
        Returns:
            bool: True if updated successfully
        """
        try:
            update_data = {
                "conversation_data": conversation_data,
                "context": conversation_data.get("context", {}),
                "last_activity": datetime.now().isoformat()
            }
            
            # Add chat_summary if provided
            if chat_summary is not None:
                update_data["chat_summary"] = chat_summary
            
            response = self.supabase.table("chatbot_conversations").update(update_data).eq("user_id", user_id).eq("session_id", session_id).eq("is_active", True).execute()
            
            if response.data:
                logger.debug(f"Conversation updated in Supabase: {user_id}/{session_id}")
                return True
            else:
                logger.warning(f"Conversation not found for update: {user_id}/{session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating conversation {user_id}/{session_id}: {e}")
            return False
    
    def delete_conversation(self, user_id: str, session_id: str) -> bool:
        """
        Deletes a conversation (marks as inactive)
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            response = self.supabase.table("chatbot_conversations").update({
                "is_active": False
            }).eq("user_id", user_id).eq("session_id", session_id).eq("is_active", True).execute()
            
            if response.data:
                logger.info(f"Conversation deleted in Supabase: {user_id}/{session_id}")
                return True
            else:
                logger.warning(f"Conversation not found for deletion: {user_id}/{session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting conversation {user_id}/{session_id}: {e}")
            return False
    
    def list_conversations(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lists conversations with optional filters
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of conversations
        """
        try:
            logger.info(f"Listing conversations with filters: {filters}")
            
            query = self.supabase.table("chatbot_conversations").select(
                "user_id", "session_id", "created_at", "last_activity", "conversation_data"
            ).eq("is_active", True)
            
            # Apply filters if provided
            if filters:
                if "user_id" in filters:
                    query = query.eq("user_id", filters["user_id"])
                    logger.info(f"Filtering by user_id: {filters['user_id']}")
                if "limit" in filters:
                    query = query.limit(filters["limit"])
                    logger.info(f"Limiting to: {filters['limit']}")
                if "order_by" in filters:
                    order_desc = filters.get("order_desc", True)
                    query = query.order(filters["order_by"], desc=order_desc)
                    logger.info(f"Ordering by: {filters['order_by']} desc={order_desc}")
            
            response = query.execute()
            logger.info(f"Raw response from Supabase: {response.data}")
            
            conversations = []
            if response.data:
                for conv in response.data:
                    conversation_data = conv["conversation_data"]
                    conversations.append({
                        "user_id": conv["user_id"],
                        "session_id": conv["session_id"],
                        "created_at": conv["created_at"],
                        "last_activity": conv["last_activity"],
                        "message_count": len(conversation_data.get("messages", []))
                    })
            
            logger.info(f"Returning {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []
    
    def update_last_activity(self, conversation_id: str) -> bool:
        """
        Updates last activity timestamp for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            bool: True if updated successfully
        """
        try:
            response = self.supabase.table("chatbot_conversations").update({
                "last_activity": datetime.now().isoformat()
            }).eq("id", conversation_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.warning(f"Error updating last activity for conversation {conversation_id}: {e}")
            return False
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a conversation by its ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data or None if not found
        """
        try:
            response = self.supabase.table("chatbot_conversations").select("*").eq("id", conversation_id).eq("is_active", True).execute()
            
            if response.data:
                return response.data[0]
            return None
                
        except Exception as e:
            logger.error(f"Error getting conversation by ID {conversation_id}: {e}")
            return None
