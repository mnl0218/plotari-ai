"""
POI Enrichment Service
Orchestrates the flow: Supabase (properties) → OSM (search POIs) → Weaviate (save POIs)
"""
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
import logging
from src.models.property import POI, POIEnrichmentRequest, POIEnrichmentResponse
from src.services.supabase import SupabasePropertyService
from src.services.osm import OSMService
from src.services.weaviate import WeaviateService

logger = logging.getLogger(__name__)


class POIEnrichmentService:
    """
    Service for enriching properties with POIs from OpenStreetMap
    
    This service:
    1. Fetches properties from Supabase (filtered by date)
    2. For each property, searches POIs in OSM using its geolocation
    3. Saves found POIs to Weaviate (with deduplication)
    """
    
    def __init__(
        self,
        supabase_service: SupabasePropertyService = None,
        osm_service: OSMService = None,
        weaviate_service: WeaviateService = None
    ):
        """
        Initialize enrichment service with dependency injection
        
        Args:
            supabase_service: Service for Supabase property operations
            osm_service: Service for OSM POI searches
            weaviate_service: Service for Weaviate operations
        """
        self.supabase_service = supabase_service or SupabasePropertyService()
        self.osm_service = osm_service or OSMService()
        self.weaviate_service = weaviate_service or WeaviateService()
        logger.info("POI Enrichment Service initialized")
    
    def enrich_properties_with_pois(
        self,
        request: POIEnrichmentRequest
    ) -> POIEnrichmentResponse:
        """
        Main enrichment flow: Supabase → OSM → Weaviate
        
        Args:
            request: Enrichment request with date, radius, amenities
            
        Returns:
            Enrichment response with statistics and status
        """
        try:
            logger.info(
                f"Starting POI enrichment: since_date={request.since_date}, "
                f"radius={request.radius}m, amenities={request.amenities}"
            )
            
            # Statistics tracking
            stats = {
                'properties_processed': 0,
                'total_pois_found': 0,
                'total_pois_saved': 0,
                'errors': []
            }
            
            # Step 1: Parse date and fetch properties from Supabase
            since_date = self._parse_date(request.since_date)
            properties = self._fetch_properties_from_supabase(since_date, stats)
            
            if not properties:
                logger.warning("No properties found for the given date filter")
                return self._build_response(request, stats, "completed")
            
            logger.info(f"Found {len(properties)} properties to process")
            
            # Step 2: Process each property (search POIs in OSM)
            all_pois = self._search_pois_for_properties(
                properties, request, stats
            )
            
            logger.info(f"Found {len(all_pois)} total POIs from OSM")
            
            # Step 3: Save POIs to Weaviate (with deduplication)
            if all_pois:
                saved_count = self._save_pois_to_weaviate(all_pois, stats)
                stats['total_pois_saved'] = saved_count
                logger.info(f"Saved {saved_count} POIs to Weaviate")
            
            return self._build_response(request, stats, "completed")
            
        except Exception as e:
            logger.error(f"Error in POI enrichment: {e}")
            stats['errors'].append(str(e))
            return self._build_response(request, stats, "failed")
    
    def _parse_date(self, date_string: str) -> datetime:
        """
        Parses date string to datetime object
        
        Args:
            date_string: ISO 8601 date string (YYYY-MM-DD or full datetime)
            
        Returns:
            datetime object
        """
        try:
            # Try parsing as datetime first
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing as date only
                return datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError as e:
                logger.error(f"Invalid date format: {date_string}")
                raise ValueError(f"Invalid date format. Use YYYY-MM-DD or ISO 8601: {e}")
    
    def _fetch_properties_from_supabase(
        self,
        since_date: datetime,
        stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fetches properties from Supabase filtered by date
        
        Args:
            since_date: Filter properties updated >= this date
            stats: Statistics dictionary to update
            
        Returns:
            List of property dictionaries
        """
        try:
            properties = self.supabase_service.get_properties_updated_since(since_date)
            logger.info(f"Fetched {len(properties)} properties from Supabase")
            return properties
        except Exception as e:
            logger.error(f"Error fetching properties from Supabase: {e}")
            stats['errors'].append(f"Supabase fetch error: {str(e)}")
            return []
    
    def _search_pois_for_properties(
        self,
        properties: List[Dict[str, Any]],
        request: POIEnrichmentRequest,
        stats: Dict[str, Any]
    ) -> List[POI]:
        """
        Searches POIs for each property using OSM
        
        Args:
            properties: List of properties from Supabase
            request: Enrichment request with search parameters
            stats: Statistics dictionary to update
            
        Returns:
            List of all POIs found (deduplicated)
        """
        all_pois: Dict[Tuple[float, float, str], POI] = {}  # Deduplication by (lat, lon, name)
        
        for prop in properties:
            try:
                # Extract geolocation
                lat = prop.get('latitude')
                lon = prop.get('longitude')
                
                if not lat or not lon:
                    logger.warning(f"Property {prop.get('zpid', 'unknown')} has no coordinates, skipping")
                    continue
                
                property_id = prop.get('zpid', 'unknown')
                logger.debug(f"Processing property {property_id} at ({lat}, {lon})")
                
                # Search POIs for each amenity type
                for amenity in request.amenities:
                    pois = self._search_pois_for_location(
                        lat, lon, request.radius, amenity, 
                        request.limit_per_property, property_id, stats
                    )
                    
                    # Deduplicate POIs using (lat, lon, name) as key
                    for poi in pois:
                        key = (poi.geo.latitude, poi.geo.longitude, poi.name)
                        if key not in all_pois:
                            all_pois[key] = poi
                
                stats['properties_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing property {prop.get('zpid', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                continue
        
        return list(all_pois.values())
    
    def _search_pois_for_location(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        amenity: str,
        limit: int,
        property_id: str,
        stats: Dict[str, Any]
    ) -> List[POI]:
        """
        Searches POIs around a specific location
        
        Args:
            latitude: Latitude of the property
            longitude: Longitude of the property
            radius: Search radius in meters
            amenity: Amenity type to search
            limit: Maximum results per search
            property_id: ID of the property (for logging)
            stats: Statistics dictionary to update
            
        Returns:
            List of POIs found
        """
        try:
            pois = self.osm_service.search_pois_around_location(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                amenity_type=amenity,
                limit=limit
            )
            
            logger.debug(
                f"Found {len(pois)} POIs of type '{amenity}' "
                f"for property {property_id}"
            )
            
            stats['total_pois_found'] += len(pois)
            return pois
            
        except Exception as e:
            error_msg = f"OSM search error for property {property_id}, amenity '{amenity}': {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return []
    
    def _save_pois_to_weaviate(
        self,
        pois: List[POI],
        stats: Dict[str, Any]
    ) -> int:
        """
        Saves POIs to Weaviate
        
        Args:
            pois: List of POIs to save
            stats: Statistics dictionary to update
            
        Returns:
            Number of POIs successfully saved
        """
        try:
            # Use WeaviateService to insert POIs
            saved_count = self.weaviate_service.insert_pois_batch(pois)
            logger.info(f"Successfully saved {saved_count} POIs to Weaviate")
            return saved_count
            
        except Exception as e:
            error_msg = f"Error saving POIs to Weaviate: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return 0
    
    def _build_response(
        self,
        request: POIEnrichmentRequest,
        stats: Dict[str, Any],
        status: str
    ) -> POIEnrichmentResponse:
        """
        Builds enrichment response
        
        Args:
            request: Original enrichment request
            stats: Statistics collected during processing
            status: Status of the enrichment process
            
        Returns:
            POIEnrichmentResponse object
        """
        return POIEnrichmentResponse(
            status=status,
            properties_processed=stats['properties_processed'],
            total_pois_found=stats['total_pois_found'],
            total_pois_saved=stats['total_pois_saved'],
            amenities_searched=request.amenities,
            errors=stats['errors'] if stats['errors'] else None,
            metadata={
                'since_date': request.since_date,
                'radius_meters': request.radius,
                'limit_per_property': request.limit_per_property
            }
        )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Clean up resources if needed
        if hasattr(self.weaviate_service, '__exit__'):
            self.weaviate_service.__exit__(exc_type, exc_val, exc_tb)

