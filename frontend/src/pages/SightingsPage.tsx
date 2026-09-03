import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Sighting } from "../api/types";

/**
 * Org-wide list of every sighting the caller can see, with a search box —
 * the sighting half of the same 2026-09-03 feedback that produced
 * ActivitiesPage; see that file's comment for why this is client-side
 * filtering over the existing list endpoint rather than new API surface.
 */
export default function SightingsPage() {
  const { data, loading, error } = useAsync(() => api.sightings.list(), []);
  const properties = useAsync(() => api.properties.list(), []);
  const [filter, setFilter] = useState("");

  const propertyName = (propertyId: number | null): string => {
    if (propertyId == null) return "No property";
    return (
      properties.data?.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property"
    );
  };

  const all = useMemo(() => data?.features ?? [], [data]);

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return all;
    return all.filter((s: Sighting) => {
      const haystack = [
        s.properties.species_detail.common_name,
        s.properties.species_detail.scientific_name,
        s.properties.notes,
        propertyName(s.properties.property),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [all, filter, properties.data]);

  const observed = (sighting: Sighting): string =>
    new Date(sighting.properties.observed_at).toLocaleDateString();

  return (
    <div className="page">
      <div className="page__header">
        <h1>Sightings</h1>
      </div>
      <p className="muted">Every sighting across your properties. Select one to view or edit it.</p>

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="form-error">Couldn't load sightings: {error}</p>}

      {!loading && !error && all.length > 0 && (
        <label className="field">
          <span>Search</span>
          <input
            type="search"
            placeholder="Filter by species, property or notes…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
      )}

      {!loading && filter.trim() && (
        <p className="muted">
          Showing {filtered.length} of {all.length}.
        </p>
      )}

      <ul className="card-list">
        {filtered.map((sighting) => {
          const label = (
            <>
              <strong>{sighting.properties.species_detail.common_name}</strong>
              <span className="muted">
                {propertyName(sighting.properties.property)} — {observed(sighting)}
              </span>
            </>
          );
          // A sighting can have no property (it's a nullable FK), and the
          // edit form lives at /properties/:id/sightings/:id/edit — so
          // there's nowhere to link one that isn't on a property. Render
          // it as a plain row rather than a dead link, the same way
          // DashboardPage handles the case.
          return sighting.properties.property != null ? (
            <li key={sighting.id} className="card card--row">
              <Link
                to={`/properties/${sighting.properties.property}/sightings/${sighting.id}/edit`}
                className="card__link"
              >
                {label}
              </Link>
            </li>
          ) : (
            <li key={sighting.id} className="card card--row">
              <div>{label}</div>
            </li>
          );
        })}
      </ul>

      {!loading && !error && all.length > 0 && filtered.length === 0 && (
        <p className="muted">No sightings match "{filter}".</p>
      )}

      {!loading && !error && all.length === 0 && (
        <div className="empty-state">
          <p>No sightings yet. Log one from a property's page, or use Quick log.</p>
          <Link to="/quick-log" className="btn btn-primary">
            ⊕ Quick log
          </Link>
        </div>
      )}
    </div>
  );
}
