import { absoluteTime, timeAgo } from "../utils/time";

/**
 * "4mo ago", as a `<time>` element carrying the exact instant.
 *
 * Extracted from `AttributionNote`, which owned the only copy, when D79's
 * fix gave the public site two more callers. The same reasoning that put
 * `timeAgo` in `utils/time.ts` applies one layer up: the *wording* is
 * shared already, but the `<time dateTime title>` wrapper and its null
 * guard are just as drift-prone, and a copy that dropped the guard would
 * render nothing where it should render nothing and something where the
 * timestamp is unparseable. Three sites, one element.
 *
 * # This is deliberately person-free, and that is the point (D79)
 *
 * `AttributionNote` exists to stop a time appearing without the person it
 * belongs to — its `created`/`updated` props are `{ by, at }` pairs so
 * that pairing is a type error to break rather than a convention to
 * remember. That rule is right where it lives and wrong if carried
 * outward, which is exactly the trap D79 names: on the public site there
 * is no person in the claim at all. "Last updated 3 weeks ago" is a
 * statement about the *record*, not about anybody, so it needs no `by`
 * and must not borrow one — reusing `AttributionNote` there would either
 * carry a member's email to an anonymous visitor (D38) or fail to
 * compile (D73's pairing).
 *
 * So this component takes a time and nothing else. `AttributionNote` is
 * the one place that pairs it with a person, and it still holds that rule
 * on its own.
 *
 * Renders nothing for an unparseable value — see `timeAgo`'s own note on
 * why it returns `null` rather than "NaNd ago".
 */
export default function RelativeTime({ at }: { at: string }) {
  const relative = timeAgo(at);
  if (relative === null) return null;
  // The machine-readable value is the ISO string the server sent, and the
  // tooltip is the exact local moment, so "4mo ago" stays glanceable
  // without being the only thing on offer.
  return (
    <time dateTime={at} title={absoluteTime(at) ?? undefined}>
      {relative}
    </time>
  );
}
