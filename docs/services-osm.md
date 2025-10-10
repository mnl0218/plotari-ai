# Servicios de OpenStreetMap (OSM)

## 📋 Descripción General

Los servicios OSM proporcionan integración con OpenStreetMap a través de la Overpass API para obtener puntos de interés (POIs) alrededor de propiedades. Esta funcionalidad enriquece los datos de propiedades con información sobre amenidades cercanas.

---

## 🏗️ Arquitectura

### Componentes Principales

```
OSMService (Orquestador Principal)
    │
    ├─── OSMConnectionService (Gestión de Conexiones)
    │
    └─── OSMPOIService (Búsqueda de POIs)
```

### Patrones de Diseño

- **Service-Oriented Architecture (SOA)**: Separación clara de responsabilidades
- **Dependency Injection**: Servicios inyectables y testeables
- **Interface Segregation**: Interfaces claras para cada servicio
- **Context Manager**: Gestión automática de recursos

---

## 📦 Servicios

### 1. OSMService (Orquestador Principal)

**Ubicación**: `src/services/osm/osm_service.py`

**Descripción**: Servicio principal que orquesta todas las operaciones de OSM.

#### Métodos Principales

##### `search_pois_around_location()`
Busca POIs alrededor de una ubicación geográfica.

**Parámetros**:
- `latitude` (float): Latitud del punto central
- `longitude` (float): Longitud del punto central
- `radius` (int): Radio de búsqueda en metros (default: 1000)
- `amenity_type` (str, opcional): Tipo de amenidad a filtrar
- `limit` (int): Número máximo de resultados (default: 50)

**Retorna**: `List[POI]`

**Ejemplo**:
```python
from src.services.osm import OSMService

osm = OSMService()

# Buscar restaurantes en 500m
restaurants = osm.search_pois_around_location(
    latitude=25.7617,
    longitude=-80.1918,
    radius=500,
    amenity_type="restaurant",
    limit=20
)

for poi in restaurants:
    print(f"{poi.name} - {poi.category}")
```

##### `search_pois_in_area()`
Busca POIs dentro de un bounding box rectangular.

**Parámetros**:
- `south` (float): Latitud sur
- `west` (float): Longitud oeste
- `north` (float): Latitud norte
- `east` (float): Longitud este
- `amenity_type` (str, opcional): Tipo de amenidad
- `limit` (int): Número máximo de resultados

**Retorna**: `List[POI]`

**Ejemplo**:
```python
# Buscar escuelas en un área específica
schools = osm.search_pois_in_area(
    south=25.76,
    west=-80.20,
    north=25.77,
    east=-80.19,
    amenity_type="school"
)
```

##### `is_service_available()`
Verifica si el servicio de Overpass API está disponible.

**Retorna**: `bool`

---

### 2. OSMConnectionService

**Ubicación**: `src/services/osm/connection_service.py`

**Descripción**: Gestiona las conexiones HTTP con la Overpass API.

#### Atributos

- `base_url` (str): URL del endpoint de Overpass API
- `DEFAULT_OVERPASS_URL` (str): URL pública por defecto

#### Métodos

##### `query()`
Ejecuta una consulta en formato Overpass QL.

**Parámetros**:
- `overpass_query` (str): Query en formato Overpass QL
- `timeout` (int): Timeout de la petición en segundos (default: 30)

**Retorna**: `Dict[str, Any]` - Respuesta JSON de la API

**Excepciones**:
- `requests.exceptions.RequestException`: Si falla la petición
- `ValueError`: Si la respuesta no es JSON válido

**Ejemplo**:
```python
from src.services.osm import OSMConnectionService

conn = OSMConnectionService()

query = """
[out:json][timeout:25];
node["amenity"="restaurant"](around:500,25.7617,-80.1918);
out body;
"""

data = conn.query(query)
print(f"Elementos encontrados: {len(data['elements'])}")
```

##### `is_available()`
Verifica disponibilidad de la API.

**Retorna**: `bool`

---

### 3. OSMPOIService

**Ubicación**: `src/services/osm/poi_service.py`

**Descripción**: Maneja búsquedas de POIs y conversión de datos OSM al modelo POI de Plotari.

#### Métodos

##### `search_pois_by_radius()`
Busca POIs usando búsqueda radial.

**Parámetros**:
- `latitude` (float): Latitud del centro
- `longitude` (float): Longitud del centro
- `radius` (int): Radio en metros
- `amenity_type` (str, opcional): Tipo de amenidad
- `limit` (int): Máximo de resultados

**Retorna**: `List[POI]`

##### `search_pois_by_bbox()`
Busca POIs en un bounding box.

**Parámetros**: Similar a búsqueda radial pero con coordenadas de bbox.

**Retorna**: `List[POI]`

#### Conversión de Datos

El servicio convierte datos de OSM al modelo `POI` existente:

**Mapeo OSM → POI**:
```python
POI(
    name=osm_tags["name"],                    # Nombre del POI
    category=osm_tags["amenity"],             # Tipo de amenidad
    rating=None,                              # OSM no tiene ratings
    source="OpenStreetMap",                   # Fuente de datos
    geo=GeoCoordinate(lat, lon),             # Coordenadas
    search_corpus=corpus_generado            # Texto para búsqueda
)
```

**Search Corpus incluye**:
- Nombre del POI
- Tipo de amenidad
- Cocina (si es restaurante)
- Marca (si aplica)
- Dirección

---

## 🎯 Tipos de Amenidades Soportadas

### Comida & Bebida
- `restaurant` - Restaurantes
- `cafe` - Cafeterías
- `bar` - Bares
- `fast_food` - Comida rápida
- `pub` - Pubs

### Educación
- `school` - Escuelas
- `university` - Universidades
- `college` - Colleges
- `kindergarten` - Guarderías
- `library` - Bibliotecas

### Salud
- `hospital` - Hospitales
- `clinic` - Clínicas
- `pharmacy` - Farmacias
- `dentist` - Dentistas
- `doctors` - Consultorios

### Transporte
- `parking` - Estacionamientos
- `fuel` - Gasolineras
- `charging_station` - Estaciones de carga
- `bus_station` - Estaciones de bus

### Otros
- `bank` - Bancos
- `atm` - Cajeros
- `supermarket` - Supermercados
- `gym` - Gimnasios
- `park` - Parques

**Ver lista completa**: [osm-overpass-analysis.md](./osm-overpass-analysis.md#tipos-de-amenidades-disponibles)

---

## 💡 Casos de Uso

### 1. Enriquecer Detalles de Propiedad

```python
from src.services.osm import OSMService

def enrich_property_with_pois(property):
    osm = OSMService()
    
    # Buscar amenidades cercanas
    restaurants = osm.search_pois_around_location(
        latitude=property.geo.latitude,
        longitude=property.geo.longitude,
        radius=1000,
        amenity_type="restaurant"
    )
    
    schools = osm.search_pois_around_location(
        latitude=property.geo.latitude,
        longitude=property.geo.longitude,
        radius=2000,
        amenity_type="school"
    )
    
    return {
        "property": property,
        "nearby_restaurants": len(restaurants),
        "nearby_schools": len(schools),
        "pois": restaurants + schools
    }
```

### 2. Scoring de Ubicación

```python
def calculate_location_score(latitude, longitude):
    osm = OSMService()
    
    score = 0
    
    # Buscar diferentes tipos de amenidades
    amenities = {
        "restaurant": 1,
        "school": 10,
        "hospital": 15,
        "supermarket": 6,
        "park": 5
    }
    
    for amenity, weight in amenities.items():
        pois = osm.search_pois_around_location(
            latitude=latitude,
            longitude=longitude,
            radius=1000,
            amenity_type=amenity,
            limit=10
        )
        score += len(pois) * weight
    
    return score
```

### 3. Comparación de Vecindarios

```python
def compare_neighborhoods(property_a, property_b):
    osm = OSMService()
    
    pois_a = osm.search_pois_around_location(
        latitude=property_a.geo.latitude,
        longitude=property_a.geo.longitude,
        radius=500
    )
    
    pois_b = osm.search_pois_around_location(
        latitude=property_b.geo.latitude,
        longitude=property_b.geo.longitude,
        radius=500
    )
    
    return {
        "property_a_pois": len(pois_a),
        "property_b_pois": len(pois_b),
        "winner": "A" if len(pois_a) > len(pois_b) else "B"
    }
```

---

## 🔧 Configuración

### Variables de Entorno (Opcional)

```bash
# URL personalizada de Overpass API (opcional)
# Por defecto usa: https://overpass-api.de/api/interpreter
OSM_OVERPASS_URL=https://your-custom-overpass-instance.com/api/interpreter
```

### Inicialización

**Inicialización Simple**:
```python
from src.services.osm import OSMService

osm = OSMService()
```

**Con Configuración Personalizada**:
```python
from src.services.osm import OSMService, OSMConnectionService

# Usar instancia propia de Overpass
conn = OSMConnectionService(
    base_url="https://custom-overpass.com/api/interpreter"
)

osm = OSMService(connection_service=conn)
```

**Como Context Manager**:
```python
with OSMService() as osm:
    pois = osm.search_pois_around_location(
        latitude=25.7617,
        longitude=-80.1918,
        radius=1000
    )
```

---

## ⚡ Performance

### Benchmarks Típicos

- Búsqueda de restaurantes (500m): 1-3s
- Búsqueda de escuelas (1km): 2-4s
- Búsqueda sin filtro (1km): 5-10s (puede timeout)

### Optimizaciones

1. **Limitar Radio**: Radios grandes pueden causar timeout
   - Recomendado: 500-1500m
   - Máximo: 5000m

2. **Filtrar por Amenidad**: Siempre especificar `amenity_type` cuando sea posible

3. **Limitar Resultados**: Usar parámetro `limit` apropiado

4. **Caché de Resultados**: Considerar cachear resultados de POIs

---

## 🐛 Manejo de Errores

### Errores Comunes

#### Timeout
```python
import requests

try:
    pois = osm.search_pois_around_location(...)
except requests.exceptions.Timeout:
    print("Query timeout - reduce radius or add filters")
```

#### API No Disponible
```python
if not osm.is_service_available():
    print("Overpass API is not available")
    # Usar fuente alternativa de datos
```

#### Sin Resultados
```python
pois = osm.search_pois_around_location(...)
if not pois:
    print("No POIs found in this area")
```

---

## 🧪 Testing

### Ejemplo de Test

```python
import pytest
from src.services.osm import OSMService

def test_search_pois_around_location():
    osm = OSMService()
    
    pois = osm.search_pois_around_location(
        latitude=25.7617,
        longitude=-80.1918,
        radius=1000,
        amenity_type="restaurant",
        limit=10
    )
    
    assert isinstance(pois, list)
    assert len(pois) <= 10
    
    if pois:
        poi = pois[0]
        assert hasattr(poi, 'name')
        assert hasattr(poi, 'category')
        assert poi.source == "OpenStreetMap"
```

---

## 🔗 Integración con Otros Servicios

### Con Property Service

```python
from src.services.weaviate import WeaviatePropertyService
from src.services.osm import OSMService

# Obtener propiedad
property_service = WeaviatePropertyService(...)
property = property_service.get_property_by_id("zpid123")

# Enriquecer con POIs
osm = OSMService()
pois = osm.search_pois_around_location(
    latitude=property.geo.latitude,
    longitude=property.geo.longitude,
    radius=1000
)
```

### Con Chatbot Service

```python
from src.services.chatbot import ChatbotService
from src.services.osm import OSMService

class EnhancedChatbotService(ChatbotService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.osm_service = OSMService()
    
    def search_properties_with_pois(self, query):
        # Buscar propiedades
        properties = self.search_properties(query)
        
        # Enriquecer con POIs
        for prop in properties:
            prop.nearby_pois = self.osm_service.search_pois_around_location(
                latitude=prop.geo.latitude,
                longitude=prop.geo.longitude,
                radius=500
            )
        
        return properties
```

---

## 📊 Modelo de Datos

### POI Model (Existente)

```python
class POI(BaseModel):
    name: str                           # Nombre del POI
    category: str                       # Categoría/tipo de amenidad
    rating: Optional[float]             # Rating (0-5)
    source: Optional[str]               # Fuente de datos
    geo: GeoCoordinate                  # Coordenadas geográficas
    search_corpus: Optional[str]        # Texto para búsqueda
```

### GeoCoordinate Model

```python
class GeoCoordinate(BaseModel):
    latitude: float                     # -90 a 90
    longitude: float                    # -180 a 180
```

---

## 📝 Mejores Prácticas

### 1. Siempre Especificar Tipo de Amenidad

❌ **Evitar**:
```python
# Puede ser lento y generar timeout
pois = osm.search_pois_around_location(
    latitude=25.7617,
    longitude=-80.1918,
    radius=5000  # Radio muy grande sin filtro
)
```

✅ **Recomendado**:
```python
# Específico y rápido
pois = osm.search_pois_around_location(
    latitude=25.7617,
    longitude=-80.1918,
    radius=1000,
    amenity_type="restaurant"
)
```

### 2. Usar Context Manager para Recursos

✅ **Recomendado**:
```python
with OSMService() as osm:
    pois = osm.search_pois_around_location(...)
```

### 3. Validar Disponibilidad

✅ **Recomendado**:
```python
osm = OSMService()

if osm.is_service_available():
    pois = osm.search_pois_around_location(...)
else:
    # Usar fuente alternativa
    pois = get_pois_from_cache()
```

### 4. Manejar Errores Gracefully

✅ **Recomendado**:
```python
try:
    pois = osm.search_pois_around_location(...)
except requests.exceptions.Timeout:
    logger.warning("OSM timeout, using cached data")
    pois = []
except Exception as e:
    logger.error(f"OSM error: {e}")
    pois = []
```

---

## 🚀 Próximos Pasos

### Mejoras Futuras

- [ ] Sistema de caché para resultados de POIs
- [ ] Soporte para búsqueda por múltiples tipos de amenidad
- [ ] Enriquecimiento de POIs con datos adicionales
- [ ] Integración con endpoints de API
- [ ] Sincronización de POIs a Weaviate
- [ ] Analytics de amenidades más buscadas

---

## 📚 Referencias

- **Overpass API**: https://overpass-api.de/
- **Overpass QL**: https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
- **OSM Wiki**: https://wiki.openstreetmap.org/
- **Análisis Completo**: [osm-overpass-analysis.md](./osm-overpass-analysis.md)

---

## 📅 Versión

**Versión Actual**: 1.0.0  
**Última Actualización**: Octubre 2025  
**Estado**: ✅ Producción

---

**Servicio desarrollado siguiendo los patrones de arquitectura de Plotari AI**

