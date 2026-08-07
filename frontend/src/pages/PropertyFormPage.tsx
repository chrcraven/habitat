import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import { ensureFillLayer, ensureLineLayer, setGeoJsonSource } from "../components/mapLayers";
import { usePolygonPoints } from "../hooks/usePolygonPoints";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../api/client";
import type { Position, Property } from "../api/types";

const DRAW_SOURCE = "draw-boundary";

/** Handles both /properties/new and /properties/:id/edit — split out so
 * `usePolygonPoints` gets the existing boundary (if any) on its very
 * first mount rather than needing to react to it arriving later. */
function PropertyForm({ existing }: { existing: Property | null }) {
  const navigate = useNavigate();
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const { points, addPoint, undo, reset, geometry } = usePolygonPoints(
    existing?.geometry?.coordinates[0],
  );
  const [name, setName] = useState(existing?.properties.name ?? "");
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
      const property = existing
        ? await api.properties.update(existing.id, { name, boundary: geometry })
        : await api.properties.create({ name, boundary: geometry });
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
        <h1>{existing ? "Edit property" : "New property"}</h1>
        <Link
          to={existing ? `/properties/${existing.id}` : "/properties"}
          className="btn btn-ghost btn-small"
        >
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

export default function PropertyFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = id !== undefined;
  const existing = useAsync(
    () => (isEdit ? api.properties.get(Number(id)) : Promise.resolve(null)),
    [id],
  );

  if (isEdit && existing.loading) {
    return <div className="full-page-status">Loading…</div>;
  }
  if (isEdit && (existing.error || !existing.data)) {
    return <p className="form-error" style={{ padding: "1rem" }}>Couldn't load that property.</p>;
  }

  return <PropertyForm existing={existing.data} />;
}
