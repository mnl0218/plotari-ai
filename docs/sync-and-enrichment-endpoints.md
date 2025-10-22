# Sync and POI Enrichment Endpoints

## Overview

This document provides detailed information about the data synchronization and POI enrichment endpoints in the Plotari AI Backend.

## Table of Contents

- [Synchronization Endpoints](#synchronization-endpoints)
- [POI Enrichment Endpoint](#poi-enrichment-endpoint)
- [Use Cases](#use-cases)
- [Error Handling](#error-handling)

---

## Synchronization Endpoints

These endpoints handle the synchronization of property data between **Supabase** (source of truth) and **Weaviate** (vector database for search).

### 1. Full Property Synchronization

**Endpoint:** `POST /api/sync/properties/full`

**Description:** Synchronizes ALL properties from Supabase to Weaviate in batches.

**Parameters:**
- `batch_size` (query parameter, optional): Number of properties to process in each batch
  - Default: 100
  - Range: 1-1000

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/sync/properties/full?batch_size=100"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Full property synchronization completed",
  "result": {
    "total_properties": 1500,
    "synced_count": 1498,
    "error_count": 2,
    "success_rate": 99.87,
    "timestamp": "2024-01-15T10:30:45.123456"
  }
}
```

**Use Case:**
- Initial data load when setting up Weaviate
- Complete database refresh after major data changes
- Recovery from data inconsistencies

---

### 2. Incremental Property Synchronization

**Endpoint:** `POST /api/sync/properties/incremental`

**Description:** Synchronizes only properties that have been updated since a specific datetime.

**Request Body:**
```json
{
  "since": "2024-01-01T00:00:00",
  "batch_size": 100
}
```

**Parameters:**
- `since` (required): ISO format datetime string
  - Format: `YYYY-MM-DDTHH:MM:SS` or `YYYY-MM-DDTHH:MM:SSZ`
  - Examples: `"2024-01-01T00:00:00"`, `"2024-01-15T10:30:00Z"`
- `batch_size` (optional): Number of properties to process per batch
  - Default: 100
  - Range: 1-1000

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/sync/properties/incremental" \
  -H "Content-Type: application/json" \
  -d '{
    "since": "2024-01-01T00:00:00",
    "batch_size": 100
  }'
```

**Response Example:**
```json
{
  "success": true,
  "message": "Incremental property synchronization completed",
  "result": {
    "total_properties": 45,
    "synced_count": 45,
    "error_count": 0,
    "success_rate": 100.0,
    "since": "2024-01-01T00:00:00",
    "timestamp": "2024-01-15T10:35:20.789012"
  }
}
```

**Use Case:**
- Daily/hourly scheduled synchronization
- Syncing recent property updates
- Keeping Weaviate up-to-date with minimal overhead

---

### 3. Single Property Synchronization

**Endpoint:** `POST /api/sync/properties/{property_id}`

**Description:** Synchronizes a single property by its ID from Supabase to Weaviate.

**Path Parameters:**
- `property_id` (required): The unique property identifier (zpid)

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/sync/properties/12345678"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Single property synchronization completed",
  "result": {
    "success": true,
    "property_id": "12345678",
    "synced": true,
    "message": "Property synced successfully"
  }
}
```

**Use Case:**
- Manual property update after specific changes
- Testing synchronization for a specific property
- Fixing sync issues for individual properties

---

### 4. Synchronization Status

**Endpoint:** `GET /api/sync/properties/status`

**Description:** Gets the current synchronization status, comparing counts between Supabase and Weaviate.

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/sync/properties/status"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Sync status retrieved successfully",
  "status": {
    "supabase_count": 1500,
    "weaviate_count": 1498,
    "in_sync": false,
    "difference": 2,
    "last_check": "2024-01-15T10:40:15.456789",
    "sync_health": "needs_attention"
  }
}
```

**Use Case:**
- Monitoring data consistency
- Identifying sync gaps
- Health check for data pipelines

---

## POI Enrichment Endpoint

This endpoint enriches properties with Points of Interest (POIs) data from OpenStreetMap and stores them in Weaviate.

### Enrich Properties with POIs

**Endpoint:** `POST /api/enrich-pois`

**Description:** Fetches properties from Supabase, searches for nearby POIs in OpenStreetMap, and saves them to Weaviate.

**Flow:**
1. **Fetch Properties** from Supabase (filtered by date)
2. **Search POIs** in OpenStreetMap for each property (based on geolocation)
3. **Save POIs** to Weaviate (with automatic deduplication)

**Request Body:**
```json
{
  "since_date": "2024-01-01",
  "radius": 1000,
  "amenities": ["restaurant", "school", "hospital", "park"],
  "limit_per_property": 20
}
```

**Parameters:**
- `since_date` (required): ISO 8601 date to filter properties
  - Format: `YYYY-MM-DD`
  - Example: `"2024-01-01"`
  - Only properties updated on or after this date will be processed
  
- `radius` (optional): Search radius in meters around each property
  - Default: 1000
  - Range: 100-5000 meters
  
- `amenities` (optional): List of amenity types to search for
  - Default: `["restaurant", "school"]`
  - Available types:
    - `restaurant` - Restaurants and eateries
    - `school` - Schools and educational institutions
    - `hospital` - Hospitals and medical facilities
    - `park` - Parks and green spaces
    - `pharmacy` - Pharmacies
    - `bank` - Banks and ATMs
    - `cafe` - Cafes and coffee shops
    - `supermarket` - Supermarkets and grocery stores
    - `gym` - Gyms and fitness centers
    - `library` - Libraries
    
- `limit_per_property` (optional): Maximum POIs to save per property
  - Default: 20
  - Range: 1-50

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/enrich-pois" \
  -H "Content-Type: application/json" \
  -d '{
    "since_date": "2024-01-01",
    "radius": 1500,
    "amenities": ["restaurant", "school", "hospital", "park"],
    "limit_per_property": 25
  }'
```

**Response Example:**
```json
{
  "properties_processed": 150,
  "total_pois_found": 3450,
  "total_pois_saved": 3200,
  "errors": [],
  "status": "completed",
  "execution_time_seconds": 185.34,
  "request_parameters": {
    "since_date": "2024-01-01",
    "radius": 1500,
    "amenities": ["restaurant", "school", "hospital", "park"],
    "limit_per_property": 25
  },
  "timestamp": "2024-01-15T11:00:00.123456"
}
```

**Response Fields:**
- `properties_processed`: Number of properties that were processed
- `total_pois_found`: Total POIs found in OpenStreetMap
- `total_pois_saved`: Total POIs successfully saved to Weaviate (after deduplication)
- `errors`: List of errors encountered during processing
- `status`: Overall status (`completed`, `partial`, or `failed`)
- `execution_time_seconds`: Total execution time in seconds
- `request_parameters`: Echo of the request parameters
- `timestamp`: Completion timestamp

**Use Case:**
- Enriching new properties with nearby amenities
- Updating POI data for existing properties
- Bulk POI enrichment for property listings
- Providing location-based insights to users

---

## Use Cases

### Complete Data Pipeline Setup

**Scenario:** Setting up a new Weaviate instance with existing Supabase data

**Steps:**
1. **Full Sync Properties:** `POST /api/sync/properties/full`
2. **Enrich with POIs:** `POST /api/enrich-pois` (all properties)
3. **Verify Status:** `GET /api/sync/properties/status`

### Daily Maintenance

**Scenario:** Daily scheduled job to keep data up-to-date

**Steps:**
1. **Incremental Sync:** `POST /api/sync/properties/incremental` (last 24 hours)
2. **POI Enrichment:** `POST /api/enrich-pois` (last 24 hours)
3. **Status Check:** `GET /api/sync/properties/status`

**Cron Example:**
```bash
# Daily at 2 AM
0 2 * * * curl -X POST "http://localhost:8000/api/sync/properties/incremental" \
  -H "Content-Type: application/json" \
  -d "{\"since\": \"$(date -d '1 day ago' -Iseconds)\"}"
```

### Manual Property Update

**Scenario:** A specific property was updated and needs immediate sync with POI refresh

**Steps:**
1. **Sync Property:** `POST /api/sync/properties/{property_id}`
2. **Enrich POIs:** `POST /api/enrich-pois` (filtered by property ID date range)

---

## Error Handling

### Common Error Responses

#### Invalid Date Format
```json
{
  "success": false,
  "error": "Invalid datetime format. Use ISO format: ...",
  "message": "Failed to parse datetime"
}
```

#### Synchronization Failure
```json
{
  "success": false,
  "error": "Connection to Weaviate failed",
  "message": "Failed to synchronize properties"
}
```

#### POI Enrichment Validation Error
```json
{
  "detail": "radius must be between 100 and 5000 meters"
}
```

### Best Practices

1. **Batch Size Selection:**
   - Use smaller batches (50-100) for initial testing
   - Increase batch size (200-500) for production sync jobs
   - Monitor memory usage with larger batches

2. **Error Recovery:**
   - Check sync status after large operations
   - Use single property sync to fix specific failures
   - Log errors for troubleshooting

3. **Performance Optimization:**
   - Schedule incremental syncs during off-peak hours
   - Use appropriate radius for POI searches (1000-1500m recommended)
   - Limit amenity types to only what's needed

4. **Monitoring:**
   - Regularly check sync status
   - Monitor execution times for enrichment jobs
   - Set up alerts for high error counts

---

## Integration Examples

### Python Script for Daily Sync

```python
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api"

# Get yesterday's date
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

# Sync properties
sync_response = requests.post(
    f"{API_BASE}/sync/properties/incremental",
    json={"since": yesterday, "batch_size": 100}
)
print(f"Sync: {sync_response.json()}")

# Enrich with POIs
enrich_response = requests.post(
    f"{API_BASE}/enrich-pois",
    json={
        "since_date": yesterday.split("T")[0],
        "radius": 1500,
        "amenities": ["restaurant", "school", "park"],
        "limit_per_property": 20
    }
)
print(f"Enrichment: {enrich_response.json()}")

# Check status
status_response = requests.get(f"{API_BASE}/sync/properties/status")
print(f"Status: {status_response.json()}")
```

### Node.js/JavaScript Example

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000/api';

async function dailySync() {
  const yesterday = new Date(Date.now() - 86400000).toISOString();
  
  // Sync properties
  const syncResult = await axios.post(
    `${API_BASE}/sync/properties/incremental`,
    { since: yesterday, batch_size: 100 }
  );
  console.log('Sync:', syncResult.data);
  
  // Enrich POIs
  const enrichResult = await axios.post(
    `${API_BASE}/enrich-pois`,
    {
      since_date: yesterday.split('T')[0],
      radius: 1500,
      amenities: ['restaurant', 'school', 'park'],
      limit_per_property: 20
    }
  );
  console.log('Enrichment:', enrichResult.data);
  
  // Check status
  const status = await axios.get(`${API_BASE}/sync/properties/status`);
  console.log('Status:', status.data);
}

dailySync().catch(console.error);
```

---

## Summary

- **4 Synchronization Endpoints** for keeping Supabase and Weaviate in sync
- **1 POI Enrichment Endpoint** for adding OpenStreetMap data
- **Flexible parameters** for different use cases
- **Batch processing** for handling large datasets
- **Comprehensive error handling** and status reporting
- **Real-world examples** for integration

For more information, visit the interactive API documentation at `/docs` or `/redoc`.

