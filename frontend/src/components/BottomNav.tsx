import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";

const navClass = ({ isActive }: { isActive: boolean }) =>
  "app-nav__link" + (isActive ? " app-nav__link--active" : "");

/** Primary navigation. Bottom tab bar on narrow (mobile) viewports,
 * repositioned to a left sidebar on wide ones — see index.css.
 * Properties/Species are the two Phase 1 top-level areas; everything
 * property-specific (activities, sightings, drawing) lives inside a
 * property's own map page rather than getting its own nav entry. "Public
 * site" and "Admin" were added alongside the public-site + org admin
 * portal work (see /CLAUDE.md task log) — Public site opens in a new tab
 * since it's a different audience's view of the same data, not a page in
 * this authed app; Admin only shows for admins (mirrors every other
 * role-gated control in the app — see auth/roles.ts). */
export default function BottomNav() {
  const { session } = useAuth();
  const isAdmin = roleAtLeast(session?.membership?.role, "admin");
  const orgId = session?.membership?.organization.id;

  return (
    <nav className="app-nav" aria-label="Primary">
      <NavLink to="/properties" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🗺️
        </span>
        Properties
      </NavLink>
      <NavLink to="/species" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🌱
        </span>
        Species
      </NavLink>
      {orgId && (
        <a
          href={`/public/org/${orgId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="app-nav__link"
        >
          <span className="app-nav__icon" aria-hidden="true">
            🌐
          </span>
          Public site
        </a>
      )}
      {isAdmin && (
        <NavLink to="/admin" className={navClass}>
          <span className="app-nav__icon" aria-hidden="true">
            ⚙️
          </span>
          Admin
        </NavLink>
      )}
    </nav>
  );
}
