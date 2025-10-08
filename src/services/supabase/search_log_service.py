"""
Search Log Service for Supabase
Handles logging of search operations for analytics and debugging
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from supabase import create_client, Client
from src.config.settings import Settings

logger = logging.getLogger(__name__)


class SearchLogService:
    """
    Service for logging search operations to chatbot_search_logs table
    """
    
    def __init__(self):
        """Initialize Supabase client for search logging"""
        try:
            settings = Settings()
            self.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("SearchLogService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SearchLogService: {e}")
            raise
    
    def log_search(
        self,
        conversation_id: str,
        search_type: str,
        query: str,
        filters: Dict[str, Any] = None,
        results_count: int = 0,
        response_time_ms: int = 0,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Log a search operation to the database
        
        Args:
            conversation_id: ID of the conversation
            search_type: Type of search (property_search, poi_search, general_inquiry)
            query: Search query text
            filters: Applied filters
            results_count: Number of results found
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata
            
        Returns:
            Log entry data or None if failed
        """
        try:
            log_data = {
                "conversation_id": conversation_id,
                "search_type": search_type,
                "query": query,
                "filters": filters or {},
                "results_count": results_count,
                "response_time_ms": response_time_ms,
                "metadata": metadata or {},
                "search_timestamp": datetime.now().isoformat()
            }
            
            response = self.supabase.table("chatbot_search_logs").insert(log_data).execute()
            
            if response.data:
                logger.info(f"Search logged successfully: {search_type} - {results_count} results")
                return response.data[0]
            return None
                
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            return None
    
    def get_search_logs(
        self,
        conversation_id: Optional[str] = None,
        search_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve search logs with optional filtering
        
        Args:
            conversation_id: Filter by conversation ID
            search_type: Filter by search type
            limit: Maximum number of logs to return
            
        Returns:
            List of search log entries
        """
        try:
            query = self.supabase.table("chatbot_search_logs").select("*")
            
            if conversation_id:
                query = query.eq("conversation_id", conversation_id)
            
            if search_type:
                query = query.eq("search_type", search_type)
            
            query = query.order("search_timestamp", desc=True).limit(limit)
            
            response = query.execute()
            return response.data or []
                
        except Exception as e:
            logger.error(f"Error retrieving search logs: {e}")
            return []
    
    def get_search_analytics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get search analytics for the specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data including counts, popular queries, etc.
        """
        try:
            # Get all search logs for the period
            all_logs = self.supabase.table("chatbot_search_logs").select("*").execute()
            
            if not all_logs.data:
                return {
                    "total_searches": 0,
                    "search_types": {},
                    "popular_queries": [],
                    "average_response_time": 0
                }
            
            # Count by search type
            search_types = {}
            response_times = []
            
            for log in all_logs.data:
                search_type = log.get("search_type", "unknown")
                search_types[search_type] = search_types.get(search_type, 0) + 1
                
                if log.get("response_time_ms"):
                    response_times.append(log["response_time_ms"])
            
            # Get popular queries (top 10)
            query_counts = {}
            for log in all_logs.data:
                query = log.get("query", "")
                if query:
                    query_counts[query] = query_counts.get(query, 0) + 1
            
            popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            analytics = {
                "total_searches": len(all_logs.data),
                "search_types": search_types,
                "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0
            }
            
            return analytics
                
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Clean up search logs older than specified days
        
        Args:
            days: Number of days to keep logs
            
        Returns:
            Number of logs deleted
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            response = self.supabase.table("chatbot_search_logs").delete().lt(
                "search_timestamp", cutoff_date.isoformat()
            ).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {deleted_count} old search logs")
            return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old search logs: {e}")
            return 0