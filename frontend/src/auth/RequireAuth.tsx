import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { loginPathFor } from "../utils/returnTo";

export default function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <div className="full-page-status">Loading…</div>;
  }
  if (status === "anonymous") {
    // Carries the destination across as ?next= so logging in can resume it;
    // this used to be a bare `/login`, which discarded it. `replace` stays
    // deliberate — the address is preserved in the parameter (and so is
    // recoverable from the login screen itself), and a history entry that
    // only bounces straight back here again is worse than none.
    // See utils/returnTo.ts, whose sanitizer is what keeps ?next= from
    // becoming an open redirect.
    return <Navigate to={loginPathFor(location)} replace />;
  }
  return <Outlet />;
}
