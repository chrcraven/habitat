import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function RequireAuth() {
  const { status } = useAuth();

  if (status === "loading") {
    return <div className="full-page-status">Loading…</div>;
  }
  if (status === "anonymous") {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
