import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import Logo from "../components/Logo";
import { returnPathFrom, withReturn } from "../utils/returnTo";

export default function SignupPage() {
  const { status, signup } = useAuth();
  const navigate = useNavigate();
  const { search } = useLocation();
  const returnTo = returnPathFrom(search);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    return <Navigate to={returnTo} replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signup({ email, password, organization_name: organizationName || undefined });
      navigate(returnTo, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-card__brand">
          <Logo size="lg" />
        </h1>
        <p className="auth-subtitle">
          Every account is its own organization — even a one-person yard — so
          this creates both your login and your account in one step.
        </p>
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
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Account name (optional)</span>
            <input
              type="text"
              placeholder="e.g. your land's name"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
            />
            {/* This field is shown publicly (it's the heading and the URL of
                your public site), and until 2026-09-07 nothing said so —
                which is how blank signups ended up publishing the user's
                email address. Say both things here: that it's public, and
                what leaving it blank does. */}
            <span className="field-hint muted">
              Shown on your public site, and used in its web address. Leave it
              blank to be called “My land” — you can rename it any time under
              Manage.
            </span>
          </label>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to={withReturn("/login", search)}>Log in</Link>
        </p>
      </div>
    </div>
  );
}
