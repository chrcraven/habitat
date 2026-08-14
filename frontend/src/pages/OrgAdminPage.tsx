import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import type { MembershipDetail, Property, Role } from "../api/types";

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

function AddMemberForm({ properties, onAdded }: { properties: Property[]; onAdded: () => void }) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [propertyIds, setPropertyIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const togglePropertyId = (id: number, checked: boolean) => {
    setPropertyIds((ids) => (checked ? [...ids, id] : ids.filter((x) => x !== id)));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.org.members.create({
        email,
        password: password || undefined,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        role,
        properties: propertyIds,
      });
      setEmail("");
      setFirstName("");
      setLastName("");
      setPassword("");
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
      <label className="field">
        <span>Initial password</span>
        <input
          type="text"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Share this with them directly — only needed for a brand-new email"
        />
      </label>
      <p className="muted">
        If this email already has a Habitat account, they're just added to your
        organization and the password above is ignored — otherwise it creates their
        account, so share it with them yourself (there's no invite email yet).
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
  const properties = useAsync(() => api.properties.list(), []);

  const [orgName, setOrgName] = useState("");
  const [renaming, setRenaming] = useState(false);
  const [renameError, setRenameError] = useState<string | null>(null);

  useEffect(() => {
    if (org.data) setOrgName(org.data.name);
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
          <Link to={`/public/org/${org.data.id}`} className="btn btn-secondary btn-small" target="_blank" rel="noopener noreferrer">
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

      <div className="page__header">
        <h2>Add a member</h2>
      </div>
      <AddMemberForm properties={propertyList} onAdded={members.reload} />
    </div>
  );
}
