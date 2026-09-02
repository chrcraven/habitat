import type { Map as MapLibreMap, GeoJSONSource } from "maplibre-gl";

// MapLibre's own GeoJSON source type is broad (Feature | FeatureCollection
// | Geometry | url string); rather than pull in @types/geojson just for
// this, accept the shapes we actually produce (see src/api/types.ts).
type GeoJsonLike = object;

/** Whether this map still has a live style to add sources/layers to.
 *
 * A page holds its map in state, so a `map` object outlives the
 * MapCanvas that created it: after MapCanvas unmounts it calls
 * `map.remove()`, which tears the style down, but any effect still
 * holding that object will happily call into it. `getSource`/`addLayer`
 * then throw on the now-undefined style, which unmounts the whole React
 * tree and leaves a blank page.
 *
 * Found for real, not by reading: the quick-log capture screen stops
 * watching the device's location when it moves to the detail step, and
 * that state change re-ran the user-location layer effect one tick after
 * MapCanvas had gone. Guarding here rather than in that one page,
 * because every map page holds its map the same way and has the same
 * hazard the moment any dependency of a layer effect changes during
 * unmount. */
function styleIsLive(map: MapLibreMap): boolean {
  // `style` is internal but is exactly what these calls dereference;
  // MapLibre offers no public "has this been removed" predicate.
  return Boolean((map as unknown as { style?: unknown }).style);
}

/** Add-or-update a GeoJSON source, tolerating the map style not being
 * loaded yet (callers already gate on `map.loaded()`/`onReady`, but a
 * defensive check here is cheap) or already torn down (see styleIsLive). */
export function setGeoJsonSource(map: MapLibreMap, id: string, data: GeoJsonLike) {
  if (!styleIsLive(map)) return;
  const source = map.getSource(id) as GeoJSONSource | undefined;
  if (source) {
    source.setData(data as Parameters<GeoJSONSource["setData"]>[0]);
  } else {
    map.addSource(id, { type: "geojson", data: data as Parameters<GeoJSONSource["setData"]>[0] });
  }
}

// MapLibre's own filter-expression type is broad; callers pass the plain
// `["==", ["get", "prop"], value]` shape, which this widens to for the
// same reason GeoJsonLike above does.
type FilterLike = unknown[];

export function ensureFillLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  opacity = 0.25,
  filter?: FilterLike,
) {
  if (!styleIsLive(map) || map.getLayer(layerId)) return;
  map.addLayer({
    id: layerId,
    type: "fill",
    source: sourceId,
    paint: { "fill-color": color, "fill-opacity": opacity },
    ...(filter ? { filter: filter as never } : {}),
  });
}

export function ensureLineLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  width = 2,
  options?: { filter?: FilterLike; dasharray?: number[] },
) {
  if (!styleIsLive(map) || map.getLayer(layerId)) return;
  map.addLayer({
    id: layerId,
    type: "line",
    source: sourceId,
    paint: {
      "line-color": color,
      "line-width": width,
      ...(options?.dasharray ? { "line-dasharray": options.dasharray } : {}),
    },
    ...(options?.filter ? { filter: options.filter as never } : {}),
  });
}

/** Activity fill+line layers, split into "done" vs "not done yet" so the
 * map visually distinguishes planned/in-progress work from completed work
 * (Phase 2's map requirement — see docs/roadmap.md). Two filtered layers
 * per source rather than one data-driven layer because MapLibre doesn't
 * support data-driven `line-dasharray` (only zoom functions), and a dashed
 * outline is what makes "not done" legible at a glance without relying on
 * color alone. `is_done` comes from ActivitySerializer (see
 * backend/apps/activities/serializers.py) — anything not done, including
 * an org's custom "in progress"-type states, renders as "not done yet"
 * rather than trying to guess a three-way split (see that serializer's
 * comment on why there's no separate `is_planned` bucket here). */
export function ensureActivityStatusLayers(map: MapLibreMap, sourceId: string) {
  const DONE_COLOR = "#2f8f5f";
  const PLANNED_COLOR = "#c9782f";
  const doneFilter: FilterLike = ["==", ["get", "is_done"], true];
  const notDoneFilter: FilterLike = ["==", ["get", "is_done"], false];

  ensureFillLayer(map, `${sourceId}-fill-planned`, sourceId, PLANNED_COLOR, 0.35, notDoneFilter);
  ensureFillLayer(map, `${sourceId}-fill-done`, sourceId, DONE_COLOR, 0.35, doneFilter);
  ensureLineLayer(map, `${sourceId}-line-planned`, sourceId, PLANNED_COLOR, 2, {
    filter: notDoneFilter,
    dasharray: [2, 2],
  });
  ensureLineLayer(map, `${sourceId}-line-done`, sourceId, DONE_COLOR, 2, { filter: doneFilter });
}

export function ensureCircleLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  color: string,
  radius = 7,
) {
  if (!styleIsLive(map) || map.getLayer(layerId)) return;
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
  if (!styleIsLive(map)) return;
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
