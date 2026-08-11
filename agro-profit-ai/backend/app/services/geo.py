"""Lightweight geospatial helpers — centroid + area from GeoJSON without a
full projection stack (no pyproj dependency for the MVP). Area uses a local
equirectangular approximation centered on the geometry's latitude, accurate
enough for farm/field-scale polygons (spec seção 8 grid model note)."""
from __future__ import annotations

import math

from shapely.geometry import shape


def centroid_and_area_ha(geojson: dict) -> tuple[float, float, float]:
    geom = shape(geojson["geometry"] if geojson.get("type") == "Feature" else geojson)
    centroid = geom.centroid
    lat, lon = centroid.y, centroid.x

    meters_per_deg_lat = 111_320.0
    meters_per_deg_lon = 111_320.0 * math.cos(math.radians(lat))

    def to_meters(x, y):
        return (x * meters_per_deg_lon, y * meters_per_deg_lat)

    projected_coords = [to_meters(x, y) for x, y in geom.exterior.coords] if geom.geom_type == "Polygon" else None
    if projected_coords:
        area_m2 = _shoelace_area(projected_coords)
    else:
        # MultiPolygon or other: sum over parts
        area_m2 = 0.0
        polys = geom.geoms if hasattr(geom, "geoms") else [geom]
        for part in polys:
            coords = [to_meters(x, y) for x, y in part.exterior.coords]
            area_m2 += _shoelace_area(coords)

    area_ha = round(area_m2 / 10_000, 2)
    return lat, lon, area_ha


def _shoelace_area(coords: list[tuple[float, float]]) -> float:
    n = len(coords)
    area = 0.0
    for i in range(n - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0
