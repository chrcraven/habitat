import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import type { Species } from "../api/types";

function SpeciesRow({
  species,
  canEdit,
  canDelete,
  onChanged,
}: {
  species: Species;
  canEdit: boolean;
  canDelete: boolean;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [commonName, setCommonName] = useState(species.common_name);
  const [scientificName, setScientificName] = useState(species.scientific_name);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.species.update(species.id, {
        common_name: commonName,
        scientific_name: scientificName,
      });
      setEditing(false);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${species.common_name}"?`)) return;
    setBusy(true);
    try {
      await api.species.remove(species.id);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setBusy(false);
    }
  };

  if (editing) {
    return (
      <li className="card">
        <form onSubmit={handleSave} className="form">
          {error && <p className="form-error">{error}</p>}
          <div className="field-row">
            <label className="field">
              <span>Common name</span>
              <input
                type="text"
                required
                value={commonName}
                onChange={(e) => setCommonName(e.target.value)}
              />
            </label>
            <label className="field">
              <span>Scientific name</span>
              <input
                type="text"
                value={scientificName}
                onChange={(e) => setScientificName(e.target.value)}
              />
            </label>
          </div>
          <div className="card__actions">
            <button type="submit" className="btn btn-primary btn-small" disabled={busy}>
              Save
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-small"
              onClick={() => setEditing(false)}
              disabled={busy}
            >
              Cancel
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className="card card--row">
      <div>
        <strong>{species.common_name}</strong>
        {species.scientific_name && <span className="muted"> — {species.scientific_name}</span>}
      </div>
      {(canEdit || canDelete) && (
        <div className="card__actions">
          {canEdit && (
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={() => setEditing(true)}
            >
              Edit
            </button>
          )}
          {canDelete && (
            <button type="button" className="btn btn-danger btn-small" onClick={handleDelete} disabled={busy}>
              Delete
            </button>
          )}
        </div>
      )}
    </li>
  );
}

export default function SpeciesPage() {
  const { data, loading, error, reload } = useAsync(() => api.species.list(), []);
  const { session } = useAuth();
  const role = session?.membership?.role;
  const canEdit = roleAtLeast(role, "editor");
  const canDelete = roleAtLeast(role, "admin");

  const [commonName, setCommonName] = useState("");
  const [scientificName, setScientificName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Client-side filter, same "fine at current scale, revisit if it stops
  // being true" reasoning as Combobox.tsx's own filtering (2026-08-27) —
  // this list isn't a picker so it gets a plain search box instead of
  // that component, but the same substring-match approach.
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return data ?? [];
    return (data ?? []).filter(
      (s) =>
        s.common_name.toLowerCase().includes(query) ||
        s.scientific_name?.toLowerCase().includes(query),
    );
  }, [data, filter]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await api.species.create({
        common_name: commonName,
        scientific_name: scientificName || undefined,
      });
      setCommonName("");
      setScientificName("");
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="page__header">
        <h1>Species</h1>
      </div>
      <p className="muted">
        Your own account's species list — activities and sightings are logged
        against these, not an external taxonomy.
      </p>

      {canEdit && (
        <form onSubmit={handleSubmit} className="form">
          {formError && <p className="form-error">{formError}</p>}
          <div className="field-row">
            <label className="field">
              <span>Common name</span>
              <input
                type="text"
                required
                value={commonName}
                onChange={(e) => setCommonName(e.target.value)}
              />
            </label>
            <label className="field">
              <span>Scientific name (optional)</span>
              <input
                type="text"
                value={scientificName}
                onChange={(e) => setScientificName(e.target.value)}
              />
            </label>
          </div>
          <button type="submit" className="btn btn-primary btn-small" disabled={submitting}>
            {submitting ? "Adding…" : "+ Add species"}
          </button>
        </form>
      )}

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="form-error">Couldn't load species: {error}</p>}

      {!loading && !error && (data?.length ?? 0) > 0 && (
        <label className="field">
          <span>Search</span>
          <input
            type="search"
            placeholder="Filter by common or scientific name…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </label>
      )}

      {!loading && filter.trim() && (
        <p className="muted">
          Showing {filtered.length} of {data?.length ?? 0}.
        </p>
      )}

      <ul className="card-list">
        {filtered.map((s) => (
          <SpeciesRow key={s.id} species={s} canEdit={canEdit} canDelete={canDelete} onChanged={reload} />
        ))}
      </ul>

      {!loading && !error && (data?.length ?? 0) > 0 && filtered.length === 0 && (
        <p className="muted">No species match "{filter}".</p>
      )}
    </div>
  );
}
