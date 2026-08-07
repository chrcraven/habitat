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
    map.on("load", () => onReadyRef.current?.(map));
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
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
    if (map.loaded()) fit();
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
