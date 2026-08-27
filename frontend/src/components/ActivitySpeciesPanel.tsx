import { useState } from "react";
import Combobox from "./Combobox";
import type { ActivitySpeciesLink, ActivitySpeciesRole, Species } from "../api/types";

const ROLES: { value: ActivitySpeciesRole | ""; label: string }[] = [
  { value: "", label: "Unspecified" },
  { value: "planted", label: "Planted" },
  { value: "treated_target", label: "Treated / targeted" },
  { value: "other", label: "Other" },
];

interface ActivitySpeciesPanelProps {
  links: ActivitySpeciesLink[];
  /** Species not already linked to this activity — the caller filters,
   * same convention as LinkedRecordsPanel's `options`. */
  options: Species[];
  canEdit: boolean;
  onAdd: (data: {
    species: number;
    role: ActivitySpeciesRole | "";
    quantity: number | null;
    detail: string;
  }) => Promise<void>;
  onUpdate: (
    linkId: number,
    data: Partial<{ role: ActivitySpeciesRole | ""; quantity: number | null; detail: string }>,
  ) => Promise<void>;
  onRemove: (linkId: number) => Promise<void>;
}

/** Shown on ActivityFormPage, edit-mode only (same gating as
 * PhotoUploader/LinkedRecordsPanel — nothing to attach species to before
 * the activity has an id). This is the Activity↔Species through model
 * (role/quantity/detail per species — e.g. a planting of three species,
 * or a treatment targeting one invasive), not the plain per-record
 * `species_names` summary — see api/types.ts's ActivitySpeciesLink
 * docstring for why this needed its own endpoints rather than a writable
 * field on Activity itself. */
export default function ActivitySpeciesPanel({
  links,
  options,
  canEdit,
  onAdd,
  onUpdate,
  onRemove,
}: ActivitySpeciesPanelProps) {
  const [selected, setSelected] = useState<number | "">("");
  const [role, setRole] = useState<ActivitySpeciesRole | "">("");
  const [quantity, setQuantity] = useState("");
  const [detail, setDetail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const handleAdd = async () => {
    if (selected === "") return;
    setBusy(true);
    setError(null);
    try {
      await onAdd({
        species: selected,
        role,
        quantity: quantity === "" ? null : Number(quantity),
        detail,
      });
      setSelected("");
      setRole("");
      setQuantity("");
      setDetail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't add that species.");
    } finally {
      setBusy(false);
    }
  };

  const handleRemove = async (linkId: number) => {
    setRemovingId(linkId);
    setError(null);
    try {
      await onRemove(linkId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't remove that species.");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="field">
      <span>Species</span>
      {error && <p className="form-error">{error}</p>}
      {links.length === 0 && <p className="muted">No species recorded for this activity yet.</p>}
      {links.length > 0 && (
        <ul className="card-list">
          {links.map((link) => (
            <li key={link.id} className="card">
              <div className="card__row">
                <strong>{link.species_name}</strong>
                {canEdit && (
                  <button
                    type="button"
                    className="btn btn-secondary btn-small"
                    onClick={() => handleRemove(link.id)}
                    disabled={removingId === link.id}
                  >
                    Remove
                  </button>
                )}
              </div>
              {canEdit ? (
                <div className="field-row">
                  <label className="field">
                    <span>Role</span>
                    <select
                      value={link.role}
                      onChange={(e) =>
                        onUpdate(link.id, { role: e.target.value as ActivitySpeciesRole | "" })
                      }
                    >
                      {ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Quantity</span>
                    <input
                      type="number"
                      min={0}
                      value={link.quantity ?? ""}
                      onChange={(e) =>
                        onUpdate(link.id, {
                          quantity: e.target.value === "" ? null : Number(e.target.value),
                        })
                      }
                    />
                  </label>
                </div>
              ) : (
                <span className="muted">
                  {ROLES.find((r) => r.value === link.role)?.label}
                  {link.quantity != null ? ` — qty ${link.quantity}` : ""}
                </span>
              )}
              {canEdit ? (
                <input
                  type="text"
                  placeholder="Detail (e.g. method or product used)"
                  value={link.detail}
                  onChange={(e) => onUpdate(link.id, { detail: e.target.value })}
                />
              ) : (
                link.detail && <span className="muted">{link.detail}</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {canEdit &&
        (options.length === 0 ? (
          <p className="muted">No other species in this account's list to add.</p>
        ) : (
          // A <div>, not a nested <form> — see LinkedRecordsPanel's
          // matching comment for why (this panel lives inside
          // ActivityFormPage's own outer <form>). Species picker is a
          // Combobox, not a plain <select> — an account's species list is
          // exactly the kind of list this was meant to help with (see
          // components/Combobox.tsx).
          <div className="card card--row activity-species-add">
            <Combobox
              options={options.map((s) => ({ id: s.id, label: s.common_name }))}
              value={selected}
              onChange={setSelected}
              placeholder="Search species…"
              aria-label="Species"
            />
            <select value={role} onChange={(e) => setRole(e.target.value as ActivitySpeciesRole | "")}>
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              placeholder="Qty"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
            <input
              type="text"
              placeholder="Detail (optional)"
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
            />
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={handleAdd}
              disabled={busy || selected === ""}
            >
              + Add
            </button>
          </div>
        ))}
    </div>
  );
}
