"""
Property synchronization service
Handles synchronization of property data between Supabase and Weaviate
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from src.services.supabase.property_service import SupabasePropertyService
from src.services.weaviate.weaviate_service import WeaviateService
from src.models.property import Property
from src.config.settings import settings

logger = logging.getLogger(__name__)


class PropertySyncService:
    """Service for synchronizing property data between Supabase and Weaviate"""
    
    def __init__(self):
        """Initialize sync service with Supabase and Weaviate services"""
        self.supabase_service = SupabasePropertyService()
        self.weaviate_service = WeaviateService()
    
    def sync_all_properties(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Synchronizes all properties from Supabase to Weaviate
        
        Args:
            batch_size: Number of properties to process in each batch
            
        Returns:
            Sync results summary
        """
        try:
            logger.info("Starting full property synchronization from Supabase to Weaviate")
            
            # Get total count for progress tracking
            total_count = self.supabase_service.get_properties_count()
            logger.info(f"Total properties to sync: {total_count}")
            
            synced_count = 0
            error_count = 0
            offset = 0
            
            while offset < total_count:
                # Get batch from Supabase
                supabase_properties = self.supabase_service.get_all_properties(
                    limit=batch_size, 
                    offset=offset
                )
                
                if not supabase_properties:
                    break
                
                # Convert to Property models
                properties = self.supabase_service.convert_properties_batch(supabase_properties)
                
                # Insert into Weaviate
                batch_synced, batch_errors = self._sync_properties_batch(properties)
                
                synced_count += batch_synced
                error_count += batch_errors
                offset += batch_size
                
                logger.info(f"Processed batch: {offset}/{total_count} properties")
            
            result = {
                "total_properties": total_count,
                "synced_count": synced_count,
                "error_count": error_count,
                "success_rate": (synced_count / total_count * 100) if total_count > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Property synchronization completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in full property synchronization: {e}")
            raise
    
    def sync_properties_updated_since(self, since: datetime, batch_size: int = 100) -> Dict[str, Any]:
        """
        Synchronizes properties updated since a specific datetime
        
        Args:
            since: Datetime to filter by
            batch_size: Number of properties to process in each batch
            
        Returns:
            Sync results summary
        """
        try:
            logger.info(f"Starting incremental property sync since {since}")
            
            # Get updated properties from Supabase
            supabase_properties = self.supabase_service.get_properties_updated_since(since)
            total_count = len(supabase_properties)
            
            if total_count == 0:
                logger.info("No properties updated since the specified time")
                return {
                    "total_properties": 0,
                    "synced_count": 0,
                    "error_count": 0,
                    "success_rate": 100.0,
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Found {total_count} properties updated since {since}")
            
            # Convert to Property models
            properties = self.supabase_service.convert_properties_batch(supabase_properties)
            
            # Sync in batches
            synced_count = 0
            error_count = 0
            
            for i in range(0, len(properties), batch_size):
                batch = properties[i:i + batch_size]
                batch_synced, batch_errors = self._sync_properties_batch(batch)
                
                synced_count += batch_synced
                error_count += batch_errors
                
                logger.info(f"Processed batch: {i + len(batch)}/{len(properties)} properties")
            
            result = {
                "total_properties": total_count,
                "synced_count": synced_count,
                "error_count": error_count,
                "success_rate": (synced_count / total_count * 100) if total_count > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Incremental property synchronization completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in incremental property synchronization: {e}")
            raise
    
    def sync_single_property(self, property_id: str) -> Dict[str, Any]:
        """
        Synchronizes a single property by ID
        
        Args:
            property_id: Property ID to sync
            
        Returns:
            Sync result
        """
        try:
            logger.info(f"Syncing single property: {property_id}")
            
            # Get property from Supabase
            supabase_property = self.supabase_service.get_property_by_id(property_id)
            if not supabase_property:
                return {
                    "success": False,
                    "error": f"Property {property_id} not found in Supabase",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Convert to Property model
            property_obj = self.supabase_service.convert_supabase_property_to_model(supabase_property)
            
            # Insert into Weaviate
            success = self._insert_property_to_weaviate(property_obj)
            
            if success:
                logger.info(f"Successfully synced property {property_id}")
                return {
                    "success": True,
                    "property_id": property_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Failed to sync property {property_id}")
                return {
                    "success": False,
                    "error": f"Failed to insert property {property_id} into Weaviate",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error syncing single property {property_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _sync_properties_batch(self, properties: List[Property]) -> Tuple[int, int]:
        """
        Syncs a batch of properties to Weaviate
        
        Args:
            properties: List of Property objects to sync
            
        Returns:
            Tuple of (synced_count, error_count)
        """
        synced_count = 0
        error_count = 0
        
        for property_obj in properties:
            try:
                if self._insert_property_to_weaviate(property_obj):
                    synced_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error syncing property {property_obj.zpid}: {e}")
                error_count += 1
        
        return synced_count, error_count
    
    def _insert_property_to_weaviate(self, property_obj: Property) -> bool:
        """
        Inserts a single property into Weaviate
        
        Args:
            property_obj: Property object to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure Weaviate connection
            self.weaviate_service.connection_service.ensure_connection()
            
            # Get Property collection
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            
            # Prepare property data for Weaviate
            property_data = {
                "zpid": property_obj.zpid,
                "address": property_obj.address,
                "city": property_obj.city,
                "state": property_obj.state,
                "zipcode": property_obj.zipcode,
                "price": property_obj.price,
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "living_area": property_obj.living_area,
                "year_built": property_obj.year_built,
                "lot_size": property_obj.lot_size, 
                "description": property_obj.description,
                "features": property_obj.features or [],
                "neighborhood_text": property_obj.neighborhood_text, 
                "property_type": property_obj.property_type,
                "geo": {
                    "latitude": property_obj.geo.latitude,
                    "longitude": property_obj.geo.longitude
                } if property_obj.geo else None,
                "search_corpus": property_obj.search_corpus
            }
            
            # Remove None values
            property_data = {k: v for k, v in property_data.items() if v is not None}
            
            # Insert into Weaviate
            prop_col.data.insert(property_data)
            
            logger.debug(f"Successfully inserted property {property_obj.zpid} into Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting property {property_obj.zpid} into Weaviate: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Gets the current sync status between Supabase and Weaviate
        
        Returns:
            Status information
        """
        try:
            # Get counts from both systems
            supabase_count = self.supabase_service.get_properties_count()
            
            # Get Weaviate count
            self.weaviate_service.connection_service.ensure_connection()
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            weaviate_count = prop_col.aggregate.over_all(total_count=True).total_count
            
            return {
                "supabase_count": supabase_count,
                "weaviate_count": weaviate_count,
                "sync_difference": supabase_count - weaviate_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
