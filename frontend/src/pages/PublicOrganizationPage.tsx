import { Link, useParams } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import PublicPageNav from "../components/PublicPageNav";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";

/**
 * The org-level public "portfolio" page — one of the two public-site
 * shapes requested (the other is PublicPropertyPage, per-property). Lists
 * every property the org has marked public (Property.is_public — see
 * backend/apps/accounts/models.py); a property left private doesn't
 * appear here at all, not even as a name. No login required; see
 * PublicHeader for the way back to the real app.
 *
 * This is also the built-in **Explore** page in the "public site
 * storytelling" feature (see /docs/open-questions.md) — an org can author
 * its own pages and pick one as the landing page instead, in which case
 * this same component renders that page's content at the URL root, with
 * Explore (this property list) still reachable via the page nav /
 * `/explore`. `forcePage="explore"` (passed by the `/explore` route in
 * App.tsx) always shows this list regardless of the landing-page pick.
 */
export default function PublicOrganizationPage({ forcePage }: { forcePage?: "explore" }) {
  // Reachable via the vanity-slug route (/public/:orgSlug), the legacy
  // numeric route (/public/org/:orgId), and the authored-page routes
  // (/public/:orgSlug/pages/:pageSlug, /public/:orgSlug/explore) — see
  // App.tsx. Resolve by whichever params this render got.
  const { orgSlug, orgId, pageSlug: routePageSlug } = useParams<{
    orgSlug?: string;
    orgId?: string;
    pageSlug?: string;
  }>();
  const { data, loading, error } = useAsync(
    () => (orgSlug ? api.public.organizationBySlug(orgSlug) : api.public.organization(Number(orgId))),
    [orgSlug, orgId],
  );

  // Which page to actually show, most-specific first: an explicit
  // /pages/:slug route, then an explicit /explore route, then the org's
  // own landing-page pick (null = Explore, the property list below). See
  // /docs/open-questions.md, "Public site storytelling / custom content".
  const activeSlug =
    routePageSlug ?? (forcePage === "explore" ? null : data?.landing_page_slug ?? null);
  const resolvedOrgSlug = data?.organization.slug ?? orgSlug;

  const page = useAsync(
    () =>
      activeSlug && resolvedOrgSlug
        ? api.public.organizationPage(resolvedOrgSlug, activeSlug)
        : Promise.resolve(null),
    [resolvedOrgSlug, activeSlug],
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
              {data.pages.length > 0 && (
                <PublicPageNav
                  basePath={`/public/${data.organization.slug}`}
                  pages={data.pages}
                  activeSlug={activeSlug}
                />
              )}
              {activeSlug ? (
                page.loading ? (
                  <p className="muted">Loading…</p>
                ) : page.error || !page.data ? (
                  <p className="form-error">Couldn't load this page.</p>
                ) : (
                  <article
                    className="page-content"
                    // Server-rendered from markdown and sanitized before
                    // ever reaching this response — see
                    // backend/apps/pages/rendering.py. Never render
                    // author-supplied text here any other way.
                    dangerouslySetInnerHTML={{ __html: page.data.body_html }}
                  />
                )
              ) : (
                <>
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
                          to={`/public/${data.organization.slug}/${property.properties.slug}`}
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
            </>
          )}
        </div>
      </main>
    </div>
  );
}
