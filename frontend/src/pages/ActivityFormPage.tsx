import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PhotoUploader from "../components/PhotoUploader";
import LinkedRecordsPanel from "../components/LinkedRecordsPanel";
import ActivitySpeciesPanel from "../components/ActivitySpeciesPanel";
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
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { api, ApiError } from "../api/client";
import type { Activity, ActivityType, Position, Property, WorkflowState } from "../api/types";
import { polygonBounds } from "../utils/geo";

const DRAW_SOURCE = "draw-activity";
const VERTICES_SOURCE = "draw-activity-vertices";
const USER_LOCATION_SOURCE = "user-location";

function ActivityForm({
  property,
  workflowStates,
  activityTypes,
  existing,
}: {
  property: Property;
  workflowStates: WorkflowState[];
  /** The org's own activity types — no longer a hardcoded enum in this
   * file (org-defined since 2026-09-02), so they're loaded alongside the
   * workflow states and passed in the same way. */
  activityTypes: ActivityType[];
  existing: Activity | null;
}) {
  const navigate = useNavigate();
  const { session } = useAuth();
  const canDeletePhotos = roleAtLeast(session?.membership?.role, "admin");
  const canEditLinks = roleAtLeast(session?.membership?.role, "editor");
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const { points, addPoint, undo, reset, geometry, canFinish } = usePolygonPoints(
    existing?.geometry?.coordinates[0],
  );

  const propertyBounds = useMemo(
    () => (property.geometry ? polygonBounds(property.geometry) : null),
    [property],
  );

  const [activityType, setActivityType] = useState<number | "">(
    existing?.properties.activity_type ?? activityTypes[0]?.id ?? "",
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

  // Direct Sighting↔Activity link — see LinkedRecordsPanel and
  // SightingFormPage's matching section for the sighting side of this
  // same relationship.
  const links = useAsync(
    () => (existing ? api.activities.links.list(existing.id) : Promise.resolve([])),
    [existing?.id],
  );
  const propertySightings = useAsync(
    () => (existing ? api.sightings.list(property.id) : Promise.resolve({ type: "FeatureCollection" as const, features: [] })),
    [existing?.id, property.id],
  );

  // Activity↔Species (role/quantity/detail per species) — see
  // ActivitySpeciesPanel for why this is its own endpoint rather than a
  // writable field on the activity itself.
  const speciesLinks = useAsync(
    () => (existing ? api.activities.species.list(existing.id) : Promise.resolve([])),
    [existing?.id],
  );
  const orgSpecies = useAsync(() => api.species.list(), []);

  // Live device position — powers both the "you are here" map marker and
  // the "drop pin at my location" button below, for drawing a boundary by
  // walking it in the field rather than only tapping a rendered map.
  const liveLocation = useWatchPosition(true);

  useEffect(() => {
    if (!map) return;
    const data = geometry ?? { type: "Polygon" as const, coordinates: [] };
    setGeoJsonSource(map, DRAW_SOURCE, data);
    ensureFillLayer(map, "draw-activity-fill", DRAW_SOURCE, "#c9782f", 0.3);
    ensureLineLayer(map, "draw-activity-line", DRAW_SOURCE, "#c9782f", 3);
  }, [map, geometry]);

  // Marker per dropped vertex — visible feedback as soon as the first pin
  // goes down, before there are enough points for the polygon preview
  // above to render anything at all.
  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, VERTICES_SOURCE, {
      type: "FeatureCollection",
      features: points.map((p) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: p }, properties: {} })),
    });
    ensureCircleLayer(map, "draw-activity-vertices-circle", VERTICES_SOURCE, "#c9782f", 5);
  }, [map, points]);

  // Also show the property boundary for context while drawing.
  useEffect(() => {
    if (!map || !property.geometry) return;
    setGeoJsonSource(map, "property-context", property.geometry);
    ensureLineLayer(map, "property-context-line", "property-context", "#2f6f4f", 2);
  }, [map, property.geometry]);

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
    if (!geometry || status === "" || activityType === "") return;
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
            className="btn btn-primary btn-small"
            onClick={handleDropPinAtLocation}
            disabled={!liveLocation.position}
          >
            📍 Drop pin here
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={undo}
            disabled={points.length === 0}
          >
            Undo
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
      <div className="map-page-scroll">
      {liveLocation.error && (
        <p className="form-error form-error--inline">
          Location unavailable ({liveLocation.error}) — you can still tap the map to place points.
        </p>
      )}

      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}

        <label className="field">
          <span>Activity type</span>
          <select
            value={activityType}
            onChange={(e) => setActivityType(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="" disabled>
              Select a type
            </option>
            {activityTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
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

        {existing && (
          <ActivitySpeciesPanel
            canEdit={canEditLinks}
            links={speciesLinks.data ?? []}
            options={(orgSpecies.data ?? []).filter(
              (s) => !(speciesLinks.data ?? []).some((l) => l.species === s.id),
            )}
            onAdd={async (data) => {
              await api.activities.species.create(existing.id, data);
              speciesLinks.reload();
            }}
            onUpdate={async (linkId, data) => {
              await api.activities.species.update(existing.id, linkId, data);
              speciesLinks.reload();
            }}
            onRemove={async (linkId) => {
              await api.activities.species.remove(existing.id, linkId);
              speciesLinks.reload();
            }}
          />
        )}

        {existing && (
          <LinkedRecordsPanel
            title="Linked sightings"
            canEdit={canEditLinks}
            links={(links.data ?? []).map((l) => ({
              id: l.id,
              label: `${l.sighting_species} — ${new Date(l.sighting_observed_at).toLocaleDateString()}`,
            }))}
            options={(propertySightings.data?.features ?? [])
              .filter((s) => !(links.data ?? []).some((l) => l.sighting === s.id))
              .map((s) => ({
                id: s.id,
                label: `${s.properties.species_detail.common_name} — ${new Date(
                  s.properties.observed_at,
                ).toLocaleDateString()}`,
              }))}
            emptyOptionsLabel="No other sightings on this property yet."
            onLink={async (sightingId) => {
              await api.activities.links.create(existing.id, sightingId);
              links.reload();
            }}
            onUnlink={async (linkId) => {
              await api.activities.links.remove(existing.id, linkId);
              links.reload();
            }}
          />
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
    </div>
  );
}

export default function ActivityFormPage() {
  const { id, activityId } = useParams<{ id: string; activityId?: string }>();
  const propertyId = Number(id);
  const isEdit = activityId !== undefined;

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const workflowStates = useAsync(() => api.workflowStates.list(), []);
  const activityTypes = useAsync(() => api.activityTypes.list(), []);
  const existing = useAsync(
    () => (isEdit ? api.activities.get(Number(activityId)) : Promise.resolve(null)),
    [activityId],
  );

  const loading =
    property.loading || workflowStates.loading || activityTypes.loading || (isEdit && existing.loading);
  const failed =
    property.error ||
    workflowStates.error ||
    activityTypes.error ||
    (isEdit && (existing.error || !existing.data));

  if (loading) return <div className="full-page-status">Loading…</div>;
  if (failed || !property.data || !workflowStates.data || !activityTypes.data) {
    return <p className="form-error" style={{ padding: "1rem" }}>Couldn't load this page.</p>;
  }

  return (
    <ActivityForm
      property={property.data}
      workflowStates={workflowStates.data}
      activityTypes={activityTypes.data}
      existing={existing.data ?? null}
    />
  );
}
