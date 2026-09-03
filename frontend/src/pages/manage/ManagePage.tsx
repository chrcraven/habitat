import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { publicSiteUrl } from "../../utils/publicSite";
import { visibleSections } from "./sections";

/**
 * The Manage menu — what used to be the single 1061-line /admin route
 * (owner feedback, 2026-09-03: "Make the admin side of the site have a
 * submenu of sorts. This is a lot of information stuck onto a single
 * page"). Each section is now its own route, so it's linkable and fetches
 * only its own data.
 *
 * Visible to every member: which entries appear is decided per section
 * (see sections.ts), not by gating the whole page behind `isAdmin` the
 * way the old Admin nav entry did. A viewer sees Properties, Species and
 * Public site and nothing else.
 */
export default function ManagePage() {
  const { session } = useAuth();
  const sections = visibleSections(session?.membership);
  const orgSlug = session?.membership?.organization.slug;

  return (
    <div className="page">
      <div className="page__header">
        <h1>Manage</h1>
      </div>
      <p className="muted">
        Your properties, species list, and organization settings. You'll see the parts your role
        gives you access to.
      </p>

      <ul className="card-list">
        {sections.map((section) => (
          <li key={section.id} className="card card--row">
            <Link to={section.to} className="card__link">
              <strong>
                <span aria-hidden="true">{section.icon}</span> {section.label}
              </strong>
              <span className="muted">{section.description}</span>
            </Link>
          </li>
        ))}

        {/* The public site is a different audience's view of the same
            data, not a page in this app — so it opens in a new tab, the
            same as it did from the old nav entry, and can't be a
            <Link>. */}
        {orgSlug && (
          <li className="card card--row">
            <a
              href={publicSiteUrl(`/public/${orgSlug}`)}
              target="_blank"
              rel="noopener noreferrer"
              className="card__link"
            >
              <strong>
                <span aria-hidden="true">🌐</span> Public site ↗
              </strong>
              <span className="muted">What visitors see. Opens in a new tab.</span>
            </a>
          </li>
        )}
      </ul>
    </div>
  );
}
