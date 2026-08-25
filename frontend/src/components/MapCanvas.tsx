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

interface MapCanvasProps {
  /** [minLng, minLat, maxLng, maxLat] — when this changes, the map zooms
   * to fit it (e.g. a property's boundary). Callers own recomputing this
   * only when the thing being fit actually changes, not on every render. */
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
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bounds) return;
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
