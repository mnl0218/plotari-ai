# weaviate_seed_full_fixed.py
import os
from uuid import UUID
from dotenv import load_dotenv

import weaviate
import weaviate.classes.config as wc
from weaviate.classes.init import Auth
from weaviate.classes.config import ReferenceProperty
from weaviate.classes.data import GeoCoordinate as DataGeo
from weaviate.classes.query import (
    Filter,
    GeoCoordinate as QueryGeo,
    QueryReference,
)

# NEW: OpenAI client for embeddings (query — and optionally objects)
from openai import OpenAI

# ---------------------------------------------
# Settings
# ---------------------------------------------
RESET_SCHEMA = True                   # drop & recreate
EMBED_OBJECTS_CLIENT_SIDE = False     # set True if your server doesn't vectorize inserts

# ---------------------------------------------
# Env & connect
# ---------------------------------------------
load_dotenv()
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WCD_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not WEAVIATE_URL or not WCD_API_KEY or not OPENAI_API_KEY:
    raise RuntimeError("Set WEAVIATE_URL, WEAVIATE_API_KEY and OPENAI_API_KEY in your .env")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WCD_API_KEY),
    headers={"X-Openai-Api-Key": OPENAI_API_KEY},  # header que algunos despliegues esperan
)

# OpenAI local client (usamos la misma API key)
oai = OpenAI(api_key=OPENAI_API_KEY)

def embed_text(text: str) -> list[float]:
    """Embed any text using OpenAI, returns a vector (list[float])."""
    r = oai.embeddings.create(model="text-embedding-3-small", input=text or "")
    return r.data[0].embedding

def build_property_corpus(p: dict) -> str:
    parts = [
        p.get("address", ""),
        f'{p.get("city", "")} {p.get("state", "")} {p.get("zipcode", "")}'.strip(),
        p.get("description", ""),
        ", ".join(p.get("features", []) or []),
        p.get("neighborhood_text", p.get("neighborhood_name", "")),
    ]
    return " | ".join([x for x in parts if x])

try:
    if not client.is_ready():
        raise ConnectionError("Weaviate is not ready")
    print("✅ Connected to Weaviate")

    # ---------------------------------------------
    # Optional reset
    # ---------------------------------------------
    if RESET_SCHEMA:
        for name in ["POI", "Property", "Neighborhood"]:
            try:
                client.collections.delete(name)
                print(f"🗑️  Dropped collection: {name}")
            except Exception:
                pass

    # ---------------------------------------------
    # Create collections (with server-side vectorizer configured)
    # (aunque pasaremos el vector del query desde cliente)
    # ---------------------------------------------
    def ensure_collection_neighborhood():
        try:
            return client.collections.get("Neighborhood")
        except Exception:
            client.collections.create(
                name="Neighborhood",
                properties=[
                    wc.Property("name", wc.DataType.TEXT),
                    wc.Property("city", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("info", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("geo_center", wc.DataType.GEO_COORDINATES),
                    wc.Property("search_corpus", wc.DataType.TEXT),
                ],
                vector_config=wc.Configure.Vectors.text2vec_openai(
                    model="text-embedding-3-small",
                    source_properties=["search_corpus"],
                ),
                inverted_index_config=wc.Configure.inverted_index(
                    stopwords_preset=wc.StopwordsPreset.EN
                ),
            )
            print("🆕 Created collection: Neighborhood")
            return client.collections.get("Neighborhood")

    def ensure_collection_property():
        try:
            return client.collections.get("Property")
        except Exception:
            client.collections.create(
                name="Property",
                properties=[
                    wc.Property("zpid", wc.DataType.TEXT),
                    wc.Property("address", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("city", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("state", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("zipcode", wc.DataType.TEXT, skip_vectorization=True),

                    wc.Property("price", wc.DataType.NUMBER),
                    wc.Property("bedrooms", wc.DataType.NUMBER),
                    wc.Property("bathrooms", wc.DataType.NUMBER),
                    wc.Property("living_area", wc.DataType.NUMBER),
                    wc.Property("year_built", wc.DataType.NUMBER),
                    wc.Property("lot_size", wc.DataType.NUMBER),

                    wc.Property("description", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("features", wc.DataType.TEXT_ARRAY, skip_vectorization=True),
                    wc.Property("neighborhood_text", wc.DataType.TEXT, skip_vectorization=True),

                    wc.Property("geo", wc.DataType.GEO_COORDINATES),
                    wc.Property("search_corpus", wc.DataType.TEXT),
                ],
                vector_config=wc.Configure.Vectors.text2vec_openai(
                    model="text-embedding-3-small",
                    source_properties=["search_corpus"],
                ),
                inverted_index_config=wc.Configure.inverted_index(
                    stopwords_preset=wc.StopwordsPreset.EN
                ),
            )
            print("🆕 Created collection: Property")
            return client.collections.get("Property")

    def ensure_collection_poi():
        try:
            return client.collections.get("POI")
        except Exception:
            client.collections.create(
                name="POI",
                properties=[
                    wc.Property("name", wc.DataType.TEXT),
                    wc.Property("category", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("rating", wc.DataType.NUMBER),
                    wc.Property("source", wc.DataType.TEXT, skip_vectorization=True),
                    wc.Property("geo", wc.DataType.GEO_COORDINATES),
                    wc.Property("search_corpus", wc.DataType.TEXT),
                ],
                vector_config=wc.Configure.Vectors.text2vec_openai(
                    model="text-embedding-3-small",
                    source_properties=["search_corpus"],
                ),
                inverted_index_config=wc.Configure.inverted_index(
                    stopwords_preset=wc.StopwordsPreset.EN
                ),
            )
            print("🆕 Created collection: POI")
            return client.collections.get("POI")

    neigh_col = ensure_collection_neighborhood()
    prop_col  = ensure_collection_property()
    poi_col   = ensure_collection_poi()

    # Asegura refs
    try:
        prop_col.config.add_property(
            ReferenceProperty(name="neighborhood", target_collection="Neighborhood")
        )
        print("🔗 Added reference Property.neighborhood -> Neighborhood")
    except Exception:
        pass
    try:
        poi_col.config.add_property(
            ReferenceProperty(name="neighborhood", target_collection="Neighborhood")
        )
        print("🔗 Added reference POI.neighborhood -> Neighborhood")
    except Exception:
        pass

    # ---------------------------------------------
    # Seed neighborhoods
    # ---------------------------------------------
    print("➡️  Inserting base neighborhood: Crescent Heights")
    n_id: UUID = neigh_col.data.insert({
        "name": "Crescent Heights",
        "city": "Crescent City",
        "info": "Quiet residential area with parks and schools.",
        "geo_center": DataGeo(latitude=41.755, longitude=-124.201),
        "search_corpus": "Crescent Heights in Crescent City | parks | schools | residential",
    })
    print("Neighborhood UUID:", n_id)

    neigh_map = {"Crescent Heights": n_id}

    extra_neighborhoods = [
        {
            "name": "Seabreeze District",
            "city": "Crescent City",
            "info": "Coastal area with ocean breeze and cafes.",
            "geo_center": DataGeo(latitude=41.7580, longitude=-124.2050),
            "search_corpus": "Seabreeze District in Crescent City | coastal | cafes | ocean breeze",
        },
        {
            "name": "Redwood Grove",
            "city": "Crescent City",
            "info": "Wooded neighborhood near trails and nature.",
            "geo_center": DataGeo(latitude=41.7600, longitude=-124.2100),
            "search_corpus": "Redwood Grove in Crescent City | wooded | trails | nature",
        },
        {
            "name": "Downtown Crescent",
            "city": "Crescent City",
            "info": "City center with shops and services.",
            "geo_center": DataGeo(latitude=41.7520, longitude=-124.2000),
            "search_corpus": "Downtown Crescent in Crescent City | shops | services | central",
        },
    ]
    for n in extra_neighborhoods:
        uid = neigh_col.data.insert(n)
        neigh_map[n["name"]] = uid
        print(f"Neighborhood inserted: {n['name']} -> {uid}")

    # ---------------------------------------------
    # Base property & POI
    # (opcionalmente insertamos con vector si EMBED_OBJECTS_CLIENT_SIDE=True)
    # ---------------------------------------------
    p_base = {
        "zpid": "18562768",
        "address": "3850 Kings Valley Rd",
        "city": "Crescent City",
        "state": "CA",
        "zipcode": "95531",
        "price": 499000,
        "bedrooms": 5,
        "bathrooms": 2,
        "living_area": 2100,
        "year_built": 1980,
        "lot_size": 12000,
        "description": "Spacious home close to parks and schools.",
        "features": ["garage", "backyard", "updated kitchen"],
        "neighborhood_text": "Crescent Heights",
        "geo": DataGeo(latitude=41.7532, longitude=-124.1989),
    }
    p_base["search_corpus"] = build_property_corpus(p_base)
    p_refs = {"neighborhood": [n_id]}
    p_vec = embed_text(p_base["search_corpus"]) if EMBED_OBJECTS_CLIENT_SIDE else None

    p_id: UUID = prop_col.data.insert(
        properties=p_base,
        references=p_refs,
        vector=p_vec,   # ← si None, el servidor vectoriza; si no hay vectorizer, úsalo en True
    )
    print("Property UUID:", p_id)

    poi_base = {
        "name": "Sunrise Elementary School",
        "category": "school",
        "rating": 4.6,
        "source": "city-open-data",
        "geo": DataGeo(latitude=41.7542, longitude=-124.1995),
        "search_corpus": "Sunrise Elementary School | school | family-friendly",
    }
    poi_id: UUID = poi_col.data.insert(
        properties=poi_base,
        references={"neighborhood": [n_id]},
        vector=None,  # para POI estamos bien sin vector; o usa embed_text(...) si lo requieres
    )
    print("POI UUID:", poi_id)

    # ---------------------------------------------
    # More properties
    # ---------------------------------------------
    more_properties = [
        {
            "zpid": "18562769",
            "address": "120 Seabreeze Ave",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 449000,
            "bedrooms": 2,
            "bathrooms": 2,
            "living_area": 1400,
            "year_built": 1995,
            "lot_size": 6000,
            "description": "Cozy condo with partial ocean view, walkable to cafes.",
            "features": ["ocean view", "balcony", "covered parking"],
            "neighborhood_name": "Seabreeze District",
            "neighborhood_text": "Seabreeze District",
            "geo": DataGeo(latitude=41.7585, longitude=-124.2060),
        },
        {
            "zpid": "18562770",
            "address": "980 Ocean View Dr",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 399000,
            "bedrooms": 3,
            "bathrooms": 2,
            "living_area": 1600,
            "year_built": 1988,
            "lot_size": 8000,
            "description": "Single-family home with backyard and updated roof.",
            "features": ["backyard", "updated roof", "fireplace"],
            "neighborhood_name": "Seabreeze District",
            "neighborhood_text": "Seabreeze District",
            "geo": DataGeo(latitude=41.7560, longitude=-124.2080),
        },
        {
            "zpid": "18562771",
            "address": "45 Harbor St Apt 3B",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 220000,
            "bedrooms": 1,
            "bathrooms": 1,
            "living_area": 700,
            "year_built": 2005,
            "lot_size": 0,
            "description": "Compact apartment near harbor; great for singles.",
            "features": ["near harbor", "low HOA", "elevator"],
            "neighborhood_name": "Downtown Crescent",
            "neighborhood_text": "Downtown Crescent",
            "geo": DataGeo(latitude=41.7510, longitude=-124.1990),
        },
        {
            "zpid": "18562772",
            "address": "600 Redwood Ln",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 650000,
            "bedrooms": 4,
            "bathrooms": 3,
            "living_area": 2300,
            "year_built": 1992,
            "lot_size": 15000,
            "description": "Spacious house nestled among redwoods; quiet street.",
            "features": ["forest views", "deck", "two-car garage"],
            "neighborhood_name": "Redwood Grove",
            "neighborhood_text": "Redwood Grove",
            "geo": DataGeo(latitude=41.7645, longitude=-124.2120),
        },
        {
            "zpid": "18562773",
            "address": "200 Main St Unit 5",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 520000,
            "bedrooms": 2,
            "bathrooms": 2,
            "living_area": 1200,
            "year_built": 2015,
            "lot_size": 0,
            "description": "Modern downtown loft with high ceilings and parking.",
            "features": ["loft", "high ceilings", "downtown parking"],
            "neighborhood_name": "Downtown Crescent",
            "neighborhood_text": "Downtown Crescent",
            "geo": DataGeo(latitude=41.7535, longitude=-124.1995),
        },
        {
            "zpid": "18562774",
            "address": "15 Grove Trail",
            "city": "Crescent City",
            "state": "CA",
            "zipcode": "95531",
            "price": 580000,
            "bedrooms": 3,
            "bathrooms": 2,
            "living_area": 1800,
            "year_built": 1999,
            "lot_size": 11000,
            "description": "Cabin-style home near trails; renovated kitchen.",
            "features": ["trail access", "renovated kitchen", "patio"],
            "neighborhood_name": "Redwood Grove",
            "neighborhood_text": "Redwood Grove",
            "geo": DataGeo(latitude=41.7610, longitude=-124.2150),
        },
        {
            "zpid": "18570001",
            "address": "101 Beachcomber Rd",
            "city": "Brookings",
            "state": "OR",
            "zipcode": "97415",
            "price": 430000,
            "bedrooms": 2,
            "bathrooms": 2,
            "living_area": 1300,
            "year_built": 1990,
            "lot_size": 7000,
            "description": "Beach cottage near coast; calm neighborhood.",
            "features": ["beach access", "porch", "storage shed"],
            "neighborhood_name": "Brookings Area",  # no existe en neigh_map
            "neighborhood_text": "Brookings Area",
            "geo": DataGeo(latitude=42.0520, longitude=-124.2900),
        },
    ]

    for p in more_properties:
        if not p.get("search_corpus"):
            p["search_corpus"] = build_property_corpus(p)

        refs = None
        neigh_name = p.get("neighborhood_name")
        if neigh_name in neigh_map:
            refs = {"neighborhood": [neigh_map[neigh_name]]}

        vec = embed_text(p["search_corpus"]) if EMBED_OBJECTS_CLIENT_SIDE else None
        uid = prop_col.data.insert(properties=p, references=refs, vector=vec)
        print(f"Property inserted: {p['address']} -> {uid}")

    # ---------------------------------------------
    # Más Neighborhoods (si quieres ampliar el mapa)
    # ---------------------------------------------
    extra_neighs_2 = [
        {
            "name": "Harbor Point",
            "city": "Crescent City",
            "info": "Waterfront living with marina access.",
            "geo_center": DataGeo(latitude=41.7505, longitude=-124.2055),
            "search_corpus": "Harbor Point in Crescent City | waterfront | marina | boats",
        },
        {
            "name": "North Ridge",
            "city": "Crescent City",
            "info": "Hilly area with hiking access and scenic views.",
            "geo_center": DataGeo(latitude=41.7665, longitude=-124.1950),
            "search_corpus": "North Ridge in Crescent City | hills | hiking | scenic views",
        },
    ]
    for n in extra_neighs_2:
        uid = neigh_col.data.insert(n)
        neigh_map[n["name"]] = uid
        print(f"Neighborhood inserted: {n['name']} -> {uid}")

    # ---------------------------------------------
    # Helper para insertar múltiples POIs por barrio
    # ---------------------------------------------
    def insert_pois_for_neighborhood(neigh_name: str, pois: list[dict]):
        neigh_id = neigh_map.get(neigh_name)
        if not neigh_id:
            print(f"[WARN] Neighborhood '{neigh_name}' no encontrado en neigh_map.")
            return

        for p in pois:
            # construir search_corpus si no viene
            if not p.get("search_corpus"):
                parts = [p.get("name",""), p.get("category",""), p.get("desc","")]
                p["search_corpus"] = " | ".join([x for x in parts if x])

            uid = poi_col.data.insert(
                properties={
                    "name": p["name"],
                    "category": p["category"],           # ej: school, park, grocery, hospital, cafe, gym, transit, police, library
                    "rating": p.get("rating", 4.0),
                    "source": p.get("source", "seed"),
                    "geo": DataGeo(latitude=p["lat"], longitude=p["lng"]),
                    "search_corpus": p["search_corpus"],
                },
                references={"neighborhood": [neigh_id]},
                vector=None  # puedes cambiarlo por embed_text(p["search_corpus"]) si EMBED_OBJECTS_CLIENT_SIDE=True
            )
            print(f"POI inserted: {p['name']} ({p['category']}) -> {uid}")

    # ---------------------------------------------
    # Catálogo de POIs por barrio (varias categorías)
    # ---------------------------------------------
    insert_pois_for_neighborhood("Seabreeze District", [
        {"name":"Blue Wave Cafe", "category":"cafe", "lat":41.7589, "lng":-124.2062, "rating":4.4, "desc":"coffee, pastries, breakfast"},
        {"name":"Oceanfront Park", "category":"park", "lat":41.7594, "lng":-124.2048, "rating":4.6, "desc":"playground, trees, benches"},
        {"name":"Seabreeze Market", "category":"grocery", "lat":41.7576, "lng":-124.2071, "rating":4.2, "desc":"groceries, produce, deli"},
        {"name":"Coastal Urgent Care", "category":"hospital", "lat":41.7569, "lng":-124.2054, "rating":4.1, "desc":"clinic, urgent care"},
        {"name":"Bus Stop A - Seabreeze Ave", "category":"transit", "lat":41.7581, "lng":-124.2056, "rating":4.0, "desc":"bus stop route 2"},
        {"name":"Harbor Fitness", "category":"gym", "lat":41.7572, "lng":-124.2066, "rating":4.3, "desc":"gym, weights, classes"},
    ])

    insert_pois_for_neighborhood("Downtown Crescent", [
        {"name":"Main St Library", "category":"library", "lat":41.7537, "lng":-124.1997, "rating":4.7, "desc":"public library, study rooms"},
        {"name":"City Hall", "category":"public_service", "lat":41.7529, "lng":-124.1993, "rating":4.3, "desc":"city services, permits"},
        {"name":"Central Police Station", "category":"police", "lat":41.7524, "lng":-124.1987, "rating":4.1, "desc":"police HQ, reporting"},
        {"name":"Downtown Transit Hub", "category":"transit", "lat":41.7532, "lng":-124.2004, "rating":4.2, "desc":"bus hub, multiple routes"},
        {"name":"Riverside Steakhouse", "category":"restaurant", "lat":41.7540, "lng":-124.2001, "rating":4.5, "desc":"steak, wine"},
    ])

    insert_pois_for_neighborhood("Redwood Grove", [
        {"name":"Trailhead North", "category":"trail", "lat":41.7638, "lng":-124.2137, "rating":4.8, "desc":"hiking trail access"},
        {"name":"Grove Elementary", "category":"school", "lat":41.7621, "lng":-124.2119, "rating":4.6, "desc":"K-5 school"},
        {"name":"Forest Market", "category":"grocery", "lat":41.7613, "lng":-124.2128, "rating":4.2, "desc":"groceries"},
        {"name":"Redwood Fire Station", "category":"fire_station", "lat":41.7618, "lng":-124.2146, "rating":4.4, "desc":"fire dept"},
    ])

    insert_pois_for_neighborhood("Crescent Heights", [
        {"name":"Sunrise Park", "category":"park", "lat":41.7546, "lng":-124.2002, "rating":4.5, "desc":"green area, families"},
        {"name":"Heights Preschool", "category":"school", "lat":41.7551, "lng":-124.1983, "rating":4.6, "desc":"early education"},
        {"name":"Family Clinic", "category":"hospital", "lat":41.7544, "lng":-124.1978, "rating":4.3, "desc":"primary care"},
    ])

    insert_pois_for_neighborhood("Harbor Point", [
        {"name":"Marina Docks", "category":"marina", "lat":41.7501, "lng":-124.2061, "rating":4.6, "desc":"boat slips"},
        {"name":"Seafood Shack", "category":"restaurant", "lat":41.7498, "lng":-124.2057, "rating":4.4, "desc":"seafood, chowder"},
    ])

    insert_pois_for_neighborhood("North Ridge", [
        {"name":"Summit Viewpoint", "category":"viewpoint", "lat":41.7671, "lng":-124.1943, "rating":4.9, "desc":"scenic lookout"},
        {"name":"Northridge High", "category":"school", "lat":41.7662, "lng":-124.1961, "rating":4.5, "desc":"grades 9-12"},
    ])

    # ---------------------------------------------
    # (Opcional) Más propiedades rápidas por nuevos barrios
    # ---------------------------------------------
    more_props2 = [
        {
            "zpid":"18580001","address":"5 Marina Way","city":"Crescent City","state":"CA","zipcode":"95531",
            "price":560000,"bedrooms":3,"bathrooms":2,"living_area":1500,"year_built":2012,"lot_size":4000,
            "description":"Townhome steps from the marina.","features":["marina access","balcony","parking"],
            "neighborhood_name":"Harbor Point","neighborhood_text":"Harbor Point",
            "geo": DataGeo(latitude=41.7509, longitude=-124.2059),
        },
        {
            "zpid":"18580002","address":"99 Ridge Rd","city":"Crescent City","state":"CA","zipcode":"95531",
            "price":610000,"bedrooms":4,"bathrooms":3,"living_area":2100,"year_built":2010,"lot_size":10000,
            "description":"Ridge home with scenic views.","features":["view deck","fireplace","2-car garage"],
            "neighborhood_name":"North Ridge","neighborhood_text":"North Ridge",
            "geo": DataGeo(latitude=41.7668, longitude=-124.1954),
        },
    ]

    for p in more_props2:
        if not p.get("search_corpus"):
            p["search_corpus"] = build_property_corpus(p)
        refs = {"neighborhood": [neigh_map[p["neighborhood_name"]]]} if p["neighborhood_name"] in neigh_map else None
        vec = embed_text(p["search_corpus"]) if EMBED_OBJECTS_CLIENT_SIDE else None
        uid = prop_col.data.insert(properties=p, references=refs, vector=vec)
        print(f"Property inserted: {p['address']} -> {uid}")


    # ---------------------------------------------
    # Hybrid query (client-side query vector)
    # ---------------------------------------------
    print("\n🔍 Hybrid query (alpha=0.5, bedrooms>1, price<600k, within 5km):")

    query_text = "2 bedroom condo in Crescent City with backyard"
    q_vec = embed_text(query_text)  # ← clave para evitar VectorFromInput en el servidor

    filters = (
        Filter.by_property("bedrooms").greater_than(1)
        & Filter.by_property("price").less_than(600000)
        & Filter.by_property("geo").within_geo_range(
            coordinate=QueryGeo(latitude=41.753, longitude=-124.200),
            distance=5000,
        )
    )

    res = prop_col.query.hybrid(
        query=query_text,           # BM25
        vector=q_vec,               # ← vector del cliente (no usa vectorizer del server)
        alpha=0.5,
        limit=5,
        filters=filters,
        return_properties=[
            "zpid","address","city","state","zipcode",
            "price","bedrooms","bathrooms","living_area","year_built","lot_size",
        ],
        return_references=QueryReference(
            link_on="neighborhood",
            return_properties=["name","city"],
        ),
    )

    for obj in res.objects:
        print("→", obj.properties)
        if "neighborhood" in obj.references:
            for ref in obj.references["neighborhood"].objects:
                print("   neighborhood:", ref.properties)

    print("\n✅ Done.")

finally:
    try:
        client.close()
    except Exception:
        pass
