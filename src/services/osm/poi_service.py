"""
Service for POI operations using OpenStreetMap data
Searches and converts OSM data to POI model objects
"""
from typing import List, Optional, Dict, Any
from src.models.property import POI, GeoCoordinate
from .interfaces import OSMPOIInterface
from .connection_service import OSMConnectionService
import logging

logger = logging.getLogger(__name__)


class OSMPOIService(OSMPOIInterface):
    """
    Service for handling POI search operations from OpenStreetMap
    Converts OSM amenity data to POI model objects
    """
    
    def __init__(self, connection_service: OSMConnectionService):
        """
        Initialize POI service
        
        Args:
            connection_service: OSM connection service instance
        """
        self.connection_service = connection_service
        logger.info("OSM POI Service initialized")
    
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
            List of POI objects using the existing POI model
        """
        try:
            logger.info(
                f"Searching POIs: lat={latitude}, lon={longitude}, "
                f"radius={radius}m, amenity={amenity_type or 'all'}"
            )
            
            # Build Overpass QL query
            query = self._build_radius_query(
                latitude, longitude, radius, amenity_type
            )
            
            # Execute query
            data = self.connection_service.query(query)
            
            # Convert results to POI objects
            pois = self._convert_osm_to_pois(data, amenity_type, limit)
            
            logger.info(f"Found {len(pois)} POIs")
            return pois
            
        except Exception as e:
            logger.error(f"Error searching POIs by radius: {e}")
            raise
    
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
        try:
            logger.info(
                f"Searching POIs in bbox: ({south},{west}) to ({north},{east}), "
                f"amenity={amenity_type or 'all'}"
            )
            
            # Build Overpass QL query
            query = self._build_bbox_query(
                south, west, north, east, amenity_type
            )
            
            # Execute query
            data = self.connection_service.query(query)
            
            # Convert results to POI objects
            pois = self._convert_osm_to_pois(data, amenity_type, limit)
            
            logger.info(f"Found {len(pois)} POIs")
            return pois
            
        except Exception as e:
            logger.error(f"Error searching POIs by bbox: {e}")
            raise
    
    def _build_radius_query(
        self,
        lat: float,
        lon: float,
        radius: int,
        amenity_type: Optional[str]
    ) -> str:
        """Builds Overpass QL query for radius search"""
        
        amenity_filter = f'="{amenity_type}"' if amenity_type else ''
        
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"{amenity_filter}](around:{radius},{lat},{lon});
          way["amenity"{amenity_filter}](around:{radius},{lat},{lon});
        );
        out body;
        """
        
        return query.strip()
    
    def _build_bbox_query(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        amenity_type: Optional[str]
    ) -> str:
        """Builds Overpass QL query for bounding box search"""
        
        amenity_filter = f'="{amenity_type}"' if amenity_type else ''
        
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"{amenity_filter}]({south},{west},{north},{east});
          way["amenity"{amenity_filter}]({south},{west},{north},{east});
        );
        out body;
        """
        
        return query.strip()
    
    def _convert_osm_to_pois(
        self,
        osm_data: Dict[str, Any],
        category: Optional[str],
        limit: int
    ) -> List[POI]:
        """
        Converts OSM data to POI model objects
        
        Args:
            osm_data: Raw OSM data from Overpass API
            category: Category to use if not specified in OSM data
            limit: Maximum number of POIs to return
            
        Returns:
            List of POI objects
        """
        pois = []
        
        for element in osm_data.get("elements", [])[:limit]:
            try:
                poi = self._convert_element_to_poi(element, category)
                if poi:
                    pois.append(poi)
            except Exception as e:
                logger.warning(f"Failed to convert OSM element {element.get('id')}: {e}")
                continue
        
        return pois
    
    def _convert_element_to_poi(
        self,
        element: Dict[str, Any],
        default_category: Optional[str]
    ) -> Optional[POI]:
        """
        Converts a single OSM element to POI object
        
        Args:
            element: OSM element data
            default_category: Default category if not in tags
            
        Returns:
            POI object or None if conversion fails
        """
        # Get coordinates (may be in element or need to be calculated)
        lat = element.get("lat")
        lon = element.get("lon")
        
        # Skip if no coordinates
        if lat is None or lon is None:
            return None
        
        tags = element.get("tags", {})
        
        # Get amenity type (category)
        amenity = tags.get("amenity", default_category or "unknown")
        
        # Get name
        name = tags.get("name", "Sin nombre")
        
        # Build search corpus for better searchability
        search_corpus_parts = [name, amenity]
        
        if tags.get("cuisine"):
            search_corpus_parts.append(tags["cuisine"])
        if tags.get("brand"):
            search_corpus_parts.append(tags["brand"])
        if tags.get("addr:street"):
            search_corpus_parts.append(tags["addr:street"])
        if tags.get("addr:city"):
            search_corpus_parts.append(tags["addr:city"])
        
        search_corpus = " ".join(filter(None, search_corpus_parts))
        
        # Extract rating if available (OSM doesn't typically have ratings)
        rating = None
        if "rating" in tags:
            try:
                rating = float(tags["rating"])
            except (ValueError, TypeError):
                rating = None
        
        # Create POI object using existing model
        poi = POI(
            name=name[:200],  # Limit to max_length
            category=amenity[:100],  # Limit to max_length
            rating=rating,
            source="OpenStreetMap",
            geo=GeoCoordinate(
                latitude=lat,
                longitude=lon
            ),
            search_corpus=search_corpus[:2000]  # Limit to max_length
        )
        
        return poi

