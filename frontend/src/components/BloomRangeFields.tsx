import { MONTH_NAMES, daysInMonth, formatBloomValue, parseBloomDate } from "../utils/bloom";

/**
 * The two ends of a species' bloom period, as month + day pickers.
 *
 * Deliberately **not** `<input type="date">`: a bloom period repeats every
 * year and has no year of its own (see backend/apps/species/models.py), so
 * a date input would force the user to pick a meaningless year and would
 * quietly imply this is a one-off date rather than an annual season.
 *
 * Either end may be cleared back to "—", which clears both — the API
 * rejects half a range, since one end alone can't be filtered on or
 * displayed as a period.
 */
function BloomDatePicker({
  label,
  value,
  onChange,
}: {
  label: string;
  /** `MM-DD`, or null for "not set". */
  value: string | null;
  onChange: (next: string | null) => void;
}) {
  const parsed = parseBloomDate(value);
  const month = parsed?.month ?? "";
  const day = parsed?.day ?? "";

  const setMonth = (nextMonth: string) => {
    if (!nextMonth) {
      onChange(null);
      return;
    }
    const m = Number(nextMonth);
    // Clamp the day when moving to a shorter month, so switching from
    // "March 31" to February can't produce a day the month doesn't have.
    const d = Math.min(Number(day) || 1, daysInMonth(m));
    onChange(formatBloomValue({ month: m, day: d }));
  };

  const setDay = (nextDay: string) => {
    if (!month) return;
    const m = Number(month);
    const d = Math.min(Math.max(Number(nextDay) || 1, 1), daysInMonth(m));
    onChange(formatBloomValue({ month: m, day: d }));
  };

  return (
    <label className="field">
      <span>{label}</span>
      <div className="field-row field-row--tight">
        <select value={month} onChange={(e) => setMonth(e.target.value)} aria-label={`${label} month`}>
          <option value="">—</option>
          {MONTH_NAMES.map((name, index) => (
            <option key={name} value={index + 1}>
              {name}
            </option>
          ))}
        </select>
        <select
          value={day}
          onChange={(e) => setDay(e.target.value)}
          disabled={!month}
          aria-label={`${label} day`}
        >
          {month === "" ? (
            <option value="">—</option>
          ) : (
            Array.from({ length: daysInMonth(Number(month)) }, (_, i) => i + 1).map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))
          )}
        </select>
      </div>
    </label>
  );
}

/** Both ends of the range, plus the note that a wrapping range is fine —
 * shared by the species add form and each species row's edit form. */
export default function BloomRangeFields({
  start,
  end,
  onChange,
}: {
  start: string | null;
  end: string | null;
  onChange: (next: { start: string | null; end: string | null }) => void;
}) {
  return (
    <>
      <div className="field-row">
        <BloomDatePicker
          label="Bloom starts"
          value={start}
          onChange={(next) => onChange({ start: next, end: next === null ? null : end })}
        />
        <BloomDatePicker
          label="Bloom ends"
          value={end}
          onChange={(next) => onChange({ start: next === null ? null : start, end: next })}
        />
      </div>
      <span className="field-hint muted">
        Repeats every year, so there's no year to pick. A period that runs through the new year
        (November to February, say) is fine — set it that way round.
      </span>
    </>
  );
}
