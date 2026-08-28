import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PhotoUploader from "../components/PhotoUploader";
import LinkedRecordsPanel from "../components/LinkedRecordsPanel";
import Combobox from "../components/Combobox";
import { ensureCircleLayer, ensureLineLayer, setGeoJsonSource } from "../components/mapLayers";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { api, ApiError } from "../api/client";
import type { Position, Property, Sighting, Species } from "../api/types";
import { getCurrentPosition, mergeBounds, pointBounds, polygonBounds } from "../utils/geo";

const DRAW_SOURCE = "draw-sighting";

function toLocalDateTimeInputValue(date: Date): string {
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function SightingForm({
  property,
  speciesList,
  existing,
}: {
  property: Property;
  speciesList: Species[];
  existing: Sighting | null;
}) {
  const navigate = useNavigate();
  const { session } = useAuth();
  const canDeletePhotos = roleAtLeast(session?.membership?.role, "admin");
  const canEditLinks = roleAtLeast(session?.membership?.role, "editor");
  const [map, setMap] = useState<MapLibreMap | null>(null);

  const [point, setPoint] = useState<Position | null>(existing?.geometry?.coordinates ?? null);
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState<string | null>(null);
  const [speciesId, setSpeciesId] = useState<number | "">(existing?.properties.species ?? "");
  const [newSpeciesName, setNewSpeciesName] = useState("");
  const [observedAt, setObservedAt] = useState(() =>
    existing
      ? toLocalDateTimeInputValue(new Date(existing.properties.observed_at))
      : toLocalDateTimeInputValue(new Date()),
  );
  const [notes, setNotes] = useState(existing?.properties.notes ?? "");
  // A brand-new sighting starts from its property's own
  // sightings_public_by_default (an existing one keeps its own saved
  // value, same as every other field here) — see Property model's
  // docstring and this same default's backend-side application in
  // SightingViewSet.perform_create (covers callers that skip the form
  // entirely, e.g. a future API client).
  const [isPublic, setIsPublic] = useState(
    existing?.properties.is_public ?? property.properties.sightings_public_by_default,
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const photos = useAsync(
    () => (existing ? api.sightings.photos.list(existing.id) : Promise.resolve([])),
    [existing?.id],
  );

  // Direct Sighting↔Activity link (see data-model-notes.md) — activities
  // on this same property, since that's the case that actually makes
  // sense ("this sighting was addressed by this planting/treatment").
  const links = useAsync(
    () => (existing ? api.sightings.links.list(existing.id) : Promise.resolve([])),
    [existing?.id],
  );
  const propertyActivities = useAsync(
    () => (existing ? api.activities.list(property.id) : Promise.resolve({ type: "FeatureCollection" as const, features: [] })),
    [existing?.id, property.id],
  );

  const propertyBounds = useMemo(
    () => (property.geometry ? polygonBounds(property.geometry) : null),
    [property],
  );
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
    map.setLayoutProperty("draw-sighting-circle", "visibility", point ? "visible" : "none");
  }, [map, point]);

  useEffect(() => {
    if (!map || !property.geometry) return;
    setGeoJsonSource(map, "property-context", property.geometry);
    ensureLineLayer(map, "property-context-line", "property-context", "#2f6f4f", 2);
  }, [map, property.geometry]);

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
      const payload = {
        species: resolvedSpeciesId,
        location: { type: "Point" as const, coordinates: point },
        observed_at: new Date(observedAt).toISOString(),
        notes,
        is_public: isPublic,
      };
      if (existing) {
        await api.sightings.update(existing.id, payload);
      } else {
        await api.sightings.create({ property: property.id, ...payload });
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
        <h1>{existing ? "Edit sighting" : "Log a sighting"}</h1>
        <Link to={`/properties/${property.id}`} className="btn btn-ghost btn-small">
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
      <div className="map-page-scroll">
      {locateError && <p className="form-error form-error--inline">{locateError}</p>}

      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}

        <label className="field">
          <span>Species</span>
          <Combobox
            options={speciesList.map((s) => ({ id: s.id, label: s.common_name }))}
            value={speciesId}
            onChange={(id) => {
              setSpeciesId(id);
              if (id !== "") setNewSpeciesName("");
            }}
            placeholder="Search your species list, or add new below…"
          />
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
          <span>Show on the public site</span>
        </label>

        {existing && (
          <div className="field">
            <span>Photos</span>
            <PhotoUploader
              photos={photos.data ?? []}
              canDelete={canDeletePhotos}
              onUpload={async (file) => {
                await api.sightings.photos.upload(existing.id, file);
                photos.reload();
              }}
              onDelete={async (photoId) => {
                await api.sightings.photos.remove(existing.id, photoId);
                photos.reload();
              }}
            />
          </div>
        )}

        {existing && (
          <LinkedRecordsPanel
            title="Linked activities"
            canEdit={canEditLinks}
            links={(links.data ?? []).map((l) => ({
              id: l.id,
              label: `${l.activity_type} — ${l.activity_property_name}`,
            }))}
            options={(propertyActivities.data?.features ?? [])
              .filter((a) => !(links.data ?? []).some((l) => l.activity === a.id))
              .map((a) => ({
                id: a.id,
                label: `${a.properties.activity_type} — ${a.properties.status_name}`,
              }))}
            emptyOptionsLabel="No other activities on this property yet."
            onLink={async (activityId) => {
              await api.sightings.links.create(existing.id, activityId);
              links.reload();
            }}
            onUnlink={async (linkId) => {
              await api.sightings.links.remove(existing.id, linkId);
              links.reload();
            }}
          />
        )}

        <button type="submit" className="btn btn-primary" disabled={submitting || !point}>
          {submitting ? "Saving…" : "Save sighting"}
        </button>
      </form>
      </div>
    </div>
  );
}

export default function SightingFormPage() {
  const { id, sightingId } = useParams<{ id: string; sightingId?: string }>();
  const propertyId = Number(id);
  const isEdit = sightingId !== undefined;

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const species = useAsync(() => api.species.list(), []);
  const existing = useAsync(
    () => (isEdit ? api.sightings.get(Number(sightingId)) : Promise.resolve(null)),
    [sightingId],
  );

  const loading = property.loading || species.loading || (isEdit && existing.loading);
  const failed = property.error || species.error || (isEdit && (existing.error || !existing.data));

  if (loading) return <div className="full-page-status">Loading…</div>;
  if (failed || !property.data || !species.data) {
    return <p className="form-error" style={{ padding: "1rem" }}>Couldn't load this page.</p>;
  }

  return (
    <SightingForm property={property.data} speciesList={species.data} existing={existing.data ?? null} />
  );
}
