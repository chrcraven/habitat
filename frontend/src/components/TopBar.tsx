import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function TopBar() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="top-bar">
      <strong className="top-bar__brand">🌿 Habitat</strong>
      <div className="top-bar__account">
        <span className="top-bar__email">{session?.user.email}</span>
        <button type="button" className="btn btn-ghost btn-small" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </header>
  );
}
