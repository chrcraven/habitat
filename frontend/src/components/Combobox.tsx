import { useEffect, useId, useMemo, useRef, useState } from "react";
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
  /** What to display when `value` is set but no entry in `options`
   * matches it — a record that is still referenced but is no longer a
   * valid *choice* (a task assigned to someone since removed from the
   * organization, D47). Without this the control silently renders its
   * placeholder, i.e. reports "nothing selected" for a row that has a
   * value, which is how the same task row came to give two different
   * answers about who owned it.
   *
   * Deliberately separate from `options` rather than the caller just
   * appending a synthetic entry: that would put a choice in the picker
   * that the server refuses (`TaskSerializer.validate_assigned_to` 400s
   * on a non-member), so the list stays exactly the set of things a user
   * may pick and this labels what is already set. */
  valueLabel?: string;
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
 *
 * Three things below exist so that ↑/↓ actually tell you what Enter will
 * take (D56, 2026-09-24). Before them the control was fully
 * keyboard-drivable with no dependable indication of the active option —
 * for *anyone*, sighted or not:
 *
 *  1. `aria-activedescendant` on the input, pointing at the active
 *     option's own `id`. This is what announces the move; DOM focus
 *     deliberately STAYS ON THE INPUT, which is the entire reason the
 *     active-descendant pattern exists. Do not "fix" a future complaint
 *     here by calling .focus() on the option — that breaks typing, which
 *     is this control's whole purpose.
 *  2. `scrollIntoView` on the active option. `.combobox__list` is
 *     `max-height: 14rem; overflow-y: auto` while up to MAX_VISIBLE rows
 *     render, so without this the highlight walks off into the clipped
 *     region past roughly the sixth row and the list does not follow.
 *  3. An option is the `<li>` itself, not a `<button>` inside it. ARIA's
 *     `option` role takes text content, not interactive descendants, and
 *     an option must not be focusable — see (1). The click/hover handlers
 *     moved onto the `<li>` unchanged.
 *
 * The ids are generated here with useId() rather than required of
 * callers: the `id` prop is optional and **no call site passes one**, so
 * requiring it would leave `aria-activedescendant` pointing at nothing on
 * every existing site — a control that is present and inert, which is
 * this repo's most-repeated failure mode (D40, D43, D45, D46, D49, D53).
 *
 * The fourth piece of D56 is in index.css, not here: the active
 * highlight's own contrast. See `.combobox__option--active`.
 */
export default function Combobox({
  options,
  value,
  onChange,
  valueLabel,
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
  const listRef = useRef<HTMLUListElement | null>(null);
  const activeOptionRef = useRef<HTMLLIElement | null>(null);
  // One base per mounted control, so two comboboxes on the same screen
  // (ActivitySpeciesPanel, TasksPage) never mint the same option id.
  const idBase = useId();
  const listId = `${idBase}-list`;
  const optionId = (index: number) => `${idBase}-option-${index}`;

  const selected = useMemo(() => options.find((o) => o.id === value) ?? null, [options, value]);

  // What the input shows when closed. A value the options can't resolve
  // is NOT the same as no value at all, which is the distinction the
  // control used to collapse: fall back to `valueLabel` before falling
  // back to empty. Everything below keys off this rather than `selected`,
  // so an unresolvable value still reads as set and still offers the ×.
  // Clearing one is an admin's own deliberate act (the same one they can
  // already perform on any assignment), not something this does for them.
  const displayLabel = selected?.label ?? (value === "" ? null : valueLabel ?? null);

  const allMatches = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;
  }, [options, query]);
  const filtered = useMemo(() => allMatches.slice(0, MAX_VISIBLE), [allMatches]);
  const truncated = allMatches.length > filtered.length;

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  // Keep the active option on screen by scrolling THIS LIST ONLY, by hand.
  //
  // The obvious implementation is
  // `activeOptionRef.current?.scrollIntoView({ block: "nearest" })`, and it
  // is wrong here in a way that is invisible to any check that merely
  // asserts the highlight is visible. Measured in a real browser: the form
  // pages put the combobox inside `.map-page-scroll`, an ancestor with its
  // own `overflow-y: auto`, and scrollIntoView walks up and scrolls
  // *whichever* ancestor it likes — so ArrowDown scrolled the whole page
  // region (the list's own scrollTop stayed 0) and dragged the control up
  // the viewport. That then slid a different option under the user's
  // stationary mouse pointer, which fires mouseenter, which set activeIndex
  // back — so the highlight bounced between rows 1 and 4 forever and
  // ArrowDown could not reach row 7 of 20.
  //
  // `offsetTop` is relative to `.combobox__list` because that list is
  // `position: absolute` and is therefore each option's offsetParent.
  useEffect(() => {
    if (!open) return;
    const option = activeOptionRef.current;
    const list = listRef.current;
    if (!option || !list) return;
    const top = option.offsetTop;
    const bottom = top + option.offsetHeight;
    // "nearest" semantics, scoped to the list: move by the minimum needed,
    // and do nothing at all when the option is already fully visible.
    if (top < list.scrollTop) list.scrollTop = top;
    else if (bottom > list.scrollTop + list.clientHeight) {
      list.scrollTop = bottom - list.clientHeight;
    }
  }, [open, activeIndex]);

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
          aria-controls={listId}
          // Only while there is genuinely an active option to point at: a
          // dangling aria-activedescendant is worse than none, and the
          // list can legitimately be empty (noOptionsLabel).
          aria-activedescendant={
            open && filtered[activeIndex] ? optionId(activeIndex) : undefined
          }
          aria-label={ariaLabel}
          autoComplete="off"
          disabled={disabled}
          placeholder={displayLabel ? undefined : placeholder}
          value={open ? query : displayLabel ?? ""}
          onFocus={() => {
            setOpen(true);
            setQuery("");
          }}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        {displayLabel && !open && (
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
        <ul className="combobox__list" role="listbox" id={listId} ref={listRef}>
          {filtered.length === 0 && <li className="combobox__empty">{noOptionsLabel}</li>}
          {filtered.map((option, index) => (
            // The option IS the <li> — see the component docstring's (3).
            // onMouseDown's preventDefault stays: it stops the input
            // blurring before the click lands, which is what lets a click
            // select rather than just close the list.
            <li
              key={option.id}
              id={optionId(index)}
              role="option"
              aria-selected={option.id === value}
              ref={index === activeIndex ? activeOptionRef : undefined}
              className={
                "combobox__option" +
                (index === activeIndex ? " combobox__option--active" : "") +
                (option.id === value ? " combobox__option--selected" : "")
              }
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => selectOption(option)}
              // onMouseMove, not onMouseEnter, and that is load-bearing:
              // scrolling the list moves options *under a pointer that has
              // not moved*, and the browser fires mouseenter for that. With
              // onMouseEnter, hover therefore clobbered the active option
              // every time ArrowDown scrolled the list — the keyboard and a
              // motionless mouse fighting each other. A pointer that has not
              // moved produces no mousemove, so this keeps hover-to-activate
              // for a real mouse user and stops scroll masquerading as hover.
              onMouseMove={() => setActiveIndex(index)}
            >
              <span>{option.label}</span>
              {option.sublabel && <span className="combobox__sublabel">{option.sublabel}</span>}
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
