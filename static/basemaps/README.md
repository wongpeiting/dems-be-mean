# Drop basemaps here

To use a map other than the built-ins, put a **GeoJSON** file in this folder and
name it (without `.json`) in your `story.json` as `"basemap"`.

Requirements:
- It must be GeoJSON (a `FeatureCollection`). If you have TopoJSON or a shapefile,
  convert it first at [mapshaper.org](https://mapshaper.org) (also good for
  shrinking big files).
- Every feature needs a name in `properties.NAME` (or `name`) — that's what your
  story's `region:` values match against.

Where to get free basemaps:
- [Natural Earth](https://www.naturalearthdata.com) — countries, states, coastlines
- [geoBoundaries](https://www.geoboundaries.org) — administrative areas worldwide
- [geojson.io](https://geojson.io) — draw or paste your own

Example: save `singapore-planning-areas.json` here, then in `story.json`:
`"basemap": "singapore-planning-areas"`.
