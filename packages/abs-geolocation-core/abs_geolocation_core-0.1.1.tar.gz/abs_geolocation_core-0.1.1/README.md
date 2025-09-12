# abs-geolocation-core

## Overview

The `abs-geolocation-core` package provides a set of utilities powered by Azure Maps for geolocation services. It includes features such as geocoding, reverse geocoding, distance calculations, routing, elevation data, weather information, and traffic data.

## Features

- **Geocode Address**: Get location by address.
- **Reverse Geocode**: Get address by latitude/longitude.
- **Distance Between**: Calculate Haversine distance in meters or by road via route.
- **Get Route**: Determine the route between two or more locations.
- **Elevation Along**: Retrieve elevation for points or lines.
- **Weather At**: Get current weather at a location.
- **Traffic At**: Get traffic flow and relative congestion at a location.
- **Nearest By Distance**: Find nearest candidates to an origin by straight-line distance.
- **Nearest By Drive Distance**: Find nearest by driving distance using Route Matrix.
- **Nearest By Drive Time**: Find nearest by driving time using Route Matrix.
- **Nearest Ranked**: Rank candidates by time and distance.
- **Nearest Ranked With Weather**: Rank candidates by time, distance, and weather conditions.
- **Nearest Ranked With Weather and Traffic**: Rank candidates by time, distance, weather, and traffic conditions.

## Installation

To install the package, use the following command:

```bash
pip install abs-geolocation-core
```

## Usage

Here is a basic example of how to use the `abs-geolocation-core` package:

```python
import asyncio
from abs_geolocation_core.location_service import AzureMapsAuth, LocationService

async def main():
    auth = AzureMapsAuth(subscription_key="<YOUR_KEY>")  # or sas_token_provider=lambda: "sv=...&sig=..."
    svc = LocationService(auth)
    places = await svc.geocode_address("Mumbai Central, Mumbai")
    print(places[0]["position"])  # lat/lon from geocode result
    origin = (19.0760, 72.8777)  # Mumbai
    dest = (18.5204, 73.8567)    # Pune
    route = await svc.get_route([origin, dest])
    print(route["routes"][0]["summary"])
    best = await svc.nearest_by_drive_time(origin, [(18.5204, 73.8567), (21.1458, 79.0882)])
    print(best)
    await svc.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Mapping to Azure Maps

The service maps to the following Azure Maps REST endpoints (host: `https://atlas.microsoft.com`):

- Search: `GET /search/address/json`, `GET /search/address/reverse/json`, `GET /search/fuzzy/json` (api-version: `1.0` configurable)
- Route: `GET /route/directions/json` (api-version: configurable), `POST /route/matrix/sync/json` (matrix api-version: configurable)
- Elevation: `GET /elevation/point/json`, `GET /elevation/line/json` (api-version: `1.0` configurable)
- Weather: `GET /weather/currentConditions/json` (api-version: `1.1` configurable)
- Traffic: `GET /traffic/flowSegment/relative/json` (api-version: `1.0` configurable)

Refer to Azure Maps REST docs for details on parameters and responses:
- Search: [Azure Maps Search REST]
- Route: [Azure Maps Route REST]
- Matrix: [Azure Maps Route Matrix REST]
- Elevation: [Azure Maps Elevation REST]
- Weather: [Azure Maps Weather REST]
- Traffic: [Azure Maps Traffic REST]

## Configuration

You can override API versions and timeouts via the `LocationService` constructor:

```python
svc = LocationService(
    AzureMapsAuth(subscription_key="<KEY>"),
    api_version_search="1.0",
    api_version_route="1.0",
    api_version_matrix="2.0",
    api_version_elevation="1.0",
    api_version_weather="1.1",
    api_version_traffic="1.0",
    timeout=10.0,
)
```

For SAS authentication:

```python
svc = LocationService(
    AzureMapsAuth(sas_token_provider=lambda: "<SAS_TOKEN>"),
)
```


## Requirements

- Python 3.11 or higher
- Azure Maps services enabled for your resource (Search, Routing, Elevation, Weather, Traffic)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For more information, please contact [info@autobridgesystems.com](mailto:info@autobridgesystems.com).
