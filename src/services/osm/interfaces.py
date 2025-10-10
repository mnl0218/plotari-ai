"""
Interfaces/Protocols for OSM services
Defines clear contracts for OpenStreetMap Overpass API services
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models.property import POI, GeoCoordinate


class OSMConnectionInterface(ABC):
    """Interface for OSM Overpass API connection management"""
    
    @abstractmethod
    def query(self, overpass_query: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes an Overpass QL query
        
        Args:
            overpass_query: Query in Overpass QL format
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON from Overpass API
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if Overpass API is available"""
        pass


class OSMPOIInterface(ABC):
    """Interface for POI search operations from OSM"""
    
    @abstractmethod
    def search_pois_by_radius(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        amenity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[POI]:
        """
        Searches POIs around a coordinate using radius
        
        Args:
            latitude: Latitude of center point
            longitude: Longitude of center point
            radius: Search radius in meters
            amenity_type: Type of amenity to filter (restaurant, school, etc.)
            limit: Maximum number of results
            
        Returns:
            List of POI objects
        """
        pass
    
    @abstractmethod
    def search_pois_by_bbox(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        amenity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[POI]:
        """
        Searches POIs within a bounding box
        
        Args:
            south: Southern latitude
            west: Western longitude
            north: Northern latitude
            east: Eastern longitude
            amenity_type: Type of amenity to filter
            limit: Maximum number of results
            
        Returns:
            List of POI objects
        """
        pass

