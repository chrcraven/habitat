import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { isPropertyScoped, roleAtLeast } from "../auth/roles";
import QrCodePanel from "../components/QrCodePanel";
import ThemeEditorPanel from "../components/ThemeEditorPanel";
import type {
  DeletedProperty,
  Feedback,
  Invitation,
  MembershipDetail,
  Page,
  Property,
  Role,
} from "../api/types";

const ROLES: { value: Role; label: string }[] = [
  { value: "viewer", label: "Viewer — read only" },
  { value: "editor", label: "Editor — read/create/update" },
  { value: "admin", label: "Admin — also delete + manage members" },
];

function propertyOptions(properties: Property[]) {
  return properties.map((p) => ({ id: p.id, name: p.properties.name }));
}

function MemberRow({
  membership,
  properties,
  isSelf,
  onChanged,
}: {
  membership: MembershipDetail;
  properties: Property[];
  isSelf: boolean;
  onChanged: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleRoleChange = async (role: Role) => {
    setBusy(true);
    setError(null);
    try {
      await api.org.members.update(membership.id, { role });
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update role.");
    } finally {
      setBusy(false);
    }
  };

  const handlePropertyToggle = async (propertyId: number, checked: boolean) => {
    const next = checked
      ? [...membership.properties, propertyId]
      : membership.properties.filter((id) => id !== propertyId);
    setBusy(true);
    setError(null);
    try {
      await api.org.members.update(membership.id, { properties: next });
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update property scope.");
    } finally {
      setBusy(false);
    }
  };

  const handleRemove = async () => {
    if (!window.confirm(`Remove ${membership.user.email} from this organization?`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.org.members.remove(membership.id);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't remove member.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row">
        <div>
          <strong>{membership.user.email}</strong>
          {isSelf && <span className="muted"> (you)</span>}
          {(membership.user.first_name || membership.user.last_name) && (
            <span className="muted">
              {" "}
              — {membership.user.first_name} {membership.user.last_name}
            </span>
          )}
        </div>
        <div className="card__actions">
          <button
            type="button"
            className="btn btn-danger btn-small"
            onClick={handleRemove}
            disabled={busy}
          >
            Remove
          </button>
        </div>
      </div>

      <label className="field">
        <span>Role</span>
        <select
          value={membership.role}
          disabled={busy}
          onChange={(e) => handleRoleChange(e.target.value as Role)}
        >
          {ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      {properties.length > 0 && (
        <div className="field">
          <span>
            Property scope — leave all unchecked for account-wide access, or limit this
            role to just the properties checked below
          </span>
          {propertyOptions(properties).map((p) => (
            <label key={p.id} className="field field--checkbox">
              <input
                type="checkbox"
                checked={membership.properties.includes(p.id)}
                disabled={busy}
                onChange={(e) => handlePropertyToggle(p.id, e.target.checked)}
              />
              <span>{p.name}</span>
            </label>
          ))}
        </div>
      )}
    </li>
  );
}

function PendingInvitationRow({
  invitation,
  onRevoked,
  onResent,
}: {
  invitation: Invitation;
  onRevoked: () => void;
  onResent: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [resent, setResent] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(invitation.accept_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.prompt("Copy this invite link:", invitation.accept_url);
    }
  };

  const handleResend = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.org.invitations.resend(invitation.id);
      setResent(true);
      setTimeout(() => setResent(false), 2000);
      // Resending also refreshes the invite's expiry clock (see
      // views.py#InvitationViewSet.resend) — reload so an "(expired)"
      // badge clears without a manual page refresh.
      onResent();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't resend that invitation.");
    } finally {
      setBusy(false);
    }
  };

  const handleRevoke = async () => {
    if (!window.confirm(`Revoke the invitation sent to ${invitation.email}?`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.org.invitations.remove(invitation.id);
      onRevoked();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't revoke that invitation.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row card__row--wrap">
        <div>
          <strong>{invitation.email}</strong>
          <span className="muted"> — invited as {invitation.role}</span>
          {invitation.is_expired && <span className="form-error"> (expired)</span>}
        </div>
        <div className="card__actions">
          <button type="button" className="btn btn-secondary btn-small" onClick={handleCopy}>
            {copied ? "Copied!" : "Copy invite link"}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={handleResend}
            disabled={busy}
          >
            {resent ? "Sent!" : "Resend"}
          </button>
          <button
            type="button"
            className="btn btn-danger btn-small"
            onClick={handleRevoke}
            disabled={busy}
          >
            Revoke
          </button>
        </div>
      </div>
      {invitation.property_names.length > 0 && (
        <p className="muted">Property scope: {invitation.property_names.join(", ")}</p>
      )}
    </li>
  );
}

function daysRemaining(purgeAt: string): number {
  const ms = new Date(purgeAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
}

/** One row in "Recently deleted" (see PropertyViewSet.deleted/restore) —
 * a soft-deleted property still inside its 30-day purge window. Same
 * card/row conventions as MemberRow/PendingInvitationRow above. */
function DeletedPropertyRow({
  property,
  onRestored,
}: {
  property: DeletedProperty;
  onRestored: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleRestore = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.properties.deleted.restore(property.id);
      onRestored();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't restore that property.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row">
        <div>
          <strong>{property.name}</strong>
          <span className="muted">
            {" "}
            — deleted {new Date(property.deleted_at).toLocaleDateString()}, purges in{" "}
            {daysRemaining(property.purge_at)} day{daysRemaining(property.purge_at) === 1 ? "" : "s"}
          </span>
        </div>
        <div className="card__actions">
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={handleRestore}
            disabled={busy}
          >
            {busy ? "Restoring…" : "Restore"}
          </button>
        </div>
      </div>
    </li>
  );
}

/** One row in the admin-only feedback review list — see
 * backend/apps/feedback and /docs/open-questions.md ("App feedback /
 * build workflow"). This is this org's own submitted feedback so an
 * admin can review it without querying the database; the external
 * scheduled routine that actually folds feedback into the build workflow
 * pulls across every org via a separate bearer-token endpoint, not this
 * one. */
function FeedbackRow({ item, onResolved }: { item: Feedback; onResolved: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleResolve = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.feedback.resolve(item.id);
      onResolved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't resolve that item.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row">
        <div>
          <p>{item.message}</p>
          <span className="muted">
            {item.submitted_by_email ?? "unknown"} — {new Date(item.created_at).toLocaleString()}
            {" — "}
            {item.status}
          </span>
        </div>
        {item.status !== "resolved" && (
          <div className="card__actions">
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={handleResolve}
              disabled={busy}
            >
              {busy ? "Saving…" : "Mark resolved"}
            </button>
          </div>
        )}
      </div>
    </li>
  );
}

/** One row in the "Pages" section — an org-level authored page (see
 * backend/apps/pages and /docs/open-questions.md, "Public site
 * storytelling / custom content"). Property-scoped pages are managed the
 * same way from PropertyMapPage instead — this list only ever shows this
 * org's own org-level pages (property IS NULL). */
function PageRow({ page, onDeleted }: { page: Page; onDeleted: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleDelete = async () => {
    if (!window.confirm(`Delete the page "${page.title}"?`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.pages.remove(page.id);
      onDeleted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't delete that page.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row">
        <div>
          <strong>{page.title}</strong>
          <span className="muted"> — /{page.slug}</span>
          {!page.is_public && <span className="muted"> (hidden)</span>}
        </div>
        <div className="card__actions">
          <Link to={`/admin/pages/${page.id}/edit`} className="btn btn-secondary btn-small">
            Edit
          </Link>
          <button
            type="button"
            className="btn btn-danger btn-small"
            onClick={handleDelete}
            disabled={busy}
          >
            Delete
          </button>
        </div>
      </div>
    </li>
  );
}

function AddMemberForm({
  properties,
  onAdded,
}: {
  properties: Property[];
  onAdded: () => void;
}) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [propertyIds, setPropertyIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const togglePropertyId = (id: number, checked: boolean) => {
    setPropertyIds((ids) => (checked ? [...ids, id] : ids.filter((x) => x !== id)));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await api.org.members.create({
        email,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        role,
        properties: propertyIds,
      });
      setSuccess(
        "accept_url" in result
          ? `Invitation sent to ${result.email}. If the email doesn't arrive, copy the ` +
            "link from the pending invitation below and share it yourself."
          : `${result.user.email} was added to your organization.`,
      );
      setEmail("");
      setFirstName("");
      setLastName("");
      setRole("viewer");
      setPropertyIds([]);
      onAdded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add that member.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form form--panel">
      {error && <p className="form-error">{error}</p>}
      {success && <p className="form-success">{success}</p>}
      <label className="field">
        <span>Email</span>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="teammate@example.com"
        />
      </label>
      <div className="field-row">
        <label className="field">
          <span>First name</span>
          <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </label>
        <label className="field">
          <span>Last name</span>
          <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </label>
      </div>
      <p className="muted">
        If this email already has a Habitat account, they're added to your organization right
        away. Otherwise they'll get an email with a link to set their own password and join —
        no more sharing a password yourself.
      </p>
      <label className="field">
        <span>Role</span>
        <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
          {ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>
      {properties.length > 0 && (
        <div className="field">
          <span>Property scope (optional — leave unchecked for account-wide)</span>
          {propertyOptions(properties).map((p) => (
            <label key={p.id} className="field field--checkbox">
              <input
                type="checkbox"
                checked={propertyIds.includes(p.id)}
                onChange={(e) => togglePropertyId(p.id, e.target.checked)}
              />
              <span>{p.name}</span>
            </label>
          ))}
        </div>
      )}
      <button type="submit" className="btn btn-primary" disabled={submitting || !email}>
        {submitting ? "Adding…" : "+ Add member"}
      </button>
    </form>
  );
}

/**
 * The org admin portal — "each org should have its own admin portal
 * link" from /CLAUDE.md's task log. Deliberately a route inside the app
 * (/admin), not Django's own /admin site: it's automatically scoped to
 * the logged-in user's org the same way every other page here is (see
 * org_scoping.py), where Django admin would need per-org queryset
 * filtering bolted on to do the same thing safely, and this is also
 * where org rename + member/role management naturally live together.
 * Admin-only — a non-admin who navigates here directly sees a plain
 * "admins only" message rather than a redirect, same as the pattern
 * elsewhere in the app for controls a role can't use.
 */
export default function OrgAdminPage() {
  const { session } = useAuth();
  const isAdmin = roleAtLeast(session?.membership?.role, "admin");

  const org = useAsync(() => api.org.get(), []);
  const members = useAsync(() => (isAdmin ? api.org.members.list() : Promise.resolve([])), [
    isAdmin,
  ]);
  const invitations = useAsync(
    () => (isAdmin ? api.org.invitations.list() : Promise.resolve([])),
    [isAdmin],
  );
  const properties = useAsync(() => api.properties.list(), []);
  const deletedProperties = useAsync(
    () => (isAdmin ? api.properties.deleted.list() : Promise.resolve([])),
    [isAdmin],
  );
  const feedback = useAsync(() => (isAdmin ? api.feedback.list() : Promise.resolve([])), [
    isAdmin,
  ]);
  const pages = useAsync(() => api.pages.list(), []);

  const reloadMembers = () => {
    members.reload();
    invitations.reload();
  };

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

  if (!isAdmin) {
    return (
      <div className="page">
        <div className="page__header">
          <h1>Admin</h1>
        </div>
        <p className="form-error">This page is for organization admins only.</p>
      </div>
    );
  }

  const propertyList = properties.data?.features ?? [];

  return (
    <div className="page">
      <div className="page__header">
        <h1>Organization admin</h1>
        {org.data && (
          <Link to={`/public/${org.data.slug}`} className="btn btn-secondary btn-small" target="_blank" rel="noopener noreferrer">
            View public site ↗
          </Link>
        )}
      </div>

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
            publicUrl={`${window.location.origin}/public/${org.data.slug}`}
          />
        </div>
      )}

      <div className="page__header">
        <h2>Theme</h2>
      </div>
      {org.data && (
        <ThemeEditorPanel
          theme={org.data}
          onSave={async (data) => {
            await api.org.update(data);
            org.reload();
          }}
          previewImageUrl={api.org.themeImage.previewUrl}
          onUploadImage={async (file) => {
            await api.org.themeImage.upload(file);
            org.reload();
          }}
          onRemoveImage={async () => {
            await api.org.themeImage.remove();
            org.reload();
          }}
        />
      )}

      <div className="page__header">
        <h2>Pages</h2>
        {/* An org-level page isn't scoped to any property, so a
            property-scoped admin can't author one (see backend
            PageViewSet.perform_create) — hide rather than show a control
            that always 403s. An unusual case in practice (most admins
            are account-wide), but consistent with the same gate on
            PropertiesPage's "+ New property". */}
        {!isPropertyScoped(session?.membership) && (
          <Link to="/admin/pages/new" className="btn btn-secondary btn-small">
            + Add page
          </Link>
        )}
      </div>
      <p className="muted">
        Authored pages for your public site — the auto-generated property list ("Explore") is
        always there too; pick which one visitors land on below.
      </p>
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

      <div className="page__header">
        <h2>Members</h2>
      </div>
      {members.loading && <p className="muted">Loading…</p>}
      {members.error && <p className="form-error">Couldn't load members: {members.error}</p>}
      <ul className="card-list">
        {members.data?.map((m) => (
          <MemberRow
            key={m.id}
            membership={m}
            properties={propertyList}
            isSelf={m.user.id === session?.user.id}
            onChanged={members.reload}
          />
        ))}
      </ul>

      {(invitations.loading || (invitations.data?.length ?? 0) > 0) && (
        <>
          <div className="page__header">
            <h2>Pending invitations</h2>
          </div>
          {invitations.loading && <p className="muted">Loading…</p>}
          {invitations.error && (
            <p className="form-error">Couldn't load invitations: {invitations.error}</p>
          )}
          <ul className="card-list">
            {invitations.data?.map((inv) => (
              <PendingInvitationRow
                key={inv.id}
                invitation={inv}
                onRevoked={invitations.reload}
                onResent={invitations.reload}
              />
            ))}
          </ul>
        </>
      )}

      {(deletedProperties.loading || (deletedProperties.data?.length ?? 0) > 0) && (
        <>
          <div className="page__header">
            <h2>Recently deleted</h2>
          </div>
          <p className="muted">
            Deleted properties (and their activities/sightings) are hidden right away but kept
            for 30 days in case that was a mistake — restore one here, or wait and it's removed
            for good.
          </p>
          {deletedProperties.loading && <p className="muted">Loading…</p>}
          {deletedProperties.error && (
            <p className="form-error">
              Couldn't load recently-deleted properties: {deletedProperties.error}
            </p>
          )}
          <ul className="card-list">
            {deletedProperties.data?.map((p) => (
              <DeletedPropertyRow
                key={p.id}
                property={p}
                onRestored={() => {
                  deletedProperties.reload();
                  properties.reload();
                }}
              />
            ))}
          </ul>
        </>
      )}

      {(feedback.loading || (feedback.data?.length ?? 0) > 0) && (
        <>
          <div className="page__header">
            <h2>Feedback</h2>
          </div>
          <p className="muted">
            Feedback your org's members have sent about Habitat itself — reviewed and folded into
            the development workflow separately; mark an item resolved once it's actually been
            addressed.
          </p>
          {feedback.loading && <p className="muted">Loading…</p>}
          {feedback.error && <p className="form-error">Couldn't load feedback: {feedback.error}</p>}
          <ul className="card-list">
            {feedback.data?.map((item) => (
              <FeedbackRow key={item.id} item={item} onResolved={feedback.reload} />
            ))}
          </ul>
        </>
      )}

      <div className="page__header">
        <h2>Add a member</h2>
      </div>
      <AddMemberForm properties={propertyList} onAdded={reloadMembers} />
    </div>
  );
}
