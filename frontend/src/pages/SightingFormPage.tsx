import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import { ensureCircleLayer, ensureLineLayer, setGeoJsonSource } from "../components/mapLayers";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../api/client";
import type { Position } from "../api/types";
import { getCurrentPosition, mergeBounds, pointBounds, polygonBounds } from "../utils/geo";

const DRAW_SOURCE = "draw-sighting";

function toLocalDateTimeInputValue(date: Date): string {
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

export default function SightingFormPage() {
  const { id } = useParams<{ id: string }>();
  const propertyId = Number(id);
  const navigate = useNavigate();
  const [map, setMap] = useState<MapLibreMap | null>(null);

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const species = useAsync(() => api.species.list(), []);

  const [point, setPoint] = useState<Position | null>(null);
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState<string | null>(null);
  const [speciesId, setSpeciesId] = useState<number | "">("");
  const [newSpeciesName, setNewSpeciesName] = useState("");
  const [observedAt, setObservedAt] = useState(() => toLocalDateTimeInputValue(new Date()));
  const [notes, setNotes] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const propertyBounds = useMemo(
    () => (property.data?.geometry ? polygonBounds(property.data.geometry) : null),
    [property.data],
  );
  // Fit to the property until a point is placed, then fit to include the
  // point too, so placing a sighting near the edge doesn't get clipped.
  const bounds = useMemo(() => {
    if (point && propertyBounds) return mergeBounds(propertyBounds, pointBounds(point));
    if (point) return pointBounds(point);
    return propertyBounds;
  }, [point, propertyBounds]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(
      map,
      DRAW_SOURCE,
      point
        ? { type: "Point" as const, coordinates: point }
        : { type: "Point" as const, coordinates: [0, 0] },
    );
    ensureCircleLayer(map, "draw-sighting-circle", DRAW_SOURCE, "#2f5fc9");
    if (!point) map.setLayoutProperty("draw-sighting-circle", "visibility", "none");
    else map.setLayoutProperty("draw-sighting-circle", "visibility", "visible");
  }, [map, point]);

  useEffect(() => {
    if (!map || !property.data?.geometry) return;
    setGeoJsonSource(map, "property-context", property.data.geometry);
    ensureLineLayer(map, "property-context-line", "property-context", "#2f6f4f", 2);
  }, [map, property.data]);

  const useMyLocation = async () => {
    setLocating(true);
    setLocateError(null);
    try {
      const position = await getCurrentPosition();
      setPoint([position.coords.longitude, position.coords.latitude]);
    } catch (err) {
      setLocateError(err instanceof Error ? err.message : "Couldn't get your location.");
    } finally {
      setLocating(false);
    }
  };

  const handleMapClick = (lngLat: { lng: number; lat: number }) => {
    setPoint([lngLat.lng, lngLat.lat]);
  };

  const resolveSpeciesId = async (): Promise<number | null> => {
    if (speciesId !== "") return speciesId;
    if (!newSpeciesName.trim()) return null;
    const created = await api.species.create({ common_name: newSpeciesName.trim() });
    return created.id;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!point) {
      setError("Set a location for this sighting first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const resolvedSpeciesId = await resolveSpeciesId();
      if (!resolvedSpeciesId) {
        setError("Pick a species, or type a new one.");
        setSubmitting(false);
        return;
      }
      await api.sightings.create({
        property: propertyId,
        species: resolvedSpeciesId,
        location: { type: "Point", coordinates: point },
        observed_at: new Date(observedAt).toISOString(),
        notes,
        is_public: isPublic,
      });
      navigate(`/properties/${propertyId}`, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page page--map">
      <div className="page__header">
        <h1>Log a sighting</h1>
        <Link to={`/properties/${propertyId}`} className="btn btn-ghost btn-small">
          Cancel
        </Link>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={bounds} onClick={handleMapClick} />
        <div className="map-overlay map-overlay--top">
          {point ? "Tap the map to adjust the location." : "Tap the map to set the location."}
        </div>
        <div className="map-overlay map-overlay--bottom">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={useMyLocation}
            disabled={locating}
          >
            {locating ? "Locating…" : "📍 Use my location"}
          </button>
        </div>
      </div>
      {locateError && <p className="form-error form-error--inline">{locateError}</p>}

      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}

        <label className="field">
          <span>Species</span>
          <select
            value={speciesId}
            onChange={(e) => {
              setSpeciesId(e.target.value ? Number(e.target.value) : "");
              if (e.target.value) setNewSpeciesName("");
            }}
          >
            <option value="">— Select or add new below —</option>
            {species.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.common_name}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Or add a new species</span>
          <input
            type="text"
            placeholder="Common name"
            value={newSpeciesName}
            onChange={(e) => {
              setNewSpeciesName(e.target.value);
              if (e.target.value) setSpeciesId("");
            }}
          />
        </label>

        <label className="field">
          <span>Observed at</span>
          <input
            type="datetime-local"
            required
            value={observedAt}
            onChange={(e) => setObservedAt(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Notes</span>
          <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>

        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
          <span>Show on the public view (no public view exists yet in Phase 1)</span>
        </label>

        <button type="submit" className="btn btn-primary" disabled={submitting || !point}>
          {submitting ? "Saving…" : "Save sighting"}
        </button>
      </form>
    </div>
  );
}
