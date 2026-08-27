import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

/**
 * Second half of the "forgot password" flow — reached from the link
 * emailed (or, until real SMTP is configured, console-logged — see
 * backend/apps/accounts/password_reset.py) by ForgotPasswordPage. A bad,
 * expired, or already-used token surfaces as one generic error, same
 * "don't confirm what's behind an opaque token" stance AcceptInvitePage
 * takes for invitation links — the backend doesn't distinguish those
 * cases either (see views.py#password_reset_confirm).
 */
export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const { status, confirmPasswordReset } = useAuth();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation don't match.");
      return;
    }
    setSubmitting(true);
    try {
      await confirmPasswordReset(token, newPassword);
      navigate("/", { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "That reset link isn't valid, has expired, or was already used.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>🌿 Habitat</h1>
        <p className="auth-subtitle">Set a new password for your account.</p>
        <form onSubmit={handleSubmit} className="form">
          {error && <p className="form-error">{error}</p>}
          <label className="field">
            <span>New password</span>
            <input
              type="password"
              autoComplete="new-password"
              autoFocus
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Confirm new password</span>
            <input
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !newPassword}
          >
            {submitting ? "Saving…" : "Reset password"}
          </button>
        </form>
        <p className="auth-switch">
          <Link to="/login">Back to log in</Link> ·{" "}
          <Link to="/forgot-password">Request a new link</Link>
        </p>
      </div>
    </div>
  );
}
