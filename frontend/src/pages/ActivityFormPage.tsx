import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PhotoUploader from "../components/PhotoUploader";
import PostSavePhotoStep from "../components/PostSavePhotoStep";
import LinkedRecordsPanel from "../components/LinkedRecordsPanel";
import ActivitySpeciesPanel from "../components/ActivitySpeciesPanel";
import RecordNotFound from "../components/RecordNotFound";
import { AttributionNote } from "../components/AttributionNote";
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
import { mergeBounds, polygonBounds } from "../utils/geo";
import { parseRouteId } from "../utils/ids";
import { returnTargetFrom } from "../utils/returnTo";
import { LoadError } from "../components/LoadError";
import { useDocumentTitle } from "../utils/documentTitle";

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
  // Where this form was opened from, when the opener said so. The list
  // pages built for finding a record (ActivitiesPage, SightingsPage) and
  // the dashboard all pass `?next=`; a link from the property's own page
  // doesn't, because that is already where these exits lead (D66a).
  //
  // The captured value is run through the same gate as every other
  // `?next=` in this app — an edit URL is shareable, so an unchecked value
  // here is an open redirect, and the Cancel control below is a real
  // `<a href>`, not a navigate() call.
  const { search } = useLocation();
  const doneTo = returnTargetFrom(search) ?? `/properties/${property.id}`;
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
  // The shape as it was when this form opened, deliberately NOT the live
  // `points` list below. Keyed on `existing` so it is computed once, on
  // load, and never again while the user is drawing.
  const existingShapeBounds = useMemo(
    () => (existing?.geometry ? polygonBounds(existing.geometry) : null),
    [existing],
  );
  // Fit to the property AND the shape being edited, so an activity drawn
  // outside its property's boundary is on screen while you work on it.
  // Before this, the viewport was the property alone (SightingFormPage has
  // merged since it was written; this file never did — D84a, 2026-10-02),
  // which put the one case you most need to see off the screen: the only
  // drawing affordances here are Undo and Clear, so an out-of-boundary
  // shape could not be seen while being undone.
  //
  // Two properties of this that are easy to undo by accident:
  //
  // 1. It merges `existingShapeBounds`, never `positionsBounds(points)`.
  //    The live list looks like the obvious source, and measured in a
  //    browser it re-fits the map every time the vertex list changes —
  //    pressing Clear alone jumped the camera back to the property. That
  //    is the D65 defect this repo already fixed (there, the map landed on
  //    the newest point at maxZoom, so a pan could not survive a second).
  //    Note this is NOT an argument that SightingFormPage's live `point`
  //    is harmless — it re-fits too, and `pointBounds` pads ±0.002°
  //    (~222 m), which on a small property is wider than the property
  //    itself. What makes it tolerable there is that placing a sighting is
  //    a single tap, not a sequence you work through; drawing a polygon is
  //    the sequence, which is why this file must not copy that shape.
  // 2. For a shape inside its property, mergeBounds returns the property's
  //    own bounds unchanged, so this is a no-op for every record that is
  //    where it claims to be. Only an out-of-boundary shape moves the
  //    viewport at all.
  const bounds = useMemo(() => {
    if (propertyBounds && existingShapeBounds) {
      return mergeBounds(propertyBounds, existingShapeBounds);
    }
    return existingShapeBounds ?? propertyBounds;
  }, [propertyBounds, existingShapeBounds]);

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
  /** Set once a *new* activity has been created, which switches this page
   * to the photo step. Never set when editing — an edit form already has
   * its own Photos panel below. */
  const [savedId, setSavedId] = useState<number | null>(null);
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
  // Feeds the "link a sighting" picker — labels only. This page's map
  // draws the activity being edited and the property boundary, never
  // these sightings. See `api.sightings.listWithoutGeometry`.
  const propertySightings = useAsync(
    () =>
      existing
        ? api.sightings.listWithoutGeometry(property.id)
        : Promise.resolve({ type: "FeatureCollection" as const, features: [] }),
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

  // Live device position, for drawing a boundary by walking it and
  // dropping a pin at each corner rather than only tapping a rendered map.
  //
  // Opt-in, and deliberately so (D69, 2026-09-25). This used to be
  // `useWatchPosition(true)` — a continuous `enableHighAccuracy: true`
  // watch running from the moment the page opened until it closed, on one
  // of the two screens a user sits on longest (notes, two dates, species,
  // status, then the photo step). It ran whether or not "Drop pin here"
  // was ever touched, so the common case — drawing by tapping the map at a
  // desk — paid a GPS watch for the whole session, and every visitor got a
  // browser location prompt before they had expressed any interest in
  // location at all.
  //
  // The toggle copies PropertyMapPage's own "Show my current location"
  // switch rather than inventing a convention: same `.visibility-toggle` /
  // `.switch` markup, same default-off. The two siblings that were already
  // scoped stay as they are — QuickLogPage keys on `step === "capture"`,
  // which is a real boundary; these form pages have no such step, the map
  // and the fields are one scrolling page, so an explicit toggle is the
  // only honest signal that someone wants their location read.
  //
  // Not persisted. Habitat keeps no per-user state at all and whether it
  // should is the owner's open question (D66b); defaulting off every visit
  // is the conservative half of that and needs no decision.
  const [useMyLocation, setUseMyLocation] = useState(false);
  const liveLocation = useWatchPosition(useMyLocation);

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
        // A brand-new activity gets the photo step rather than leaving
        // straight away — photos hang off a saved record's id, so this is
        // the first moment one can be attached, and until now that meant
        // saving, reopening the record, and uploading from the edit form.
        // Quick log set this precedent on 2026-09-03; see
        // components/PostSavePhotoStep.
        const created = await api.activities.create({ property: property.id, ...payload });
        setSavedId(created.id);
        return; // `finally` below still clears the submitting flag.
      }
      navigate(doneTo, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  if (savedId !== null) {
    return (
      <PostSavePhotoStep
        kind="activity"
        recordId={savedId}
        onFinish={() => navigate(doneTo, { replace: true })}
      />
    );
  }

  return (
    <div className="page page--map">
      <div className="page__header">
        <h1>{existing ? "Edit activity" : "Log an activity"}</h1>
        <Link to={doneTo} className="btn btn-ghost btn-small">
          Cancel
        </Link>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={bounds} onClick={handleClick} drawing />
        <div className="map-overlay map-overlay--top">
          {points.length === 0
            ? useMyLocation
              ? "Tap the map, or drop a pin at your location, to draw the area this activity covers."
              : "Tap the map to draw the area this activity covers. To drop pins where you're standing, turn on \u201cUse my location\u201d below."
            : `${points.length} point${points.length === 1 ? "" : "s"} placed${
                canFinish ? " — shape ready." : " — need at least 3."
              }`}
        </div>
        <div className="map-overlay map-overlay--bottom">
          {useMyLocation && (
            <button
              type="button"
              className="btn btn-primary btn-small"
              onClick={handleDropPinAtLocation}
              disabled={!liveLocation.position}
            >
              📍 Drop pin here
            </button>
          )}
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
      <div className="visibility-toggle">
        <label className="switch">
          <input
            type="checkbox"
            checked={useMyLocation}
            onChange={(e) => setUseMyLocation(e.target.checked)}
          />
          <span>Use my location (lets you drop pins where you're standing)</span>
        </label>
      </div>
      {useMyLocation && liveLocation.error && (
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
          {/* D19: this used to read "Show on the public view (no public view
            * exists yet in Phase 1)" — a parenthetical left over from before
            * the public site shipped (2026-08-14). It was the only on-screen
            * account of what this flag does, and it denied that the flag does
            * anything, while the flag is what publishes this activity's
            * geometry, dates, notes, species and photos to anyone with the
            * URL. Wording matches SightingFormPage/PropertyFormPage/
            * QuickLogPage deliberately: one vocabulary ("the public site",
            * which is also the nav entry and the manual's term) across all
            * four forms is what stops this drifting again. */}
          <span>Show on the public site</span>
        </label>

        {/* Who made this, and who touched it last. Placed directly above
          * the save button rather than at the top of the form, because
          * this form PATCHes every field from the snapshot it opened with
          * (D29) — so the moment it matters is the moment before you
          * overwrite somebody else's edit, not the moment you arrive. */}
        {existing && (
          <AttributionNote
            created={{
              by: existing.properties.created_by_email,
              at: existing.properties.created_at,
            }}
            updated={{
              by: existing.properties.updated_by_email,
              at: existing.properties.updated_at,
            }}
          />
        )}

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
              note: `Linked by ${l.linked_by_email ?? "unknown"}`,
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

/** Guards both route parameters before any request is issued — see
 * utils/ids.ts. A `NaN` id here 404'd rather than 500ing (it only ever
 * reached detail routes), but it still issued a request the app already
 * knew was malformed and showed a generic failure where "no such property"
 * was the truth. */
export default function ActivityFormPage() {
  const { id, activityId } = useParams<{ id: string; activityId?: string }>();
  const propertyId = parseRouteId(id);
  // `activityId` absent means "new activity"; present-but-unusable is a
  // mistyped edit URL, which is a different thing and not a create form.
  const parsedActivityId = activityId === undefined ? undefined : parseRouteId(activityId);
  const badId = propertyId === null || parsedActivityId === null;
  useDocumentTitle(
    badId ? "Not found" : activityId === undefined ? "Log an activity" : "Edit activity",
  );
  if (propertyId === null) return <RecordNotFound what="property" />;
  if (parsedActivityId === null) {
    return (
      <RecordNotFound
        what="activity"
        backTo={`/properties/${propertyId}`}
        backLabel="← Back to property"
      />
    );
  }
  return <ActivityFormLoader propertyId={propertyId} activityId={parsedActivityId} />;
}

function ActivityFormLoader({
  propertyId,
  activityId,
}: {
  propertyId: number;
  activityId: number | undefined;
}) {
  const isEdit = activityId !== undefined;

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const workflowStates = useAsync(() => api.workflowStates.list(), []);
  const activityTypes = useAsync(() => api.activityTypes.list(), []);
  const existing = useAsync(
    () => (activityId !== undefined ? api.activities.get(activityId) : Promise.resolve(null)),
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
    // Retries all four — see SightingFormPage's twin for why (D63a).
    const retry = () => {
      property.reload();
      workflowStates.reload();
      activityTypes.reload();
      existing.reload();
    };
    return (
      <div style={{ padding: "1rem" }}>
        <LoadError
          what="this page"
          error={
            property.error ?? workflowStates.error ?? activityTypes.error ?? existing.error ?? ""
          }
          onRetry={retry}
        />
      </div>
    );
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
