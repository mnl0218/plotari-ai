"""
POI Enrichment endpoints
Endpoints for enriching properties with POIs from OpenStreetMap
"""
from fastapi import APIRouter, HTTPException, status
import logging
from src.models.property import POIEnrichmentRequest, POIEnrichmentResponse
from src.services.enrichment import POIEnrichmentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Enrichment"])


@router.post("/enrich-pois", response_model=POIEnrichmentResponse)
async def enrich_properties_with_pois(request: POIEnrichmentRequest):
    """
    POST /enrich-pois
    
    Enriches properties with POIs from OpenStreetMap and saves them to Weaviate.
    
    This endpoint:
    1. Fetches properties from Supabase filtered by date (>= since_date)
    2. For each property, searches POIs in OSM using its geolocation
    3. Saves found POIs to Weaviate (with deduplication)
    
    Args:
        request: POIEnrichmentRequest with:
            - since_date: ISO 8601 date to filter properties (YYYY-MM-DD)
            - radius: Search radius in meters for each property (100-5000)
            - amenities: List of amenity types to search (restaurant, school, etc.)
            - limit_per_property: Max POIs per property (1-50)
    
    Returns:
        POIEnrichmentResponse with statistics about the enrichment process
        
    Example:
        ```json
        {
            "since_date": "2024-01-01",
            "radius": 1000,
            "amenities": ["restaurant", "school", "hospital"],
            "limit_per_property": 20
        }
        ```
    """
    try:
        logger.info(
            f"Received POI enrichment request: since_date={request.since_date}, "
            f"radius={request.radius}m, amenities={request.amenities}"
        )
        
        # Initialize enrichment service
        enrichment_service = POIEnrichmentService()
        
        # Execute enrichment flow
        response = enrichment_service.enrich_properties_with_pois(request)
        
        logger.info(
            f"POI enrichment completed: {response.properties_processed} properties, "
            f"{response.total_pois_found} POIs found, "
            f"{response.total_pois_saved} POIs saved"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in POI enrichment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in POI enrichment endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enriching properties with POIs: {str(e)}"
        )

