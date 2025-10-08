"""
Temporary cache system using JSON files
Allows persisting conversations between server restarts
"""
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import fcntl
import time

logger = logging.getLogger(__name__)

class JSONCacheManager:
    """JSON file cache manager"""
    
    def __init__(self, cache_dir: str = "cache/conversations", max_age_hours: int = 24):
        """
        Initializes the JSON cache manager
        
        Args:
            cache_dir: Directory where to store cache files
            max_age_hours: Hours after which to delete old files
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_hours = max_age_hours
        self.lock_timeout = 5  # seconds for lock timeout
        
        # Create directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Note: Metadata file was removed as it was not necessary
        
        logger.info(f"JSONCacheManager initialized at: {self.cache_dir}")
    
    def _get_file_path(self, user_id: str, session_id: str) -> Path:
        """Gets the file path for a user session"""
        # Use hash to avoid problems with special characters
        safe_user_id = user_id.replace('/', '_').replace('\\', '_')
        safe_session_id = session_id.replace('/', '_').replace('\\', '_')
        
        # Create user directory if it doesn't exist
        user_dir = self.cache_dir / f"user_{safe_user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        
        return user_dir / f"session_{safe_session_id}.json"
    
    def _acquire_lock(self, file_path: Path) -> Optional[Any]:
        """Acquires an exclusive lock on a file"""
        try:
            lock_file = open(f"{file_path}.lock", 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_file
        except (IOError, OSError):
            return None
    
    def _release_lock(self, lock_file: Any) -> None:
        """Releases the lock of a file"""
        try:
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
        except (IOError, OSError):
            pass
    
    def save_conversation(self, user_id: str, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """
        Saves a conversation to JSON cache
        
        Args:
            user_id: User ID
            session_id: Session ID
            conversation_data: Conversation data
            
        Returns:
            bool: True if saved successfully
        """
        try:
            file_path = self._get_file_path(user_id, session_id)
            
            # Add cache metadata
            cache_data = {
                "user_id": user_id,
                "session_id": session_id,
                "cached_at": datetime.now().isoformat(),
                "last_activity": conversation_data.get("last_activity", datetime.now().isoformat()),
                "conversation": conversation_data
            }
            
            # Acquire lock for safe writing
            lock_file = self._acquire_lock(file_path)
            if not lock_file:
                logger.warning(f"Could not acquire lock for {session_id}")
                return False
            
            try:
                # Write temporary file first
                temp_path = file_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
                # Move temporary file at the end (atomic operation)
                shutil.move(str(temp_path), str(file_path))
                
                # Metadata removed - not necessary
                
                logger.debug(f"Conversation {user_id}/{session_id} saved to cache")
                return True
                
            finally:
                self._release_lock(lock_file)
                
        except Exception as e:
            logger.error(f"Error saving conversation {user_id}/{session_id}: {e}")
            return False
    
    def load_conversation(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads a conversation from JSON cache
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict with conversation data or None if it doesn't exist
        """
        try:
            file_path = self._get_file_path(user_id, session_id)
            
            if not file_path.exists():
                return None
            
            # Check if file is not too old
            if self._is_file_expired(file_path):
                self.delete_conversation(user_id, session_id)
                return None
            
            # Acquire lock for safe reading
            lock_file = self._acquire_lock(file_path)
            if not lock_file:
                logger.warning(f"Could not acquire lock to read {user_id}/{session_id}")
                return None
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Verify data integrity
                if not self._validate_cache_data(cache_data):
                    logger.warning(f"Corrupted cache data for {user_id}/{session_id}")
                    return None
                
                conversation_data = cache_data.get("conversation", {})
                
                # Update last activity
                conversation_data["last_activity"] = datetime.now().isoformat()
                
                logger.debug(f"Conversation {user_id}/{session_id} loaded from cache")
                return conversation_data
                
            finally:
                self._release_lock(lock_file)
                
        except Exception as e:
            logger.error(f"Error loading conversation {user_id}/{session_id}: {e}")
            return None
    
    def delete_conversation(self, user_id: str, session_id: str) -> bool:
        """
        Deletes a conversation from cache
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            file_path = self._get_file_path(user_id, session_id)
            
            if file_path.exists():
                # Acquire lock before deleting
                lock_file = self._acquire_lock(file_path)
                try:
                    file_path.unlink()
                    # Delete lock file as well
                    lock_path = Path(f"{file_path}.lock")
                    if lock_path.exists():
                        lock_path.unlink()
                    
                    logger.debug(f"Conversation {user_id}/{session_id} deleted from cache")
                    return True
                finally:
                    if lock_file:
                        self._release_lock(lock_file)
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting conversation {user_id}/{session_id}: {e}")
            return False
    
    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists all conversations in cache, optionally filtered by user_id
        
        Args:
            user_id: Optional user ID to filter conversations
            
        Returns:
            List of dictionaries with conversation information
        """
        conversations = []
        
        try:
            # If user_id is provided, only search in that user's directory
            if user_id:
                safe_user_id = user_id.replace('/', '_').replace('\\', '_')
                user_dir = self.cache_dir / f"user_{safe_user_id}"
                if not user_dir.exists():
                    return conversations
                search_pattern = user_dir / "session_*.json"
            else:
                # Search all user directories
                search_pattern = self.cache_dir / "user_*" / "session_*.json"
            
            for file_path in self.cache_dir.glob(str(search_pattern)):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if self._validate_cache_data(cache_data):
                        conversation = cache_data.get("conversation", {})
                        conversations.append({
                            "user_id": cache_data.get("user_id"),
                            "session_id": cache_data.get("session_id"),
                            "cached_at": cache_data.get("cached_at"),
                            "last_activity": conversation.get("last_activity"),
                            "message_count": len(conversation.get("messages", [])),
                            "file_size": file_path.stat().st_size
                        })
                        
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
        
        return conversations
    
    def cleanup_expired_conversations(self) -> int:
        """
        Cleans expired conversations
        
        Returns:
            int: Number of conversations deleted
        """
        deleted_count = 0
        
        try:
            # Search all user directories
            for file_path in self.cache_dir.glob("user_*/*/session_*.json"):
                if self._is_file_expired(file_path):
                    try:
                        # Extract user_id and session_id from path
                        path_parts = file_path.parts
                        user_dir = path_parts[-2]  # user_xxx directory
                        session_file = path_parts[-1]  # session_xxx.json
                        
                        user_id = user_dir.replace("user_", "").replace("_", "/")
                        session_id = session_file.replace("session_", "").replace(".json", "")
                        
                        if self.delete_conversation(user_id, session_id):
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Error deleting expired file {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleanup completed: {deleted_count} conversations deleted")
                
        except Exception as e:
            logger.error(f"Error in cache cleanup: {e}")
        
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Gets cache statistics
        
        Returns:
            Dict with cache statistics
        """
        try:
            conversations = self.list_conversations()
            total_files = len(list(self.cache_dir.glob("user_*/*/session_*.json")))
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("user_*/*/session_*.json"))
            
            return {
                "total_conversations": len(conversations),
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "cache_directory": str(self.cache_dir),
                "max_age_hours": self.max_age_hours,
                "oldest_conversation": min([c["cached_at"] for c in conversations], default=None),
                "newest_conversation": max([c["cached_at"] for c in conversations], default=None)
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def _is_file_expired(self, file_path: Path) -> bool:
        """Checks if a file has expired"""
        try:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
            return file_time < cutoff_time
        except Exception:
            return True  # If there is error, consider expired
    
    def _validate_cache_data(self, cache_data: Dict[str, Any]) -> bool:
        """Validates the structure of cache data"""
        required_fields = ["user_id", "session_id", "cached_at", "conversation"]
        return all(field in cache_data for field in required_fields)
    
    # Method _update_metadata removed - not necessary
    
    def clear_all_cache(self) -> int:
        """
        Deletes all cache
        
        Returns:
            int: Number of files deleted
        """
        deleted_count = 0
        
        try:
            for file_path in self.cache_dir.glob("user_*/*/session_*.json"):
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error deleting {file_path}: {e}")
            
            # Clean lock files
            for lock_file in self.cache_dir.glob("**/*.lock"):
                try:
                    lock_file.unlink()
                except Exception:
                    pass
            
            logger.info(f"Cache cleaned: {deleted_count} files deleted")
            
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
        
        return deleted_count
