import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { isPropertyScoped, roleAtLeast } from "../auth/roles";
import { useAnnounce } from "../components/Announcer";
import { LoadError } from "../components/LoadError";
import { countLabel } from "../utils/counts";

export default function PropertiesPage() {
  const { data, loading, error, reload } = useAsync(() => api.properties.listWithoutGeometry(), []);
  const { session } = useAuth();
  const role = session?.membership?.role;
  // A property-scoped member can't create a *new* property (see
  // backend PropertyViewSet.perform_create) — creating one is an
  // account-wide action, and a scoped member is by definition limited to
  // properties they've already been granted. Hide the control rather
  // than show one that always 403s.
  const canCreate = roleAtLeast(role, "editor") && !isPropertyScoped(session?.membership);
  const canEdit = roleAtLeast(role, "editor");
  const canDelete = roleAtLeast(role, "admin");
  const properties = data?.features ?? [];
  // Counted from the list this screen already holds, which reads through
  // Property.objects — the manager that hides soft-deleted rows. So a
  // property in its 30-day window is excluded here and counted on Manage →
  // Recently deleted instead. That is correct (it is not in this list) and
  // is written down so it doesn't get "fixed" into all_objects by someone
  // who reads the number as "properties this organization has ever had".
  const propertyCount = countLabel(data?.features, "property", "properties");
  const [deleteError, setDeleteError] = useState<{ id: number; message: string } | null>(null);
  // D71a. This was the one list screen in the app with no filter at all —
  // its only useState held a delete error — while two of its siblings
  // advertise filtering *by property*. Client-side substring match, the
  // same shape and the same "fine at current scale" reasoning as
  // SpeciesPage's own box (and Combobox.tsx's, 2026-08-27).
  //
  // Name and slug, and deliberately not the "Private" badge's own word: a
  // property named "Private Woodlot" would then match a search for
  // "private" and read as a visibility hit. That is the rule
  // ActivitiesPage's haystack comment already sets, and here there is no
  // visibility select to own that dimension, so the safer half is to not
  // claim it at all.
  const [filter, setFilter] = useState("");
  const announce = useAnnounce();

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return properties;
    return properties.filter((p) =>
      [p.properties.name, p.properties.slug].join(" ").toLowerCase().includes(query),
    );
  }, [properties, filter]);

  const handleDelete = async (id: number, name: string) => {
    if (
      !window.confirm(
        // This names a *nav path the user has to find*, so it has to track the
        // nav's real labels: "Manage" is BottomNav.tsx's entry (it was "Admin"
        // until 2026-09-03) and "Recently deleted" is that section's own label
        // in manage/sections.ts. Rename either and this string — plus its twin
        // in PropertyMapPage.tsx — has to move with it, or the one sentence a
        // user reads while destroying something sends them somewhere that
        // doesn't exist. The /admin → /manage redirect doesn't help here:
        // this is a menu path, not a URL.
        `Delete "${name}"? This also hides its activities and sightings. ` +
          "An admin can restore it from Manage → Recently deleted within 30 days, " +
          "after which it's removed for good.",
      )
    ) {
      return;
    }
    setDeleteError(null);
    try {
      await api.properties.remove(id);
      reload();
    } catch (err) {
      // Keyed by property id so the message lands on the row whose Delete
      // was pressed, rather than at the top of a list the user may have
      // scrolled past. Without this the row simply stayed put — which on a
      // *list* is weak feedback (the argument PropertyMapPage's
      // handleDeletePage makes for swallowing) and on the twin handler in
      // PropertyMapPage is none at all, since that one navigates away on
      // success. See D55 (2026-09-24); both twins need it.
      // Announcing the *same* string that renders, not a summary of it —
      // on almost every real failure this is the server's own `detail` or
      // D21's statusFallback rather than the literal below (see D55a's own
      // correction), and a message invented here would disagree with the
      // one on screen. D57a, 2026-09-24.
      const message = err instanceof ApiError ? err.message : "Couldn't delete that property.";
      setDeleteError({ id, message });
      announce(message);
    }
  };

  return (
    <div className="page">
      <div className="page__header">
        <h1>Properties</h1>
        {canCreate && (
          <Link to="/properties/new" className="btn btn-primary btn-small">
            + New property
          </Link>
        )}
      </div>

      {loading && <p className="muted">Loading…</p>}
      {/* The affordance that was here, alone, for twenty other screens —
          now shared, so the next screen inherits it rather than the
          message alone (see components/LoadError.tsx). */}
      {error && <LoadError what="properties" error={error} onRetry={reload} />}

      {!loading && !error && properties.length > 0 && (
        <label className="field">
          <span>Search</span>
          <input
            type="search"
            placeholder="Filter by name…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
      )}

      {/* Only once there is something to count: the empty state below
          already says "No properties yet" in prose, and a "0 properties."
          above it would be the same fact twice. Narrowed, it becomes
          "Showing X of Y" — SpeciesPage's wording, and the reason that
          page keys on the filter rather than dropping the count while
          something is typed. */}
      {propertyCount && properties.length > 0 && (
        <p className="muted">
          {filter.trim() ? `Showing ${filtered.length} of ${propertyCount}` : propertyCount}.
        </p>
      )}

      {!loading && !error && properties.length === 0 && (
        <div className="empty-state">
          {/* The prose follows the gate for the same reason the button
              does: "Draw your first boundary" is an instruction, and a viewer has no way to
              follow either route. Swept across all four empty states
              rather than fixed only where it was noticed — D25 fixing
              one of three quick-log links and recording the class as
              closed is exactly what produced D76. */}
          <p>
            {canCreate
              ? "No properties yet. Draw your first boundary to get started."
              : "No properties to show yet."}
          </p>
          {canCreate && (
            <Link to="/properties/new" className="btn btn-primary">
              + New property
            </Link>
          )}
        </div>
      )}

      <ul className="card-list">
        {filtered.map((property) => (
          <li key={property.id} className="card card--row">
            {/* The link and any delete error share one .card__stack so this
                stays a two-item .card--row — a third top-level child would
                land in its space-between layout (SpeciesRow keeps its own
                error inside the info div for the same reason). */}
            <div className="card__stack">
              <Link to={`/properties/${property.id}`} className="card__link">
                <strong>
                  {property.properties.name}
                  {!property.properties.is_public && <span className="badge">Private</span>}
                </strong>
                {/* `has_boundary`, not `geometry` — this list opts out of
                    geometry, so every row's would be null and every
                    property would read as undrawn. See
                    backend/apps/accounts/geometry.py. */}
                <span className="muted">
                  {property.properties.has_boundary ? "Boundary drawn" : "No boundary drawn yet"}
                </span>
              </Link>
              {deleteError?.id === property.id && (
                <p className="form-error">{deleteError.message}</p>
              )}
            </div>
            {(canEdit || canDelete) && (
              <div className="card__actions">
                {canEdit && (
                  <Link to={`/properties/${property.id}/edit`} className="btn btn-secondary btn-small">
                    Edit
                  </Link>
                )}
                {canDelete && (
                  <button
                    type="button"
                    className="btn btn-danger btn-small"
                    onClick={() => handleDelete(property.id, property.properties.name)}
                  >
                    Delete
                  </button>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>

      {!loading && !error && properties.length > 0 && filtered.length === 0 && (
        <p className="muted">No properties match "{filter}".</p>
      )}
    </div>
  );
}
