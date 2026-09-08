import { Link } from "react-router-dom";

/** Shown when a route's `:id` parameter isn't a usable id at all — a
 * mistyped or stale URL like `/properties/abc`.
 *
 * Deliberately distinct from the "Couldn't load this page" message the form
 * pages show when a *well-formed* request fails: this one is certain, needs
 * no request to establish, and can say the useful thing ("no such
 * property") instead of a generic failure. See utils/ids.ts for why this
 * case existed silently until now.
 */
export default function RecordNotFound({
  what = "page",
  backTo = "/properties",
  backLabel = "← Properties",
}: {
  what?: string;
  backTo?: string;
  backLabel?: string;
}) {
  return (
    <div className="page">
      <div className="page__header">
        <Link to={backTo} className="btn-link">
          {backLabel}
        </Link>
      </div>
      <p className="form-error">
        That {what} doesn't exist — the address may have been mistyped or the{" "}
        {what} may have been deleted.
      </p>
    </div>
  );
}
