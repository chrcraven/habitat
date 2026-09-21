import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { countLabel } from "../utils/counts";
import type { Activity } from "../api/types";
import {
  ACTIVITY_NOUN,
  countVisibility,
  matchesVisibilityFilter,
  publicCountSummary,
  publicVisibility,
  visibilityBadgeClass,
  visibilityLabel,
  wouldPublishSummary,
  type PropertyVisibility,
  type VisibilityFilter,
} from "../utils/publicVisibility";

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
 *
 * ## Why the public/private filter is client-side (D39, 2026-09-16)
 *
 * `api.activities.list()` takes a typed `ListFilter.isPublic` that goes
 * straight to the backend's `filter_is_public`, and PropertyMapPage uses
 * it. Reaching for it here would be the obvious move and is the wrong one,
 * for a reason specific to this page: **it would collapse the denominator.**
 * The question this screen exists to answer is "how much of ours is
 * public?", which needs public and private counted against the same total
 * — and a server-side filter makes `all` contain only what passed it, so
 * "6 of 9" becomes "6 of 6". Client-side also keeps this filter the same
 * mechanism as the status filter beside it, rather than two controls that
 * look alike and behave differently.
 */
export default function ActivitiesPage() {
  const { data, loading, error } = useAsync(() => api.activities.list(), []);
  const properties = useAsync(() => api.properties.list(), []);
  const [filter, setFilter] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [visibility, setVisibility] = useState<VisibilityFilter>("all");

  const propertyName = (propertyId: number | null): string => {
    if (propertyId == null) return "No property";
    return (
      properties.data?.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property"
    );
  };

  const all = useMemo(() => data?.features ?? [], [data]);

  // null until the property list resolves (or if it fails) — the second
  // half of the two-condition public rule is genuinely unknown until then,
  // and publicVisibility must not guess it. See utils/publicVisibility.ts.
  const propertyVisibility = useMemo<PropertyVisibility[] | null>(
    () =>
      properties.data?.features.map((p) => ({
        id: p.id,
        isPublic: p.properties.is_public,
      })) ?? null,
    [properties.data],
  );

  const visibilityOf = (activity: Activity) =>
    publicVisibility(activity.properties.is_public, activity.properties.property, propertyVisibility);

  const counts = useMemo(
    () => countVisibility(all.map(visibilityOf)),
    [all, propertyVisibility],
  );

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    return all.filter((a: Activity) => {
      if (status === "planned" && a.properties.is_done) return false;
      if (status === "done" && !a.properties.is_done) return false;
      if (!matchesVisibilityFilter(visibility, visibilityOf(a))) return false;
      if (!query) return true;
      // Everything a person might reasonably remember an activity by:
      // what it was, where it was, what state it's in, what was planted,
      // and whatever they typed in the notes.
      //
      // Deliberately NOT the public/private badge's own words: a note
      // reading "spoke to the public about this" would then match a search
      // for "public" and read as a visibility hit. The Visibility select is
      // the affordance for that, and it can't produce a false positive.
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
  }, [all, filter, status, visibility, properties.data]);

  const dateLabel = (activity: Activity): string | null => {
    const { date_done, date_planned } = activity.properties;
    if (date_done) return `done ${date_done}`;
    if (date_planned) return `planned ${date_planned}`;
    return null;
  };

  const narrowed = filter.trim() !== "" || status !== "all" || visibility !== "all";
  const activityCount = countLabel(data?.features, "activity", "activities");

  return (
    <div className="page">
      <div className="page__header">
        <h1>Activities</h1>
      </div>
      <p className="muted">Every activity across your properties. Select one to view or edit it.</p>

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="form-error">Couldn't load activities: {error}</p>}

      {/* The exposure summary sits above the controls, not below them: on a
          phone the three filter fields stack, and putting the one line that
          answers "what of ours is public?" underneath them buries the
          point of the screen below the fold. */}
      {!loading && !error && all.length > 0 && propertyVisibility != null && (
        <>
          <p className="muted">{publicCountSummary(counts, ACTIVITY_NOUN)}</p>
          {wouldPublishSummary(counts, ACTIVITY_NOUN) && (
            <p className="muted">{wouldPublishSummary(counts, ACTIVITY_NOUN)}</p>
          )}
        </>
      )}
      {/* Without the property list the public/private state of a record is
          genuinely undecidable (see utils/publicVisibility.ts), so no badge
          renders. Say so rather than leaving a silent absence — D21's
          misattribution lesson: a screen that quietly omits something looks
          like a screen that has nothing to say. */}
      {!loading && !error && all.length > 0 && properties.error && (
        <p className="muted">
          Couldn't load your properties, so public/private status isn't shown here.
        </p>
      )}

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
          <label className="field">
            <span>Visibility</span>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as VisibilityFilter)}
            >
              <option value="all">All</option>
              <option value="public">On the public site</option>
              <option value="not-public">Not on the public site</option>
            </select>
          </label>
        </>
      )}

      {/* Unnarrowed, this said nothing at all — so the one screen listing
          every activity an organization has could not answer how many that
          is until you typed something into it. Both filters here are
          client-side (the list is fetched once, unfiltered), so `all` really
          is the organization's total and the count needs no qualifier,
          unlike Tasks and Species. */}
      {!loading &&
        (narrowed ? (
          <p className="muted">
            Showing {filtered.length} of {all.length}.
          </p>
        ) : (
          activityCount && all.length > 0 && <p className="muted">{activityCount}.</p>
        ))}

      <ul className="card-list">
        {filtered.map((activity) => {
          const state = visibilityOf(activity);
          return (
          <li key={activity.id} className="card card--row">
            <Link
              to={`/properties/${activity.properties.property}/activities/${activity.id}/edit`}
              className="card__link"
            >
              <strong>
                {activity.properties.activity_type_name}
                <span className="muted"> — {activity.properties.status_name}</span>
                {/* Both states are marked, unlike the "Private"-only badge
                    on a property's own page. Marking only the exception is
                    right where you already know the context; on the screen
                    whose job is answering "what of ours is public?" it
                    means reading publication off the *absence* of a badge,
                    which is what D39 found. */}
                {/* Gated on the property list as a whole, not just on this
                    row's own state: a private record is decidable without
                    it, so otherwise half the rows badge themselves a beat
                    before the rest and the unbadged ones read as having no
                    status at all. One gate, one moment — the same one the
                    exposure summary above uses. */}
                {propertyVisibility != null && state && (
                  <span className={visibilityBadgeClass(state)}>{visibilityLabel(state)}</span>
                )}
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
          );
        })}
      </ul>

      {/* "your search" was already inaccurate when only the Status select
          was narrowing, and a Visibility select makes that the common case
          rather than a corner — so it names whichever is actually doing it. */}
      {!loading && !error && all.length > 0 && filtered.length === 0 && (
        <p className="muted">
          No activities match {filter.trim() ? "your search" : "these filters"}.
        </p>
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
