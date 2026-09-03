import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";
import { WorkflowStateRow } from "./rows";
import { moveRow } from "./reorder";

/** The org's own activity workflow — the states an activity moves
 * through. Org-level reference data, so account-wide admins only, the
 * same gate the activity types beside it use (see sections.ts).
 *
 * The endpoint behind this was read-only until 2026-09-03; every org has
 * been living with the seeded Planned → In Progress → Done set since
 * Phase 1 because there was nowhere to change it. */
export default function WorkflowStatesSection() {
  // Don't fire a request this role will only be 403'd for — the wrapper
  // renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const states = useAsync(
    () => (allowed ? api.workflowStates.list() : Promise.resolve([])),
    [allowed],
  );
  const [newState, setNewState] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setError(null);
    try {
      await api.workflowStates.create({
        name: newState.trim(),
        order: states.data?.length ?? 0,
      });
      setNewState("");
      states.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add that state.");
    } finally {
      setAdding(false);
    }
  };

  const handleMove = async (index: number, direction: -1 | 1) => {
    if (!states.data) return;
    setError(null);
    try {
      await moveRow(states.data, index, direction, api.workflowStates.update);
      states.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reorder those states.");
      states.reload();
    }
  };

  const list = states.data ?? [];

  return (
    <ManageSectionPage
      title="Workflow states"
      access="account-admin"
      intro={
        <p className="muted">
          The states an activity moves through, in the order you work them. Yours to name — rename
          one and every activity in it is re-labelled. A state still in use can't be deleted until
          those activities are moved to another state.
        </p>
      }
    >
      {states.loading && <p className="muted">Loading…</p>}
      {states.error && (
        <p className="form-error">Couldn't load workflow states: {states.error}</p>
      )}
      {error && <p className="form-error">{error}</p>}
      <ul className="card-list">
        {list.map((state, i) => (
          <WorkflowStateRow
            key={state.id}
            state={state}
            onChanged={states.reload}
            onMove={(direction) => handleMove(i, direction)}
            isFirst={i === 0}
            isLast={i === list.length - 1}
          />
        ))}
      </ul>
      <p className="muted">
        <strong>Counts as finished work</strong> is what the public map, your dashboard and the
        Activities filter read to tell completed work from planned work, so your workflow always
        needs at least one state marked that way. <strong>Starting state</strong> is just the state
        a new activity is created in.
      </p>
      <form onSubmit={handleAdd} className="form">
        <label className="field">
          <span>Add a workflow state</span>
          <input
            type="text"
            required
            value={newState}
            onChange={(e) => setNewState(e.target.value)}
            placeholder="e.g. Awaiting permit"
          />
        </label>
        <button
          type="submit"
          className="btn btn-secondary btn-small"
          disabled={adding || !newState.trim()}
        >
          {adding ? "Adding…" : "Add state"}
        </button>
      </form>
    </ManageSectionPage>
  );
}
