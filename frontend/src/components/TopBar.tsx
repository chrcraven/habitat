import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Logo from "./Logo";
import NotificationsBell from "./NotificationsBell";

export default function TopBar() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="top-bar">
      {/* The brand links home — the dashboard, not the properties list
          (feedback, 2026-09-02: "clicking the logo or habit should return
          the user to the home page"). The public site's own header links
          somewhere different; see PublicHeader. */}
      <Link to="/" className="top-bar__brand logo-link" aria-label="Habitat home">
        <Logo />
      </Link>
      {/* The organization you're currently acting in. Every page in this
          app shows that org's data and nothing else, and until this line
          existed the app never said which one it was — the name was
          delivered in every session payload and rendered nowhere (D28,
          /docs/open-questions.md). It belongs in the chrome rather than on
          one page because the scoping it describes applies to all of them.

          Deliberately kept to a single line that does NOT grow the bar:
          --topbar-height is a hardcoded 61px that .app-nav's desktop
          sidebar uses as its own `top` offset, so a taller top bar would
          put the sidebar back over its corner — the exact bug fixed on
          2026-08-28. It ellipses instead of wrapping for the same reason.

          Not a link: there is nowhere to go. Switching orgs is an open
          owner question (D28 Q1), and pointing this at a page that can't
          switch would be the "control that looks available and isn't"
          class this finding is already an instance of. */}
      {session?.membership && (
        <div className="top-bar__org" title={session.membership.organization.name}>
          <span className="top-bar__org-label">Organization</span>
          <span className="top-bar__org-name">{session.membership.organization.name}</span>
        </div>
      )}
      <div className="top-bar__account">
        <NotificationsBell />
        <Link to="/account" className="top-bar__email">
          {session?.user.email}
        </Link>
        <button type="button" className="btn btn-ghost btn-small" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </header>
  );
}
