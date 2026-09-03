import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import type {
  ActivityType as ActivityTypeRecord,
  DeletedProperty,
  Feedback,
  Invitation,
  MembershipDetail,
  Page,
  Property,
  Role,
} from "../../api/types";

/**
 * The row/form components the Manage sections are built from — extracted
 * verbatim from the old single-route OrgAdminPage when it was split into
 * sub-routes (2026-09-03, owner feedback: "This is a lot of information
 * stuck onto a single page"). Behavior is unchanged; only where they're
 * rendered moved. Each is exported because the sections now live in
 * separate files under this directory.
 */
export const ROLES: { value: Role; label: string }[] = [
  { value: "viewer", label: "Viewer — read only" },
  { value: "editor", label: "Editor — read/create/update" },
  { value: "admin", label: "Admin — also delete + manage members" },
];

export function propertyOptions(properties: Property[]) {
  return properties.map((p) => ({ id: p.id, name: p.properties.name }));
}

export function MemberRow({
  membership,
  properties,
  isSelf,
  scopedAdmin,
  onChanged,
}: {
  membership: MembershipDetail;
  properties: Property[];
  isSelf: boolean;
  /** See AddMemberForm's own prop — a property-scoped admin can move a
   * member around within its own properties but can't unscope them. */
  scopedAdmin: boolean;
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
            {scopedAdmin
              ? "Property scope — the properties your admin role covers; a member has to keep at least one"
              : "Property scope — leave all unchecked for account-wide access, or limit this role to just the properties checked below"}
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

export function PendingInvitationRow({
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

export function daysRemaining(purgeAt: string): number {
  const ms = new Date(purgeAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)));
}

/** One row in "Recently deleted" (see PropertyViewSet.deleted/restore) —
 * a soft-deleted property still inside its 30-day purge window. Same
 * card/row conventions as MemberRow/PendingInvitationRow above. */
export function DeletedPropertyRow({
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

/** One of the org's own activity types (org-defined since 2026-09-02 —
 * see backend/apps/activities/models.py#ActivityType). Renaming saves on
 * blur rather than needing a Save button, matching the inline-edit
 * convention MemberRow and TaskRow already use; the name is what every
 * activity displays, so a rename here re-labels them all at once. */
export function ActivityTypeRow({
  type,
  onChanged,
}: {
  type: ActivityTypeRecord;
  onChanged: () => void;
}) {
  const [name, setName] = useState(type.name);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleRename = async () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === type.name) {
      setName(type.name);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.activityTypes.update(type.id, { name: trimmed });
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't rename that type.");
      setName(type.name);
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete the "${type.name}" activity type?`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.activityTypes.remove(type.id);
      onChanged();
    } catch (err) {
      // The API answers with a plain explanation when activities still
      // use this type (the FK is PROTECT) — show it rather than a
      // generic failure, since it tells the admin exactly what to do.
      setError(err instanceof ApiError ? err.message : "Couldn't delete that type.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      <div className="card__row">
        <div>
          <input
            type="text"
            value={name}
            disabled={busy}
            onChange={(e) => setName(e.target.value)}
            onBlur={handleRename}
            aria-label={`Name for the ${type.name} activity type`}
          />
        </div>
        <div className="card__actions">
          <button
            type="button"
            className="btn btn-ghost btn-small"
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

/** One row in the admin-only feedback review list — see
 * backend/apps/feedback and /docs/open-questions.md ("App feedback /
 * build workflow"). This is this org's own submitted feedback so an
 * admin can review it without querying the database; the external
 * scheduled routine that actually folds feedback into the build workflow
 * pulls across every org via a separate bearer-token endpoint, not this
 * one. */
export function FeedbackRow({ item, onResolved }: { item: Feedback; onResolved: () => void }) {
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
            {/* The screen it was sent from — older items predate the
                capture and simply don't have one. */}
            {item.page_path && ` — sent from ${item.page_path}`}
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
export function PageRow({ page, onDeleted }: { page: Page; onDeleted: () => void }) {
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
          <Link to={`/manage/pages/${page.id}/edit`} className="btn btn-secondary btn-small">
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

export function AddMemberForm({
  properties,
  requireProperty,
  onAdded,
}: {
  properties: Property[];
  /** True when the admin filling this in is itself property-scoped: it can
   * only add a member inside its own scope, so "account-wide" isn't an
   * option and at least one property has to be picked (the backend rejects
   * an empty scope from a scoped admin — see MembershipViewSet.create). */
  requireProperty: boolean;
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
    if (requireProperty && propertyIds.length === 0) {
      setError("Pick at least one property for this member.");
      return;
    }
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
          <span>
            {requireProperty
              ? "Property scope — pick at least one of your properties"
              : "Property scope (optional — leave unchecked for account-wide)"}
          </span>
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
