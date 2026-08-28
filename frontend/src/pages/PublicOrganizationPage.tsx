import { Link, useParams } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";

/**
 * The org-level public "portfolio" page — one of the two public-site
 * shapes requested (the other is PublicPropertyPage, per-property). Lists
 * every property the org has marked public (Property.is_public — see
 * backend/apps/accounts/models.py); a property left private doesn't
 * appear here at all, not even as a name. No login required; see
 * PublicHeader for the way back to the real app.
 */
export default function PublicOrganizationPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const { data, loading, error } = useAsync(
    () => api.public.organization(Number(orgId)),
    [orgId],
  );

  return (
    <div className="app-shell app-shell--public">
      <PublicHeader />
      <main className="app-main">
        <div className="page page--public">
          {loading && <p className="muted">Loading…</p>}
          {error && <p className="form-error">Couldn't load this page.</p>}
          {data && (
            <>
              <div className="page__header">
                <h1>{data.organization.name}</h1>
              </div>
              <p className="muted">
                Land managed with Habitat. {data.properties.features.length === 0
                  ? "No public properties yet."
                  : `${data.properties.features.length} public ${
                      data.properties.features.length === 1 ? "property" : "properties"
                    }.`}
              </p>
              <ul className="card-list card-list--grid">
                {data.properties.features.map((property) => (
                  <li key={property.id} className="card card--row">
                    <Link
                      to={`/public/properties/${property.id}`}
                      className="card__link"
                    >
                      <strong>{property.properties.name}</strong>
                      <span className="muted">
                        {property.geometry ? "Boundary drawn" : "No boundary drawn yet"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
