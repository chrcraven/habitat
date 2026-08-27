import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import Combobox from "../components/Combobox";
import type { Activity, MembershipDetail, Sighting, Task, TaskStatus } from "../api/types";

/** Shared member-list → Combobox-option mapping — an org's roster is
 * exactly the kind of list that stops scaling as a plain <select> once
 * membership grows past a handful (see components/Combobox.tsx). */
const memberOptions = (members: MembershipDetail[]) =>
  members.map((m) => ({ id: m.user.id, label: m.user.email }));

const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: "open", label: "Open" },
  { value: "assigned", label: "Assigned" },
  { value: "resolved", label: "Resolved" },
  { value: "dismissed", label: "Dismissed" },
];

function originLabel(task: Task): string | null {
  if (task.origin_sighting) return `From sighting: ${task.origin_sighting_species}`;
  if (task.origin_activity) return `From activity: ${task.origin_activity_type}`;
  return null;
}

function TaskRow({
  task,
  members,
  canEdit,
  canDelete,
  onChanged,
}: {
  task: Task;
  members: MembershipDetail[];
  canEdit: boolean;
  canDelete: boolean;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleFieldChange = async (data: Partial<{ status: TaskStatus; assigned_to: number | null }>) => {
    setBusy(true);
    setError(null);
    try {
      await api.tasks.update(task.id, data);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update task.");
    } finally {
      setBusy(false);
    }
  };

  const handleSaveEdit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.tasks.update(task.id, { title, description });
      setEditing(false);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't update task.");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete task "${task.title}"?`)) return;
    setBusy(true);
    try {
      await api.tasks.remove(task.id);
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't delete task.");
      setBusy(false);
    }
  };

  return (
    <li className="card">
      {error && <p className="form-error">{error}</p>}
      {editing ? (
        <form onSubmit={handleSaveEdit} className="form">
          <label className="field">
            <span>Title</span>
            <input type="text" required value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
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
      ) : (
        <>
          <div className="card__row">
            <div>
              <strong>{task.title}</strong>
              <span className="badge">{STATUSES.find((s) => s.value === task.status)?.label}</span>
            </div>
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
                <button
                  type="button"
                  className="btn btn-danger btn-small"
                  onClick={handleDelete}
                  disabled={busy}
                >
                  Delete
                </button>
              )}
            </div>
          </div>
          {task.description && <p>{task.description}</p>}
          {originLabel(task) && <span className="muted">{originLabel(task)}</span>}

          {canEdit ? (
            <div className="field-row">
              <label className="field">
                <span>Assigned to</span>
                <Combobox
                  options={memberOptions(members)}
                  value={task.assigned_to ?? ""}
                  disabled={busy}
                  placeholder="Unassigned"
                  onChange={(id) => handleFieldChange({ assigned_to: id === "" ? null : id })}
                />
              </label>
              <label className="field">
                <span>Status</span>
                <select
                  value={task.status}
                  disabled={busy}
                  onChange={(e) => handleFieldChange({ status: e.target.value as TaskStatus })}
                >
                  {STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : (
            <span className="muted">
              {task.assigned_to_email ? `Assigned to ${task.assigned_to_email}` : "Unassigned"}
            </span>
          )}
        </>
      )}
    </li>
  );
}

function AddTaskForm({
  members,
  activities,
  sightings,
  onAdded,
}: {
  members: MembershipDetail[];
  activities: Activity[];
  sightings: Sighting[];
  onAdded: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignedTo, setAssignedTo] = useState<number | "">("");
  const [originSighting, setOriginSighting] = useState<number | "">("");
  const [originActivity, setOriginActivity] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.tasks.create({
        title,
        description: description || undefined,
        assigned_to: assignedTo === "" ? null : assignedTo,
        origin_sighting: originSighting === "" ? null : originSighting,
        origin_activity: originActivity === "" ? null : originActivity,
        status: assignedTo === "" ? "open" : "assigned",
      });
      setTitle("");
      setDescription("");
      setAssignedTo("");
      setOriginSighting("");
      setOriginActivity("");
      onAdded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create task.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form form--panel">
      {error && <p className="form-error">{error}</p>}
      <label className="field">
        <span>Title</span>
        <input
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Check out the bindweed report"
        />
      </label>
      <label className="field">
        <span>Description</span>
        <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      <label className="field">
        <span>Assign to</span>
        <Combobox
          options={memberOptions(members)}
          value={assignedTo}
          onChange={setAssignedTo}
          placeholder="Unassigned"
        />
      </label>
      <div className="field-row">
        <label className="field">
          <span>From a sighting (optional)</span>
          <Combobox
            options={sightings.map((s) => ({
              id: s.id,
              label: s.properties.species_detail.common_name,
              sublabel: new Date(s.properties.observed_at).toLocaleDateString(),
            }))}
            value={originSighting}
            onChange={setOriginSighting}
            placeholder="None"
          />
        </label>
        <label className="field">
          <span>From an activity (optional)</span>
          <Combobox
            options={activities.map((a) => ({
              id: a.id,
              label: a.properties.activity_type,
              sublabel: a.properties.status_name,
            }))}
            value={originActivity}
            onChange={setOriginActivity}
            placeholder="None"
          />
        </label>
      </div>
      <button type="submit" className="btn btn-primary" disabled={submitting || !title}>
        {submitting ? "Adding…" : "+ Add task"}
      </button>
    </form>
  );
}

/**
 * Simple, optional, user-to-user task assignment (see
 * /docs/data-model-notes.md, "Task record") — the other explicitly-named
 * Phase 1 mechanism (alongside the sighting↔activity link, see
 * SightingFormPage/ActivityFormPage) that had a data model but no API or
 * UI until this session. Org-wide, not property-scoped — a task can
 * originate from a sighting/activity on any property, or from nothing at
 * all (a general to-do). Any member can view; editor+ can create/update
 * (including reassigning and changing status); admin can delete — same
 * role convention as everything else (see org_scoping.py).
 */
export default function TasksPage() {
  const { session } = useAuth();
  const role = session?.membership?.role;
  const canEdit = roleAtLeast(role, "editor");
  const canDelete = roleAtLeast(role, "admin");

  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("");

  const tasks = useAsync(
    () => api.tasks.list(statusFilter ? { status: statusFilter } : {}),
    [statusFilter],
  );
  const members = useAsync(() => api.org.members.list(), []);
  const activities = useAsync(() => api.activities.list(), []);
  const sightings = useAsync(() => api.sightings.list(), []);

  return (
    <div className="page">
      <div className="page__header">
        <h1>Tasks</h1>
      </div>
      <p className="muted">
        Simple user-to-user assignment — optionally tied to a sighting or activity, but not
        required for anything else in the app.
      </p>

      <label className="field">
        <span>Filter by status</span>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as TaskStatus | "")}>
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>

      {tasks.loading && <p className="muted">Loading…</p>}
      {tasks.error && <p className="form-error">Couldn't load tasks: {tasks.error}</p>}
      {!tasks.loading && (tasks.data?.length ?? 0) === 0 && <p className="muted">No tasks yet.</p>}

      <ul className="card-list">
        {tasks.data?.map((task) => (
          <TaskRow
            key={task.id}
            task={task}
            members={members.data ?? []}
            canEdit={canEdit}
            canDelete={canDelete}
            onChanged={tasks.reload}
          />
        ))}
      </ul>

      {canEdit && (
        <>
          <div className="page__header">
            <h2>Add a task</h2>
          </div>
          <AddTaskForm
            members={members.data ?? []}
            activities={activities.data?.features ?? []}
            sightings={sightings.data?.features ?? []}
            onAdded={tasks.reload}
          />
        </>
      )}
    </div>
  );
}
