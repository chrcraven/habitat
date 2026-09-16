import type { ReactNode } from "react";

/**
 * "Added by alice@example.com · Last edited by bob@example.com"
 *
 * One component rather than the same JSX at each site, for the reason D6
 * and D34 both record: the original D6 defect was one content-type check
 * copy-pasted into four upload sites and wrong in all four, and D34's
 * four-word delete prompt stayed four words precisely because nobody read
 * the two dialogs side by side. A shared component means the next record
 * type that grows attribution inherits this wording or opts out
 * deliberately.
 *
 * Why this matters more than it looks (D38): Habitat has recorded who
 * created and last edited every activity since Phase 1 and showed it to
 * nobody — the app would tell you who complained about a button and not
 * who redrew the boundary of a restoration site. It composes badly with
 * two other open defects: the activity form PATCHes *every* field from the
 * snapshot it opened with (D29), so a colleague's status change, either
 * date, the public/private flag or a redrawn boundary is silently reverted
 * by someone fixing a typo; and nothing is backed up (D35). Naming the
 * last editor does not fix either. It makes them visible, which is the
 * difference between "the app changed my work" and "I can go ask Bob".
 *
 * `null` is a normal value, not an edge case — the underlying FKs are
 * SET_NULL, and a record nobody has edited has no editor. A missing
 * creator renders "unknown" (the fallback the Feedback row already uses);
 * a missing *editor* renders nothing at all, because "Last edited by
 * unknown" on a never-edited record would be actively misleading.
 *
 * This is never rendered on the public site. The email only reaches an
 * authenticated org member, because the backend only serves it from its
 * `…WithAttribution` serializers — see
 * backend/apps/accounts/attribution.py. The types enforce the same split
 * (`PublicActivity` does not carry these fields), so rendering this on a
 * public page is a compile error rather than a leak.
 */
export function AttributionNote({
  createdBy,
  updatedBy,
}: {
  createdBy: string | null;
  updatedBy?: string | null;
}) {
  const parts: ReactNode[] = [<>Added by {createdBy ?? "unknown"}</>];
  // Only when someone actually has edited it, and only when that is
  // someone other than the creator — "Added by A · Last edited by A" is
  // noise that makes the useful case (a *different* name) harder to spot.
  if (updatedBy && updatedBy !== createdBy) {
    parts.push(<>Last edited by {updatedBy}</>);
  }
  return (
    <p className="attribution-note">
      {parts.map((part, i) => (
        // Each clause is its own inline-block (see the stylesheet) so a
        // wrap falls *between* clauses rather than inside one. Two emails
        // rarely fit on one phone-width line, and the naive version broke
        // mid-phrase — line one ending "· Last", line two starting
        // "edited by" — which only showed up on looking at the render.
        // The separator trails its own clause rather than leading the next
        // one, so a wrapped second line never starts with a stray "·".
        <span className="attribution-note__part" key={i}>
          {part}
          {i < parts.length - 1 && <span aria-hidden="true"> · </span>}
        </span>
      ))}
    </p>
  );
}
