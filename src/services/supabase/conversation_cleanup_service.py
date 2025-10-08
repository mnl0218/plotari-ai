"""
Conversation cleanup service
Handles conversation cleanup and maintenance operations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ConversationCleanupService:
    """Service for conversation cleanup and maintenance operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            logger.info("Conversation cleanup service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    def cleanup_expired_conversations(self, max_age_hours: int = 24) -> int:
        """
        Cleans up expired conversations by marking them as inactive
        
        Args:
            max_age_hours: Maximum age in hours before conversation is considered expired
            
        Returns:
            int: Number of conversations cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Mark expired conversations as inactive
            response = self.supabase.table("chatbot_conversations").update({
                "is_active": False
            }).lt("expires_at", datetime.now().isoformat()).eq("is_active", True).execute()
            
            cleaned_count = len(response.data) if response.data else 0
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired conversations (older than {max_age_hours} hours)")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired conversations: {e}")
            return 0
    
    def cleanup_inactive_conversations(self, inactive_hours: int = 168) -> int:
        """
        Cleans up conversations that have been inactive for a specified time
        
        Args:
            inactive_hours: Hours of inactivity before cleanup (default: 7 days)
            
        Returns:
            int: Number of conversations cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=inactive_hours)
            
            # Mark inactive conversations as inactive
            response = self.supabase.table("chatbot_conversations").update({
                "is_active": False
            }).lt("last_activity", cutoff_time.isoformat()).eq("is_active", True).execute()
            
            cleaned_count = len(response.data) if response.data else 0
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} inactive conversations (inactive for {inactive_hours} hours)")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive conversations: {e}")
            return 0
    
    def archive_old_conversations(self, archive_days: int = 30) -> int:
        """
        Archives old conversations by moving them to an archive table or marking them as archived
        
        Args:
            archive_days: Days after which to archive conversations
            
        Returns:
            int: Number of conversations archived
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=archive_days)
            
            # Get conversations to archive
            response = self.supabase.table("chatbot_conversations").select("*").lt("created_at", cutoff_time.isoformat()).eq("is_active", True).execute()
            
            if not response.data:
                return 0
            
            # Mark as archived (you could also move to a separate table)
            archived_count = 0
            for conv in response.data:
                try:
                    # Add archive metadata
                    conversation_data = conv["conversation_data"]
                    conversation_data["archived_at"] = datetime.now().isoformat()
                    conversation_data["archive_reason"] = "automatic_archive"
                    
                    # Update conversation
                    update_response = self.supabase.table("chatbot_conversations").update({
                        "conversation_data": conversation_data,
                        "is_active": False
                    }).eq("id", conv["id"]).execute()
                    
                    if update_response.data:
                        archived_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error archiving conversation {conv['id']}: {e}")
                    continue
            
            if archived_count > 0:
                logger.info(f"Archived {archived_count} old conversations (older than {archive_days} days)")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"Error archiving old conversations: {e}")
            return 0
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Performs database optimization operations
        
        Returns:
            Dict with optimization results
        """
        try:
            results = {
                "expired_cleaned": 0,
                "inactive_cleaned": 0,
                "archived": 0,
                "total_optimized": 0
            }
            
            # Clean expired conversations
            results["expired_cleaned"] = self.cleanup_expired_conversations()
            
            # Clean inactive conversations
            results["inactive_cleaned"] = self.cleanup_inactive_conversations()
            
            # Archive old conversations
            results["archived"] = self.archive_old_conversations()
            
            # Calculate total
            results["total_optimized"] = (
                results["expired_cleaned"] + 
                results["inactive_cleaned"] + 
                results["archived"]
            )
            
            logger.info(f"Database optimization completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return {
                "expired_cleaned": 0,
                "inactive_cleaned": 0,
                "archived": 0,
                "total_optimized": 0,
                "error": str(e)
            }
    
    def clear_all_conversations(self) -> int:
        """
        Clears all active conversations (marks as inactive)
        
        Returns:
            int: Number of conversations cleared
        """
        try:
            response = self.supabase.table("chatbot_conversations").update({
                "is_active": False
            }).eq("is_active", True).execute()
            
            cleared_count = len(response.data) if response.data else 0
            
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} conversations from Supabase")
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error clearing all conversations: {e}")
            return 0
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Gets statistics about conversations that could be cleaned up
        
        Returns:
            Dict with cleanup statistics
        """
        try:
            now = datetime.now()
            
            # Get expired conversations
            expired_response = self.supabase.table("chatbot_conversations").select("id", count="exact").lt("expires_at", now.isoformat()).eq("is_active", True).execute()
            expired_count = expired_response.count or 0
            
            # Get inactive conversations (7 days)
            inactive_cutoff = now - timedelta(hours=168)
            inactive_response = self.supabase.table("chatbot_conversations").select("id", count="exact").lt("last_activity", inactive_cutoff.isoformat()).eq("is_active", True).execute()
            inactive_count = inactive_response.count or 0
            
            # Get old conversations (30 days)
            old_cutoff = now - timedelta(days=30)
            old_response = self.supabase.table("chatbot_conversations").select("id", count="exact").lt("created_at", old_cutoff.isoformat()).eq("is_active", True).execute()
            old_count = old_response.count or 0
            
            # Get total active conversations
            total_response = self.supabase.table("chatbot_conversations").select("id", count="exact").eq("is_active", True).execute()
            total_active = total_response.count or 0
            
            return {
                "total_active_conversations": total_active,
                "expired_conversations": expired_count,
                "inactive_conversations": inactive_count,
                "old_conversations": old_count,
                "cleanup_candidates": expired_count + inactive_count + old_count,
                "last_checked": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cleanup statistics: {e}")
            return {
                "total_active_conversations": 0,
                "expired_conversations": 0,
                "inactive_conversations": 0,
                "old_conversations": 0,
                "cleanup_candidates": 0,
                "error": str(e)
            }
    
    def schedule_cleanup(self, cleanup_type: str = "all") -> Dict[str, Any]:
        """
        Schedules cleanup operations
        
        Args:
            cleanup_type: Type of cleanup to perform ("expired", "inactive", "archive", "all")
            
        Returns:
            Dict with cleanup results
        """
        try:
            results = {}
            
            if cleanup_type in ["expired", "all"]:
                results["expired_cleaned"] = self.cleanup_expired_conversations()
            
            if cleanup_type in ["inactive", "all"]:
                results["inactive_cleaned"] = self.cleanup_inactive_conversations()
            
            if cleanup_type in ["archive", "all"]:
                results["archived"] = self.archive_old_conversations()
            
            if cleanup_type == "all":
                results["total_cleaned"] = sum(results.values())
            
            logger.info(f"Scheduled cleanup completed ({cleanup_type}): {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}")
            return {"error": str(e)}
