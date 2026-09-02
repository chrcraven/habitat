/**
 * A species' bloom period (see backend/apps/species/models.py).
 *
 * The API carries each end as `MM-DD` with no year, because a bloom
 * period is annual and recurring — so everything here works in month/day
 * pairs and never constructs a `Date`. A range is also allowed to **wrap
 * the year** ("11-01" to "02-15" for a winter bloomer), which is why
 * nothing below tries to order the two ends or treat start > end as an
 * error.
 */

export const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/** Day counts for a leap year: February 29 is a real bloom date, and
 * since the stored value carries no year there's nothing that could rule
 * it out. Matches the backend's own leap-year day validation. */
const DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

export interface BloomDate {
  /** 1-12. */
  month: number;
  /** 1-31, bounded by daysInMonth(month). */
  day: number;
}

export function daysInMonth(month: number): number {
  return DAYS_IN_MONTH[month - 1] ?? 31;
}

/** `"05-01"` -> `{ month: 5, day: 1 }`; null/empty/malformed -> null. */
export function parseBloomDate(value: string | null | undefined): BloomDate | null {
  if (!value) return null;
  const match = /^(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const month = Number(match[1]);
  const day = Number(match[2]);
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(month)) return null;
  return { month, day };
}

/** `{ month: 5, day: 1 }` -> `"05-01"`, the wire format the API expects. */
export function formatBloomValue(date: BloomDate): string {
  return `${String(date.month).padStart(2, "0")}-${String(date.day).padStart(2, "0")}`;
}

/** `"05-01"` -> `"May 1"` — for display, never for sending back. */
export function formatBloomDate(value: string | null | undefined): string {
  const parsed = parseBloomDate(value);
  if (!parsed) return "";
  return `${MONTH_NAMES[parsed.month - 1]} ${parsed.day}`;
}

/** `"05-01"`, `"08-15"` -> `"Blooms May 1 – August 15"`; "" when the
 * species has no bloom period recorded. Shown both in the app's species
 * list and on the public site, so it lives here rather than in either
 * page. */
export function formatBloomRange(
  start: string | null | undefined,
  end: string | null | undefined,
): string {
  const from = formatBloomDate(start);
  const to = formatBloomDate(end);
  if (!from || !to) return "";
  return `Blooms ${from} – ${to}`;
}

/** Today as `MM-DD`, for the "blooming now" filter. Local date on
 * purpose: "what's blooming now" is a question about where the user is,
 * not about UTC. */
export function todayBloomValue(): string {
  const now = new Date();
  return formatBloomValue({ month: now.getMonth() + 1, day: now.getDate() });
}
