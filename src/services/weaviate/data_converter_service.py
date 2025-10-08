"""
Service for data conversion and transformation
Handles conversion between Weaviate objects and domain models
"""
from typing import Any, List, Optional
from src.models.property import Property, POI, Neighborhood, GeoCoordinate
from .interfaces import WeaviateDataConverterInterface
import logging

logger = logging.getLogger(__name__)


class WeaviateDataConverterService(WeaviateDataConverterInterface):
    """Service for handling data conversion and transformation"""
    
    def convert_geo_coordinate(self, geo_data: Any) -> GeoCoordinate:
        """Converts geo data to GeoCoordinate object"""
        try:
            if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                # If already a Weaviate GeoCoordinate, convert to our model
                return GeoCoordinate(
                    latitude=geo_data.latitude,
                    longitude=geo_data.longitude
                )
            elif isinstance(geo_data, dict):
                # If it's a dictionary, convert from dictionary
                return GeoCoordinate(
                    latitude=geo_data["latitude"],
                    longitude=geo_data["longitude"]
                )
            else:
                raise ValueError("Unrecognized geo coordinate format")
        except Exception as e:
            logger.error(f"Error converting geo coordinate: {e}")
            raise
    
    def convert_property_from_weaviate(self, obj: Any) -> Property:
        """Converts Weaviate object to Property"""
        try:
            prop_data = dict(obj.properties)
            
            # Convert geo coordinates if necessary
            if prop_data.get("geo"):
                prop_data["geo"] = self.convert_geo_coordinate(prop_data["geo"])
            
            return Property(**prop_data)
        except Exception as e:
            logger.error(f"Error converting property from Weaviate: {e}")
            raise
    
    def convert_poi_from_weaviate(self, obj: Any) -> POI:
        """Converts Weaviate object to POI"""
        try:
            poi_data = dict(obj.properties)
            
            # Convert geo coordinates if necessary
            if poi_data.get("geo"):
                poi_data["geo"] = self.convert_geo_coordinate(poi_data["geo"])
            
            return POI(**poi_data)
        except Exception as e:
            logger.error(f"Error converting POI from Weaviate: {e}")
            raise
    
    def convert_neighborhood_from_weaviate(self, obj: Any) -> Neighborhood:
        """Converts Weaviate object to Neighborhood"""
        try:
            neigh_data = dict(obj.properties)
            
            # Convert geo center if necessary
            if neigh_data.get("geo_center"):
                neigh_data["geo_center"] = self.convert_geo_coordinate(neigh_data["geo_center"])
            
            return Neighborhood(**neigh_data)
        except Exception as e:
            logger.error(f"Error converting neighborhood from Weaviate: {e}")
            raise
    
    def _extract_geo_coordinates(self, geo_data: Any) -> tuple[float, float]:
        """Extracts latitude and longitude from geo data"""
        try:
            if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                return geo_data.latitude, geo_data.longitude
            elif isinstance(geo_data, dict):
                return geo_data["latitude"], geo_data["longitude"]
            else:
                raise ValueError("Unrecognized geo coordinate format")
        except Exception as e:
            logger.error(f"Error extracting geo coordinates: {e}")
            raise
    
    def convert_properties_list(self, objects: List[Any]) -> List[Property]:
        """Converts a list of Weaviate objects to Property list"""
        properties = []
        for obj in objects:
            try:
                properties.append(self.convert_property_from_weaviate(obj))
            except Exception as e:
                logger.warning(f"Error converting property: {e}")
                continue
        return properties
    
    def convert_pois_list(self, objects: List[Any]) -> List[POI]:
        """Converts a list of Weaviate objects to POI list"""
        pois = []
        for obj in objects:
            try:
                pois.append(self.convert_poi_from_weaviate(obj))
            except Exception as e:
                logger.warning(f"Error converting POI: {e}")
                continue
        return pois
