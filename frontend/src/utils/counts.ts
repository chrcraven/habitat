/**
 * The one place that turns a loaded list into the count sentence the
 * org-wide list screens show (D50a).
 *
 * It takes the *list*, not its length, and answers `null` for a list that
 * isn't loaded. The alternative every call site would otherwise reach for
 * — `data?.length ?? 0` — reports "0 properties" in two situations that
 * are not the same fact as an empty list: while the fetch is still in
 * flight, and when it failed outright. That is D47's lesson (an empty
 * value and an absent one are different facts) and D21's (a failed load
 * rendered as an empty list tells someone something false about their own
 * data). A count is exactly the kind of two-line render where that would
 * be reintroduced by copy-paste, so the distinction lives in the type
 * here rather than in a convention each caller has to remember: pass
 * `data` or `data?.features` straight through and render nothing when
 * this returns null.
 *
 * `plural` is explicit rather than `${singular}s` at every call site
 * because three of the five nouns this is used for are irregular —
 * "properties", "species" (unchanged), and the status-qualified task
 * labels. Singular is not cosmetic either: D30 shipped "All 1 sightings
 * are plotted", which reads as broken in the state a brand-new account is
 * actually in, so it is the first thing many people would see.
 *
 * What this deliberately does NOT do is decide what the number *means*.
 * Two of the five screens narrow their list server-side — TasksPage's
 * `?status=` and SpeciesPage's blooming-today — so on those the loaded
 * list is not the organization's total and the caller has to say what it
 * counted ("2 open tasks", "3 species blooming today"). Handing this
 * function a server-filtered list and printing a bare "N species" is the
 * attractive wrong fix here, and it is the same shape as the pagination
 * trap D30 recorded, except reachable today by clicking a control rather
 * than waiting for a feature nobody has built.
 */
export function countLabel(
  items: readonly unknown[] | null | undefined,
  singular: string,
  plural: string,
): string | null {
  if (!items) return null;
  return `${items.length} ${items.length === 1 ? singular : plural}`;
}
