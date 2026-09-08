/** Turning a `:id` route parameter into a number you can actually send.
 *
 * This exists because `Number(id)` was used unguarded in three page
 * components, and `Number("abc")` is `NaN` rather than an error. `NaN` then
 * flowed straight into the API client, whose `withQuery` skips only
 * `undefined` — so `String(NaN)` went on the wire as the literal `NaN`,
 * reached the database layer, and returned an unhandled 500 from three
 * separate endpoints on one mistyped URL.
 *
 * The backend now rejects such a value properly (400 on the filters, 404 on
 * the pages lookup — see backend/apps/accounts/query_params.py), but that is
 * the outer guard, not the fix: the app shouldn't be issuing a request it
 * already knows is malformed, and "no such property" is a better thing to
 * show than a generic failure. Both halves are wanted.
 *
 * Rejects a negative or fractional value too, not just a non-numeric one:
 * every id in this app is a positive integer primary key, and `Number("1.5")`
 * or `Number("-3")` are perfectly good numbers that no row will ever match.
 */
export function parseRouteId(raw: string | undefined): number | null {
  if (raw === undefined || raw === "") return null;
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) return null;
  return value;
}
