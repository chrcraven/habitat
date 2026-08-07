import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PhotoUploader from "../components/PhotoUploader";
import { ensureFillLayer, ensureLineLayer, setGeoJsonSource } from "../components/mapLayers";
import { usePolygonPoints } from "../hooks/usePolygonPoints";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { api, ApiError } from "../api/client";
import type { Activity, ActivityType, Position, Property, WorkflowState } from "../api/types";
import { polygonBounds } from "../utils/geo";

const DRAW_SOURCE = "draw-activity";

const ACTIVITY_TYPES: { value: ActivityType; label: string }[] = [
  { value: "seeding", label: "Seeding" },
  { value: "planting", label: "Planting" },
  { value: "treatment", label: "Treatment" },
  { value: "removal", label: "Removal" },
  { value: "monitoring", label: "Monitoring" },
  { value: "maintenance", label: "Maintenance" },
  { value: "intervention", label: "Intervention (general)" },
  { value: "other", label: "Other" },
];

function ActivityForm({
  property,
  workflowStates,
  existing,
}: {
  property: Property;
  workflowStates: WorkflowState[];
  existing: Activity | null;
}) {
  const navigate = useNavigate();
  const { session } = useAuth();
  const canDeletePhotos = roleAtLeast(session?.membership?.role, "admin");
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const { points, addPoint, undo, reset, geometry, canFinish } = usePolygonPoints(
    existing?.geometry?.coordinates[0],
  );

  const propertyBounds = useMemo(
    () => (property.geometry ? polygonBounds(property.geometry) : null),
    [property],
  );

  const [activityType, setActivityType] = useState<ActivityType>(
    existing?.properties.activity_type ?? "planting",
  );
  const [status, setStatus] = useState<number | "">(
    existing?.properties.status ??
      workflowStates.find((s) => s.is_planned)?.id ??
      workflowStates[0]?.id ??
      "",
  );
  const [datePlanned, setDatePlanned] = useState(existing?.properties.date_planned ?? "");
  const [dateDone, setDateDone] = useState(existing?.properties.date_done ?? "");
  const [notes, setNotes] = useState(existing?.properties.notes ?? "");
  const [isPublic, setIsPublic] = useState(existing?.properties.is_public ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const photos = useAsync(
    () => (existing ? api.activities.photos.list(existing.id) : Promise.resolve([])),
    [existing?.id],
  );

  useEffect(() => {
    if (!map) return;
    const data = geometry ?? { type: "Polygon" as const, coordinates: [] };
    setGeoJsonSource(map, DRAW_SOURCE, data);
    ensureFillLayer(map, "draw-activity-fill", DRAW_SOURCE, "#c9782f", 0.3);
    ensureLineLayer(map, "draw-activity-line", DRAW_SOURCE, "#c9782f", 3);
  }, [map, geometry]);

  // Also show the property boundary for context while drawing.
  useEffect(() => {
    if (!map || !property.geometry) return;
    setGeoJsonSource(map, "property-context", property.geometry);
    ensureLineLayer(map, "property-context-line", "property-context", "#2f6f4f", 2);
  }, [map, property.geometry]);

  const handleClick = (lngLat: { lng: number; lat: number }) => {
    addPoint([lngLat.lng, lngLat.lat] as Position);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!geometry || status === "") return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        activity_type: activityType,
        status,
        geometry,
        date_planned: datePlanned || null,
        date_done: dateDone || null,
        notes,
        is_public: isPublic,
      };
      if (existing) {
        await api.activities.update(existing.id, payload);
      } else {
        await api.activities.create({ property: property.id, ...payload });
      }
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
        <h1>{existing ? "Edit activity" : "Log an activity"}</h1>
        <Link to={`/properties/${property.id}`} className="btn btn-ghost btn-small">
          Cancel
        </Link>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={propertyBounds} onClick={handleClick} drawing />
        <div className="map-overlay map-overlay--top">
          {points.length === 0
            ? "Tap the map to draw the area this activity covers."
            : `${points.length} point${points.length === 1 ? "" : "s"} placed${
                canFinish ? " — shape ready." : " — need at least 3."
              }`}
        </div>
        <div className="map-overlay map-overlay--bottom">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={undo}
            disabled={points.length === 0}
          >
            Undo point
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={reset}
            disabled={points.length === 0}
          >
            Clear
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}

        <label className="field">
          <span>Activity type</span>
          <select
            value={activityType}
            onChange={(e) => setActivityType(e.target.value as ActivityType)}
          >
            {ACTIVITY_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="" disabled>
              Select a status
            </option>
            {workflowStates.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>

        <div className="field-row">
          <label className="field">
            <span>Date planned</span>
            <input
              type="date"
              value={datePlanned}
              onChange={(e) => setDatePlanned(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Date done</span>
            <input type="date" value={dateDone} onChange={(e) => setDateDone(e.target.value)} />
          </label>
        </div>

        <label className="field">
          <span>Notes</span>
          <textarea
            rows={3}
            placeholder="Conditions, quantities, follow-up needed…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>

        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
          <span>Show on the public view (no public view exists yet in Phase 1)</span>
        </label>

        {existing && (
          <div className="field">
            <span>Photos</span>
            <PhotoUploader
              photos={photos.data ?? []}
              canDelete={canDeletePhotos}
              onUpload={async (file) => {
                await api.activities.photos.upload(existing.id, file);
                photos.reload();
              }}
              onDelete={async (photoId) => {
                await api.activities.photos.remove(existing.id, photoId);
                photos.reload();
              }}
            />
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || !canFinish || status === ""}
        >
          {submitting ? "Saving…" : "Save activity"}
        </button>
      </form>
    </div>
  );
}

export default function ActivityFormPage() {
  const { id, activityId } = useParams<{ id: string; activityId?: string }>();
  const propertyId = Number(id);
  const isEdit = activityId !== undefined;

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const workflowStates = useAsync(() => api.workflowStates.list(), []);
  const existing = useAsync(
    () => (isEdit ? api.activities.get(Number(activityId)) : Promise.resolve(null)),
    [activityId],
  );

  const loading = property.loading || workflowStates.loading || (isEdit && existing.loading);
  const failed = property.error || workflowStates.error || (isEdit && (existing.error || !existing.data));

  if (loading) return <div className="full-page-status">Loading…</div>;
  if (failed || !property.data || !workflowStates.data) {
    return <p className="form-error" style={{ padding: "1rem" }}>Couldn't load this page.</p>;
  }

  return (
    <ActivityForm
      property={property.data}
      workflowStates={workflowStates.data}
      existing={existing.data ?? null}
    />
  );
}
