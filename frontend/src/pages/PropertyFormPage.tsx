import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import {
  ensureCircleLayer,
  ensureFillLayer,
  ensureLineLayer,
  ensureUserLocationLayer,
  setGeoJsonSource,
} from "../components/mapLayers";
import { usePolygonPoints } from "../hooks/usePolygonPoints";
import { useAsync } from "../hooks/useAsync";
import { useWatchPosition } from "../hooks/useWatchPosition";
import { api, ApiError } from "../api/client";
import type { Position, Property } from "../api/types";
import { polygonBounds } from "../utils/geo";

const DRAW_SOURCE = "draw-boundary";
const VERTICES_SOURCE = "draw-boundary-vertices";
const USER_LOCATION_SOURCE = "user-location";

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
  const [isPublic, setIsPublic] = useState(existing?.properties.is_public ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Zoom to the property's already-drawn boundary when opening the edit
  // form — previously this map always opened at the default world view
  // even when editing a property that already had a shape (bug: the
  // *new*-property flow never needed this since there's nothing to fit
  // yet, but re-opening an existing one to tweak it did). Doesn't refit
  // continuously while adding new points below — that would fight the
  // user's own pan/zoom mid-draw.
  const existingBounds = useMemo(
    () => (existing?.geometry ? polygonBounds(existing.geometry) : null),
    [existing],
  );

  // Live device position — lets you draw a property boundary by walking
  // it and dropping a pin at each corner, same as ActivityFormPage.
  const liveLocation = useWatchPosition(true);

  useEffect(() => {
    if (!map) return;
    const data = geometry ?? { type: "Polygon" as const, coordinates: [] };
    setGeoJsonSource(map, DRAW_SOURCE, data);
    ensureFillLayer(map, "draw-boundary-fill", DRAW_SOURCE, "#2f6f4f", 0.2);
    ensureLineLayer(map, "draw-boundary-line", DRAW_SOURCE, "#2f6f4f", 3);
  }, [map, geometry]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, VERTICES_SOURCE, {
      type: "FeatureCollection",
      features: points.map((p) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: p }, properties: {} })),
    });
    ensureCircleLayer(map, "draw-boundary-vertices-circle", VERTICES_SOURCE, "#2f6f4f", 5);
  }, [map, points]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(
      map,
      USER_LOCATION_SOURCE,
      liveLocation.position
        ? { type: "Point" as const, coordinates: liveLocation.position }
        : { type: "Point" as const, coordinates: [0, 0] },
    );
    ensureUserLocationLayer(map, USER_LOCATION_SOURCE);
    const visibility = liveLocation.position ? "visible" : "none";
    map.setLayoutProperty(`${USER_LOCATION_SOURCE}-halo`, "visibility", visibility);
    map.setLayoutProperty(`${USER_LOCATION_SOURCE}-dot`, "visibility", visibility);
  }, [map, liveLocation.position]);

  const handleClick = (lngLat: { lng: number; lat: number }) => {
    addPoint([lngLat.lng, lngLat.lat] as Position);
  };

  const handleDropPinAtLocation = () => {
    if (liveLocation.position) addPoint(liveLocation.position);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const property = existing
        ? await api.properties.update(existing.id, { name, boundary: geometry, is_public: isPublic })
        : await api.properties.create({ name, boundary: geometry, is_public: isPublic });
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
        <MapCanvas onReady={setMap} onClick={handleClick} drawing bounds={existingBounds} />
        <div className="map-overlay map-overlay--top">
          {points.length === 0
            ? "Tap the map, or drop a pin at your location, to draw the property boundary (optional — you can draw it later)."
            : `${points.length} point${points.length === 1 ? "" : "s"} placed.`}
        </div>
        <div className="map-overlay map-overlay--bottom">
          <button
            type="button"
            className="btn btn-primary btn-small"
            onClick={handleDropPinAtLocation}
            disabled={!liveLocation.position}
          >
            📍 Drop pin here
          </button>
          <button type="button" className="btn btn-secondary btn-small" onClick={undo} disabled={points.length === 0}>
            Undo
          </button>
          <button type="button" className="btn btn-secondary btn-small" onClick={reset} disabled={points.length === 0}>
            Clear
          </button>
        </div>
      </div>
      {liveLocation.error && (
        <p className="form-error form-error--inline">
          Location unavailable ({liveLocation.error}) — you can still tap the map to place points.
        </p>
      )}

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
        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
          <span>Show this property on the public site (its public activities/sightings still each need their own public flag too)</span>
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
