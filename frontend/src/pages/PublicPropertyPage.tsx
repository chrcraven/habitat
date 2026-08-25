import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PublicHeader from "../components/PublicHeader";
import PublicPhotoGrid from "../components/PublicPhotoGrid";
import ActivityStatusLegend from "../components/ActivityStatusLegend";
import {
  ensureActivityStatusLayers,
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

/**
 * The per-property public page — the other of the two public-site shapes
 * requested (see PublicOrganizationPage for the org-portfolio one). Read
 * only: no edit/delete controls, no FABs, no private-records toggle
 * (there's nothing to toggle — the public API only ever returns
 * is_public=true records in the first place, see
 * backend/apps/public_site/views.py). Visually modeled on
 * PropertyMapPage but stripped down.
 */
export default function PublicPropertyPage() {
  const { propertyId } = useParams<{ propertyId: string }>();
  const id = Number(propertyId);
  const [map, setMap] = useState<MapLibreMap | null>(null);

  const property = useAsync(() => api.public.property(id), [id]);
  const activities = useAsync(() => api.public.activities(id), [id]);
  const sightings = useAsync(() => api.public.sightings(id), [id]);

  const bounds = useMemo(
    () => (property.data?.geometry ? polygonBounds(property.data.geometry) : null),
    [property.data],
  );

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

  if (property.loading) {
    return (
      <div className="app-shell">
        <PublicHeader />
        <main className="app-main">
          <div className="full-page-status">Loading…</div>
        </main>
      </div>
    );
  }

  if (property.error || !property.data) {
    return (
      <div className="app-shell">
        <PublicHeader />
        <main className="app-main">
          <p className="form-error" style={{ padding: "1rem" }}>
            This property isn't public, or doesn't exist.
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <PublicHeader
        back={{
          to: `/public/org/${property.data.organization.id}`,
          label: `← ${property.data.organization.name}`,
        }}
      />
      <main className="app-main">
        <div className="page page--map">
          <div className="page__header">
            <h1>{property.data.properties.name}</h1>
          </div>

          <div className="map-panel">
            <MapCanvas onReady={setMap} bounds={bounds} />
            <ActivityStatusLegend />
          </div>

          <div className="record-lists">
            <section>
              <h2>Activities</h2>
              {activities.loading && <p className="muted">Loading…</p>}
              {!activities.loading && (activities.data?.features.length ?? 0) === 0 && (
                <p className="muted">Nothing to show yet.</p>
              )}
              <ul className="card-list">
                {activities.data?.features.map((activity) => (
                  <li key={activity.id} className="card">
                    <div>
                      <strong>{activity.properties.activity_type}</strong>
                      <span className="muted"> — {activity.properties.status_name}</span>
                    </div>
                    {activity.properties.date_planned && (
                      <span className="muted">Planned: {activity.properties.date_planned}</span>
                    )}
                    {activity.properties.date_done && (
                      <span className="muted">Done: {activity.properties.date_done}</span>
                    )}
                    {activity.properties.notes && <p>{activity.properties.notes}</p>}
                    <PublicPhotoGrid kind="activity" id={activity.id} />
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h2>Sightings</h2>
              {sightings.loading && <p className="muted">Loading…</p>}
              {!sightings.loading && (sightings.data?.features.length ?? 0) === 0 && (
                <p className="muted">Nothing to show yet.</p>
              )}
              <ul className="card-list">
                {sightings.data?.features.map((sighting) => (
                  <li key={sighting.id} className="card">
                    <strong>{sighting.properties.species_detail.common_name}</strong>
                    <span className="muted">
                      {" "}
                      — {new Date(sighting.properties.observed_at).toLocaleDateString()}
                    </span>
                    {sighting.properties.notes && <p>{sighting.properties.notes}</p>}
                    <PublicPhotoGrid kind="sighting" id={sighting.id} />
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
