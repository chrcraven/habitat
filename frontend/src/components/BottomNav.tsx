import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";

const navClass = ({ isActive }: { isActive: boolean }) =>
  "app-nav__link" + (isActive ? " app-nav__link--active" : "");

// The user/admin manual (docs/manual/) is a checked-in part of this repo,
// not a page this app serves itself — there's no in-app docs viewer, and
// no separate docs-hosting decision yet (see /docs/open-questions.md,
// "Hosting/ops model"). Linking straight to it on GitHub is the simplest
// thing that actually gets a user to it today; revisit if/when Habitat
// gets a real docs site. Points at `main` specifically (not whatever
// branch built this bundle) so the link is stable and always shows the
// merged, current manual rather than a feature branch's in-progress copy.
const MANUAL_URL = "https://github.com/chrcraven/habitat/blob/main/docs/manual/README.md";

/** Primary navigation. Bottom tab bar on narrow (mobile) viewports,
 * repositioned to a left sidebar on wide ones — see index.css. "Home"
 * (DashboardPage) is the landing page after login — see App.tsx.
 * Properties/Species are the two Phase 1 top-level areas; everything
 * property-specific (activities, sightings, drawing) lives inside a
 * property's own map page rather than getting its own nav entry. "Tasks"
 * is org-wide rather than property-specific (a task isn't tied to one
 * property the way an activity/sighting is), so it does get its own nav
 * entry. "Public site" and "Admin" were added alongside the public-site +
 * org admin portal work (see /CLAUDE.md task log) — Public site opens in
 * a new tab since it's a different audience's view of the same data, not
 * a page in this authed app; Admin only shows for admins (mirrors every
 * other role-gated control in the app — see auth/roles.ts). "Help" (added
 * later, same reasoning as Public site) opens the user/admin manual on
 * GitHub in a new tab — see MANUAL_URL above. "Account" (change password)
 * also lives in TopBar as a link on the caller's own email, but that's
 * hidden below 480px (see .top-bar__email in index.css) — it needs a spot
 * here too so it's actually reachable on a phone-width viewport, not just
 * desktop. */
export default function BottomNav() {
  const { session } = useAuth();
  const isAdmin = roleAtLeast(session?.membership?.role, "admin");
  const orgSlug = session?.membership?.organization.slug;

  return (
    <nav className="app-nav" aria-label="Primary">
      <NavLink to="/" end className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🏠
        </span>
        Home
      </NavLink>
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
      <NavLink to="/tasks" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          ✅
        </span>
        Tasks
      </NavLink>
      {orgSlug && (
        <a
          href={`/public/${orgSlug}`}
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
      <a href={MANUAL_URL} target="_blank" rel="noopener noreferrer" className="app-nav__link">
        <span className="app-nav__icon" aria-hidden="true">
          📖
        </span>
        Help
      </a>
      {isAdmin && (
        <NavLink to="/admin" className={navClass}>
          <span className="app-nav__icon" aria-hidden="true">
            ⚙️
          </span>
          Admin
        </NavLink>
      )}
      <NavLink to="/account" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          👤
        </span>
        Account
      </NavLink>
    </nav>
  );
}
