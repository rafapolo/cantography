#!/usr/bin/env python3
"""Write the outline of Switzerland the map keeps its place names inside.

The basemap's place labels carry no country, so the names chip filters them with
MapLibre's "within" against this outline. Source: geoBoundaries CHE ADM0, from
swisstopo. Simplified to ~200 m (0.002°), enough for a town's label point; the two
enclaves, Büsingen and Campione d'Italia, stay as holes.

Output:
    data/switzerland.json   a GeoJSON MultiPolygon, 4 decimals

Usage:
    python3 scripts/switzerland_outline.py
"""
import json, os, urllib.request

from shapely.geometry import shape

URL = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/CHE/ADM0/geoBoundaries-CHE-ADM0.geojson"
TOLERANCE = 0.002
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "switzerland.json")


def ring(r):
    return [[round(x, 4), round(y, 4)] for x, y in r.coords]


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "cantography-research"})
    with urllib.request.urlopen(req) as res:
        country = shape(json.load(res)["features"][0]["geometry"])
    simple = country.simplify(TOLERANCE, preserve_topology=True)
    polys = [p for p in getattr(simple, "geoms", [simple]) if p.area > 1e-5]
    outline = {"type": "MultiPolygon", "coordinates": [[ring(p.exterior)] + [ring(i) for i in p.interiors] for p in polys]}
    with open(OUT, "w") as f:
        json.dump(outline, f, separators=(",", ":"))
    points = sum(len(r) for p in outline["coordinates"] for r in p)
    print(f"{OUT}: {len(polys)} polygon(s), {points} points, {os.path.getsize(OUT):,} bytes")


if __name__ == "__main__":
    main()
