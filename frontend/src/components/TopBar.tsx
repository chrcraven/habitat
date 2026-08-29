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
      <Logo className="top-bar__brand" />
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
