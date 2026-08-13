import { NavLink } from "react-router-dom";

const navClass = ({ isActive }: { isActive: boolean }) =>
  "app-nav__link" + (isActive ? " app-nav__link--active" : "");

/** Primary navigation. Bottom tab bar on narrow (mobile) viewports,
 * repositioned to a left sidebar on wide ones — see index.css. Kept to the
 * two Phase 1 top-level areas; everything property-specific (activities,
 * sightings, drawing) lives inside a property's own map page rather than
 * getting its own nav entry. */
export default function BottomNav() {
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
    </nav>
  );
}
