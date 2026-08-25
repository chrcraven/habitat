import { useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

/**
 * Self-service "change your password" page — resolves the open-questions.md
 * gap where a member added via the org admin portal (an admin sets their
 * initial password directly, see OrgAdminPage) had no way to change it
 * themselves afterward. Deliberately just password change for now, not a
 * broader "account settings" page — name/email editing isn't asked for yet.
 */
export default function AccountPage() {
  const { session } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation don't match.");
      return;
    }
    setSubmitting(true);
    try {
      await api.auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't change your password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="page__header">
        <h1>Account</h1>
      </div>
      <p className="muted">{session?.user.email}</p>

      <div className="page__header">
        <h2>Change password</h2>
      </div>
      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}
        {success && <p className="form-success">Password updated.</p>}
        <label className="field">
          <span>Current password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </label>
        <label className="field">
          <span>New password</span>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Confirm new password</span>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </label>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || !currentPassword || !newPassword}
        >
          {submitting ? "Saving…" : "Change password"}
        </button>
      </form>
    </div>
  );
}
