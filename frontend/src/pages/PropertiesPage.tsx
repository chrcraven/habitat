import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { isPropertyScoped, roleAtLeast } from "../auth/roles";

export default function PropertiesPage() {
  const { data, loading, error, reload } = useAsync(() => api.properties.list(), []);
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
    await api.properties.remove(id);
    reload();
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
      {error && (
        <p className="form-error">
          Couldn't load properties: {error}{" "}
          <button type="button" className="btn-link" onClick={reload}>
            Retry
          </button>
        </p>
      )}

      {!loading && !error && properties.length === 0 && (
        <div className="empty-state">
          <p>No properties yet. Draw your first boundary to get started.</p>
          {canCreate && (
            <Link to="/properties/new" className="btn btn-primary">
              + New property
            </Link>
          )}
        </div>
      )}

      <ul className="card-list">
        {properties.map((property) => (
          <li key={property.id} className="card card--row">
            <Link to={`/properties/${property.id}`} className="card__link">
              <strong>
                {property.properties.name}
                {!property.properties.is_public && <span className="badge">Private</span>}
              </strong>
              <span className="muted">
                {property.geometry ? "Boundary drawn" : "No boundary drawn yet"}
              </span>
            </Link>
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
    </div>
  );
}
