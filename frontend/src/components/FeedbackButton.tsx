import { useState } from "react";
import type { FormEvent } from "react";
import { useLocation } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";

/**
 * Floating "Send feedback" button (decided 2026-08-29 — see /docs/open-
 * questions.md, "App feedback / build workflow") — a corner button on
 * every authenticated page (see AppShell), not a nav entry, opening a
 * small submission form. Renders nothing at all when the feature is
 * turned off (`GET /api/feedback/config/`, backed by the
 * HABITAT_FEEDBACK_ENABLED env var) — most deployments won't have this
 * enabled, so there's no dead button to explain.
 *
 * Deliberately no client-side AI summarization or "digest" here — per the
 * owner's decision, feedback is pulled and reviewed by an external
 * scheduled routine via the authenticated retrieval endpoint
 * (backend/apps/feedback/views.py#feedback_pull), not processed in-app.
 * This component is just the submission box.
 */
export default function FeedbackButton() {
  const config = useAsync(() => api.feedback.config(), []);
  // Which screen this was sent from, submitted alongside the message so
  // the build queue knows where to start (owner request, 2026-09-02).
  // Read at submit time rather than when the panel opens — the widget
  // lives in AppShell and survives navigation, so a stale capture would
  // name whatever page the user was on when they first opened it.
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  if (!config.data?.enabled) return null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.feedback.submit(message, `${location.pathname}${location.search}`);
      setSent(true);
      setMessage("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send that feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSent(false);
    setError(null);
  };

  return (
    <div className="feedback-widget">
      {open ? (
        <div className="feedback-panel">
          <div className="feedback-panel__header">
            <strong>Send feedback</strong>
            <button
              type="button"
              className="btn-link"
              onClick={handleClose}
              aria-label="Close feedback"
            >
              ✕
            </button>
          </div>
          {sent ? (
            <p className="form-success">Thanks — your feedback was sent.</p>
          ) : (
            <form onSubmit={handleSubmit} className="form">
              {error && <p className="form-error">{error}</p>}
              <label className="field">
                <span>What's on your mind?</span>
                <textarea
                  required
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="A bug, something confusing, an idea…"
                />
              </label>
              <button type="submit" className="btn btn-primary btn-small" disabled={submitting}>
                {submitting ? "Sending…" : "Send"}
              </button>
            </form>
          )}
        </div>
      ) : (
        <button
          type="button"
          className="feedback-widget__toggle"
          onClick={() => setOpen(true)}
          aria-label="Send feedback"
        >
          💬
        </button>
      )}
    </div>
  );
}
