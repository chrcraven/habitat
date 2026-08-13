import type { Map as MapLibreMap, GeoJSONSource } from "maplibre-gl";

// MapLibre's own GeoJSON source type is broad (Feature | FeatureCollection
// | Geometry | url string); rather than pull in @types/geojson just for
// this, accept the shapes we actually produce (see src/api/types.ts).
type GeoJsonLike = object;

/** Add-or-update a GeoJSON source, tolerating the map style not being
 * loaded yet (callers already gate on `map.loaded()`/`onReady`, but a
 * defensive check here is cheap). */
export function setGeoJsonSource(map: MapLibreMap, id: string, data: GeoJsonLike) {
  const source = map.getSource(id) as GeoJSONSource | undefined;
  if (source) {
    source.setData(data as Parameters<GeoJSONSource["setData"]>[0]);
  } else {
    map.addSource(id, { type: "geojson", data: data as Parameters<GeoJSONSource["setData"]>[0] });
  }
}

export function ensureFillLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  opacity = 0.25,
) {
  if (map.getLayer(layerId)) return;
  map.addLayer({
    id: layerId,
    type: "fill",
    source: sourceId,
    paint: { "fill-color": color, "fill-opacity": opacity },
  });
}

export function ensureLineLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  width = 2,
) {
  if (map.getLayer(layerId)) return;
  map.addLayer({
    id: layerId,
    type: "line",
    source: sourceId,
    paint: { "line-color": color, "line-width": width },
  });
}

export function ensureCircleLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  radius = 7,
) {
  if (map.getLayer(layerId)) return;
  map.addLayer({
    id: layerId,
    type: "circle",
    source: sourceId,
    paint: {
      "circle-color": color,
      "circle-radius": radius,
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff",
    },
  });
}

/** "You are here" marker — a low-opacity halo behind a solid dot, the
 * common current-location convention, styled distinctly from sightings'
 * plain blue circles (see PropertyMapPage/ActivityFormPage) so the two
 * don't get confused when both are on screen at once. Not tied to the
 * device's actual accuracy radius — a fixed decorative halo, not a
 * measurement. */
export function ensureUserLocationLayer(map: MapLibreMap, sourceId: string) {
  if (!map.getLayer(`${sourceId}-halo`)) {
    map.addLayer({
      id: `${sourceId}-halo`,
      type: "circle",
      source: sourceId,
      paint: { "circle-color": "#1a73e8", "circle-radius": 16, "circle-opacity": 0.2 },
    });
  }
  if (!map.getLayer(`${sourceId}-dot`)) {
    map.addLayer({
      id: `${sourceId}-dot`,
      type: "circle",
      source: sourceId,
      paint: {
        "circle-color": "#1a73e8",
        "circle-radius": 6,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });
  }
}
