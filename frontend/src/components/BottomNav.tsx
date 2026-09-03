import { NavLink } from "react-router-dom";

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
 * repositioned to a left sidebar on wide ones — see index.css.
 *
 * The entries are Home, Activities, Sightings, Tasks, Manage, Account
 * (plus Help) — owner decision, 2026-09-03: "By default home, tasks,
 * activities, and sightings. Along with admin and account." Properties,
 * Species and Public site moved *under* Manage (see pages/manage/
 * ManagePage.tsx) rather than each holding a top-level slot.
 *
 * **Nothing here is role-gated any more.** "Admin" used to be, because
 * /admin was an admin-only console; "Manage" is a section every member
 * can open, with the admin-only surfaces gated per section inside it (see
 * pages/manage/sections.ts). Activities and Sightings are org-wide record
 * lists, new in the same change — a viewer can read them, which is
 * exactly what a viewer role is for.
 *
 * "Help" opens the user/admin manual on GitHub in a new tab (see
 * MANUAL_URL above). "Account" (change password) also lives in TopBar as
 * a link on the caller's own email, but that's hidden below 480px (see
 * .top-bar__email in index.css) — it needs a spot here too so it's
 * actually reachable on a phone-width viewport, not just desktop. */
export default function BottomNav() {
  return (
    <nav className="app-nav" aria-label="Primary">
      <NavLink to="/" end className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🏠
        </span>
        Home
      </NavLink>
      <NavLink to="/activities" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🌾
        </span>
        Activities
      </NavLink>
      <NavLink to="/sightings" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          🦋
        </span>
        Sightings
      </NavLink>
      <NavLink to="/tasks" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          ✅
        </span>
        Tasks
      </NavLink>
      <NavLink to="/manage" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          ⚙️
        </span>
        Manage
      </NavLink>
      <a href={MANUAL_URL} target="_blank" rel="noopener noreferrer" className="app-nav__link">
        <span className="app-nav__icon" aria-hidden="true">
          📖
        </span>
        Help
      </a>
      <NavLink to="/account" className={navClass}>
        <span className="app-nav__icon" aria-hidden="true">
          👤
        </span>
        Account
      </NavLink>
    </nav>
  );
}
