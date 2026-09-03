import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import type { ManageAccess } from "./sections";

/**
 * Chrome shared by every Manage sub-page: a back link to the section
 * menu, the section's own heading, and — importantly — the same access
 * check the menu used to decide whether to list it.
 *
 * The guard is here rather than only in the menu because a sub-page has
 * its own URL: leaving it out would mean a viewer who typed
 * /manage/members got a page that rendered its controls and only failed
 * once the API rejected each call. The backend is still what enforces
 * this (see sections.ts); this is what makes the refusal legible.
 */
export default function ManageSectionPage({
  title,
  access,
  intro,
  actions,
  children,
}: {
  title: string;
  access: ManageAccess;
  intro?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const { session } = useAuth();

  return (
    <div className="page">
      <Link to="/manage" className="btn-link">
        ← Manage
      </Link>
      <div className="page__header">
        <h1>{title}</h1>
        {canAccess(session?.membership, access) && actions}
      </div>
      {!canAccess(session?.membership, access) ? (
        <p className="form-error">
          You don't have access to this part of Manage. Ask an organization admin if you think you
          should.
        </p>
      ) : (
        <>
          {intro}
          {children}
        </>
      )}
    </div>
  );
}
