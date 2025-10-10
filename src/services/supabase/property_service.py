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
        Gets all properties from Supabase with latest price from price_history
        
        Args:
            limit: Maximum number of properties to return
            offset: Number of properties to skip
            
        Returns:
            List of property dictionaries
        """
        try:
            # Select properties with price_history ordered by created_at desc and limited to 1
            query = self.supabase.table("properties").select(
                "*, price_history(price, event_date)"
            ).order(
                "event_date", desc=True, foreign_table="price_history"
            ).limit(1, foreign_table="price_history")
            
            if offset > 0:
                query = query.range(offset, offset + (limit or 1000) - 1)
            elif limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            # Process the response to extract price from price_history
            properties = []
            
            for item in response.data:
                # Extract price from price_history (already ordered and limited to 1)
                price_history = item.get('price_history', [])
                item['price'] = price_history[0].get('price') if price_history else None
                item.pop('price_history', None)
                properties.append(item)
                
            
            return properties
            
        except Exception as e:
            logger.error(f"Error getting properties from Supabase: {e}")
            raise
    
    def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a specific property by ID with latest price from price_history
        
        Args:
            property_id: Property ID to search for
            
        Returns:
            Property dictionary or None if not found
        """
        try:
            # Get property with latest price from price_history ordered by created_at desc
            response = self.supabase.table("properties").select(
                "*, price_history(price, event_date)"
            ).eq("id", property_id).order(
                "event_date", desc=True, foreign_table="price_history"
            ).limit(1, foreign_table="price_history").execute()
            
            logger.info(f"Supabase response for property {property_id}: {response.data}")
            
            if response.data and len(response.data) > 0:
                property_data = response.data[0]
                
                logger.info(f"Property data before extraction: zpid={property_data.get('zpid')}, price_history={property_data.get('price_history')}")
                
                # Extract price from price_history (already ordered and limited to 1)
                price_history = property_data.get('price_history', [])
                property_data['price'] = price_history[0].get('price') if price_history else None
                property_data.pop('price_history', None)
                
                logger.info(f"Property data after extraction: zpid={property_data.get('zpid')}, price={property_data.get('price')}")
                
                return property_data
            return None
                
        except Exception as e:
            logger.error(f"Error getting property {property_id} from Supabase: {e}")
            return None
    
    def get_properties_updated_since(self, since: datetime) -> List[Dict[str, Any]]:
        """
        Gets properties updated since a specific datetime with latest price from price_history
        
        Args:
            since: Datetime to filter by
            
        Returns:
            List of property dictionaries
        """
        try:
            # Select properties with latest price from price_history ordered by created_at desc
            response = self.supabase.table("properties").select(
                "*, price_history(price, event_date)"
            ).gte("created_at", since.isoformat()).order(
                "event_date", desc=True, foreign_table="price_history"
            ).limit(1, foreign_table="price_history").execute()
            
            # Process each property to extract price from price_history
            properties = []
            for property_data in response.data:
                # Extract price from price_history (already ordered and limited to 1)
                price_history = property_data.get('price_history', [])
                property_data['price'] = price_history[0].get('price') if price_history else None
                property_data.pop('price_history', None)
                properties.append(property_data)
            
            return properties
            
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
            # Map Supabase fields to Property model
            property_data = {
                "zpid": str(supabase_property.get("zpid", "")),  # Assuming id maps to zpid
                "address": supabase_property.get("address", ""),
                "city": supabase_property.get("city", ""),
                "state": supabase_property.get("state", ""),
                "zipcode": supabase_property.get("zipcode", ""),
                "price": supabase_property.get("price"),
                "bedrooms": supabase_property.get("bedrooms"),
                "bathrooms": supabase_property.get("bathrooms"),
                "living_area": supabase_property.get("living_area"),
                "year_built": supabase_property.get("year_built"),
                "lot_size": supabase_property.get("lot_size_sqft"),
                "description": supabase_property.get("description"),
                "features": supabase_property.get("features", []),
                "neighborhood_text": supabase_property.get("neighborhood"),
                "property_type": supabase_property.get("property_type"),
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
            if property_data["features"]:
                search_corpus_parts.extend(property_data["features"])
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
