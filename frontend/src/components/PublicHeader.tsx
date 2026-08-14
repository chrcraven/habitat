import { Link } from "react-router-dom";

/** Header for every unauthenticated public-site page (org portfolio +
 * property pages) — reuses the authed app's .top-bar styling so the two
 * feel like the same product, but always offers a "Log in" link back to
 * the real app (per the request that started this: the public site needs
 * "a method to get to the backend/login"). `back` is an optional
 * breadcrumb-style link (property page → its org's portfolio page). */
export default function PublicHeader({
  back,
}: {
  back?: { to: string; label: string };
}) {
  return (
    <header className="top-bar">
      <strong className="top-bar__brand">🌿 Habitat</strong>
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
