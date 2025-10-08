"""
Service for Weaviate connection management
Handles connection establishment, health checks, and reconnection
"""
import weaviate
from weaviate.classes.init import Auth
from typing import Optional
from src.config.settings import settings
from .interfaces import WeaviateConnectionInterface
import logging

logger = logging.getLogger(__name__)


class WeaviateConnectionService(WeaviateConnectionInterface):
    """Service for handling Weaviate connection operations"""
    
    def __init__(self):
        self.client: Optional[weaviate.Client] = None
        self.connect()
    
    def connect(self) -> None:
        """Establishes connection with Weaviate"""
        try:
            # Establish connection using direct method as in original code
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=settings.WEAVIATE_URL,
                auth_credentials=Auth.api_key(settings.WEAVIATE_API_KEY),
                headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
            )
            
            # Verify connection
            if not self.client.is_ready():
                raise ConnectionError("Could not connect to Weaviate")
            
            logger.info("Weaviate connection established successfully")
                
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            raise
    
    def ensure_connection(self) -> None:
        """Ensures connection is active, reconnects if necessary"""
        try:
            if not self.client or not self.client.is_ready():
                logger.warning("Connection lost, reconnecting...")
                self.connect()
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            self.connect()
    
    def is_connected(self) -> bool:
        """Checks if connection is active"""
        try:
            return self.client is not None and self.client.is_ready()
        except Exception:
            return False
    
    def close(self) -> None:
        """Closes the connection with Weaviate"""
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
