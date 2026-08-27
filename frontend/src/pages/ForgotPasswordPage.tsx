import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

/**
 * "Forgot password" — start of the flow (see
 * backend/apps/accounts/views.py#password_reset_request and
 * /docs/open-questions.md, "Auth and API"). Deliberately shows the exact
 * same confirmation message whether or not the email actually has an
 * account, matching the backend's anti-enumeration stance — this page
 * must not branch its UI on success/failure of "does this email exist."
 */
export default function ForgotPasswordPage() {
  const { status, requestPasswordReset } = useAuth();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const detail = await requestPasswordReset(email);
      setMessage(detail);
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
        <p className="auth-subtitle">
          Enter the email on your account and we'll send a link to reset your password.
        </p>
        {message ? (
          <p className="form-success">{message}</p>
        ) : (
          <form onSubmit={handleSubmit} className="form">
            {error && <p className="form-error">{error}</p>}
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                inputMode="email"
                autoComplete="email"
                autoFocus
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}
        <p className="auth-switch">
          <Link to="/login">Back to log in</Link>
        </p>
      </div>
    </div>
  );
}
