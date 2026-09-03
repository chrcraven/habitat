import { api } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";
import { FeedbackRow } from "./rows";

/** Feedback this org's members have sent about Habitat itself. Org-level,
 * so account-wide admins only — a property-scoped admin gets a 403 from
 * the backend rather than an empty list (see sections.ts). */
export default function FeedbackSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "account-admin");
  const feedback = useAsync(() => (allowed ? api.feedback.list() : Promise.resolve([])), [allowed]);

  return (
    <ManageSectionPage
      title="Feedback"
      access="account-admin"
      intro={
        <p className="muted">
          Feedback your org's members have sent about Habitat itself — reviewed and folded into the
          development workflow separately; mark an item resolved once it's actually been addressed.
        </p>
      }
    >
      {feedback.loading && <p className="muted">Loading…</p>}
      {feedback.error && <p className="form-error">Couldn't load feedback: {feedback.error}</p>}
      <ul className="card-list">
        {feedback.data?.map((item) => (
          <FeedbackRow key={item.id} item={item} onResolved={feedback.reload} />
        ))}
      </ul>
      {!feedback.loading && !feedback.error && (feedback.data?.length ?? 0) === 0 && (
        <p className="muted">No feedback submitted yet.</p>
      )}
    </ManageSectionPage>
  );
}
