import type { ReactNode } from "react";
import { absoluteTime, timeAgo } from "../utils/time";

/**
 * "Added by alice@example.com, 3mo ago · Last edited by bob@example.com,
 * saved 2h ago"
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
 * # Why each clause carries a time (D73)
 *
 * D38 shipped the name and left the time behind, in a payload that was
 * already carrying it — `created_at` and `updated_at` are on the same
 * serializer, one line from `created_by_email` and `updated_by_email`.
 * That is D38's own sharpest line inverted: it found "the timestamp
 * travelled and the person didn't" and fixed the half it was looking at.
 *
 * It is a defect rather than a nicety because the manual's remedy for
 * D29 rests on it, in two chapters: *"if the name isn't yours and the
 * record matters, reload the page before saving."* A name with no time
 * cannot separate an edit made five minutes ago (reload) from one made
 * five months ago (irrelevant), so on a team where a colleague once
 * edited every record the advice degrades to "always reload" — and
 * reloading costs whatever you have typed, because nothing in this app
 * persists a draft.
 *
 * # The rule: a time never appears without the person it belongs to
 *
 * `created` and `updated` are each a `{ by, at }` pair rather than four
 * loose props, so the pairing is a type error to break rather than a
 * convention to remember. That matters because the tempting wrong
 * version is real: `Sighting` and `Task` both carry `updated_at` and
 * **neither has an `updated_by` column**, so an "edited 2h ago" line on
 * either would be an unattributed claim — "somebody changed this and we
 * won't say who", which is worse than silence. Passing `updated` here
 * requires supplying a `by`, and on those two types there is no such
 * field to supply, so the mistake does not compile.
 *
 * `Activity` is the one model with both halves, and its `updated_by` is
 * one column written at exactly one site
 * (`ActivityViewSet.perform_update`), so the editor named can never be
 * stale or wrong.
 *
 * # "saved", not "edited at"
 *
 * `Activity.updated_at` moves when the **Activity row** saves. Photos,
 * species links and sighting links live in their own tables, so a photo
 * added a minute ago does not move it. "Last edited by bob, saved 2h
 * ago" is therefore true as written where "edited 2h ago" would quietly
 * claim nothing about the record has changed since. The manual says the
 * same thing at more length.
 *
 * `null` is a normal value, not an edge case — the underlying FKs are
 * SET_NULL, and a record nobody has edited has no editor. A missing
 * creator renders "unknown" (the fallback the Feedback row already uses);
 * a missing *editor* renders no edit clause at all, because "Last edited
 * by unknown" on a never-edited record would be actively misleading.
 *
 * This is never rendered on the public site. The email only reaches an
 * authenticated org member, because the backend only serves it from its
 * `…WithAttribution` serializers — see
 * backend/apps/accounts/attribution.py. The types enforce the same split
 * (`PublicActivity` does not carry these fields), so rendering this on a
 * public page is a compile error rather than a leak.
 */

/** A person and the moment they acted, kept together on purpose — see
 * "The rule" above. `by` is nullable (SET_NULL, and null until a record
 * is first edited); `at` always exists, because both timestamps are
 * `auto_now_add`/`auto_now` columns. */
export interface Attribution {
  by: string | null;
  at: string;
}

function When({ at }: { at: string }) {
  const relative = timeAgo(at);
  if (relative === null) return null;
  // <time> rather than a bare span: the machine-readable value is the
  // ISO string the server sent, and the tooltip is the exact local
  // moment, so "4mo ago" stays glanceable without being the only thing
  // on offer.
  return (
    <time dateTime={at} title={absoluteTime(at) ?? undefined}>
      {relative}
    </time>
  );
}

export function AttributionNote({
  created,
  updated,
}: {
  created: Attribution;
  updated?: Attribution;
}) {
  const parts: ReactNode[] = [
    <>
      Added by {created.by ?? "unknown"}, <When at={created.at} />
    </>,
  ];

  if (updated?.by) {
    // The name is repeated only when it differs. "Added by A · Last
    // edited by A" is noise that makes the useful case — a *different*
    // name — harder to spot, which is why the original suppressed the
    // whole clause in that case. Suppressing it wholesale is what D73
    // corrects: when the creator is also the last editor, the *time* is
    // still new information, and it is precisely the information the
    // D29 remedy needs. "bob added this three months ago and last saved
    // it five minutes ago" is a collision warning; "Added by bob" alone
    // is not. So the name drops out and the time stays.
    parts.push(
      updated.by === created.by ? (
        <>
          last saved <When at={updated.at} />
        </>
      ) : (
        <>
          Last edited by {updated.by}, saved <When at={updated.at} />
        </>
      ),
    );
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
