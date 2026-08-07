import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import {
  ensureCircleLayer,
  ensureFillLayer,
  ensureLineLayer,
  setGeoJsonSource,
} from "../components/mapLayers";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { polygonBounds } from "../utils/geo";

const PROPERTY_SOURCE = "property-boundary";
const ACTIVITIES_SOURCE = "activities";
const SIGHTINGS_SOURCE = "sightings";

export default function PropertyMapPage() {
  const { id } = useParams<{ id: string }>();
  const propertyId = Number(id);
  const [map, setMap] = useState<MapLibreMap | null>(null);

  const property = useAsync(() => api.properties.get(propertyId), [propertyId]);
  const activities = useAsync(() => api.activities.list(propertyId), [propertyId]);
  const sightings = useAsync(() => api.sightings.list(propertyId), [propertyId]);

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
    ensureFillLayer(map, "activities-fill", ACTIVITIES_SOURCE, "#c9782f", 0.35);
    ensureLineLayer(map, "activities-line", ACTIVITIES_SOURCE, "#c9782f", 2);
  }, [map, activities.data]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, SIGHTINGS_SOURCE, {
      type: "FeatureCollection",
      features: sightings.data?.features ?? [],
    });
    ensureCircleLayer(map, "sightings-circle", SIGHTINGS_SOURCE, "#2f5fc9");
  }, [map, sightings.data]);

  return (
    <div className="page page--map">
      <div className="page__header">
        <Link to="/properties" className="btn-link">
          ← Properties
        </Link>
        <h1>{property.data?.properties.name ?? "…"}</h1>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={bounds} />
        <div className="map-fabs">
          <Link to={`/properties/${propertyId}/sightings/new`} className="fab fab--secondary">
            + Sighting
          </Link>
          <Link to={`/properties/${propertyId}/activities/new`} className="fab">
            + Activity
          </Link>
        </div>
      </div>

      <div className="record-lists">
        <section>
          <h2>Activities</h2>
          {activities.loading && <p className="muted">Loading…</p>}
          {!activities.loading && (activities.data?.features.length ?? 0) === 0 && (
            <p className="muted">No activities logged yet.</p>
          )}
          <ul className="card-list">
            {activities.data?.features.map((activity) => (
              <li key={activity.id} className="card">
                <strong>{activity.properties.activity_type}</strong>
                <span className="muted">{activity.properties.status_name}</span>
                {activity.properties.date_planned && (
                  <span className="muted">Planned: {activity.properties.date_planned}</span>
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
            <p className="muted">No sightings logged yet.</p>
          )}
          <ul className="card-list">
            {sightings.data?.features.map((sighting) => (
              <li key={sighting.id} className="card">
                <strong>{sighting.properties.species_detail.common_name}</strong>
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
