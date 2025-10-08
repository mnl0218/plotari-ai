"""
Service for interacting with Weaviate
Based on the insert_test_data.py schema
"""
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter, GeoCoordinate as QueryGeo
from typing import List, Optional, Dict, Any
from src.config.settings import settings
from src.models.property import (
    Property, PropertySearchRequest, PropertySearchResponse,
    PropertyDetailResponse, POI, POISearchRequest, POISearchResponse,
    PropertyCompareRequest, PropertyCompareResponse, Neighborhood,
    GeoCoordinate
)
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class WeaviateService:
    """Service for handling Weaviate operations"""
    
    def __init__(self):
        self.client = None
        self.openai_client = None
        self._connect()
    
    def _connect(self) -> None:
        """Establishes connection with Weaviate"""
        try:
            # Establish connection using direct method as in original code
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=settings.WEAVIATE_URL,
                auth_credentials=Auth.api_key(settings.WEAVIATE_API_KEY),
                headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
            )
            
            # Verify connection
            if not self.client.is_ready():
                raise ConnectionError("Could not connect to Weaviate")
            
            # Initialize OpenAI client for embeddings
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            logger.info("Weaviate connection established successfully")
                
        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {e}")
            raise
    
    def _ensure_connection(self) -> None:
        """Asegura que la conexión esté activa, reconecta si es necesario"""
        try:
            if not self.client or not self.client.is_ready():
                logger.warning("Conexión perdida, reconectando...")
                self._connect()
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            self._connect()
    
    def _embed_text(self, text: str) -> List[float]:
        """Genera embedding para texto usando OpenAI"""
        try:
            if not text:
                return []
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return []
    
    def _build_filters(self, search_request: PropertySearchRequest) -> Optional[Filter]:
        """Construye filtros para la búsqueda"""
        filters = []
        
        # Filtros de precio
        if search_request.min_price is not None or search_request.max_price is not None:
            price_filter = Filter.by_property("price")
            if search_request.min_price is not None:
                price_filter = price_filter.greater_or_equal(search_request.min_price)
            if search_request.max_price is not None:
                price_filter = price_filter.less_or_equal(search_request.max_price)
            filters.append(price_filter)
        
        # Filtros de habitaciones
        if search_request.min_bedrooms is not None or search_request.max_bedrooms is not None:
            bedroom_filter = Filter.by_property("bedrooms")
            if search_request.min_bedrooms is not None:
                bedroom_filter = bedroom_filter.greater_or_equal(search_request.min_bedrooms)
            if search_request.max_bedrooms is not None:
                bedroom_filter = bedroom_filter.less_or_equal(search_request.max_bedrooms)
            filters.append(bedroom_filter)
        
        # Filtros de baños
        if search_request.min_bathrooms is not None or search_request.max_bathrooms is not None:
            bathroom_filter = Filter.by_property("bathrooms")
            if search_request.min_bathrooms is not None:
                bathroom_filter = bathroom_filter.greater_or_equal(search_request.min_bathrooms)
            if search_request.max_bathrooms is not None:
                bathroom_filter = bathroom_filter.less_or_equal(search_request.max_bathrooms)
            filters.append(bathroom_filter)
        
        # Filtros de ciudad y estado
        if search_request.city:
            filters.append(Filter.by_property("city").equal(search_request.city))
        if search_request.state:
            filters.append(Filter.by_property("state").equal(search_request.state))
        
        # Filtro geográfico
        if (search_request.latitude is not None and 
            search_request.longitude is not None and 
            search_request.radius is not None):
            geo_filter = Filter.by_property("geo").within_geo_range(
                coordinate=QueryGeo(
                    latitude=search_request.latitude,
                    longitude=search_request.longitude
                ),
                distance=search_request.radius
            )
            filters.append(geo_filter)
        
        # Combinar todos los filtros
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            return combined_filter
        
        return None
    
    def search_properties(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Busca propiedades usando búsqueda híbrida con filtros"""
        try:
            self._ensure_connection()
            
            # Obtener colección de propiedades
            prop_col = self.client.collections.get("Property")
            
            # Construir filtros
            filters = self._build_filters(search_request)
            
            # Generar embedding si hay query
            query_vector = None
            if search_request.query:
                query_vector = self._embed_text(search_request.query)
            
            # Realizar búsqueda híbrida
            if search_request.query and query_vector:
                result = prop_col.query.hybrid(
                    query=search_request.query,
                    vector=query_vector,
                    alpha=0.5,
                    limit=search_request.limit,
                    filters=filters,
                    return_properties=[
                        "zpid", "address", "city", "state", "zipcode",
                        "price", "bedrooms", "bathrooms", "living_area", 
                        "year_built", "lot_size", "description", "features",
                        "neighborhood_text", "geo", "search_corpus"
                    ]
                )
                search_type = "hybrid"
            else:
                # Búsqueda BM25 si no hay query o embedding
                result = prop_col.query.bm25(
                    query=search_request.query or "*",
                    limit=search_request.limit,
                    filters=filters,
                    return_properties=[
                        "zpid", "address", "city", "state", "zipcode",
                        "price", "bedrooms", "bathrooms", "living_area", 
                        "year_built", "lot_size", "description", "features",
                        "neighborhood_text", "geo", "search_corpus"
                    ]
                )
                search_type = "bm25"
            
            # Convertir resultados a objetos Property
            properties = []
            for obj in result.objects:
                try:
                    prop_data = dict(obj.properties)
                    # Convertir geo coordinates si es necesario
                    if prop_data.get("geo"):
                        geo_data = prop_data["geo"]
                        # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                        if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                            prop_data["geo"] = GeoCoordinate(
                                latitude=geo_data.latitude,
                                longitude=geo_data.longitude
                            )
                        # Si es un diccionario, convertir desde diccionario
                        elif isinstance(geo_data, dict):
                            prop_data["geo"] = GeoCoordinate(
                                latitude=geo_data["latitude"],
                                longitude=geo_data["longitude"]
                            )
                    properties.append(Property(**prop_data))
                except Exception as e:
                    logger.warning(f"Error convirtiendo propiedad: {e}")
                    logger.warning(f"Datos de la propiedad: {prop_data}")
                    continue
            
            # Construir filtros aplicados para metadata
            filters_applied = {}
            if search_request.min_price is not None:
                filters_applied["min_price"] = search_request.min_price
            if search_request.max_price is not None:
                filters_applied["max_price"] = search_request.max_price
            if search_request.min_bedrooms is not None:
                filters_applied["min_bedrooms"] = search_request.min_bedrooms
            if search_request.max_bedrooms is not None:
                filters_applied["max_bedrooms"] = search_request.max_bedrooms
            if search_request.city:
                filters_applied["city"] = search_request.city
            if search_request.state:
                filters_applied["state"] = search_request.state
            if search_request.latitude and search_request.longitude and search_request.radius:
                filters_applied["geo_search"] = {
                    "latitude": search_request.latitude,
                    "longitude": search_request.longitude,
                    "radius": search_request.radius
                }
            
            return PropertySearchResponse(
                properties=properties,
                total_count=len(properties),
                query=search_request.query,
                search_type=search_type,
                filters_applied=filters_applied
            )
            
        except Exception as e:
            logger.error(f"Error en búsqueda de propiedades: {e}")
            raise
    
    def get_property_detail(self, property_id: str) -> Optional[PropertyDetailResponse]:
        """Obtiene detalle de propiedad con recomendaciones similares"""
        try:
            self._ensure_connection()
            
            # Obtener colecciones
            prop_col = self.client.collections.get("Property")
            neigh_col = self.client.collections.get("Neighborhood")
            
            # Buscar la propiedad por zpid
            result = prop_col.query.bm25(
                query=property_id,
                limit=1,
                return_properties=[
                    "zpid", "address", "city", "state", "zipcode",
                    "price", "bedrooms", "bathrooms", "living_area", 
                    "year_built", "lot_size", "description", "features",
                    "neighborhood_text", "geo", "search_corpus"
                ]
            )
            
            if not result.objects:
                return None
            
            # Obtener la propiedad principal
            main_prop_data = dict(result.objects[0].properties)
            if main_prop_data["zpid"] != property_id:
                return None
            
            # Convertir geo coordinates si es necesario
            if main_prop_data.get("geo"):
                geo_data = main_prop_data["geo"]
                # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                    main_prop_data["geo"] = GeoCoordinate(
                        latitude=geo_data.latitude,
                        longitude=geo_data.longitude
                    )
                # Si es un diccionario, convertir desde diccionario
                elif isinstance(geo_data, dict):
                    main_prop_data["geo"] = GeoCoordinate(
                        latitude=geo_data["latitude"],
                        longitude=geo_data["longitude"]
                    )
            
            main_property = Property(**main_prop_data)
            
            # Buscar propiedades similares usando vector search
            similar_properties = []
            if main_property.search_corpus:
                query_vector = self._embed_text(main_property.search_corpus)
                if query_vector:
                    similar_result = prop_col.query.near_vector(
                        near_vector=query_vector,
                        limit=4,  # 4 similares + 1 original = 5 total
                        filters=Filter.by_property("zpid").not_equal(property_id),
                        return_properties=[
                            "zpid", "address", "city", "state", "zipcode",
                            "price", "bedrooms", "bathrooms", "living_area", 
                            "year_built", "lot_size", "description", "features",
                            "neighborhood_text", "geo", "search_corpus"
                        ]
                    )
                    
                    for obj in similar_result.objects:
                        try:
                            prop_data = dict(obj.properties)
                            # Convertir geo coordinates si es necesario
                            if prop_data.get("geo"):
                                geo_data = prop_data["geo"]
                                # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                                if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                                    prop_data["geo"] = GeoCoordinate(
                                        latitude=geo_data.latitude,
                                        longitude=geo_data.longitude
                                    )
                                # Si es un diccionario, convertir desde diccionario
                                elif isinstance(geo_data, dict):
                                    prop_data["geo"] = GeoCoordinate(
                                        latitude=geo_data["latitude"],
                                        longitude=geo_data["longitude"]
                                    )
                            similar_properties.append(Property(**prop_data))
                        except Exception as e:
                            logger.warning(f"Error convirtiendo propiedad similar: {e}")
                            continue
            
            # Buscar información del vecindario si está disponible
            neighborhood = None
            if main_property.neighborhood_text:
                try:
                    neigh_result = neigh_col.query.bm25(
                        query=main_property.neighborhood_text,
                        limit=1,
                        return_properties=["name", "city", "info", "geo_center", "search_corpus"]
                    )
                    
                    if neigh_result.objects:
                        neigh_data = dict(neigh_result.objects[0].properties)
                        if neigh_data.get("geo_center"):
                            geo_data = neigh_data["geo_center"]
                            # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                            if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                                neigh_data["geo_center"] = GeoCoordinate(
                                    latitude=geo_data.latitude,
                                    longitude=geo_data.longitude
                                )
                            # Si es un diccionario, convertir desde diccionario
                            elif isinstance(geo_data, dict):
                                neigh_data["geo_center"] = GeoCoordinate(
                                    latitude=geo_data["latitude"],
                                    longitude=geo_data["longitude"]
                                )
                        neighborhood = Neighborhood(**neigh_data)
                except Exception as e:
                    logger.warning(f"Error obteniendo vecindario: {e}")
            
            return PropertyDetailResponse(
                property=main_property,
                similar_properties=similar_properties,
                neighborhood=neighborhood
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo detalle de propiedad {property_id}: {e}")
            raise
    
    def search_pois(self, poi_request: POISearchRequest) -> POISearchResponse:
        """Busca POIs cerca de una propiedad"""
        try:
            self._ensure_connection()
            
            # Obtener colecciones
            prop_col = self.client.collections.get("Property")
            poi_col = self.client.collections.get("POI")
            
            # Obtener ubicación de la propiedad
            prop_result = prop_col.query.bm25(
                query=poi_request.property_id,
                limit=1,
                return_properties=["geo"]
            )
            
            if not prop_result.objects:
                raise ValueError(f"Propiedad {poi_request.property_id} no encontrada")
            
            prop_geo = prop_result.objects[0].properties["geo"]
            
            # Extraer coordenadas del GeoCoordinate
            if hasattr(prop_geo, 'latitude') and hasattr(prop_geo, 'longitude'):
                # Si ya es un GeoCoordinate de Weaviate
                lat = prop_geo.latitude
                lon = prop_geo.longitude
            elif isinstance(prop_geo, dict):
                # Si es un diccionario
                lat = prop_geo["latitude"]
                lon = prop_geo["longitude"]
            else:
                raise ValueError("Formato de coordenadas no reconocido")
            
            # Construir filtros para POIs
            filters = Filter.by_property("geo").within_geo_range(
                coordinate=QueryGeo(latitude=lat, longitude=lon),
                distance=poi_request.radius
            )
            
            # Agregar filtro de categoría si se especifica
            if poi_request.category:
                filters = filters & Filter.by_property("category").equal(poi_request.category)
            
            # Buscar POIs usando fetch_objects con filtros
            poi_result = poi_col.query.fetch_objects(
                limit=poi_request.limit,
                filters=filters,
                return_properties=["name", "category", "rating", "source", "geo", "search_corpus"]
            )
            
            # Convertir resultados a objetos POI
            pois = []
            for obj in poi_result.objects:
                try:
                    poi_data = dict(obj.properties)
                    # Convertir geo coordinates si es necesario
                    if poi_data.get("geo"):
                        geo_data = poi_data["geo"]
                        # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                        if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                            poi_data["geo"] = GeoCoordinate(
                                latitude=geo_data.latitude,
                                longitude=geo_data.longitude
                            )
                        # Si es un diccionario, convertir desde diccionario
                        elif isinstance(geo_data, dict):
                            poi_data["geo"] = GeoCoordinate(
                                latitude=geo_data["latitude"],
                                longitude=geo_data["longitude"]
                            )
                    pois.append(POI(**poi_data))
                except Exception as e:
                    logger.warning(f"Error convirtiendo POI: {e}")
                    continue
            
            return POISearchResponse(
                pois=pois,
                property_id=poi_request.property_id,
                category=poi_request.category,
                radius=poi_request.radius
            )
            
        except Exception as e:
            logger.error(f"Error buscando POIs: {e}")
            raise
    
    def _get_pois_by_category(self, category: str) -> List[POI]:
        """Obtiene todos los POIs de una categoría específica"""
        try:
            if not category:
                return []
                
            self._ensure_connection()
            
            poi_col = self.client.collections.get("POI")
            
            # Buscar POIs por categoría
            category_filter = Filter.by_property("category").equal(category)
            result = poi_col.query.fetch_objects(
                limit=50,  # Máximo 50 POIs
                filters=category_filter,
                return_properties=["name", "category", "rating", "source", "geo", "search_corpus"]
            )
            
            # Convertir resultados a objetos POI
            pois = []
            for obj in result.objects:
                try:
                    poi_data = dict(obj.properties)
                    # Convertir geo coordinates si es necesario
                    if poi_data.get("geo"):
                        geo_data = poi_data["geo"]
                        # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                        if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                            poi_data["geo"] = GeoCoordinate(
                                latitude=geo_data.latitude,
                                longitude=geo_data.longitude
                            )
                        # Si es un diccionario, convertir desde diccionario
                        elif isinstance(geo_data, dict):
                            poi_data["geo"] = GeoCoordinate(
                                latitude=geo_data["latitude"],
                                longitude=geo_data["longitude"]
                            )
                    pois.append(POI(**poi_data))
                except Exception as e:
                    logger.warning(f"Error convirtiendo POI: {e}")
                    continue
            
            return pois
            
        except Exception as e:
            logger.error(f"Error obteniendo POIs por categoría {category}: {e}")
            return []
    
    def compare_properties(self, compare_request: PropertyCompareRequest) -> PropertyCompareResponse:
        """Compara propiedades y genera tabla de comparación con pros/cons"""
        try:
            self._ensure_connection()
            
            # Obtener colección de propiedades
            prop_col = self.client.collections.get("Property")
            
            # Obtener todas las propiedades
            properties = []
            for property_id in compare_request.property_ids:
                result = prop_col.query.bm25(
                    query=property_id,
                    limit=1,
                    return_properties=[
                        "zpid", "address", "city", "state", "zipcode",
                        "price", "bedrooms", "bathrooms", "living_area", 
                        "year_built", "lot_size", "description", "features",
                        "neighborhood_text", "geo", "search_corpus"
                    ]
                )
                
                if result.objects and result.objects[0].properties["zpid"] == property_id:
                    prop_data = dict(result.objects[0].properties)
                    # Convertir geo coordinates si es necesario
                    if prop_data.get("geo"):
                        geo_data = prop_data["geo"]
                        # Si ya es un GeoCoordinate de Weaviate, convertir a nuestro modelo
                        if hasattr(geo_data, 'latitude') and hasattr(geo_data, 'longitude'):
                            prop_data["geo"] = GeoCoordinate(
                                latitude=geo_data.latitude,
                                longitude=geo_data.longitude
                            )
                        # Si es un diccionario, convertir desde diccionario
                        elif isinstance(geo_data, dict):
                            prop_data["geo"] = GeoCoordinate(
                                latitude=geo_data["latitude"],
                                longitude=geo_data["longitude"]
                            )
                    properties.append(Property(**prop_data))
            
            if len(properties) != len(compare_request.property_ids):
                raise ValueError("No se encontraron todas las propiedades especificadas")
            
            # Crear tabla de comparación
            comparison_table = {
                "address": [p.address for p in properties],
                "city": [p.city for p in properties],
                "price": [p.price for p in properties],
                "bedrooms": [p.bedrooms for p in properties],
                "bathrooms": [p.bathrooms for p in properties],
                "living_area": [p.living_area for p in properties],
                "year_built": [p.year_built for p in properties],
                "lot_size": [p.lot_size for p in properties],
                "neighborhood": [p.neighborhood_text for p in properties]
            }
            
            # Generar pros y contras usando OpenAI
            pros_cons = {}
            try:
                for prop in properties:
                    pros, cons = self._generate_pros_cons(prop, properties)
                    pros_cons[prop.zpid] = {"pros": pros, "cons": cons}
            except Exception as e:
                logger.warning(f"Error generando pros/cons: {e}")
                # Fallback: pros/cons básicos
                for prop in properties:
                    pros_cons[prop.zpid] = {
                        "pros": ["Ubicación accesible", "Precio competitivo"],
                        "cons": ["Información limitada disponible"]
                    }
            
            return PropertyCompareResponse(
                properties=properties,
                comparison_table=comparison_table,
                pros_cons=pros_cons
            )
            
        except Exception as e:
            logger.error(f"Error comparando propiedades: {e}")
            raise
    
    def _generate_pros_cons(self, property_obj: Property, all_properties: List[Property]) -> tuple:
        """Genera pros y contras para una propiedad usando OpenAI"""
        try:
            # Crear contexto de comparación
            context = f"Propiedad: {property_obj.address}, {property_obj.city}\n"
            context += f"Precio: ${property_obj.price:,}\n"
            context += f"Habitaciones: {property_obj.bedrooms}, Baños: {property_obj.bathrooms}\n"
            context += f"Área: {property_obj.living_area} sqft\n"
            context += f"Año: {property_obj.year_built}\n"
            
            # Agregar contexto de otras propiedades para comparación
            other_props = [p for p in all_properties if p.zpid != property_obj.zpid]
            if other_props:
                context += "\nOtras propiedades en comparación:\n"
                for prop in other_props:
                    context += f"- {prop.address}: ${prop.price:,}, {prop.bedrooms}br/{prop.bathrooms}ba, {prop.living_area}sqft\n"
            
            prompt = f"""
            Analiza la siguiente propiedad inmobiliaria y genera 3 pros y 3 contras específicos basados en sus características y comparación con otras propiedades similares.
            
            {context}
            
            Responde en formato JSON:
            {{
                "pros": ["pro1", "pro2", "pro3"],
                "cons": ["con1", "con2", "con3"]
            }}
            
            Los pros y contras deben ser específicos, objetivos y útiles para un comprador potencial.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result["pros"], result["cons"]
            
        except Exception as e:
            logger.warning(f"Error generando pros/cons con OpenAI: {e}")
            # Fallback básico
            pros = ["Ubicación accesible", "Precio competitivo", "Características básicas"]
            cons = ["Información limitada", "Requiere más investigación", "Comparación necesaria"]
            return pros, cons
    
    def close(self) -> None:
        """Cierra la conexión con Weaviate"""
        if self.client:
            try:
                self.client.close()
                logger.info("Conexión con Weaviate cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando conexión: {e}")
    
    def is_connected(self) -> bool:
        """Verifica si la conexión está activa"""
        try:
            return self.client is not None and self.client.is_ready()
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()