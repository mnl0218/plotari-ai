"""
Service for managing connections to OpenStreetMap Overpass API
Handles HTTP requests and API availability
"""
import requests
from typing import Dict, Any
from .interfaces import OSMConnectionInterface
import logging

logger = logging.getLogger(__name__)


class OSMConnectionService(OSMConnectionInterface):
    """
    Service for handling connections to Overpass API
    
    Attributes:
        base_url: Overpass API endpoint URL
    """
    
    # Public Overpass API endpoint
    DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    def __init__(self, base_url: str = None):
        """
        Initialize connection service
        
        Args:
            base_url: Custom Overpass API endpoint (optional)
                     Defaults to public API if not provided
        """
        self.base_url = base_url or self.DEFAULT_OVERPASS_URL
        logger.info(f"OSM Connection Service initialized with endpoint: {self.base_url}")
    
    def query(self, overpass_query: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes an Overpass QL query
        
        Args:
            overpass_query: Query in Overpass QL format
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON from Overpass API
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If the response is not valid JSON
        """
        try:
            logger.debug(f"Executing Overpass query with timeout {timeout}s")
            
            response = requests.post(
                self.base_url,
                data={"data": overpass_query},
                timeout=timeout
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Query successful. Elements returned: {len(data.get('elements', []))}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Query timeout after {timeout}s")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise
    
    def is_available(self) -> bool:
        """
        Checks if Overpass API is available
        
        Returns:
            True if API is available, False otherwise
        """
        try:
            # Simple test query to check availability
            test_query = "[out:json][timeout:5]; node(0); out;"
            
            response = requests.post(
                self.base_url,
                data={"data": test_query},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"Overpass API unavailable: {e}")
            return False

