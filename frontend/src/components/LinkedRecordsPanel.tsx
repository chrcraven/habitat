import { useState } from "react";
import Combobox from "./Combobox";

interface LinkOption {
  id: number;
  label: string;
}

interface LinkedRecordsPanelProps {
  /** "Linked activities" (shown on a sighting's edit form) or "Linked
   * sightings" (shown on an activity's edit form) — see
   * /docs/data-model-notes.md, "Do sightings and activities share a data
   * model?" for why this is a direct link rather than gated behind a
   * Task. */
  title: string;
  links: { id: number; label: string }[];
  /** Candidates to link — already filtered by the caller to exclude
   * anything already linked. */
  options: LinkOption[];
  onLink: (id: number) => Promise<void>;
  onUnlink: (linkId: number) => Promise<void>;
  canEdit: boolean;
  emptyOptionsLabel: string;
}

/** Shared by SightingFormPage and ActivityFormPage's edit-mode-only
 * "linked activities"/"linked sightings" section — same interaction
 * shape either way: a list with an unlink button per row, plus a
 * dropdown + "+ Link" button to add one. Only rendered once a record
 * exists (same gating as PhotoUploader — nothing to link on the *create*
 * forms since the id doesn't exist yet). */
export default function LinkedRecordsPanel({
  title,
  links,
  options,
  onLink,
  onUnlink,
  canEdit,
  emptyOptionsLabel,
}: LinkedRecordsPanelProps) {
  const [selected, setSelected] = useState<number | "">("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unlinkingId, setUnlinkingId] = useState<number | null>(null);

  const handleLink = async () => {
    if (selected === "") return;
    setBusy(true);
    setError(null);
    try {
      await onLink(selected);
      setSelected("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't create that link.");
    } finally {
      setBusy(false);
    }
  };

  const handleUnlink = async (linkId: number) => {
    setUnlinkingId(linkId);
    setError(null);
    try {
      await onUnlink(linkId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't remove that link.");
    } finally {
      setUnlinkingId(null);
    }
  };

  return (
    <div className="field">
      <span>{title}</span>
      {error && <p className="form-error">{error}</p>}
      {links.length === 0 && <p className="muted">Not linked to anything yet.</p>}
      {links.length > 0 && (
        <ul className="card-list">
          {links.map((link) => (
            <li key={link.id} className="card card--row">
              <span>{link.label}</span>
              {canEdit && (
                <button
                  type="button"
                  className="btn btn-secondary btn-small"
                  onClick={() => handleUnlink(link.id)}
                  disabled={unlinkingId === link.id}
                >
                  Unlink
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {canEdit &&
        (options.length === 0 ? (
          <p className="muted">{emptyOptionsLabel}</p>
        ) : (
          // A <div>, not a nested <form> — this whole panel is already
          // rendered inside the page's own <form> (see
          // SightingFormPage/ActivityFormPage), and nested forms are
          // invalid HTML that browsers silently reparent, which broke
          // this control in practice (caught via a React DOM-nesting
          // warning during Playwright verification, not just theory).
          // Combobox (type-to-filter), not a plain <select> — a flat
          // dropdown of every unlinked record on the property stops being
          // usable once there are more than a handful (see
          // components/Combobox.tsx).
          <div className="field-row">
            <Combobox
              options={options}
              value={selected}
              onChange={setSelected}
              placeholder="Search to link…"
              aria-label={title}
            />
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={handleLink}
              disabled={busy || selected === ""}
            >
              + Link
            </button>
          </div>
        ))}
    </div>
  );
}
