"""
Main OSM Service - Orchestrator for OpenStreetMap operations
Provides high-level interface for OSM data access
"""
from typing import List, Optional
from src.models.property import POI
from .connection_service import OSMConnectionService
from .poi_service import OSMPOIService
import logging

logger = logging.getLogger(__name__)


class OSMService:
    """
    Main orchestrator service for OpenStreetMap operations
    
    This service provides a high-level interface for accessing OSM data,
    managing connections, and coordinating between different OSM sub-services.
    
    Attributes:
        connection_service: Handles API connections
        poi_service: Handles POI searches
    """
    
    def __init__(
        self,
        connection_service: OSMConnectionService = None,
        poi_service: OSMPOIService = None
    ):
        """
        Initialize OSM Service with dependency injection
        
        Args:
            connection_service: Optional connection service instance
            poi_service: Optional POI service instance
        """
        # Initialize connection service
        self.connection_service = connection_service or OSMConnectionService()
        
        # Initialize POI service
        self.poi_service = poi_service or OSMPOIService(self.connection_service)
        
        logger.info("OSM Service initialized successfully")
    
    def search_pois_around_location(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1000,
        amenity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[POI]:
        """
        Search POIs around a geographic location
        
        Args:
            latitude: Latitude of center point
            longitude: Longitude of center point
            radius: Search radius in meters (default: 1000m = 1km)
            amenity_type: Type of amenity (restaurant, school, hospital, etc.)
                         If None, searches all amenity types
            limit: Maximum number of results (default: 50)
            
        Returns:
            List of POI objects
            
        Example:
            >>> osm = OSMService()
            >>> pois = osm.search_pois_around_location(
            ...     latitude=25.7617,
            ...     longitude=-80.1918,
            ...     radius=500,
            ...     amenity_type="restaurant"
            ... )
        """
        return self.poi_service.search_pois_by_radius(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            amenity_type=amenity_type,
            limit=limit
        )
    
    def search_pois_in_area(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        amenity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[POI]:
        """
        Search POIs within a bounding box area
        
        Args:
            south: Southern latitude boundary
            west: Western longitude boundary
            north: Northern latitude boundary
            east: Eastern longitude boundary
            amenity_type: Type of amenity to filter
            limit: Maximum number of results
            
        Returns:
            List of POI objects
            
        Example:
            >>> osm = OSMService()
            >>> pois = osm.search_pois_in_area(
            ...     south=25.76, west=-80.20,
            ...     north=25.77, east=-80.19,
            ...     amenity_type="school"
            ... )
        """
        return self.poi_service.search_pois_by_bbox(
            south=south,
            west=west,
            north=north,
            east=east,
            amenity_type=amenity_type,
            limit=limit
        )
    
    def is_service_available(self) -> bool:
        """
        Check if OSM service is available
        
        Returns:
            True if service is available, False otherwise
        """
        return self.connection_service.is_available()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Clean up resources if needed
        pass

