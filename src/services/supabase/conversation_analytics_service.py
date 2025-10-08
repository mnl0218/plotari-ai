"""
Conversation analytics service
Handles conversation statistics and analytics operations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ConversationAnalyticsService:
    """Service for conversation analytics and statistics"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            logger.info("Conversation analytics service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Gets general conversation statistics
        
        Returns:
            Dict with conversation statistics
        """
        try:
            # Get total active conversations
            active_response = self.supabase.table("chatbot_conversations").select("id", count="exact").eq("is_active", True).execute()
            total_conversations = active_response.count or 0
            
            # Get total messages
            messages_response = self.supabase.table("chatbot_conversations").select("conversation_data").eq("is_active", True).execute()
            total_messages = 0
            
            if messages_response.data:
                for conv in messages_response.data:
                    messages = conv["conversation_data"].get("messages", [])
                    total_messages += len(messages)
            
            # Get oldest and newest conversations
            oldest_response = self.supabase.table("chatbot_conversations").select("created_at").eq("is_active", True).order("created_at", desc=False).limit(1).execute()
            newest_response = self.supabase.table("chatbot_conversations").select("created_at").eq("is_active", True).order("created_at", desc=True).limit(1).execute()
            
            oldest_conversation = oldest_response.data[0]["created_at"] if oldest_response.data else None
            newest_conversation = newest_response.data[0]["created_at"] if newest_response.data else None
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_sessions": total_conversations,
                "oldest_conversation": oldest_conversation,
                "newest_conversation": newest_conversation,
                "storage_type": "supabase_database"
            }
            
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
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = self.supabase.table("chatbot_conversations").select("*").gte("created_at", cutoff_date).eq("is_active", True)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                return {
                    "total_users": 0,
                    "total_conversations": 0,
                    "total_messages": 0,
                    "avg_messages_per_conversation": 0,
                    "most_active_users": [],
                    "period_days": days
                }
            
            # Calculate statistics
            total_conversations = len(response.data)
            total_messages = 0
            user_stats = {}
            
            for conv in response.data:
                messages = conv["conversation_data"].get("messages", [])
                total_messages += len(messages)
                
                user_id_conv = conv["user_id"]
                if user_id_conv not in user_stats:
                    user_stats[user_id_conv] = {
                        "conversations": 0,
                        "messages": 0
                    }
                user_stats[user_id_conv]["conversations"] += 1
                user_stats[user_id_conv]["messages"] += len(messages)
            
            # Get most active users
            most_active_users = sorted(
                user_stats.items(),
                key=lambda x: x[1]["messages"],
                reverse=True
            )[:10]
            
            avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
            
            return {
                "total_users": len(user_stats),
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_conversation": round(avg_messages_per_conversation, 2),
                "most_active_users": [
                    {
                        "user_id": user_id,
                        "conversations": stats["conversations"],
                        "messages": stats["messages"]
                    }
                    for user_id, stats in most_active_users
                ],
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity statistics: {e}")
            return {
                "total_users": 0,
                "total_conversations": 0,
                "total_messages": 0,
                "avg_messages_per_conversation": 0,
                "most_active_users": [],
                "period_days": days,
                "error": str(e)
            }
    
    def get_conversation_metrics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets detailed conversation metrics
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Dict with conversation metrics
        """
        try:
            query = self.supabase.table("chatbot_conversations").select("conversation_data", "created_at", "last_activity").eq("is_active", True)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                return {
                    "total_conversations": 0,
                    "avg_conversation_length": 0,
                    "avg_session_duration_minutes": 0,
                    "conversation_length_distribution": {},
                    "peak_hours": [],
                    "message_types": {}
                }
            
            # Calculate metrics
            total_conversations = len(response.data)
            total_messages = 0
            session_durations = []
            hourly_activity = {}
            message_types = {}
            
            for conv in response.data:
                conversation_data = conv["conversation_data"]
                messages = conversation_data.get("messages", [])
                total_messages += len(messages)
                
                # Calculate session duration
                created_at = datetime.fromisoformat(conv["created_at"].replace('Z', '+00:00'))
                last_activity = datetime.fromisoformat(conv["last_activity"].replace('Z', '+00:00'))
                duration_minutes = (last_activity - created_at).total_seconds() / 60
                session_durations.append(duration_minutes)
                
                # Track hourly activity
                hour = created_at.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                
                # Track message types
                for message in messages:
                    role = message.get("role", "unknown")
                    message_types[role] = message_types.get(role, 0) + 1
            
            # Calculate averages
            avg_conversation_length = total_messages / total_conversations if total_conversations > 0 else 0
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            
            # Get peak hours
            peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Conversation length distribution
            length_distribution = {}
            for conv in response.data:
                length = len(conv["conversation_data"].get("messages", []))
                if length <= 5:
                    bucket = "1-5"
                elif length <= 10:
                    bucket = "6-10"
                elif length <= 20:
                    bucket = "11-20"
                else:
                    bucket = "20+"
                length_distribution[bucket] = length_distribution.get(bucket, 0) + 1
            
            return {
                "total_conversations": total_conversations,
                "avg_conversation_length": round(avg_conversation_length, 2),
                "avg_session_duration_minutes": round(avg_session_duration, 2),
                "conversation_length_distribution": length_distribution,
                "peak_hours": [
                    {"hour": hour, "conversations": count}
                    for hour, count in peak_hours
                ],
                "message_types": message_types
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation metrics: {e}")
            return {
                "total_conversations": 0,
                "avg_conversation_length": 0,
                "avg_session_duration_minutes": 0,
                "conversation_length_distribution": {},
                "peak_hours": [],
                "message_types": {},
                "error": str(e)
            }
    
    def get_conversation_history_stats(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Gets statistics for a specific conversation
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict with conversation-specific statistics
        """
        try:
            response = self.supabase.table("chatbot_conversations").select("*").eq("user_id", user_id).eq("session_id", session_id).eq("is_active", True).execute()
            
            if not response.data:
                return {
                    "exists": False,
                    "message_count": 0,
                    "duration_minutes": 0,
                    "user_messages": 0,
                    "assistant_messages": 0
                }
            
            conv = response.data[0]
            conversation_data = conv["conversation_data"]
            messages = conversation_data.get("messages", [])
            
            # Calculate statistics
            user_messages = len([m for m in messages if m.get("role") == "user"])
            assistant_messages = len([m for m in messages if m.get("role") == "assistant"])
            
            # Calculate duration
            created_at = datetime.fromisoformat(conv["created_at"].replace('Z', '+00:00'))
            last_activity = datetime.fromisoformat(conv["last_activity"].replace('Z', '+00:00'))
            duration_minutes = (last_activity - created_at).total_seconds() / 60
            
            return {
                "exists": True,
                "message_count": len(messages),
                "duration_minutes": round(duration_minutes, 2),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "created_at": conv["created_at"],
                "last_activity": conv["last_activity"]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history stats {user_id}/{session_id}: {e}")
            return {
                "exists": False,
                "message_count": 0,
                "duration_minutes": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "error": str(e)
            }
