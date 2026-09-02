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
