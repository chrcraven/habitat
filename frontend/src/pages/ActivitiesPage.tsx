import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Activity } from "../api/types";

type StatusFilter = "all" | "planned" | "done";

/**
 * Org-wide list of every activity the caller can see, with a search box —
 * owner feedback, 2026-09-03: "All activities or sightings can be found
 * and edited on their respective pages using a search/filtering
 * function." Until now activities were only reachable *inside* a property
 * (/properties/:id), which was fine in Phase 1 with a handful of records
 * and stopped being fine once there was real data.
 *
 * Deliberately not a new API surface: it reuses the same org-wide list
 * endpoints DashboardPage already calls and filters client-side, the same
 * tradeoff SpeciesPage's own search box takes (see its comment). Revisit
 * if a single org's activity count ever makes fetching them all
 * unreasonable.
 *
 * Property scoping is enforced server-side (filter_by_property_scope), so
 * a property-scoped member simply gets fewer features back — there's no
 * client-side scope filtering to duplicate here.
 */
export default function ActivitiesPage() {
  const { data, loading, error } = useAsync(() => api.activities.list(), []);
  const properties = useAsync(() => api.properties.list(), []);
  const [filter, setFilter] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");

  const propertyName = (propertyId: number | null): string => {
    if (propertyId == null) return "No property";
    return (
      properties.data?.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property"
    );
  };

  const all = useMemo(() => data?.features ?? [], [data]);

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    return all.filter((a: Activity) => {
      if (status === "planned" && a.properties.is_done) return false;
      if (status === "done" && !a.properties.is_done) return false;
      if (!query) return true;
      // Everything a person might reasonably remember an activity by:
      // what it was, where it was, what state it's in, what was planted,
      // and whatever they typed in the notes.
      const haystack = [
        a.properties.activity_type_name,
        a.properties.status_name,
        a.properties.notes,
        propertyName(a.properties.property),
        ...a.properties.species_names,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [all, filter, status, properties.data]);

  const dateLabel = (activity: Activity): string | null => {
    const { date_done, date_planned } = activity.properties;
    if (date_done) return `done ${date_done}`;
    if (date_planned) return `planned ${date_planned}`;
    return null;
  };

  const narrowed = filter.trim() !== "" || status !== "all";

  return (
    <div className="page">
      <div className="page__header">
        <h1>Activities</h1>
      </div>
      <p className="muted">Every activity across your properties. Select one to view or edit it.</p>

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="form-error">Couldn't load activities: {error}</p>}

      {!loading && !error && all.length > 0 && (
        <>
          <label className="field">
            <span>Search</span>
            <input
              type="search"
              placeholder="Filter by type, property, species, status or notes…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
              <option value="all">All</option>
              <option value="planned">Planned / in progress</option>
              <option value="done">Completed</option>
            </select>
          </label>
        </>
      )}

      {!loading && narrowed && (
        <p className="muted">
          Showing {filtered.length} of {all.length}.
        </p>
      )}

      <ul className="card-list">
        {filtered.map((activity) => (
          <li key={activity.id} className="card card--row">
            <Link
              to={`/properties/${activity.properties.property}/activities/${activity.id}/edit`}
              className="card__link"
            >
              <strong>
                {activity.properties.activity_type_name}
                <span className="muted"> — {activity.properties.status_name}</span>
              </strong>
              <span className="muted">
                {propertyName(activity.properties.property)}
                {dateLabel(activity) && ` — ${dateLabel(activity)}`}
              </span>
              {activity.properties.species_names.length > 0 && (
                <span className="muted">Species: {activity.properties.species_names.join(", ")}</span>
              )}
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && all.length > 0 && filtered.length === 0 && (
        <p className="muted">No activities match your search.</p>
      )}

      {/* A property-scoped member with nothing here isn't in the same
          situation as a brand-new account — they can't create a property
          to fix it, and the records may simply belong to properties
          outside their scope. Keep the empty state neutral about why. */}
      {!loading && !error && all.length === 0 && (
        <div className="empty-state">
          <p>No activities yet. Log one from a property's page, or use Quick log.</p>
          <Link to="/quick-log" className="btn btn-primary">
            ⊕ Quick log
          </Link>
        </div>
      )}
    </div>
  );
}
