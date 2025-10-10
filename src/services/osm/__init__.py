"""
OSM Services Module
Provides services for accessing OpenStreetMap data via Overpass API

Main Components:
- OSMService: Main orchestrator for all OSM operations
- OSMConnectionService: Handles API connections
- OSMPOIService: Handles POI search operations
- Interfaces: Define service contracts

Example Usage:
    >>> from src.services.osm import OSMService
    >>> 
    >>> osm = OSMService()
    >>> pois = osm.search_pois_around_location(
    ...     latitude=25.7617,
    ...     longitude=-80.1918,
    ...     radius=1000,
    ...     amenity_type="restaurant"
    ... )
"""

from .osm_service import OSMService
from .connection_service import OSMConnectionService
from .poi_service import OSMPOIService
from .interfaces import (
    OSMConnectionInterface,
    OSMPOIInterface
)

__all__ = [
    "OSMService",
    "OSMConnectionService",
    "OSMPOIService",
    "OSMConnectionInterface",
    "OSMPOIInterface",
]

