"""
Script de prueba para el nuevo servicio OSM
Verifica que todos los componentes funcionan correctamente
"""
from src.services.osm import OSMService
from pprint import pprint
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_service_availability():
    """Prueba 1: Verificar disponibilidad del servicio"""
    print("\n" + "="*80)
    print("PRUEBA 1: Verificar disponibilidad del servicio OSM")
    print("="*80)
    
    osm = OSMService()
    
    if osm.is_service_available():
        print("✅ Servicio OSM disponible")
        return True
    else:
        print("❌ Servicio OSM no disponible")
        return False


def test_search_restaurants():
    """Prueba 2: Buscar restaurantes en Miami Beach"""
    print("\n" + "="*80)
    print("PRUEBA 2: Buscar restaurantes en Miami Beach (500m)")
    print("="*80)
    
    osm = OSMService()
    
    # Miami Beach coordinates
    lat, lon = 25.7907, -80.1300
    
    print(f"📍 Ubicación: {lat}, {lon}")
    print(f"🔍 Buscando restaurantes en radio de 500m...")
    
    pois = osm.search_pois_around_location(
        latitude=lat,
        longitude=lon,
        radius=500,
        amenity_type="restaurant",
        limit=10
    )
    
    print(f"\n✅ Encontrados: {len(pois)} restaurantes")
    
    if pois:
        print("\n📋 Primeros 5 resultados:")
        for i, poi in enumerate(pois[:5], 1):
            print(f"\n{i}. {poi.name}")
            print(f"   Categoría: {poi.category}")
            print(f"   Ubicación: ({poi.geo.latitude}, {poi.geo.longitude})")
            print(f"   Fuente: {poi.source}")
            if poi.search_corpus:
                print(f"   Corpus: {poi.search_corpus[:100]}...")
    
    return pois


def test_search_schools():
    """Prueba 3: Buscar escuelas en Downtown Miami"""
    print("\n" + "="*80)
    print("PRUEBA 3: Buscar escuelas en Downtown Miami (2km)")
    print("="*80)
    
    osm = OSMService()
    
    # Downtown Miami
    lat, lon = 25.7617, -80.1918
    
    print(f"📍 Ubicación: {lat}, {lon}")
    print(f"🔍 Buscando escuelas en radio de 2km...")
    
    pois = osm.search_pois_around_location(
        latitude=lat,
        longitude=lon,
        radius=2000,
        amenity_type="school",
        limit=15
    )
    
    print(f"\n✅ Encontradas: {len(pois)} escuelas")
    
    if pois:
        print("\n📚 Escuelas encontradas:")
        for poi in pois[:10]:
            print(f"  • {poi.name}")
    
    return pois


def test_search_multiple_amenities():
    """Prueba 4: Buscar múltiples tipos de amenidades"""
    print("\n" + "="*80)
    print("PRUEBA 4: Buscar múltiples tipos de amenidades")
    print("="*80)
    
    osm = OSMService()
    
    lat, lon = 25.7617, -80.1918
    
    amenities = ["restaurant", "cafe", "school", "bank", "pharmacy"]
    
    results = {}
    
    for amenity in amenities:
        print(f"\n🔍 Buscando {amenity}...")
        
        try:
            pois = osm.search_pois_around_location(
                latitude=lat,
                longitude=lon,
                radius=1000,
                amenity_type=amenity,
                limit=10
            )
            
            results[amenity] = len(pois)
            print(f"   ✅ Encontrados: {len(pois)}")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            results[amenity] = 0
    
    print("\n📊 Resumen:")
    print("-" * 40)
    for amenity, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{amenity:15} : {count:3} POIs")
    
    return results


def test_bbox_search():
    """Prueba 5: Búsqueda por bounding box"""
    print("\n" + "="*80)
    print("PRUEBA 5: Búsqueda por Bounding Box")
    print("="*80)
    
    osm = OSMService()
    
    # Área pequeña en Downtown Miami
    south, west = 25.7600, -80.1950
    north, east = 25.7650, -80.1900
    
    print(f"📦 BBox: ({south},{west}) → ({north},{east})")
    print(f"🔍 Buscando cafeterías...")
    
    pois = osm.search_pois_in_area(
        south=south,
        west=west,
        north=north,
        east=east,
        amenity_type="cafe",
        limit=10
    )
    
    print(f"\n✅ Encontradas: {len(pois)} cafeterías")
    
    if pois:
        print("\n☕ Cafeterías encontradas:")
        for poi in pois[:5]:
            print(f"  • {poi.name}")
    
    return pois


def test_context_manager():
    """Prueba 6: Uso como context manager"""
    print("\n" + "="*80)
    print("PRUEBA 6: Uso como Context Manager")
    print("="*80)
    
    with OSMService() as osm:
        pois = osm.search_pois_around_location(
            latitude=25.7617,
            longitude=-80.1918,
            radius=500,
            amenity_type="bank",
            limit=5
        )
        
        print(f"✅ Encontrados {len(pois)} bancos usando context manager")
        
        return pois


def test_model_validation():
    """Prueba 7: Validar que los POIs cumplen con el modelo"""
    print("\n" + "="*80)
    print("PRUEBA 7: Validación del Modelo POI")
    print("="*80)
    
    osm = OSMService()
    
    pois = osm.search_pois_around_location(
        latitude=25.7617,
        longitude=-80.1918,
        radius=500,
        amenity_type="restaurant",
        limit=5
    )
    
    if pois:
        poi = pois[0]
        
        print("✅ Validando estructura del modelo POI:")
        print(f"   ✓ name: {poi.name} (type: {type(poi.name).__name__})")
        print(f"   ✓ category: {poi.category} (type: {type(poi.category).__name__})")
        print(f"   ✓ rating: {poi.rating} (type: {type(poi.rating).__name__})")
        print(f"   ✓ source: {poi.source} (type: {type(poi.source).__name__})")
        print(f"   ✓ geo.latitude: {poi.geo.latitude} (type: {type(poi.geo.latitude).__name__})")
        print(f"   ✓ geo.longitude: {poi.geo.longitude} (type: {type(poi.geo.longitude).__name__})")
        print(f"   ✓ search_corpus: {poi.search_corpus[:50]}... (len: {len(poi.search_corpus or '')})")
        
        # Validar que cumple con restricciones del modelo
        assert len(poi.name) <= 200, "Name exceeds max_length"
        assert len(poi.category) <= 100, "Category exceeds max_length"
        if poi.rating:
            assert 0 <= poi.rating <= 5, "Rating out of range"
        assert -90 <= poi.geo.latitude <= 90, "Latitude out of range"
        assert -180 <= poi.geo.longitude <= 180, "Longitude out of range"
        if poi.search_corpus:
            assert len(poi.search_corpus) <= 2000, "Search corpus exceeds max_length"
        
        print("\n✅ Modelo POI válido - Todas las validaciones pasaron")
    else:
        print("⚠️  No se encontraron POIs para validar")
    
    return True


if __name__ == "__main__":
    print("\n" + "🗺️ " * 40)
    print("SUITE DE PRUEBAS - SERVICIO OSM")
    print("🗺️ " * 40)
    
    try:
        # Ejecutar todas las pruebas
        results = {
            "availability": test_service_availability(),
            "restaurants": test_search_restaurants(),
            "schools": test_search_schools(),
            "multiple": test_search_multiple_amenities(),
            "bbox": test_bbox_search(),
            "context_manager": test_context_manager(),
            "validation": test_model_validation()
        }
        
        print("\n" + "="*80)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*80)
        
        for test_name, result in results.items():
            status = "✅" if result else "⚠️ "
            result_text = "PASÓ" if result else "SIN RESULTADOS"
            print(f"{status} {test_name:20} : {result_text}")
        
        print("\n" + "="*80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*80)
        
        print("\n💡 Próximos pasos:")
        print("   1. Revisar docs/services-osm.md para documentación completa")
        print("   2. Integrar con endpoints de API")
        print("   3. Implementar caché de resultados")
        print("   4. Integrar con ChatbotService")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

