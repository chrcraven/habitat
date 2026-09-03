import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { publicSiteUrl } from "../../utils/publicSite";
import QrCodePanel from "../../components/QrCodePanel";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";

/** Organization name, public URL name, and the public-site QR code —
 * the org-level settings from the old single-route admin page. Restricted
 * to an account-wide admin: a property-scoped admin administers its own
 * properties, not the organization (see sections.ts). */
export default function OrganizationSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const org = useAsync(() => (allowed ? api.org.get() : Promise.resolve(null)), [allowed]);

  const [orgName, setOrgName] = useState("");
  const [renaming, setRenaming] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);

  const [orgSlug, setOrgSlug] = useState("");
  const [savingSlug, setSavingSlug] = useState(false);
  const [slugError, setSlugError] = useState<string | null>(null);

  useEffect(() => {
    if (org.data) {
      setOrgName(org.data.name);
      setOrgSlug(org.data.slug);
    }
  }, [org.data]);

  const handleRename = async (e: FormEvent) => {
    e.preventDefault();
    setRenaming(true);
    setRenameError(null);
    try {
      await api.org.update({ name: orgName });
      org.reload();
    } catch (err) {
      setRenameError(err instanceof ApiError ? err.message : "Couldn't rename organization.");
    } finally {
      setRenaming(false);
    }
  };

  const handleSlugSave = async (e: FormEvent) => {
    e.preventDefault();
    setSavingSlug(true);
    setSlugError(null);
    try {
      await api.org.update({ slug: orgSlug });
      org.reload();
    } catch (err) {
      setSlugError(err instanceof ApiError ? err.message : "Couldn't update the public URL.");
    } finally {
      setSavingSlug(false);
    }
  };

  return (
    <ManageSectionPage
      title="Organization"
      access="account-admin"
      actions={
        org.data && (
          <a
            href={publicSiteUrl(`/public/${org.data.slug}`)}
            className="btn btn-secondary btn-small"
            target="_blank"
            rel="noopener noreferrer"
          >
            View public site ↗
          </a>
        )
      }
    >
      {org.loading && <p className="muted">Loading…</p>}
      {org.error && <p className="form-error">Couldn't load organization: {org.error}</p>}

      <form onSubmit={handleRename} className="form">
        {renameError && <p className="form-error">{renameError}</p>}
        <label className="field">
          <span>Organization name</span>
          <input type="text" required value={orgName} onChange={(e) => setOrgName(e.target.value)} />
        </label>
        <button
          type="submit"
          className="btn btn-secondary btn-small"
          disabled={renaming || !orgName || orgName === org.data?.name}
        >
          {renaming ? "Saving…" : "Save name"}
        </button>
      </form>

      <form onSubmit={handleSlugSave} className="form">
        {slugError && <p className="form-error">{slugError}</p>}
        <label className="field">
          <span>Public URL name</span>
          <input
            type="text"
            value={orgSlug}
            onChange={(e) => setOrgSlug(e.target.value)}
            placeholder="e.g. mira-canyon-trust"
          />
          <span className="field-hint muted">
            Your public site lives at <code>/public/{orgSlug || org.data?.slug}</code>. Lowercase
            letters, numbers, and hyphens; leave blank to regenerate it from the organization name.
          </span>
        </label>
        <button
          type="submit"
          className="btn btn-secondary btn-small"
          disabled={savingSlug || orgSlug === org.data?.slug}
        >
          {savingSlug ? "Saving…" : "Save URL name"}
        </button>
      </form>

      {org.data && (
        <div className="form">
          <label className="field">
            <span>Public QR code</span>
            <span className="field-hint muted">
              A scannable code for your public site — put it on a sign, a flyer, or a card.
            </span>
          </label>
          <QrCodePanel
            fetchQr={(logo) => api.org.qrCode(logo)}
            downloadName={`habitat-${org.data.slug}-qr.png`}
            publicUrl={publicSiteUrl(`/public/${org.data.slug}`)}
          />
        </div>
      )}
    </ManageSectionPage>
  );
}
