import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";

export default function PropertiesPage() {
  const { data, loading, error, reload } = useAsync(() => api.properties.list(), []);
  const properties = data?.features ?? [];

  return (
    <div className="page">
      <div className="page__header">
        <h1>Properties</h1>
        <Link to="/properties/new" className="btn btn-primary btn-small">
          + New property
        </Link>
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
          <Link to="/properties/new" className="btn btn-primary">
            + New property
          </Link>
        </div>
      )}

      <ul className="card-list">
        {properties.map((property) => (
          <li key={property.id}>
            <Link to={`/properties/${property.id}`} className="card card--link">
              <strong>{property.properties.name}</strong>
              <span className="muted">
                {property.geometry ? "Boundary drawn" : "No boundary drawn yet"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
