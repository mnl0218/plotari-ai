"""
Script de prueba para explorar OpenStreetMap con Overpass API
Este script realiza consultas básicas para entender:
1. Cómo consumir el API por geolocalización
2. Qué tipo de datos devuelve
"""

import requests
import json
from typing import Dict, List, Any
from pprint import pprint


class OverpassAPITester:
    """Cliente de prueba para Overpass API"""
    
    def __init__(self):
        # URL del servidor Overpass API público
        self.base_url = "https://overpass-api.de/api/interpreter"
        
    def query_by_radius(
        self, 
        lat: float, 
        lon: float, 
        radius: int = 1000,
        amenity_type: str = None
    ) -> Dict[str, Any]:
        """
        Consulta POIs alrededor de una coordenada usando radio
        
        Args:
            lat: Latitud
            lon: Longitud
            radius: Radio en metros (default: 1000m = 1km)
            amenity_type: Tipo de amenidad (restaurant, school, hospital, etc.)
        
        Returns:
            Respuesta JSON de Overpass API
        """
        
        # Construir query en Overpass QL
        if amenity_type:
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="{amenity_type}"](around:{radius},{lat},{lon});
              way["amenity"="{amenity_type}"](around:{radius},{lat},{lon});
              relation["amenity"="{amenity_type}"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
        else:
            # Sin filtro, obtener todos los amenities
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"](around:{radius},{lat},{lon});
              way["amenity"](around:{radius},{lat},{lon});
              relation["amenity"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
        
        try:
            response = requests.post(
                self.base_url,
                data={"data": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en request: {e}")
            return {"error": str(e)}
    
    def query_by_bbox(
        self,
        south: float,
        west: float,
        north: float,
        east: float,
        amenity_type: str = None
    ) -> Dict[str, Any]:
        """
        Consulta POIs en un bounding box (área rectangular)
        
        Args:
            south: Latitud sur
            west: Longitud oeste
            north: Latitud norte
            east: Longitud este
            amenity_type: Tipo de amenidad opcional
        
        Returns:
            Respuesta JSON de Overpass API
        """
        
        if amenity_type:
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="{amenity_type}"]({south},{west},{north},{east});
              way["amenity"="{amenity_type}"]({south},{west},{north},{east});
              relation["amenity"="{amenity_type}"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
            """
        else:
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"]({south},{west},{north},{east});
              way["amenity"]({south},{west},{north},{east});
              relation["amenity"]({south},{west},{north},{east});
            );
            out body;
            >;
            out skel qt;
            """
        
        try:
            response = requests.post(
                self.base_url,
                data={"data": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en request: {e}")
            return {"error": str(e)}
    
    def analyze_response(self, data: Dict[str, Any]) -> None:
        """Analiza y muestra información sobre la respuesta"""
        
        if "error" in data:
            print(f"\n❌ Error en respuesta: {data['error']}")
            return
        
        elements = data.get("elements", [])
        
        print("\n" + "="*80)
        print(f"📊 ANÁLISIS DE RESPUESTA")
        print("="*80)
        print(f"\n✅ Total de elementos encontrados: {len(elements)}")
        
        # Contar por tipo
        types_count = {}
        for elem in elements:
            elem_type = elem.get("type", "unknown")
            types_count[elem_type] = types_count.get(elem_type, 0) + 1
        
        print(f"\n📍 Por tipo de elemento:")
        for elem_type, count in types_count.items():
            print(f"  - {elem_type}: {count}")
        
        # Contar amenities
        amenities = {}
        for elem in elements:
            tags = elem.get("tags", {})
            amenity = tags.get("amenity")
            if amenity:
                amenities[amenity] = amenities.get(amenity, 0) + 1
        
        if amenities:
            print(f"\n🏪 Tipos de amenidades encontradas:")
            for amenity, count in sorted(amenities.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {amenity}: {count}")
        
        # Mostrar ejemplos
        print(f"\n📝 Ejemplos de elementos (primeros 3):")
        for i, elem in enumerate(elements[:3], 1):
            print(f"\n--- Ejemplo {i} ---")
            print(f"Type: {elem.get('type')}")
            print(f"ID: {elem.get('id')}")
            if 'lat' in elem and 'lon' in elem:
                print(f"Location: ({elem.get('lat')}, {elem.get('lon')})")
            
            tags = elem.get('tags', {})
            if tags:
                print("Tags:")
                for key, value in list(tags.items())[:5]:  # Solo primeros 5 tags
                    print(f"  - {key}: {value}")


def test_miami_downtown():
    """
    Prueba 1: Buscar amenidades en Downtown Miami
    Coordenadas: 25.7617, -80.1918
    """
    print("\n" + "🌴" * 40)
    print("PRUEBA 1: Downtown Miami - Todos los amenities (1km)")
    print("🌴" * 40)
    
    tester = OverpassAPITester()
    
    # Downtown Miami coordinates
    lat, lon = 25.7617, -80.1918
    
    data = tester.query_by_radius(lat, lon, radius=1000)
    tester.analyze_response(data)
    
    return data


def test_miami_restaurants():
    """
    Prueba 2: Buscar solo restaurantes en Miami Beach
    Coordenadas: 25.7907, -80.1300
    """
    print("\n" + "🍽️" * 40)
    print("PRUEBA 2: Miami Beach - Solo Restaurantes (500m)")
    print("🍽️" * 40)
    
    tester = OverpassAPITester()
    
    # Miami Beach coordinates
    lat, lon = 25.7907, -80.1300
    
    data = tester.query_by_radius(lat, lon, radius=500, amenity_type="restaurant")
    tester.analyze_response(data)
    
    # Mostrar detalles de restaurantes
    if "elements" in data:
        print("\n🍴 Detalles de Restaurantes encontrados:")
        for elem in data["elements"][:5]:  # Primeros 5
            tags = elem.get("tags", {})
            name = tags.get("name", "Sin nombre")
            cuisine = tags.get("cuisine", "No especificado")
            addr = tags.get("addr:street", "")
            print(f"\n  • {name}")
            print(f"    Tipo cocina: {cuisine}")
            if addr:
                print(f"    Dirección: {addr}")
    
    return data


def test_miami_schools():
    """
    Prueba 3: Buscar escuelas en área específica
    """
    print("\n" + "🏫" * 40)
    print("PRUEBA 3: Miami - Escuelas (2km)")
    print("🏫" * 40)
    
    tester = OverpassAPITester()
    
    lat, lon = 25.7617, -80.1918
    
    data = tester.query_by_radius(lat, lon, radius=2000, amenity_type="school")
    tester.analyze_response(data)
    
    # Mostrar nombres de escuelas
    if "elements" in data:
        print("\n📚 Escuelas encontradas:")
        for elem in data["elements"][:10]:
            tags = elem.get("tags", {})
            name = tags.get("name", "Sin nombre")
            print(f"  • {name}")
    
    return data


def test_bbox_query():
    """
    Prueba 4: Buscar usando Bounding Box
    Área pequeña de Downtown Miami
    """
    print("\n" + "📦" * 40)
    print("PRUEBA 4: BoundingBox - Hospitales en Downtown Miami")
    print("📦" * 40)
    
    tester = OverpassAPITester()
    
    # Bounding box pequeño en Downtown Miami
    # south, west, north, east
    south, west = 25.7600, -80.1950
    north, east = 25.7650, -80.1900
    
    data = tester.query_by_bbox(south, west, north, east, amenity_type="hospital")
    tester.analyze_response(data)
    
    return data


def show_available_amenity_types():
    """
    Muestra tipos comunes de amenities que se pueden buscar
    """
    print("\n" + "📋" * 40)
    print("TIPOS COMUNES DE AMENITIES EN OSM")
    print("📋" * 40)
    
    amenities = {
        "Comida & Bebida": ["restaurant", "cafe", "bar", "fast_food", "pub"],
        "Educación": ["school", "university", "college", "kindergarten", "library"],
        "Salud": ["hospital", "clinic", "pharmacy", "dentist", "doctors"],
        "Transporte": ["parking", "fuel", "charging_station", "bus_station", "taxi"],
        "Finanzas": ["bank", "atm", "bureau_de_change"],
        "Entretenimiento": ["cinema", "theatre", "nightclub", "casino", "arts_centre"],
        "Compras": ["marketplace", "supermarket", "mall"],
        "Servicios": ["police", "fire_station", "post_office", "townhall"],
        "Religión": ["place_of_worship", "monastery"],
        "Otros": ["gym", "park", "swimming_pool", "playground"]
    }
    
    for category, items in amenities.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🗺️  PRUEBAS DE OVERPASS API - OpenStreetMap")
    print("="*80)
    
    # Mostrar tipos disponibles
    show_available_amenity_types()
    
    # Ejecutar pruebas
    try:
        # Prueba 1: Todos los amenities en 1km
        result1 = test_miami_downtown()
        
        # Prueba 2: Solo restaurantes
        result2 = test_miami_restaurants()
        
        # Prueba 3: Solo escuelas
        result3 = test_miami_schools()
        
        # Prueba 4: Bounding box
        result4 = test_bbox_query()
        
        print("\n" + "="*80)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*80)
        
        # Guardar un ejemplo de respuesta completa
        print("\n💾 Guardando ejemplo de respuesta completa en 'osm_response_example.json'")
        with open("osm_response_example.json", "w", encoding="utf-8") as f:
            json.dump(result2, f, indent=2, ensure_ascii=False)
        print("✅ Archivo guardado")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

