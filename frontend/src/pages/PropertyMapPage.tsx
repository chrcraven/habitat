import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import ActivityStatusLegend from "../components/ActivityStatusLegend";
import {
  ensureActivityStatusLayers,
  ensureCircleLayer,
  ensureFillLayer,
  ensureLineLayer,
  ensureUserLocationLayer,
  setGeoJsonSource,
} from "../components/mapLayers";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useWatchPosition } from "../hooks/useWatchPosition";
import { useFocusedListItem } from "../hooks/useFocusedListItem";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { polygonBounds } from "../utils/geo";
import type { Activity, Sighting } from "../api/types";

const PROPERTY_SOURCE = "property-boundary";
const ACTIVITIES_SOURCE = "activities";
const SIGHTINGS_SOURCE = "sightings";
const USER_LOCATION_SOURCE = "user-location";

/** One combined row in the activity+sighting list below the map — see
 * that list's own comment for why the two are merged into one scroll
 * order instead of two separate sections. */
type CombinedItem =
  | { key: string; kind: "activity"; id: number; sortDate: string | null; data: Activity }
  | { key: string; kind: "sighting"; id: number; sortDate: string | null; data: Sighting };

export default function PropertyMapPage() {
  const { id } = useParams<{ id: string }>();
  const propertyId = Number(id);
  const navigate = useNavigate();
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const [showPrivate, setShowPrivate] = useState(false);
  // What's shown on the map is no longer just "everything loaded" — it's
  // whichever single item the user has scrolled into focus in the list
  // below (see useFocusedListItem), plus any items they've explicitly
  // pinned via that item's checkbox so more than one can show at once.
  // Pinned ids are tracked (not hidden ones) since the default is now
  // "nothing pinned, follow scroll" rather than "everything shown".
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  // Opt-in, off by default — this is a *viewing* page, not a drawing one,
  // so tracking shouldn't start without the user asking for it (see
  // ActivityFormPage/PropertyFormPage, where it's always on because
  // that's the whole point of those pages).
  const [showMyLocation, setShowMyLocation] = useState(false);
  const liveLocation = useWatchPosition(showMyLocation);

  const { session } = useAuth();
  const role = session?.membership?.role;
  const canEdit = roleAtLeast(role, "editor");
  const canDelete = roleAtLeast(role, "admin");

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const activities = useAsync(
    () => api.activities.list(propertyId, { isPublic: showPrivate ? undefined : true }),
    [propertyId, showPrivate],
  );
  const sightings = useAsync(
    () => api.sightings.list(propertyId, { isPublic: showPrivate ? undefined : true }),
    [propertyId, showPrivate],
  );

  const bounds = useMemo(
    () => (property.data?.geometry ? polygonBounds(property.data.geometry) : null),
    [property.data],
  );

  // Merged, newest-first (by the most meaningful date each record type
  // has — an activity's done date if it has one, else its planned date;
  // a sighting's observed date). Records with no date at all sort last
  // rather than being dropped.
  const combinedItems = useMemo<CombinedItem[]>(() => {
    const activityItems: CombinedItem[] = (activities.data?.features ?? []).map((a) => ({
      key: `activity-${a.id}`,
      kind: "activity",
      id: a.id,
      sortDate: a.properties.date_done ?? a.properties.date_planned,
      data: a,
    }));
    const sightingItems: CombinedItem[] = (sightings.data?.features ?? []).map((s) => ({
      key: `sighting-${s.id}`,
      kind: "sighting",
      id: s.id,
      sortDate: s.properties.observed_at,
      data: s,
    }));
    return [...activityItems, ...sightingItems].sort((a, b) => {
      if (!a.sortDate && !b.sortDate) return 0;
      if (!a.sortDate) return 1;
      if (!b.sortDate) return -1;
      return b.sortDate.localeCompare(a.sortDate);
    });
  }, [activities.data, sightings.data]);

  const itemIds = useMemo(() => combinedItems.map((item) => item.key), [combinedItems]);
  const { focusedId, registerItem } = useFocusedListItem(scrollContainerRef, itemIds);

  // Shown on the map: whatever's currently scrolled into focus, plus
  // anything explicitly pinned.
  const shownIds = useMemo(() => {
    const next = new Set(pinnedIds);
    if (focusedId) next.add(focusedId);
    return next;
  }, [pinnedIds, focusedId]);

  const togglePinned = (key: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const visibleActivityFeatures = useMemo(
    () => (activities.data?.features ?? []).filter((a) => shownIds.has(`activity-${a.id}`)),
    [activities.data, shownIds],
  );
  const visibleSightingFeatures = useMemo(
    () => (sightings.data?.features ?? []).filter((s) => shownIds.has(`sighting-${s.id}`)),
    [sightings.data, shownIds],
  );

  // Base layers: set up once the map is ready and whenever the property
  // boundary changes.
  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(
      map,
      PROPERTY_SOURCE,
      property.data?.geometry ?? { type: "Polygon", coordinates: [] },
    );
    ensureFillLayer(map, "property-boundary-fill", PROPERTY_SOURCE, "#2f6f4f", 0.08);
    ensureLineLayer(map, "property-boundary-line", PROPERTY_SOURCE, "#2f6f4f", 2);
  }, [map, property.data]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, ACTIVITIES_SOURCE, {
      type: "FeatureCollection",
      features: visibleActivityFeatures,
    });
    ensureActivityStatusLayers(map, ACTIVITIES_SOURCE);
  }, [map, visibleActivityFeatures]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, SIGHTINGS_SOURCE, {
      type: "FeatureCollection",
      features: visibleSightingFeatures,
    });
    ensureCircleLayer(map, "sightings-circle", SIGHTINGS_SOURCE, "#2f5fc9");
  }, [map, visibleSightingFeatures]);

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

  const handleDeleteProperty = async () => {
    if (!property.data) return;
    if (
      !window.confirm(
        `Delete "${property.data.properties.name}"? This also deletes its activities and sightings.`,
      )
    ) {
      return;
    }
    await api.properties.remove(propertyId);
    navigate("/properties", { replace: true });
  };

  const handleDeleteActivity = async (activityId: number) => {
    if (!window.confirm("Delete this activity?")) return;
    await api.activities.remove(activityId);
    activities.reload();
  };

  const handleDeleteSighting = async (sightingId: number) => {
    if (!window.confirm("Delete this sighting?")) return;
    await api.sightings.remove(sightingId);
    sightings.reload();
  };

  const loading = activities.loading || sightings.loading;

  return (
    <div className="page page--map">
      <div className="page__header">
        <Link to="/properties" className="btn-link">
          ← Properties
        </Link>
        <h1>{property.data?.properties.name ?? "…"}</h1>
        {(canEdit || canDelete) && (
          <div className="card__actions">
            {canEdit && (
              <Link to={`/properties/${propertyId}/edit`} className="btn btn-secondary btn-small">
                Edit
              </Link>
            )}
            {canDelete && (
              <button type="button" className="btn btn-danger btn-small" onClick={handleDeleteProperty}>
                Delete
              </button>
            )}
          </div>
        )}
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={bounds} />
        <ActivityStatusLegend />
        {canEdit && (
          <div className="map-fabs">
            <Link to={`/properties/${propertyId}/sightings/new`} className="fab fab--secondary">
              + Sighting
            </Link>
            <Link to={`/properties/${propertyId}/activities/new`} className="fab">
              + Activity
            </Link>
          </div>
        )}
      </div>

      <div className="map-page-scroll" ref={scrollContainerRef}>
      <div className="visibility-toggle">
        <label className="switch">
          <input
            type="checkbox"
            checked={showPrivate}
            onChange={(e) => setShowPrivate(e.target.checked)}
          />
          <span>Show private records too (showing public only by default)</span>
        </label>
        <label className="switch">
          <input
            type="checkbox"
            checked={showMyLocation}
            onChange={(e) => setShowMyLocation(e.target.checked)}
          />
          <span>Show my current location on the map</span>
        </label>
        {showMyLocation && liveLocation.error && (
          <p className="form-error form-error--inline">Location unavailable ({liveLocation.error})</p>
        )}
      </div>

      <p className="muted map-selection-hint">
        Showing {shownIds.size} of {combinedItems.length} on the map — scroll to bring one into
        focus (highlighted below), or check a box to pin more at once.
      </p>

      <div className="record-list">
        <div className="page__header">
          <h2>Activities &amp; sightings</h2>
          {pinnedIds.size > 0 && (
            <div className="card__actions">
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={() => setPinnedIds(new Set())}
              >
                Clear all
              </button>
            </div>
          )}
        </div>
        {loading && <p className="muted">Loading…</p>}
        {!loading && combinedItems.length === 0 && <p className="muted">Nothing to show yet.</p>}
        <ul className="card-list">
          {combinedItems.map((item) => {
            const isFocused = focusedId === item.key;
            const isPinned = pinnedIds.has(item.key);
            const label =
              item.kind === "activity"
                ? item.data.properties.activity_type
                : item.data.properties.species_detail.common_name;
            return (
              <li
                key={item.key}
                ref={registerItem(item.key)}
                data-item-id={item.key}
                className={`card${isFocused ? " card--focused" : ""}`}
              >
                <div className="card__row">
                  <div className="card__main">
                    <label className="map-toggle" title="Pin to map">
                      <input
                        type="checkbox"
                        checked={isPinned}
                        onChange={() => togglePinned(item.key)}
                        aria-label={`Pin ${label} to the map`}
                      />
                    </label>
                    <div>
                      <span className={`type-badge type-badge--${item.kind}`}>
                        {item.kind === "activity" ? "Activity" : "Sighting"}
                      </span>
                      {item.kind === "activity" ? (
                        <>
                          <strong>{item.data.properties.activity_type}</strong>
                          <span className="muted"> — {item.data.properties.status_name}</span>
                        </>
                      ) : (
                        <strong>{item.data.properties.species_detail.common_name}</strong>
                      )}
                      {!item.data.properties.is_public && <span className="badge">Private</span>}
                    </div>
                  </div>
                  {(canEdit || canDelete) && (
                    <div className="card__actions">
                      {canEdit && (
                        <Link
                          to={
                            item.kind === "activity"
                              ? `/properties/${propertyId}/activities/${item.id}/edit`
                              : `/properties/${propertyId}/sightings/${item.id}/edit`
                          }
                          className="btn btn-secondary btn-small"
                        >
                          Edit
                        </Link>
                      )}
                      {canDelete && (
                        <button
                          type="button"
                          className="btn btn-danger btn-small"
                          onClick={() =>
                            item.kind === "activity"
                              ? handleDeleteActivity(item.id)
                              : handleDeleteSighting(item.id)
                          }
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {item.kind === "activity" ? (
                  <>
                    {item.data.properties.date_planned && (
                      <span className="muted">Planned: {item.data.properties.date_planned}</span>
                    )}
                    {item.data.properties.species_names.length > 0 && (
                      <span className="muted">
                        Species: {item.data.properties.species_names.join(", ")}
                      </span>
                    )}
                  </>
                ) : (
                  <span className="muted">
                    {new Date(item.data.properties.observed_at).toLocaleString()}
                  </span>
                )}
                {item.data.properties.notes && <p>{item.data.properties.notes}</p>}
              </li>
            );
          })}
        </ul>
      </div>
      </div>
    </div>
  );
}
