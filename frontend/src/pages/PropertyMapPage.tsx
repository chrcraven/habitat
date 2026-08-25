import { useEffect, useMemo, useState } from "react";
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
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import { polygonBounds } from "../utils/geo";

const PROPERTY_SOURCE = "property-boundary";
const ACTIVITIES_SOURCE = "activities";
const SIGHTINGS_SOURCE = "sightings";
const USER_LOCATION_SOURCE = "user-location";

export default function PropertyMapPage() {
  const { id } = useParams<{ id: string }>();
  const propertyId = Number(id);
  const navigate = useNavigate();
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const [showPrivate, setShowPrivate] = useState(false);
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
      features: activities.data?.features ?? [],
    });
    ensureActivityStatusLayers(map, ACTIVITIES_SOURCE);
  }, [map, activities.data]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, SIGHTINGS_SOURCE, {
      type: "FeatureCollection",
      features: sightings.data?.features ?? [],
    });
    ensureCircleLayer(map, "sightings-circle", SIGHTINGS_SOURCE, "#2f5fc9");
  }, [map, sightings.data]);

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

      <div className="record-lists">
        <section>
          <h2>Activities</h2>
          {activities.loading && <p className="muted">Loading…</p>}
          {!activities.loading && (activities.data?.features.length ?? 0) === 0 && (
            <p className="muted">No activities to show.</p>
          )}
          <ul className="card-list">
            {activities.data?.features.map((activity) => (
              <li key={activity.id} className="card">
                <div className="card__row">
                  <div>
                    <strong>{activity.properties.activity_type}</strong>
                    <span className="muted"> — {activity.properties.status_name}</span>
                    {!activity.properties.is_public && <span className="badge">Private</span>}
                  </div>
                  {(canEdit || canDelete) && (
                    <div className="card__actions">
                      {canEdit && (
                        <Link
                          to={`/properties/${propertyId}/activities/${activity.id}/edit`}
                          className="btn btn-secondary btn-small"
                        >
                          Edit
                        </Link>
                      )}
                      {canDelete && (
                        <button
                          type="button"
                          className="btn btn-danger btn-small"
                          onClick={() => handleDeleteActivity(activity.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {activity.properties.date_planned && (
                  <span className="muted">Planned: {activity.properties.date_planned}</span>
                )}
                {activity.properties.species_names.length > 0 && (
                  <span className="muted">
                    Species: {activity.properties.species_names.join(", ")}
                  </span>
                )}
                {activity.properties.notes && <p>{activity.properties.notes}</p>}
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2>Sightings</h2>
          {sightings.loading && <p className="muted">Loading…</p>}
          {!sightings.loading && (sightings.data?.features.length ?? 0) === 0 && (
            <p className="muted">No sightings to show.</p>
          )}
          <ul className="card-list">
            {sightings.data?.features.map((sighting) => (
              <li key={sighting.id} className="card">
                <div className="card__row">
                  <div>
                    <strong>{sighting.properties.species_detail.common_name}</strong>
                    {!sighting.properties.is_public && <span className="badge">Private</span>}
                  </div>
                  {(canEdit || canDelete) && (
                    <div className="card__actions">
                      {canEdit && (
                        <Link
                          to={`/properties/${propertyId}/sightings/${sighting.id}/edit`}
                          className="btn btn-secondary btn-small"
                        >
                          Edit
                        </Link>
                      )}
                      {canDelete && (
                        <button
                          type="button"
                          className="btn btn-danger btn-small"
                          onClick={() => handleDeleteSighting(sighting.id)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  )}
                </div>
                <span className="muted">
                  {new Date(sighting.properties.observed_at).toLocaleString()}
                </span>
                {sighting.properties.notes && <p>{sighting.properties.notes}</p>}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
