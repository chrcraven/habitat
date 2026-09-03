import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";
import { ActivityTypeRow } from "./rows";
import { moveRow } from "./reorder";

/** The org's own activity types — the kinds of work it logs. Org-level
 * reference data, so account-wide admins only (see sections.ts). */
export default function ActivityTypesSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const activityTypes = useAsync(() => (allowed ? api.activityTypes.list() : Promise.resolve([])), [allowed]);
  const [newActivityType, setNewActivityType] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setError(null);
    try {
      await api.activityTypes.create({
        name: newActivityType.trim(),
        order: activityTypes.data?.length ?? 0,
      });
      setNewActivityType("");
      activityTypes.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add that type.");
    } finally {
      setAdding(false);
    }
  };

  const handleMove = async (index: number, direction: -1 | 1) => {
    if (!activityTypes.data) return;
    setError(null);
    try {
      await moveRow(activityTypes.data, index, direction, api.activityTypes.update);
      activityTypes.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reorder those types.");
      activityTypes.reload();
    }
  };

  const list = activityTypes.data ?? [];

  return (
    <ManageSectionPage
      title="Activity types"
      access="account-admin"
      intro={
        <p className="muted">
          The kinds of work you log — yours to name. Every activity picks one of these, and
          renaming one re-labels every activity that uses it. A type still in use can't be deleted
          until those activities are changed to another type. The order here is the order they
          appear in every type picker — the arrows move one up or down.
        </p>
      }
    >
      {activityTypes.loading && <p className="muted">Loading…</p>}
      {activityTypes.error && (
        <p className="form-error">Couldn't load activity types: {activityTypes.error}</p>
      )}
      {error && <p className="form-error">{error}</p>}
      <ul className="card-list">
        {list.map((t, i) => (
          <ActivityTypeRow
            key={t.id}
            type={t}
            onChanged={activityTypes.reload}
            onMove={(direction) => handleMove(i, direction)}
            isFirst={i === 0}
            isLast={i === list.length - 1}
          />
        ))}
      </ul>
      <form onSubmit={handleAdd} className="form">
        <label className="field">
          <span>Add an activity type</span>
          <input
            type="text"
            required
            value={newActivityType}
            onChange={(e) => setNewActivityType(e.target.value)}
            placeholder="e.g. Prescribed burn"
          />
        </label>
        <button
          type="submit"
          className="btn btn-secondary btn-small"
          disabled={adding || !newActivityType.trim()}
        >
          {adding ? "Adding…" : "Add type"}
        </button>
      </form>
    </ManageSectionPage>
  );
}
