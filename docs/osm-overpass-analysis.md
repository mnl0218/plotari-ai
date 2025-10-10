# Análisis de OpenStreetMap con Overpass API

## 📋 Resumen de Pruebas

Este documento resume las pruebas realizadas para consumir OpenStreetMap usando Overpass API y evaluar su integración con Plotari AI.

---

## ✅ Resultados de Pruebas

### 1. Conectividad con API
- ✅ **API accesible**: https://overpass-api.de/api/interpreter
- ✅ **Respuestas en JSON**: Formato estructurado y fácil de parsear
- ⚠️ **Timeouts**: Consultas muy amplias pueden generar timeout (>1km con todos los amenities)
- ✅ **Solución**: Limitar radio o filtrar por tipo de amenidad

### 2. Tipos de Consultas Probadas

#### ✅ Consulta por Radio (around)
```python
# Ejemplo: Restaurantes en 500m alrededor de un punto
lat, lon = 25.7907, -80.1300
radius = 500  # metros
amenity_type = "restaurant"
```
**Resultado**: 34 restaurantes encontrados en Miami Beach

#### ✅ Consulta por Bounding Box
```python
# Área rectangular definida por coordenadas
south, west = 25.7600, -80.1950
north, east = 25.7650, -80.1900
```
**Uso**: Ideal para búsquedas en áreas específicas

---

## 📊 Estructura de Datos Devueltos

### Respuesta Base
```json
{
  "version": 0.6,
  "generator": "Overpass API 0.7.62.8",
  "osm3s": {
    "timestamp_osm_base": "2025-10-10T12:59:43Z",
    "copyright": "..."
  },
  "elements": [...]
}
```

### Estructura de Cada Elemento (POI)
```json
{
  "type": "node",           // node, way, o relation
  "id": 2180354779,         // ID único en OSM
  "lat": 25.7921566,        // Latitud
  "lon": -80.1299504,       // Longitud
  "tags": {                 // Metadatos del POI
    "amenity": "restaurant",
    "name": "Dolce",
    "cuisine": "italian",
    "phone": "+17869752550",
    "website": "https://...",
    "addr:postcode": "33139",
    "addr:street": "Collins Avenue",
    "addr:housenumber": "1732",
    "addr:city": "Miami Beach",
    "opening_hours": "13:00-03:00"
  }
}
```

---

## 🏷️ Tags Comunes Disponibles

### Información Básica
- `amenity`: Tipo de amenidad (restaurant, school, hospital, etc.)
- `name`: Nombre del lugar
- `name:es`: Nombre en español (si existe)

### Ubicación
- `addr:street`: Calle
- `addr:housenumber`: Número
- `addr:city`: Ciudad
- `addr:postcode`: Código postal
- `addr:state`: Estado

### Detalles Específicos
- `cuisine`: Tipo de comida (para restaurantes)
- `phone`: Teléfono
- `website`: Sitio web
- `opening_hours`: Horarios
- `capacity`: Capacidad
- `outdoor_seating`: Asientos al aire libre
- `level`: Nivel/piso

### Otros
- `brand`: Marca (ej: Cheesecake Factory)
- `brand:wikidata`: ID de Wikidata
- `internet_access`: Acceso a internet

---

## 🎯 Tipos de Amenidades Disponibles

### 🍽️ Comida & Bebida
- `restaurant` - Restaurantes ✅ Probado
- `cafe` - Cafeterías
- `bar` - Bares
- `fast_food` - Comida rápida
- `pub` - Pubs

### 🎓 Educación
- `school` - Escuelas ✅ Probado
- `university` - Universidades
- `college` - Colleges
- `kindergarten` - Guarderías
- `library` - Bibliotecas

### 🏥 Salud
- `hospital` - Hospitales ✅ Probado
- `clinic` - Clínicas
- `pharmacy` - Farmacias
- `dentist` - Dentistas
- `doctors` - Consultorios médicos

### 🚗 Transporte
- `parking` - Estacionamientos
- `fuel` - Gasolineras
- `charging_station` - Estaciones de carga
- `bus_station` - Estaciones de bus
- `taxi` - Paradas de taxi

### 💰 Finanzas
- `bank` - Bancos
- `atm` - Cajeros automáticos
- `bureau_de_change` - Casa de cambio

### 🎭 Entretenimiento
- `cinema` - Cines
- `theatre` - Teatros
- `nightclub` - Discotecas
- `casino` - Casinos
- `arts_centre` - Centros de arte

### 🛒 Compras
- `marketplace` - Mercados
- `supermarket` - Supermercados
- `mall` - Centros comerciales

### 🏛️ Servicios
- `police` - Policía
- `fire_station` - Bomberos
- `post_office` - Correos
- `townhall` - Ayuntamiento

### Otros
- `gym` - Gimnasios
- `park` - Parques
- `swimming_pool` - Piscinas
- `playground` - Parques infantiles

---

## 🔍 Casos de Uso para Plotari AI

### 1. Enriquecer Detalles de Propiedades
**Problema**: Necesitamos mostrar POIs cercanos a una propiedad

**Solución con OSM**:
```python
# Para cada propiedad
property_lat = property.latitude
property_lon = property.longitude

# Buscar POIs relevantes en 1km
pois = overpass.query_by_radius(
    lat=property_lat,
    lon=property_lon,
    radius=1000,
    amenity_type="restaurant"  # o school, hospital, etc.
)
```

**Beneficios**:
- ✅ Datos gratuitos y actualizados por la comunidad
- ✅ Cobertura global
- ✅ Información detallada (horarios, teléfono, web)

### 2. Búsqueda por Proximidad a Amenidades
**Problema**: Usuario quiere propiedades "cerca de escuelas"

**Solución**:
1. Detectar intención: "cerca de escuelas"
2. Buscar todas las escuelas en el área de interés
3. Filtrar propiedades cercanas a esas escuelas

### 3. Comparación de Vecindarios
**Problema**: Comparar dos propiedades según amenidades cercanas

**Solución**:
```python
# Propiedad A
pois_a = get_pois_around(property_a, radius=500)

# Propiedad B  
pois_b = get_pois_around(property_b, radius=500)

# Comparar cantidad y tipo de amenidades
comparison = compare_amenities(pois_a, pois_b)
```

### 4. Scoring de Ubicaciones
**Scoring basado en amenidades**:
- Restaurantes: +2 puntos c/u
- Escuelas: +5 puntos c/u
- Hospitales: +10 puntos c/u
- Transporte público: +3 puntos c/u

---

## 💡 Ventajas vs Desventajas

### ✅ Ventajas

1. **Gratuito y Open Source**
   - Sin costos de API
   - Sin límites de consultas (respetando fair use)

2. **Datos Ricos**
   - Múltiples tags descriptivos
   - Información actualizada por comunidad global
   - Cobertura mundial

3. **Flexibilidad**
   - Queries personalizadas (Overpass QL)
   - Búsqueda por radio o bounding box
   - Filtros múltiples

4. **Integración Sencilla**
   - API REST simple
   - Respuestas en JSON
   - No requiere autenticación

### ⚠️ Desventajas

1. **Calidad Variable**
   - Depende de contribuciones de usuarios
   - Algunas áreas mejor mapeadas que otras
   - Datos pueden estar desactualizados

2. **Performance**
   - Consultas grandes pueden ser lentas
   - Timeouts en queries complejas
   - Necesita optimización de queries

3. **Complejidad de Queries**
   - Overpass QL tiene curva de aprendizaje
   - Necesita conocer estructura de datos OSM

4. **Sin Garantías**
   - No hay SLA
   - Servidor público puede estar caído
   - Recomendable tener instancia propia para producción

---

## 🚀 Próximos Pasos

### Fase 1: Integración Básica ✅ (Completado)
- [x] Probar conectividad con API
- [x] Entender estructura de datos
- [x] Identificar tipos de amenidades útiles

### Fase 2: Desarrollo de Servicio ✅ (Completado)
- [x] Crear `OSMService` en `src/services/osm/`
- [x] Crear interfaces para servicios OSM
- [x] Implementar `OSMConnectionService`
- [x] Implementar `OSMPOIService`
- [x] Usar modelo POI existente de Pydantic
- [x] Documentar servicio completo
- [ ] Implementar caché de resultados (Futuro)
- [ ] Endpoints para consultar POIs (Siguiente)

### Fase 3: Integración con Chatbot
- [ ] Integrar con `PropertySearchService`
- [ ] Actualizar `IntentExtractor` para detectar búsquedas por amenidades
- [ ] Enriquecer respuestas del chatbot con POIs

### Fase 4: Analytics
- [ ] Trackear amenidades más buscadas
- [ ] Scoring de propiedades por amenidades
- [ ] Insights de vecindarios

---

## 📝 Ejemplo de Datos Reales

### Restaurante en Miami Beach
```json
{
  "type": "node",
  "id": 2180354779,
  "lat": 25.7921566,
  "lon": -80.1299504,
  "tags": {
    "addr:postcode": "33139",
    "amenity": "restaurant",
    "cuisine": "italian",
    "name": "Dolce",
    "phone": "+17869752550",
    "website": "https://www.dolceitalianrestaurant.com/"
  }
}
```

### Escuela en Miami
```json
{
  "type": "node",
  "id": 358706951,
  "lat": 25.7617662,
  "lon": -80.1942144,
  "tags": {
    "amenity": "school",
    "ele": "3",
    "gnis:feature_id": "291458",
    "name": "Southside School"
  }
}
```

---

## 🔗 Referencias

- **Overpass API**: https://overpass-api.de/
- **Overpass QL Docs**: https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
- **OSM Wiki**: https://wiki.openstreetmap.org/
- **Tag Info**: https://taginfo.openstreetmap.org/ (explorar todos los tags disponibles)
- **Overpass Turbo**: https://overpass-turbo.eu/ (IDE interactivo para probar queries)

---

## 🎓 Conclusiones

1. **Viabilidad**: ✅ OSM con Overpass API es completamente viable para Plotari AI
2. **Uso Recomendado**: Enriquecer propiedades con POIs cercanos
3. **Implementación**: Crear servicio dedicado con caché
4. **Performance**: Optimizar queries y considerar instancia propia para producción

**Estado**: Listo para pasar a Fase 2 (Desarrollo de Servicio)

