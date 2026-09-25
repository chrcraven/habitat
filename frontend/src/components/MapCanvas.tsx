import { useEffect, useRef } from "react";
import maplibregl, { Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { BBox } from "../utils/geo";

// MapLibre GL chosen over Mapbox GL JS specifically for being
// open-source/no-API-key-required — see /docs/tech-stack-options.md.
// This demo style (OSM raster tiles) is a placeholder; picking a real
// basemap style/provider is unresolved (see /docs/open-questions.md if it
// grows into one).
const DEMO_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

/** Whether two bounding boxes describe the same box.
 *
 * The refit below compares by VALUE for a reason (D65, 2026-09-27). This
 * prop used to be documented as "callers own recomputing this only when
 * the thing being fit actually changes" — a contract that depended on
 * referential identity and was written down nowhere the callers could see
 * it. Five of six callers happened to honour it by memoising;
 * `QuickLogPage` passed an inline `positionsBounds(points)`, which returns
 * a fresh array every call, on a screen where `useWatchPosition` re-renders
 * on every GPS callback. Measured in a browser against that screen: five
 * simulated fixes produced **ten** `fitBounds` calls, and the map did not
 * merely drift — it jumped to the single dropped point at maxZoom. A user
 * who panned away was thrown back within about a second, every time.
 *
 * Memoising at that one call site would have closed that instance and left
 * the next caller free to reintroduce it. The decision "has the thing we
 * are fitting actually changed?" is made by the effect below, so the guard
 * belongs there (D33's question: does the chokepoint sit where the decision
 * is made?).
 */
function sameBounds(a: BBox | null, b: BBox | null): boolean {
  if (a === null || b === null) return a === b;
  return a[0] === b[0] && a[1] === b[1] && a[2] === b[2] && a[3] === b[3];
}

interface MapCanvasProps {
  /** [minLng, minLat, maxLng, maxLat] — when this changes *in value*, the
   * map zooms to fit it (e.g. a property's boundary). Passing a freshly
   * built array describing the same box is a no-op, so callers do not have
   * to memoise; re-fitting is driven by the box, not by render count. */
  bounds?: BBox | null;
  /** Fired once, after the map's initial style has loaded. Use this to add
   * sources/layers imperatively rather than via React children — MapLibre
   * isn't a React-children-based API. */
  onReady?: (map: MapLibreMap) => void;
  onClick?: (lngLat: maplibregl.LngLat) => void;
  /** Larger touch target + crosshair cursor while a draw tool is active. */
  drawing?: boolean;
}

export default function MapCanvas({ bounds, onReady, onClick, drawing }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  // Whether the map's one-time "load" event has already fired. Tracked
  // separately from map.loaded() (which reflects whether the *current
  // viewport's tiles* have finished loading, and can be false long after
  // the style itself is ready — e.g. while tiles are still retrying/
  // erroring) because the bounds effect below used to gate on
  // map.loaded() and register `map.once("load", fit)` when it was false.
  // A caller whose `bounds` prop only becomes available some time after
  // mount (e.g. PropertyMapPage, which renders the map immediately and
  // fetches the property separately, rather than gating render on the
  // fetch like the form pages do) would then race: by the time `bounds`
  // resolved, "load" had already fired once and consumed, so that
  // `.once("load", fit)` registration would wait for an event that would
  // never come again — silently leaving the map at its default world
  // view forever. Style-loaded state doesn't have that one-shot problem.
  const loadedRef = useRef(false);
  // The bounds the map has most recently been asked to fit, so an
  // identical box arriving as a new array is recognised as the same
  // request. Reset alongside the map itself below: a torn-down map is a
  // fresh map at the default world view, so it must be fitted again even
  // though the prop's value never changed.
  const requestedRef = useRef<BBox | null>(null);
  // Refs so the map-creation effect (which must run only once) always
  // calls the latest callback without needing to be in its dep array.
  const onReadyRef = useRef(onReady);
  onReadyRef.current = onReady;
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: DEMO_STYLE,
      center: [0, 20],
      zoom: 1.5,
      // Default attribution control anchors bottom-right, the same corner
      // as our FAB buttons (see .map-fabs in index.css) — it was silently
      // eating taps on "+ Activity"/"+ Sighting" once expanded. Move it
      // out of the way instead of fighting z-index.
      attributionControl: false,
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-left");
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: false,
      }),
      "top-right",
    );
    map.on("click", (e) => onClickRef.current?.(e.lngLat));
    map.on("load", () => {
      loadedRef.current = true;
      onReadyRef.current?.(map);
    });
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      loadedRef.current = false;
      requestedRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bounds) return;
    // Value comparison, not identity — see sameBounds above. Recorded
    // when *requested* rather than when the fit actually runs, so that a
    // burst of identity-only changes arriving before the style has loaded
    // registers one deferred fit instead of one per render.
    if (sameBounds(requestedRef.current, bounds)) return;
    requestedRef.current = bounds;
    const fit = () => {
      const [minLng, minLat, maxLng, maxLat] = bounds;
      map.fitBounds(
        [
          [minLng, minLat],
          [maxLng, maxLat],
        ],
        { padding: 56, maxZoom: 18, duration: 400 },
      );
    };
    if (loadedRef.current) fit();
    else map.once("load", fit);
  }, [bounds]);

  return (
    <div
      ref={containerRef}
      className="map-canvas"
      style={{ flex: 1, minHeight: 0, cursor: drawing ? "crosshair" : undefined }}
    />
  );
}
