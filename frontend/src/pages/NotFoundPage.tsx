import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Logo from "../components/Logo";

/**
 * The app's catch-all: an address matching no route at all.
 *
 * This replaced `<Route path="*" element={<Navigate to="/" replace />} />`,
 * which sent every unmatched address to `/` — and `/` is inside
 * `RequireAuth`, which answers an anonymous visitor with the login screen,
 * byte-identical to a legitimate visit to `/login`. So a mistyped address
 * and a locked door were the same screen: the app reported "you need to log
 * in" as the cause of "that address doesn't exist".
 *
 * It landed hardest on the public site, which is the *unauthenticated* half
 * of the product. A visitor who mistypes `/public/…` may have no account at
 * all, so the screen they were handed was one they could neither use nor get
 * past. `PublicHeader`'s own docstring already refuses to link its brand mark
 * to `/` for precisely this reason — the catch-all was doing the very thing
 * that comment exists to prevent.
 *
 * Two properties here are load-bearing and easy to undo by accident:
 *
 *   - **It renders in place; it does not redirect.** The old bounce used
 *     `replace`, so the URL bar ended up reading `/login` and pressing Back
 *     returned `/login` again — a visitor could not reread their own typo in
 *     order to correct it. Keeping the address is what makes it correctable,
 *     and it is echoed below as plain text for the same reason (as text, not
 *     a link: it is untrusted input that failed to match any route).
 *   - **It is mounted outside `RequireAuth`** in App.tsx, so it never
 *     bounces regardless of session state. Moving it inside would restore
 *     the whole defect.
 *
 * The way out is offered per audience rather than as one generic link, since
 * the two audiences need opposite things: a signed-in member wants back into
 * the app, while an anonymous visitor most likely followed a broken public
 * link and cannot use a dashboard at all.
 *
 * Scope, stated so it isn't mistaken for more than it is: this is a
 * *client-side* not-found. The deployment serves the SPA with a catch-all
 * fallback, so the HTTP status for an unmatched address is still 200 and this
 * fix does not change that — it is what a person sees, not what a crawler is
 * told. Returning a real 404 status is a serving-layer concern.
 */
export default function NotFoundPage() {
  const { status } = useAuth();
  const location = useLocation();
  const attempted = `${location.pathname}${location.search}`;

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-card__brand">
          <Logo size="lg" />
        </h1>
        <p className="form-error">
          That page doesn't exist — the address may have been mistyped, or the
          page may have been moved or deleted.
        </p>
        <p className="muted auth-notfound__address">
          You asked for <code>{attempted}</code>
        </p>
        {status === "authenticated" && (
          <p className="auth-switch">
            <Link to="/">Go to your dashboard</Link> ·{" "}
            <Link to="/properties">Your properties</Link>
          </p>
        )}
        {status === "anonymous" && (
          <>
            <p className="muted">
              If someone shared a link to a public Habitat page, check the
              address above for a typo — links are sometimes cut short when
              they're copied.
            </p>
            <p className="auth-switch">
              Have an account? <Link to="/login">Log in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
