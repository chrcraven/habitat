import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import { ensureFillLayer, ensureLineLayer, setGeoJsonSource } from "../components/mapLayers";
import { usePolygonPoints } from "../hooks/usePolygonPoints";
import { api, ApiError } from "../api/client";
import type { Position } from "../api/types";

const DRAW_SOURCE = "draw-boundary";

export default function PropertyFormPage() {
  const navigate = useNavigate();
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const { points, addPoint, undo, reset, geometry } = usePolygonPoints();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!map) return;
    const data = geometry ?? { type: "Polygon" as const, coordinates: [] };
    setGeoJsonSource(map, DRAW_SOURCE, data);
    ensureFillLayer(map, "draw-boundary-fill", DRAW_SOURCE, "#2f6f4f", 0.2);
    ensureLineLayer(map, "draw-boundary-line", DRAW_SOURCE, "#2f6f4f", 3);
  }, [map, geometry]);

  const handleClick = (lngLat: { lng: number; lat: number }) => {
    addPoint([lngLat.lng, lngLat.lat] as Position);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const property = await api.properties.create({ name, boundary: geometry });
      navigate(`/properties/${property.id}`, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page page--map">
      <div className="page__header">
        <h1>New property</h1>
        <Link to="/properties" className="btn btn-ghost btn-small">
          Cancel
        </Link>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} onClick={handleClick} drawing />
        <div className="map-overlay map-overlay--top">
          {points.length === 0
            ? "Tap the map to draw the property boundary (optional — you can draw it later)."
            : `${points.length} point${points.length === 1 ? "" : "s"} placed.`}
        </div>
        <div className="map-overlay map-overlay--bottom">
          <button type="button" className="btn btn-secondary btn-small" onClick={undo} disabled={points.length === 0}>
            Undo point
          </button>
          <button type="button" className="btn btn-secondary btn-small" onClick={reset} disabled={points.length === 0}>
            Clear
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}
        <label className="field">
          <span>Property name</span>
          <input
            type="text"
            autoFocus
            required
            placeholder="e.g. Back Yard"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <button type="submit" className="btn btn-primary" disabled={submitting || !name}>
          {submitting ? "Saving…" : "Save property"}
        </button>
      </form>
    </div>
  );
}
