import { api } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { isPropertyScoped, roleAtLeast } from "../../auth/roles";
import ManageSectionPage from "./ManageSectionPage";
import { countLabel } from "../../utils/counts";
import { AddMemberForm, MemberRow, PendingInvitationRow } from "./rows";
import { LoadError } from "../../components/LoadError";

/** Members, pending invitations, and the add-member form — the three
 * pieces of one job, so they stay on one route rather than being split
 * three ways.
 *
 * Open to any admin, including a property-scoped one: the 2026-09-02
 * narrowing means a scoped admin sees only the members scoped to its own
 * properties (the backend filters the list) and must give a new member a
 * property, which is what `requireProperty` reflects. */
export default function MembersSection() {
  const { session } = useAuth();
  const isAdmin = roleAtLeast(session?.membership?.role, "admin");
  const scopedAdmin = isAdmin && isPropertyScoped(session?.membership);

  const members = useAsync(
    () => (isAdmin ? api.org.members.list() : Promise.resolve([])),
    [isAdmin],
  );
  const invitations = useAsync(
    () => (isAdmin ? api.org.invitations.list() : Promise.resolve([])),
    [isAdmin],
  );
  const properties = useAsync(() => api.properties.listWithoutGeometry(), []);
  const propertyList = properties.data?.features ?? [];
  const memberCount = countLabel(members.data, "member", "members");

  const reloadMembers = () => {
    members.reload();
    invitations.reload();
  };

  return (
    <ManageSectionPage
      title="Members"
      access="admin"
      intro={
        scopedAdmin ? (
          <p className="muted">
            Your admin role is limited to specific properties, so this covers the members scoped to
            them. Organization-wide members are handled by an organization-wide admin.
          </p>
        ) : undefined
      }
    >
      {members.loading && <p className="muted">Loading…</p>}
      {members.error && (
        <LoadError what="members" error={members.error} onRetry={members.reload} />
      )}
      {/* The qualifier is not decoration. The backend narrows this list for
          a property-scoped admin (the 2026-09-02 change), so a bare "3
          members" here would tell that admin their organization has three
          members when it may have thirty — a number contradicting the org,
          on the one screen whose job is managing people. The count has to
          say what it counted. */}
      {memberCount && (
        <p className="muted">
          {memberCount}
          {scopedAdmin ? " scoped to your properties." : "."}
        </p>
      )}
      <ul className="card-list">
        {members.data?.map((m) => (
          <MemberRow
            key={m.id}
            membership={m}
            properties={propertyList}
            isSelf={m.user.id === session?.user.id}
            scopedAdmin={scopedAdmin}
            onChanged={members.reload}
          />
        ))}
      </ul>

      {(invitations.loading || (invitations.data?.length ?? 0) > 0) && (
        <>
          <div className="page__header">
            <h2>Pending invitations</h2>
          </div>
          {invitations.loading && <p className="muted">Loading…</p>}
          {invitations.error && (
            <LoadError
              what="invitations"
              error={invitations.error}
              onRetry={invitations.reload}
            />
          )}
          <ul className="card-list">
            {invitations.data?.map((inv) => (
              <PendingInvitationRow
                key={inv.id}
                invitation={inv}
                onRevoked={invitations.reload}
                onResent={invitations.reload}
              />
            ))}
          </ul>
        </>
      )}

      <div className="page__header">
        <h2>Add a member</h2>
      </div>
      <AddMemberForm
        properties={propertyList}
        requireProperty={scopedAdmin}
        onAdded={reloadMembers}
      />
    </ManageSectionPage>
  );
}
