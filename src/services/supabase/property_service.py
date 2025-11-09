"""
Supabase property service
Handles property data operations from Supabase database
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from supabase import create_client, Client
from src.config.settings import settings
from src.models.property import Property, GeoCoordinate

logger = logging.getLogger(__name__)


class SupabasePropertyService:
    """Service for handling property operations in Supabase"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            logger.info("Supabase property service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    def get_all_properties(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Gets all properties from Supabase including their latest listing data
        
        Args:
            limit: Maximum number of properties to return
            offset: Number of properties to skip
            
        Returns:
            List of property dictionaries
        """
        try:
            # Select properties with related listing data
            query = self.supabase.table("properties").select(
                "id, zpid, address, city, state, zipcode, neighborhood, property_type, latitude, longitude, year_built, lot_size_sqft, listings(id, price, bedrooms, bathrooms, living_area, listing_type, description)"
            )

            if limit is not None:
                start = offset
                end = offset + limit - 1
                query = query.range(start, end)
            elif offset > 0:
                start = offset
                end = offset + 999
                query = query.range(start, end)

            response = query.execute()

            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting properties from Supabase: {e}")
            raise
    
    def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a specific property by ID along with its latest listing data
        
        Args:
            property_id: Property ID to search for
            
        Returns:
            Property dictionary or None if not found
        """
        try:
            response = self.supabase.table("properties").select(
                "id, zpid, address, city, state, zipcode, neighborhood, property_type, latitude, longitude, year_built, lot_size_sqft, listings(id, price, bedrooms, bathrooms, living_area, listing_type, description)"
            ).eq("id", property_id).execute()

            logger.info(f"Supabase response for property {property_id}: {response.data}")

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
                
        except Exception as e:
            logger.error(f"Error getting property {property_id} from Supabase: {e}")
            return None
    
    def get_properties_updated_since(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Gets properties updated since a specific datetime, including listing data
        
        Args:
            since: Datetime to filter by
            
        Returns:
            List of property dictionaries
        """
        try:
            response = self.supabase.table("properties").select(
                "id, zpid, address, city, state, zipcode, neighborhood, property_type, latitude, longitude, year_built, lot_size_sqft, listings(id, price, bedrooms, bathrooms, living_area, listing_type, description)"
            ).gte("created_at", since.isoformat()).execute()

            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting properties updated since {since}: {e}")
            raise
    
    def get_properties_count(self) -> int:
        """
        Gets the total count of properties in Supabase
        
        Returns:
            Total number of properties
        """
        try:
            response = self.supabase.table("properties").select("id", count="exact").execute()
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Error getting properties count: {e}")
            return 0
    
    def convert_supabase_property_to_model(self, supabase_property: Dict[str, Any]) -> Property:
        """
        Converts Supabase property data to Property model
        
        Args:
            supabase_property: Property data from Supabase
            
        Returns:
            Property model instance
        """
        try:
            property_id = supabase_property.get("id")
            if property_id is None:
                raise ValueError("Supabase property record is missing 'id'")

            listings = supabase_property.get("listings")
            listing_record: Optional[Dict[str, Any]] = None
            if isinstance(listings, list) and listings:
                listing_record = listings[0]
            elif isinstance(listings, dict):
                listing_record = listings

            zpid_value = supabase_property.get("zpid") or property_id

            property_data = {
                "zpid": str(zpid_value),
                "property_id": int(property_id),
                "address": supabase_property.get("address") or "",
                "city": supabase_property.get("city") or "",
                "state": (supabase_property.get("state") or "").strip(),
                "zipcode": str(supabase_property.get("zipcode") or ""),
                "year_built": supabase_property.get("year_built"),
                "lot_size": supabase_property.get("lot_size_sqft"),
                "neighborhood_text": supabase_property.get("neighborhood"),
                "property_type": supabase_property.get("property_type"),
                "price": listing_record.get("price") if listing_record else None,
                "bedrooms": listing_record.get("bedrooms") if listing_record else None,
                "bathrooms": listing_record.get("bathrooms") if listing_record else None,
                "living_area": listing_record.get("living_area") if listing_record else None,
                "description": listing_record.get("description") if listing_record else None,
                "listing_id": int(listing_record.get("id")) if listing_record and listing_record.get("id") is not None else None,
                "listing_type": listing_record.get("listing_type") if listing_record else None,
            }

            # Handle geo coordinates
            if supabase_property.get("latitude") and supabase_property.get("longitude"):
                property_data["geo"] = GeoCoordinate(
                    latitude=float(supabase_property["latitude"]),
                    longitude=float(supabase_property["longitude"])
                )
             
            # Generate search corpus for vectorization
            search_corpus_parts = []
            if property_data["address"]:
                search_corpus_parts.append(property_data["address"])
            if property_data["city"]:
                search_corpus_parts.append(property_data["city"])
            if property_data["state"]:
                search_corpus_parts.append(property_data["state"])
            if property_data["description"]:
                search_corpus_parts.append(property_data["description"])
            if property_data["neighborhood_text"]:
                search_corpus_parts.append(property_data["neighborhood_text"])
            if property_data["property_type"]:
                search_corpus_parts.append(property_data["property_type"])
            
            property_data["search_corpus"] = " | ".join(search_corpus_parts)
            
            return Property(**property_data)
            
        except Exception as e:
            logger.error(f"Error converting Supabase property to model: {e}")
            raise
    
    def convert_properties_batch(self, supabase_properties: List[Dict[str, Any]]) -> List[Property]:
        """
        Converts a batch of Supabase properties to Property models
        
        Args:
            supabase_properties: List of property data from Supabase
            
        Returns:
            List of Property model instances
        """
        properties = []
        for prop_data in supabase_properties:
            try:
                properties.append(self.convert_supabase_property_to_model(prop_data))
            except Exception as e:
                logger.warning(f"Error converting property {prop_data.get('id', 'unknown')}: {e}")
                continue
        return properties
