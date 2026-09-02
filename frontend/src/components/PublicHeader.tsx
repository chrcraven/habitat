import { Link } from "react-router-dom";
import Logo from "./Logo";

/** Header for every unauthenticated public-site page (org portfolio +
 * property pages) — reuses the authed app's .top-bar styling so the two
 * feel like the same product, but always offers a "Log in" link back to
 * the real app (per the request that started this: the public site needs
 * "a method to get to the backend/login"). `back` is an optional
 * breadcrumb-style link (property page → its org's portfolio page).
 *
 * `home` is where the brand mark points (feedback, 2026-09-02). Note this
 * deliberately is *not* "/" the way the authenticated TopBar's is: "/" is
 * the login-gated app, so sending a public visitor there would drop them
 * on a login screen. It's this public site's own root — the org's vanity
 * URL — and it stays relative, since we're already on whichever origin
 * serves the public site (see utils/publicSite.ts). It's optional because
 * the loading and "not public" states render this header before the org
 * is known, and a brand mark linking nowhere in particular is worse than
 * one that isn't a link yet. */
export default function PublicHeader({
  back,
  home,
}: {
  back?: { to: string; label: string };
  home?: string;
}) {
  return (
    <header className="top-bar">
      {home ? (
        <Link to={home} className="top-bar__brand logo-link" aria-label="Home">
          <Logo />
        </Link>
      ) : (
        <Logo className="top-bar__brand" />
      )}
      <div className="top-bar__account">
        {back && (
          <Link to={back.to} className="btn-link">
            {back.label}
          </Link>
        )}
        <Link to="/login" className="btn btn-secondary btn-small">
          Log in
        </Link>
      </div>
    </header>
  );
}
