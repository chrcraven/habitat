/**
 * Relative and absolute rendering of a server timestamp.
 *
 * Extracted from `NotificationsBell`, which owned the only copy, when
 * the attribution line grew a second caller (D73). The D6/D34/D39/D47
 * precedent applies with unusual force here: the wording of a relative
 * time is exactly the kind of thing that drifts when copied, and two
 * surfaces disagreeing about whether something happened "2h ago" or
 * "yesterday" is worse than either wording on its own.
 *
 * # Why this returns `string | null`
 *
 * The version this replaces rendered an unparseable timestamp as
 * `"NaNd ago"` — `new Date("nonsense").getTime()` is `NaN`, every
 * comparison against `NaN` is false, so control fell through every
 * branch to the last one and interpolated the `NaN` straight into the
 * string. Returning `null` instead lets a caller render nothing, which
 * is what both callers want: a missing time reads as "no information",
 * where `"NaNd ago"` reads as a broken app. React renders `null` as
 * nothing, so neither call site needs a branch for it.
 *
 * # Clock skew
 *
 * A timestamp in the future (server clock ahead of the browser's)
 * produces a negative `ms`, which lands in the `< 1 minute` branch and
 * reads "just now". That is the right degradation: a record saved
 * "just now" is the most cautious thing this line can say, and the
 * alternative ("in 3 minutes") would read as a bug.
 *
 * # Staleness
 *
 * This is computed at render time and does not tick. `NotificationsBell`
 * re-renders on its own 60-second poll; the attribution line on a form
 * does not re-render at all while you sit there. So a form left open for
 * an hour still says what it said on arrival — which understates the
 * record's age, and understating it is the safe direction for the one
 * decision this line exists to inform (D73: "is somebody else's edit
 * recent enough that I should reload before saving?"). A stale-low
 * number makes a reader *more* cautious, not less. The `title` from
 * `absoluteTime` is exact either way.
 */

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "just now" / "5m ago" / "3h ago" / "9d ago" / "4mo ago" / "2y ago".
 *
 * The month and year bands are new here — the notifications-only version
 * stopped at days, which was fine for a list that is usually minutes old
 * and poor for the attribution line, where a record created a year ago
 * is ordinary. It improves the notification list too: notifications are
 * never purged (D30's retention half is still open), so a genuinely old
 * one used to read "247d ago".
 *
 * A month is 30 days and a year is 365, deliberately approximate — this
 * is a "roughly how long ago" line, and anyone who needs the exact
 * moment has it in the `title`. */
export function timeAgo(iso: string): string | null {
  const ms = Date.now() - new Date(iso).getTime();
  if (!Number.isFinite(ms)) return null;
  if (ms < MINUTE) return "just now";
  if (ms < HOUR) return `${Math.floor(ms / MINUTE)}m ago`;
  if (ms < DAY) return `${Math.floor(ms / HOUR)}h ago`;
  const days = Math.floor(ms / DAY);
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

/** The same instant in the reader's own locale and timezone, for a
 * `title`/tooltip beside the relative form.
 *
 * "4mo ago" is the right thing to read at a glance and the wrong thing
 * to quote to a colleague. Rather than choose, the relative form is what
 * renders and this is what a hover reveals. */
export function absoluteTime(iso: string): string | null {
  const date = new Date(iso);
  if (!Number.isFinite(date.getTime())) return null;
  return date.toLocaleString();
}

/** The relative time of `updatedAt`, or `null` when it falls in the same
 * band as `createdAt`.
 *
 * This exists because the obvious test for "has this record been edited
 * since it was created?" — `createdAt !== updatedAt` — is **wrong, for
 * every record**. `auto_now_add` and `auto_now` each call
 * `timezone.now()` in their own field's `pre_save`, so the two values
 * differ by a few microseconds on a row nobody has ever touched.
 * Measured on the deployment's own public activities: four of six have
 * never been edited and all four differ, by 5-7 microseconds. A
 * string-inequality check would claim every record on the public site
 * had been updated.
 *
 * A fixed threshold ("more than a minute apart") would fix that and
 * introduce a quieter problem. The same measurement found two activities
 * edited 23 and 60 seconds after creation — the create-then-add-photos
 * flow, not a later revision — and both are 34 days old now, so any
 * threshold they cleared would render "logged 1mo ago · updated 1mo ago":
 * two identical times, which looks like information and is not.
 *
 * So the comparison is made at **the granularity the line actually
 * renders at**. If both timestamps land in the same band there is nothing
 * to say, and saying it twice is worse than silence. No constant to pick,
 * and the rule cannot drift out of step with the bands above because it
 * is defined in terms of them.
 *
 * Its limit, stated because it is real: two edits in one band are
 * indistinguishable, so a record logged 59 days ago and edited 31 days
 * ago reads as "1mo ago" with no update clause. That understates how
 * current the record is, which is the safe direction for a public
 * record — a reader treats it as older than it is rather than newer. */
export function editedTimeAgo(createdAt: string, updatedAt: string): string | null {
  const updated = timeAgo(updatedAt);
  if (updated === null) return null;
  return updated === timeAgo(createdAt) ? null : updated;
}
