import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PhotoUploader from "../components/PhotoUploader";
import Combobox from "../components/Combobox";
import {
  ensureCircleLayer,
  ensureFillLayer,
  ensureLineLayer,
  ensureUserLocationLayer,
  setGeoJsonSource,
} from "../components/mapLayers";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { usePolygonPoints } from "../hooks/usePolygonPoints";
import { useWatchPosition } from "../hooks/useWatchPosition";
import { mergeBounds, polygonBounds, positionInPolygon, positionsBounds } from "../utils/geo";
import type { BBox } from "../utils/geo";
import type { Photo, PointGeometry, Position, Property } from "../api/types";

const PROPERTIES_SOURCE = "quick-log-properties";
const DRAW_SOURCE = "quick-log-draw";
const VERTICES_SOURCE = "quick-log-vertices";
const USER_LOCATION_SOURCE = "user-location";

/** What the points placed so far can become. One point is a sighting;
 * three or more enclose an area, so they're an activity. Two is the one
 * genuinely ambiguous count — too many for a sighting, too few for a
 * polygon — and is called out rather than guessed at. */
type Intent = "sighting" | "activity" | "incomplete";

function intentFor(pointCount: number): Intent {
  if (pointCount === 1) return "sighting";
  if (pointCount >= 3) return "activity";
  return "incomplete";
}

/**
 * Quick log — the geometry-first capture flow (owner decision,
 * 2026-09-02, from user feedback: *"User would enter that space, drop a
 * point for a sighting, or drop more to define an activity area. After
 * area or point is defined then subsequent popups would collect more
 * info."*).
 *
 * Three deliberate shape decisions, all recorded in build-questions.md:
 *
 * - **An additional mode, not a replacement.** ActivityFormPage and
 *   SightingFormPage are untouched and still handle editing; this is a
 *   second way in, reached from the dashboard.
 * - **Geometry decides the record type**, rather than the user choosing
 *   up front. Dropping one point means a sighting; enclosing an area
 *   means an activity. That's what makes it geometry-*first* — you place
 *   what you see, and the app works out what kind of record that is.
 * - **The property is inferred from where the points land** (see
 *   utils/geo.ts#positionInPolygon), so "which property?" isn't a step.
 *   It stays overridable, and a point outside every boundary falls back
 *   to asking, which is also the only way to log a sighting with no
 *   property at all.
 *
 * The map gets the whole screen while capturing — this is the same
 * feedback's *"rough issue with real estate screen space on phone"*, and
 * a capture screen that isn't sharing the viewport with a form is the
 * cheapest real answer to it. The detail step then takes over the screen
 * in turn, so neither half is ever squeezed.
 *
 * **No draft persistence** (recorded default): backing out discards the
 * capture. A half-finished quick log is cheap to redo, and a real draft
 * model is its own feature rather than something to infer here.
 */
export default function QuickLogPage() {
  const navigate = useNavigate();
  const { session } = useAuth();
  // Photo delete is admin-only on the backend (ensure_role), same as on
  // the edit forms — don't offer a control that would 403.
  const canDeletePhotos = roleAtLeast(session?.membership?.role, "admin");
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const { points, addPoint, undo, reset, geometry } = usePolygonPoints();
  const [step, setStep] = useState<"capture" | "detail" | "photos">("capture");
  /** The record that was just created, once there is one — what the photo
   * step uploads against. Photos are nested under a saved record's id, so
   * this step can only exist after the save, which is also exactly what
   * the feedback asked for ("After [save] happens, next prompt should be
   * for photos to associate, or to skip"). */
  const [saved, setSaved] = useState<{ kind: "sighting" | "activity"; id: number } | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);

  const properties = useAsync(() => api.properties.list(), []);
  const species = useAsync(() => api.species.list(), []);
  const activityTypes = useAsync(() => api.activityTypes.list(), []);
  const workflowStates = useAsync(() => api.workflowStates.list(), []);

  // Active only while capturing — the detail step doesn't need the
  // device's location, and leaving the watch running would keep the OS
  // location indicator lit for no reason.
  const liveLocation = useWatchPosition(step === "capture");

  const propertyList = useMemo(() => properties.data?.features ?? [], [properties.data]);
  const intent = intentFor(points.length);

  // Which property the placed geometry sits on. Uses the first point:
  // for a sighting that's the whole geometry, and for an activity area
  // it's where the user started drawing, which is on the property they
  // walked to. A shape spanning two properties is possible in principle
  // but the first point still names the one they meant — and the picker
  // below is right there if it doesn't.
  const detectedProperty = useMemo<Property | null>(() => {
    const first = points[0];
    if (!first) return null;
    return (
      propertyList.find((p) => p.geometry && positionInPolygon(first, p.geometry)) ?? null
    );
  }, [points, propertyList]);

  const [propertyOverride, setPropertyOverride] = useState<number | "">("");
  const propertyId: number | "" = propertyOverride || detectedProperty?.id || "";
  const selectedProperty = propertyList.find((p) => p.id === propertyId) ?? null;

  // Detail-step fields. Seeded, not persisted — see the "no draft
  // persistence" note above.
  const [speciesId, setSpeciesId] = useState<number | "">("");
  const [observedAt, setObservedAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [activityTypeId, setActivityTypeId] = useState<number | "">("");
  const [statusId, setStatusId] = useState<number | "">("");
  const [notes, setNotes] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Default the two activity pickers once the org's own lists arrive.
  useEffect(() => {
    if (activityTypeId === "" && activityTypes.data?.length) {
      setActivityTypeId(activityTypes.data[0].id);
    }
  }, [activityTypes.data, activityTypeId]);
  useEffect(() => {
    if (statusId === "" && workflowStates.data?.length) {
      const planned = workflowStates.data.find((s) => s.is_planned);
      setStatusId((planned ?? workflowStates.data[0]).id);
    }
  }, [workflowStates.data, statusId]);

  // A new sighting's default visibility follows the property it landed
  // on, same rule SightingFormPage applies (see
  // Property.sightings_public_by_default).
  useEffect(() => {
    if (intent === "sighting" && selectedProperty) {
      setIsPublic(selectedProperty.properties.sightings_public_by_default);
    }
  }, [intent, selectedProperty]);

  // Start zoomed to everything the user can see, so "enter that space"
  // means panning within their own land rather than hunting for it on a
  // world map. Computed once from the loaded properties; the map is free
  // to move afterwards.
  const initialBounds = useMemo<BBox | null>(() => {
    const boxes = propertyList
      .filter((p) => p.geometry)
      .map((p) => polygonBounds(p.geometry!));
    if (boxes.length === 0) return null;
    return boxes.reduce(mergeBounds);
  }, [propertyList]);

  // Property boundaries, drawn as context so the user can see what
  // they're standing on.
  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, PROPERTIES_SOURCE, {
      type: "FeatureCollection",
      features: propertyList
        .filter((p) => p.geometry)
        .map((p) => ({
          type: "Feature" as const,
          id: p.id,
          geometry: p.geometry!,
          properties: {},
        })),
    });
    ensureFillLayer(map, "quick-log-properties-fill", PROPERTIES_SOURCE, "#2f6f4f", 0.08);
    ensureLineLayer(map, "quick-log-properties-line", PROPERTIES_SOURCE, "#2f6f4f");
  }, [map, propertyList]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, DRAW_SOURCE, {
      type: "FeatureCollection",
      features: geometry ? [{ type: "Feature", geometry, properties: {} }] : [],
    });
    ensureFillLayer(map, "quick-log-draw-fill", DRAW_SOURCE, "#d98324", 0.35);
    ensureLineLayer(map, "quick-log-draw-line", DRAW_SOURCE, "#d98324");
  }, [map, geometry]);

  // Every placed point gets its own marker — with fewer than three there's
  // no polygon to render, so without these the first tap would look like
  // nothing happened (the same reason ActivityFormPage draws them).
  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, VERTICES_SOURCE, {
      type: "FeatureCollection",
      features: points.map((p) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: p },
        properties: {},
      })),
    });
    ensureCircleLayer(map, "quick-log-vertices", VERTICES_SOURCE, "#d98324");
  }, [map, points]);

  useEffect(() => {
    if (!map) return;
    const position = liveLocation.position;
    setGeoJsonSource(map, USER_LOCATION_SOURCE, {
      type: "FeatureCollection",
      features: position
        ? [
            {
              type: "Feature" as const,
              geometry: { type: "Point" as const, coordinates: position },
              properties: {},
            },
          ]
        : [],
    });
    ensureUserLocationLayer(map, USER_LOCATION_SOURCE);
  }, [map, liveLocation.position]);

  const captureHint = () => {
    if (points.length === 0) {
      return "Tap the map — or drop a pin where you're standing. One point logs a sighting; three or more enclose an area for an activity.";
    }
    if (intent === "sighting") {
      return "One point — this will be a sighting. Add two more to make it an activity area instead.";
    }
    if (intent === "incomplete") {
      return "Two points can't enclose an area yet — add one more for an activity, or undo back to one for a sighting.";
    }
    return `${points.length} points — this will be an activity area.`;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (intent === "sighting") {
        if (speciesId === "") throw new ApiError("Pick a species for this sighting.", 400);
        const location: PointGeometry = { type: "Point", coordinates: points[0] };
        const sighting = await api.sightings.create({
          property: propertyId === "" ? null : propertyId,
          species: speciesId,
          location,
          observed_at: new Date(observedAt).toISOString(),
          notes,
          is_public: isPublic,
        });
        setSaved({ kind: "sighting", id: sighting.id });
      } else {
        if (propertyId === "") throw new ApiError("Pick which property this activity is on.", 400);
        if (activityTypeId === "" || statusId === "") {
          throw new ApiError("Pick an activity type and status.", 400);
        }
        if (!geometry) throw new ApiError("That area isn't complete.", 400);
        const activity = await api.activities.create({
          property: propertyId,
          activity_type: activityTypeId,
          status: statusId,
          geometry,
          notes,
          is_public: isPublic,
        });
        setSaved({ kind: "activity", id: activity.id });
      }
      // The record is saved at this point. Rather than leaving straight
      // away, offer the photo step — the one thing you can only do on a
      // record that already exists, and the thing you're most likely to
      // want while still standing where you logged it.
      setPhotos([]);
      setStep("photos");
      setSubmitting(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  };

  /** Where the flow ends up — unchanged from before the photo step
   * existed: the property that now holds the record, so the thing just
   * logged is visible rather than requiring another navigation. With no
   * property (a sighting logged off any boundary) the dashboard is the
   * only place that lists it. Both "Skip" and "Done" land here. */
  const finish = () => {
    navigate(propertyId === "" ? "/" : `/properties/${propertyId}`, { replace: true });
  };

  const uploadPhoto = async (file: File) => {
    if (!saved) return;
    const photo =
      saved.kind === "sighting"
        ? await api.sightings.photos.upload(saved.id, file)
        : await api.activities.photos.upload(saved.id, file);
    setPhotos((current) => [...current, photo]);
  };

  const deletePhoto = async (photoId: number) => {
    if (!saved) return;
    if (saved.kind === "sighting") {
      await api.sightings.photos.remove(saved.id, photoId);
    } else {
      await api.activities.photos.remove(saved.id, photoId);
    }
    setPhotos((current) => current.filter((p) => p.id !== photoId));
  };

  const propertyOptions = propertyList.map((p) => ({ id: p.id, label: p.properties.name }));

  // Photos, offered after the save and skippable (owner feedback,
  // 2026-09-03). PhotoUploader already prefers the rear camera on a phone
  // (`capture="environment"`), so "allow taking of photos" needs no new
  // capability — just somewhere in the flow to do it. This is the first
  // place in the app where a photo can be attached without a separate
  // trip to an edit form.
  if (step === "photos" && saved) {
    return (
      <div className="page">
        <div className="page__header">
          <h1>Add photos</h1>
          <button type="button" className="btn btn-ghost btn-small" onClick={finish}>
            Skip
          </button>
        </div>
        <p className="muted">
          Your {saved.kind} is saved. Add photos now while you're still there, or skip — you can
          always add them later by editing the record.
        </p>
        <PhotoUploader
          photos={photos}
          canDelete={canDeletePhotos}
          onUpload={uploadPhoto}
          onDelete={deletePhoto}
        />
        <button type="button" className="btn btn-primary" onClick={finish}>
          {photos.length > 0 ? "Done" : "Done — no photos"}
        </button>
      </div>
    );
  }

  if (step === "detail") {
    return (
      <div className="page">
        <div className="page__header">
          <h1>{intent === "sighting" ? "New sighting" : "New activity"}</h1>
          <button
            type="button"
            className="btn btn-ghost btn-small"
            onClick={() => setStep("capture")}
          >
            ← Back to map
          </button>
        </div>
        <p className="muted">
          {detectedProperty
            ? `On ${detectedProperty.properties.name}, from where you placed it.`
            : "That spot isn't inside any of your property boundaries — pick a property below."}
        </p>

        <form onSubmit={handleSubmit} className="form">
          {error && <p className="form-error">{error}</p>}

          <label className="field">
            <span>Property{intent === "sighting" ? " (optional)" : ""}</span>
            <Combobox
              options={propertyOptions}
              value={propertyId}
              onChange={setPropertyOverride}
              placeholder="Search properties…"
              aria-label="Property"
            />
          </label>

          {intent === "sighting" ? (
            <>
              <label className="field">
                <span>Species</span>
                <Combobox
                  options={(species.data ?? []).map((s) => ({
                    id: s.id,
                    label: s.common_name,
                    sublabel: s.scientific_name || undefined,
                  }))}
                  value={speciesId}
                  onChange={setSpeciesId}
                  placeholder="Search species…"
                  noOptionsLabel="No species in your list yet."
                  aria-label="Species"
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
            </>
          ) : (
            <div className="field-row">
              <label className="field">
                <span>Activity type</span>
                <select
                  value={activityTypeId}
                  onChange={(e) => setActivityTypeId(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="" disabled>
                    Select a type
                  </option>
                  {activityTypes.data?.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Status</span>
                <select
                  value={statusId}
                  onChange={(e) => setStatusId(e.target.value ? Number(e.target.value) : "")}
                >
                  <option value="" disabled>
                    Select a status
                  </option>
                  {workflowStates.data?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

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
            <span>Show this on the public site</span>
          </label>

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : intent === "sighting" ? "Save sighting" : "Save activity"}
          </button>
          <p className="muted">
            Photos, species on an activity, and linking records are on the record's own edit
            page — save this first, then open it from the property.
          </p>
        </form>
      </div>
    );
  }

  return (
    <div className="page page--capture">
      <div className="map-panel map-panel--full">
        <MapCanvas
          onReady={setMap}
          bounds={
            initialBounds ??
            (points.length > 0 ? positionsBounds(points) : null)
          }
          onClick={(lngLat) => addPoint([lngLat.lng, lngLat.lat] as Position)}
          drawing
        />
        <div className="map-overlay map-overlay--top">{captureHint()}</div>
        <div className="map-overlay map-overlay--bottom">
          <button
            type="button"
            className="btn btn-primary btn-small"
            onClick={() => liveLocation.position && addPoint(liveLocation.position)}
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
        <div className="capture-actions">
          <Link to="/" className="btn btn-ghost btn-small">
            Cancel
          </Link>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setStep("detail")}
            disabled={intent === "incomplete"}
          >
            {/* Short on purpose — the bar is one line on a phone. */}
            {intent === "sighting" ? "Next: sighting" : "Next: activity"}
          </button>
        </div>
      </div>
    </div>
  );
}
