import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

export interface ComboboxOption {
  id: number;
  label: string;
  /** Shown as a smaller second line under the label, only while picking
   * (not once selected) — e.g. a date next to a sighting's species name. */
  sublabel?: string;
}

interface ComboboxProps {
  options: ComboboxOption[];
  /** "" means nothing selected — same convention every dropdown in this
   * app already uses for an optional/unset value. */
  value: number | "";
  onChange: (id: number | "") => void;
  placeholder?: string;
  noOptionsLabel?: string;
  disabled?: boolean;
  id?: string;
  "aria-label"?: string;
}

// Bound how much of a long list actually renders at once. This is the
// direct fix for "dropdowns will not scale with more data" (see task log):
// a plain <select> with hundreds of sightings/species/members is slow to
// scroll and hard to scan, so this filters as you type instead and only
// ever mounts this many rows regardless of how big `options` is. It's
// still a client-side filter over an already-fetched list, not server-side
// search/pagination — fine at the sizes a single org's data reaches today;
// revisit (see docs/open-questions.md) if a list ever grows past what's
// reasonable to fetch in one request at all.
const MAX_VISIBLE = 50;

/**
 * A type-to-filter replacement for a plain <select>, used everywhere this
 * app lets a user pick one record out of an account's own list (species,
 * sightings, activities, org members) — see LinkedRecordsPanel,
 * ActivitySpeciesPanel, TasksPage. Hand-rolled rather than a dependency:
 * this app has no UI-kit dependency yet (see the "no drawing library"
 * decision for map polygons, same reasoning — one component doesn't
 * justify adding one).
 *
 * Behavior: focusing the input opens a filtered list of all options;
 * typing narrows it (plain case-insensitive substring match); arrow
 * keys/Enter/Escape work; clicking an option selects it and closes the
 * list; an already-selected value shows its label in the input plus a ×
 * to clear back to "" (the same "Unassigned"/"None" affordance the
 * dropdowns this replaces had via their empty first option).
 */
export default function Combobox({
  options,
  value,
  onChange,
  placeholder = "Search…",
  noOptionsLabel = "No matches.",
  disabled = false,
  id,
  "aria-label": ariaLabel,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => options.find((o) => o.id === value) ?? null, [options, value]);

  const allMatches = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;
  }, [options, query]);
  const filtered = useMemo(() => allMatches.slice(0, MAX_VISIBLE), [allMatches]);
  const truncated = allMatches.length > filtered.length;

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  // A click on an option fires the input's onBlur first (see the
  // onMouseDown preventDefault below, which stops that for the option
  // buttons themselves) — but a click anywhere *else* outside the
  // control should still close the list, hence this rather than relying
  // on onBlur alone.
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const selectOption = (option: ComboboxOption | null) => {
    onChange(option ? option.id : "");
    setOpen(false);
    setQuery("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!open) {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        e.preventDefault();
        setOpen(true);
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[activeIndex]) selectOption(filtered[activeIndex]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  };

  return (
    <div className="combobox" ref={containerRef}>
      <div className="combobox__control">
        <input
          id={id}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          aria-label={ariaLabel}
          autoComplete="off"
          disabled={disabled}
          placeholder={selected ? undefined : placeholder}
          value={open ? query : selected?.label ?? ""}
          onFocus={() => {
            setOpen(true);
            setQuery("");
          }}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        {selected && !open && (
          <button
            type="button"
            className="combobox__clear"
            aria-label="Clear selection"
            onClick={() => selectOption(null)}
            disabled={disabled}
          >
            ×
          </button>
        )}
      </div>
      {open && (
        <ul className="combobox__list" role="listbox">
          {filtered.length === 0 && <li className="combobox__empty">{noOptionsLabel}</li>}
          {filtered.map((option, index) => (
            <li key={option.id} role="option" aria-selected={option.id === value}>
              <button
                type="button"
                className={
                  "combobox__option" +
                  (index === activeIndex ? " combobox__option--active" : "") +
                  (option.id === value ? " combobox__option--selected" : "")
                }
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => selectOption(option)}
                onMouseEnter={() => setActiveIndex(index)}
              >
                <span>{option.label}</span>
                {option.sublabel && <span className="combobox__sublabel">{option.sublabel}</span>}
              </button>
            </li>
          ))}
          {truncated && (
            <li className="combobox__hint">Showing first {MAX_VISIBLE} — keep typing to narrow.</li>
          )}
        </ul>
      )}
    </div>
  );
}
