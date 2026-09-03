import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";
import { PageRow } from "./rows";

/** Org-level authored pages for the public site, plus which one visitors
 * land on. An org-level page isn't scoped to any property, so a
 * property-scoped admin can't author one (backend
 * PageViewSet.perform_create) — hence account-admin only. */
export default function PagesSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const org = useAsync(() => (allowed ? api.org.get() : Promise.resolve(null)), [allowed]);
  const pages = useAsync(() => (allowed ? api.pages.list() : Promise.resolve([])), [allowed]);
  const [savingLandingPage, setSavingLandingPage] = useState(false);
  const [landingPageError, setLandingPageError] = useState<string | null>(null);

  const handleLandingPageChange = async (value: string) => {
    setSavingLandingPage(true);
    setLandingPageError(null);
    try {
      await api.org.update({ landing_page: value ? Number(value) : null });
      org.reload();
    } catch (err) {
      setLandingPageError(
        err instanceof ApiError ? err.message : "Couldn't update the landing page.",
      );
    } finally {
      setSavingLandingPage(false);
    }
  };

  return (
    <ManageSectionPage
      title="Pages"
      access="account-admin"
      actions={
        <Link to="/manage/pages/new" className="btn btn-secondary btn-small">
          + Add page
        </Link>
      }
      intro={
        <p className="muted">
          Authored pages for your public site — the auto-generated property list ("Explore") is
          always there too; pick which one visitors land on below.
        </p>
      }
    >
      {pages.loading && <p className="muted">Loading…</p>}
      {pages.error && <p className="form-error">Couldn't load pages: {pages.error}</p>}
      {(pages.data?.length ?? 0) > 0 && (
        <ul className="card-list">
          {pages.data?.map((p) => (
            <PageRow key={p.id} page={p} onDeleted={pages.reload} />
          ))}
        </ul>
      )}
      {org.data && (
        <label className="field">
          <span>Landing page</span>
          <select
            value={org.data.landing_page ?? ""}
            disabled={savingLandingPage}
            onChange={(e) => handleLandingPageChange(e.target.value)}
          >
            <option value="">Explore (the auto-generated property list)</option>
            {pages.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
          <span className="field-hint muted">
            Which page visitors see first at <code>/public/{org.data.slug}</code>. Explore stays
            reachable from the page nav either way.
          </span>
          {landingPageError && <span className="form-error">{landingPageError}</span>}
        </label>
      )}
    </ManageSectionPage>
  );
}
