/**
 * A failed load, said the same way everywhere — and with the one thing
 * that lets the reader do something about it.
 *
 * **Why this is a component rather than a line of JSX per screen (D63,
 * 2026-09-25).** Habitat renders a failed load on 21 screens. Exactly one
 * of them — `PropertiesPage` — paired that message with a control, and it
 * had done since the wording was first written; the other twenty offered a
 * dead end. `useAsync` has exposed `reload` the whole time, so nothing was
 * missing but the affordance, at twenty of twenty-one sites.
 *
 * That is the shape this repo keeps paying for: one correct implementation
 * and N copies of the half of it somebody remembered (D6's content-type
 * check in four upload sites, D26's guard on two of three reference lists,
 * D34's delete prompt, D47a's assignee label, D50a's counts). A ternary per
 * screen would have been the same bet again — the next screen that loads
 * something would inherit the message and not the button, because a copy is
 * only ever as complete as the line the author's eye landed on. A component
 * inherits both or neither.
 *
 * **Retrying is genuinely free here, which is what makes a button the right
 * affordance rather than advice.** Every caller is a `GET` through
 * `useAsync`, so pressing it re-issues an idempotent read; there is no
 * partially-applied write to worry about and nothing to confirm. The one
 * thing it cannot do is tell a slow link from a dead one, because nothing
 * in the app bounds a request (D61) — so a retry against no signal hangs in
 * "Loading…" exactly as the first attempt did. That is D61's to fix, and
 * the owner's to decide; it is not a reason to withhold the button, since
 * the common failure this answers is a 502/503 during the deployment's own
 * 15-minute image refresh, where one press genuinely works.
 *
 * @param what Names the thing that failed, lower-case, as the object of
 *   "Couldn't load ___" — "species", "your tasks", "recently-deleted
 *   properties". Kept as a prop rather than a whole message so the sentence
 *   itself can't drift between screens.
 * @param error The message from `useAsync`, which for a dropped connection
 *   is the browser's own raw text ("Failed to fetch"). Shown as-is; making
 *   that legible is D64's, and the owner's.
 * @param onRetry Almost always the `reload` a `useAsync` already returns.
 */
export function LoadError({
  what,
  error,
  onRetry,
}: {
  what: string;
  error: string;
  onRetry: () => void;
}) {
  return (
    <p className="form-error">
      Couldn't load {what}: {error}{" "}
      <button type="button" className="btn-link" onClick={onRetry}>
        Retry
      </button>
    </p>
  );
}
