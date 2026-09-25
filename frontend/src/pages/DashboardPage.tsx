import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { isPropertyScoped, roleAtLeast } from "../auth/roles";
import type { Activity, Sighting, TaskStatus } from "../api/types";
import { LoadError } from "../components/LoadError";
import { withReturnTo } from "../utils/returnTo";

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  open: "Open",
  assigned: "Assigned",
  resolved: "Resolved",
  dismissed: "Dismissed",
};

/** How many rows the two "Recent" sections show. Three, not five, per
 * owner feedback (2026-09-03: "Recents should limit to last three") —
 * they're a glance at what was just logged, not a list to work from. */
const RECENT_LIMIT = 3;

/** "Your tasks" and "Planned / in progress" answer "what do I still have to
 * do," so they keep the longer list — the feedback above was about the
 * Recent sections specifically. */
const TODO_LIMIT = 5;

/** Sort newest-first by an ISO datetime string — every list here already
 * comes back unsorted from the API (list endpoints don't guarantee
 * order), and ISO 8601 strings sort correctly lexically. */
function byRecency<T>(items: T[], isoDate: (item: T) => string): T[] {
  return [...items].sort((a, b) => (isoDate(a) < isoDate(b) ? 1 : -1));
}

/** The whole of this app's notion of "finished": one boolean column, never
 * a date. Named for what it actually reads — the old name, `isUpcoming`,
 * asserted a futurity the predicate cannot check (nothing anywhere compares
 * `date_planned` to today), and that is how the section heading below came
 * to claim it too. See the comment on that heading (D54a). */
function isDone(activity: Activity): boolean {
  return activity.properties.is_done;
}

/**
 * Landing page for a logged-in user — replaces the old bare redirect to
 * /properties (see App.tsx/BottomNav.tsx). Deliberately a read-only
 * summary, not another place to edit records: "your tasks," work that
 * isn't done yet, and what's most recently been logged, each
 * linking out to the page that actually handles it. Fetches the same
 * org-wide lists TasksPage/PropertyMapPage already fetch (no new API
 * endpoints) and does the "recent"/"not done" sorting client-side — fine
 * at the scale a single org's data reaches today (see Combobox.tsx's
 * matching note on the same tradeoff for picker lists).
 */
export default function DashboardPage() {
  // The address to come back to after editing a row (D66a). The dashboard
  // has no filters of its own, but it links to the same two edit forms as
  // the list pages and had the same defect: clicking a row here used to
  // leave you on that record's property page rather than back here.
  const { pathname, search } = useLocation();
  const origin = `${pathname}${search}`;
  const { session } = useAuth();
  const canEdit = roleAtLeast(session?.membership?.role, "editor");
  const properties = useAsync(() => api.properties.listWithoutGeometry(), []);
  // No map on this page, so no coordinates are read — all three lists
  // opt out. See `api.activities.listWithoutGeometry` and
  // backend/apps/accounts/geometry.py. The properties list was the last
  // holdout: `Property.boundary` is nullable, so it could only join once
  // the row carried `has_boundary` separately.
  const activities = useAsync(() => api.activities.listWithoutGeometry(), []);
  const sightings = useAsync(() => api.sightings.listWithoutGeometry(), []);
  const tasks = useAsync(() => api.tasks.list(), []);

  /** Returns `null` — *not* "Unknown property" — when the property list
   * hasn't arrived, so a row can leave the clause out rather than assert
   * something it doesn't know.
   *
   * "Unknown property" claims we looked this id up and it wasn't there,
   * which is a real state (a soft-deleted property) and a different one
   * from "the list failed to load". Before the D63a sweep those collapsed,
   * so a failed properties fetch labelled every row on the landing page
   * with a name that read as a fact about the record. D47a's lesson — ask
   * what a list's empty value means — one row down from `failed` above. */
  const propertyName = (propertyId: number | null): string | null => {
    if (propertyId == null) return "No property";
    if (!properties.data) return null;
    return properties.data.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property";
  };

  const myTasks = useMemo(() => {
    if (!session?.user) return [];
    const mine = (tasks.data ?? []).filter(
      (t) => t.assigned_to === session.user.id && (t.status === "open" || t.status === "assigned"),
    );
    return byRecency(mine, (t) => t.created_at).slice(0, TODO_LIMIT);
  }, [tasks.data, session]);

  // Planned/in-progress activities — its own section (hidden entirely when
  // there's nothing left to do) rather than folded into "recent
  // activities," since "what still needs doing" and "what was just
  // logged" answer different questions and a done activity from
  // yesterday shouldn't crowd out a planted-but-not-yet-done one from
  // last month. Sorted soonest-planned-first, undated ones last.
  //
  // That sort plus TODO_LIMIT is what makes the section's own cap
  // load-bearing: it fills from the *stalest* end, so a slipped item
  // outranks a genuinely upcoming one. Whether that ranking is right is
  // D54b's Q2 and is deliberately untouched here — D54a only stopped the
  // heading claiming otherwise.
  const notDoneActivities = useMemo(() => {
    const notDone = (activities.data?.features ?? []).filter((a) => !isDone(a));
    const sorted = [...notDone].sort((a, b) => {
      const ad = a.properties.date_planned;
      const bd = b.properties.date_planned;
      if (ad && bd) return ad < bd ? -1 : ad > bd ? 1 : 0;
      if (ad) return -1;
      if (bd) return 1;
      return 0;
    });
    return sorted.slice(0, TODO_LIMIT);
  }, [activities.data]);

  // Done activities only. "Recent" used to sort *every* activity by
  // created_at, so a freshly logged planned activity appeared here and in
  // "Planned / in progress" at once — the same record counted twice on one
  // screen (owner feedback, 2026-09-03: "Anything planned should not show
  // under recent"). Sharing one predicate with the section above, used in
  // both directions, keeps the two complementary by construction rather
  // than by a second rule that could drift from the first.
  const recentActivities = useMemo(
    () =>
      byRecency(
        (activities.data?.features ?? []).filter(isDone),
        (a) => a.properties.created_at,
      ).slice(0, RECENT_LIMIT),
    [activities.data],
  );

  const recentSightings = useMemo(
    () => byRecency(sightings.data?.features ?? [], (s) => s.properties.created_at).slice(0, RECENT_LIMIT),
    [sightings.data],
  );

  // Found while sweeping D63a, and the more serious half of it: this page
  // renders **no load error at all** — four fetches, not one `.error`
  // read — so a failed load didn't merely lack a Retry, it was reported as
  // an answer. `useAsync` leaves `data` null and `loading` false when a
  // request fails, so every `data?.x ?? []` below quietly became "you have
  // none", on the landing page, with no indication anything had gone
  // wrong. A user whose properties request dropped was told **"No
  // properties yet. Draw your first boundary to get started."** with a
  // "+ New property" button under it.
  //
  // D21's false-cause class, and the exact defect D50a fixed on TasksPage
  // ("No tasks yet." beneath its own "Couldn't load tasks") — reached here
  // from the other direction, since the error message that would have
  // contradicted the empty state was never rendered in the first place.
  const failed = properties.error ?? activities.error ?? sightings.error ?? tasks.error;
  const retry = () => {
    properties.reload();
    activities.reload();
    sightings.reload();
    tasks.reload();
  };

  const nothingYet =
    !failed &&
    !properties.loading &&
    !activities.loading &&
    !sightings.loading &&
    !tasks.loading &&
    (properties.data?.features.length ?? 0) === 0;

  return (
    <div className="page">
      <div className="page__header">
        <h1>{session?.user.first_name ? `Welcome back, ${session.user.first_name}` : "Welcome back"}</h1>
      </div>
      <p className="muted">
        Your open tasks, planned work, and what's most recently been logged across all your properties.
      </p>

      {/* One message for four fetches, deliberately. The sections below are
          four views of one question ("what needs my attention?"), and
          naming which of them failed would ask the reader to work out what
          that means for the rest — where the honest summary is that this
          page is not showing them everything. */}
      {failed && <LoadError what="your dashboard" error={failed} onRetry={retry} />}

      {/* The dashboard's first action — everything else here is a
          read-only summary that links out. Quick log is the geometry-first
          capture flow (owner decision, 2026-09-02: "quick log makes sense
          on the dashboard"); the per-property "+ Activity"/"+ Sighting"
          buttons still exist and still work, this is an additional way in.
          Hidden until there's a property to log against, since the flow
          works out which property you're on from where you tap.

          Also editor+ (D25, 2026-09-12). This was the app's only create
          control with no role check — a viewer saw it, walked the whole
          capture, filled in the detail step and was refused by the
          backend on save. The backend gate is the real one; this stops
          offering work that can only end in a refusal, matching the
          nine other files that compute the same check (PropertyMapPage's
          per-property "+ Sighting"/"+ Activity" FABs are the closest
          siblings — same action, reached a different way). */}
      {!nothingYet && canEdit && (
        <Link to="/quick-log" className="btn btn-primary">
          ⊕ Quick log
        </Link>
      )}

      {nothingYet && (
        <div className="empty-state">
          <p>No properties yet. Draw your first boundary to get started.</p>
          {/* A property-scoped member can't create a new property (see
              PropertiesPage's matching gate) — if they land here with
              zero visible properties, that means their own scoped
              property was itself removed, not that they can fix it by
              creating one. */}
          {!isPropertyScoped(session?.membership) && (
            <Link to="/properties/new" className="btn btn-primary">
              + New property
            </Link>
          )}
        </div>
      )}

      {!nothingYet && (
        <>
          <section>
            <div className="page__header">
              <h2>Your tasks</h2>
              <Link to="/tasks" className="btn-link">
                All tasks →
              </Link>
            </div>
            {/* `!error` as well as `!loading`: an empty list and a list
                that never arrived are the same value here, and only one of
                them means "none" (D21/D50a). */}
            {!tasks.loading && !tasks.error && myTasks.length === 0 && (
              <p className="muted">No open tasks assigned to you.</p>
            )}
            {myTasks.length > 0 && (
              <ul className="card-list">
                {myTasks.map((task) => (
                  <li key={task.id} className="card card--row">
                    <div>
                      <strong>{task.title}</strong>
                      <span className="badge">{TASK_STATUS_LABELS[task.status]}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {notDoneActivities.length > 0 && (
            <section>
              <div className="page__header">
                {/* NOT "Planned / upcoming activities" (D54a, 2026-09-23).
                    The predicate below is `!isDone` and never looks at a
                    date — nothing anywhere in this app compares
                    `date_planned` to anything — so this set is every
                    not-done activity, slipped ones included. "upcoming"
                    claimed a futurity the set doesn't have, and the
                    ascending sort plus TODO_LIMIT makes the claim worst
                    exactly when it matters: the more work slips, the more
                    completely the cap fills from the stalest end and hides
                    what's genuinely ahead.

                    "Planned / in progress" is the app's own existing
                    wording for this same `!is_done` set, in both places it
                    already appears: ActivityStatusLegend (the map key) and
                    ActivitiesPage's Status filter — which is where the link
                    below goes, so a reader who clicks through and narrows
                    the list sees the identical words.

                    Measured before settling on the length, so it isn't
                    re-derived: at a 390px viewport the row leaves 230px
                    beside the link, and this heading is 421px, so it wraps
                    to two lines and the link takes a third. That wrap is
                    NOT new — the old heading was 400px and already wrapped;
                    the link's own line is the whole delta. Shortening to
                    "Planned / in progress" does not buy a one-line header
                    either (288px, still wraps); only inventing a short
                    phrase like "Still to do" (132px) would, and that adds a
                    fourth name for a set the app already names twice.
                    Nothing clips at 320/390/1280px. Reuse beat tidiness.

                    Deliberately decides nothing about whether a passed
                    planned date is a concept at all, nor about the sort and
                    cap — both are open owner questions (D54b's Q1/Q2 in
                    docs/open-questions.md). This aligns the heading with
                    what the code does; it does not change what the code
                    does. */}
                <h2>Planned / in progress activities</h2>
                {/* The only one of the dashboard's four sections that had
                    no link out, while "Your tasks" above has carried one
                    all along. That matters most here because this is the
                    section whose cap silently truncates. Unfiltered, like
                    its sibling: "All tasks →" widens from *your* open
                    tasks to the whole org's list, and "All" is the word
                    doing that work. */}
                <Link to="/activities" className="btn-link">
                  All activities →
                </Link>
              </div>
              <ul className="card-list">
                {notDoneActivities.map((activity) => (
                  <li key={activity.id} className="card card--row">
                    <Link
                      to={withReturnTo(`/properties/${activity.properties.property}/activities/${activity.id}/edit`, origin)}
                      className="card__link"
                    >
                      <strong>
                        {activity.properties.activity_type_name}
                        <span className="muted"> — {activity.properties.status_name}</span>
                      </strong>
                      <span className="muted">
                        {propertyName(activity.properties.property)}
                        {activity.properties.date_planned &&
                          `${propertyName(activity.properties.property) ? " — " : ""}planned ${activity.properties.date_planned}`}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <div className="page__header">
              <h2>Recent activities</h2>
            </div>
            {/* Not "no activities logged yet" — this section now shows
                only completed ones, so a user whose activities are all
                still planned has plenty logged and would be told
                otherwise. */}
            {!activities.loading && !activities.error && recentActivities.length === 0 && (
              <p className="muted">No completed activities yet.</p>
            )}
            {recentActivities.length > 0 && (
              <ul className="card-list">
                {recentActivities.map((activity) => (
                  <li key={activity.id} className="card card--row">
                    <Link
                      to={withReturnTo(`/properties/${activity.properties.property}/activities/${activity.id}/edit`, origin)}
                      className="card__link"
                    >
                      <strong>
                        {activity.properties.activity_type_name}
                        <span className="muted"> — {activity.properties.status_name}</span>
                      </strong>
                      <span className="muted">{propertyName(activity.properties.property)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <div className="page__header">
              <h2>Recent sightings</h2>
            </div>
            {!sightings.loading && !sightings.error && recentSightings.length === 0 && (
              <p className="muted">No sightings logged yet.</p>
            )}
            {recentSightings.length > 0 && (
              <ul className="card-list">
                {recentSightings.map((sighting: Sighting) =>
                  sighting.properties.property != null ? (
                    <li key={sighting.id} className="card card--row">
                      <Link
                        to={withReturnTo(`/properties/${sighting.properties.property}/sightings/${sighting.id}/edit`, origin)}
                        className="card__link"
                      >
                        <strong>{sighting.properties.species_detail.common_name}</strong>
                        <span className="muted">
                          {propertyName(sighting.properties.property) &&
                            `${propertyName(sighting.properties.property)} — `}
                          {new Date(sighting.properties.observed_at).toLocaleDateString()}
                        </span>
                      </Link>
                    </li>
                  ) : (
                    <li key={sighting.id} className="card card--row">
                      <div>
                        <strong>{sighting.properties.species_detail.common_name}</strong>
                        <span className="muted">
                          {" "}
                          — {new Date(sighting.properties.observed_at).toLocaleDateString()}
                        </span>
                      </div>
                    </li>
                  ),
                )}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
