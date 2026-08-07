import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";

export default function SpeciesPage() {
  const { data, loading, error, reload } = useAsync(() => api.species.list(), []);
  const [commonName, setCommonName] = useState("");
  const [scientificName, setScientificName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="form-error">Couldn't load species: {error}</p>}

      <ul className="card-list">
        {data?.map((s) => (
          <li key={s.id} className="card">
            <strong>{s.common_name}</strong>
            {s.scientific_name && <span className="muted">{s.scientific_name}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
