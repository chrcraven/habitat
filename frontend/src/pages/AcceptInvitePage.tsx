import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../api/client";
import type { InvitationPreview } from "../api/types";

const ROLE_LABEL: Record<string, string> = {
  admin: "an admin",
  editor: "an editor",
  viewer: "a viewer",
};

/**
 * The org-invite counterpart to SignupPage — reached from the accept link
 * an admin shares (email or copy/paste, see OrgAdminPage) instead of
 * creating a brand-new organization, this joins the *inviting* org. See
 * backend/apps/accounts/views.py#invitation_detail/invitation_accept and
 * /docs/open-questions.md ("Auth and API", real email-invite flow).
 */
export default function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>();
  const { status, acceptInvitation } = useAuth();
  const navigate = useNavigate();

  const [invitation, setInvitation] = useState<InvitationPreview | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const preview = await api.invitations.get(token);
        if (!cancelled) setInvitation(preview);
      } catch {
        // Covers a bad token, an expired one, and an already-accepted one
        // alike — the backend 404s on all three rather than distinguishing
        // them (same "don't confirm what's behind an ID" stance as the
        // public site), so there's no more specific detail to surface here.
        if (!cancelled) {
          setLoadError("That invitation link isn't valid, has expired, or was already used.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      await acceptInvitation(token, {
        password,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>🌿 Habitat</h1>
        {loading && <p className="muted">Loading invitation…</p>}
        {!loading && loadError && (
          <>
            <p className="form-error">{loadError}</p>
            <p className="auth-switch">
              Ask whoever invited you to send a new invitation, or{" "}
              <Link to="/login">log in</Link> if you already have an account.
            </p>
          </>
        )}
        {!loading && invitation && (
          <>
            <p className="auth-subtitle">
              You've been invited to join <strong>{invitation.organization_name}</strong> on
              Habitat as {ROLE_LABEL[invitation.role] ?? invitation.role}. Set a password for{" "}
              <strong>{invitation.email}</strong> to finish joining.
            </p>
            <form onSubmit={handleSubmit} className="form">
              {error && <p className="form-error">{error}</p>}
              <div className="field-row">
                <label className="field">
                  <span>First name</span>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Last name</span>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </label>
              </div>
              <label className="field">
                <span>Password</span>
                <input
                  type="password"
                  autoComplete="new-password"
                  autoFocus
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Joining…" : `Join ${invitation.organization_name}`}
              </button>
            </form>
          </>
        )}
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
