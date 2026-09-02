import { useMemo } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { isPropertyScoped } from "../auth/roles";
import type { Activity, Sighting, TaskStatus } from "../api/types";

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  open: "Open",
  assigned: "Assigned",
  resolved: "Resolved",
  dismissed: "Dismissed",
};

const RECENT_LIMIT = 5;

/** Sort newest-first by an ISO datetime string — every list here already
 * comes back unsorted from the API (list endpoints don't guarantee
 * order), and ISO 8601 strings sort correctly lexically. */
function byRecency<T>(items: T[], isoDate: (item: T) => string): T[] {
  return [...items].sort((a, b) => (isoDate(a) < isoDate(b) ? 1 : -1));
}

function isUpcoming(activity: Activity): boolean {
  return !activity.properties.is_done;
}

/**
 * Landing page for a logged-in user — replaces the old bare redirect to
 * /properties (see App.tsx/BottomNav.tsx). Deliberately a read-only
 * summary, not another place to edit records: "your tasks," planned/
 * upcoming work still to do, and what's most recently been logged, each
 * linking out to the page that actually handles it. Fetches the same
 * org-wide lists TasksPage/PropertyMapPage already fetch (no new API
 * endpoints) and does the "recent"/"upcoming" sorting client-side — fine
 * at the scale a single org's data reaches today (see Combobox.tsx's
 * matching note on the same tradeoff for picker lists).
 */
export default function DashboardPage() {
  const { session } = useAuth();
  const properties = useAsync(() => api.properties.list(), []);
  const activities = useAsync(() => api.activities.list(), []);
  const sightings = useAsync(() => api.sightings.list(), []);
  const tasks = useAsync(() => api.tasks.list(), []);

  const propertyName = (propertyId: number | null): string => {
    if (propertyId == null) return "No property";
    return properties.data?.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property";
  };

  const myTasks = useMemo(() => {
    if (!session?.user) return [];
    const mine = (tasks.data ?? []).filter(
      (t) => t.assigned_to === session.user.id && (t.status === "open" || t.status === "assigned"),
    );
    return byRecency(mine, (t) => t.created_at).slice(0, RECENT_LIMIT);
  }, [tasks.data, session]);

  // Planned/in-progress activities — its own section (hidden entirely
  // when there's nothing upcoming) rather than folded into "recent
  // activities," since "what still needs doing" and "what was just
  // logged" answer different questions and a done activity from
  // yesterday shouldn't crowd out a planted-but-not-yet-done one from
  // last month. Sorted soonest-planned-first, undated ones last.
  const upcomingActivities = useMemo(() => {
    const upcoming = (activities.data?.features ?? []).filter(isUpcoming);
    const sorted = [...upcoming].sort((a, b) => {
      const ad = a.properties.date_planned;
      const bd = b.properties.date_planned;
      if (ad && bd) return ad < bd ? -1 : ad > bd ? 1 : 0;
      if (ad) return -1;
      if (bd) return 1;
      return 0;
    });
    return sorted.slice(0, RECENT_LIMIT);
  }, [activities.data]);

  const recentActivities = useMemo(
    () => byRecency(activities.data?.features ?? [], (a) => a.properties.created_at).slice(0, RECENT_LIMIT),
    [activities.data],
  );

  const recentSightings = useMemo(
    () => byRecency(sightings.data?.features ?? [], (s) => s.properties.created_at).slice(0, RECENT_LIMIT),
    [sightings.data],
  );

  const nothingYet =
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

      {/* The dashboard's first action — everything else here is a
          read-only summary that links out. Quick log is the geometry-first
          capture flow (owner decision, 2026-09-02: "quick log makes sense
          on the dashboard"); the per-property "+ Activity"/"+ Sighting"
          buttons still exist and still work, this is an additional way in.
          Hidden until there's a property to log against, since the flow
          works out which property you're on from where you tap. */}
      {!nothingYet && (
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
            {!tasks.loading && myTasks.length === 0 && (
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

          {upcomingActivities.length > 0 && (
            <section>
              <div className="page__header">
                <h2>Planned / upcoming activities</h2>
              </div>
              <ul className="card-list">
                {upcomingActivities.map((activity) => (
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
                        {activity.properties.date_planned && ` — planned ${activity.properties.date_planned}`}
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
            {!activities.loading && recentActivities.length === 0 && (
              <p className="muted">No activities logged yet.</p>
            )}
            {recentActivities.length > 0 && (
              <ul className="card-list">
                {recentActivities.map((activity) => (
                  <li key={activity.id} className="card card--row">
                    <Link
                      to={`/properties/${activity.properties.property}/activities/${activity.id}/edit`}
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
            {!sightings.loading && recentSightings.length === 0 && (
              <p className="muted">No sightings logged yet.</p>
            )}
            {recentSightings.length > 0 && (
              <ul className="card-list">
                {recentSightings.map((sighting: Sighting) =>
                  sighting.properties.property != null ? (
                    <li key={sighting.id} className="card card--row">
                      <Link
                        to={`/properties/${sighting.properties.property}/sightings/${sighting.id}/edit`}
                        className="card__link"
                      >
                        <strong>{sighting.properties.species_detail.common_name}</strong>
                        <span className="muted">
                          {propertyName(sighting.properties.property)} —{" "}
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
