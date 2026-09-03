import { api } from "../../api/client";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../auth/AuthContext";
import { canAccess } from "./sections";
import ManageSectionPage from "./ManageSectionPage";
import { DeletedPropertyRow } from "./rows";

/** Soft-deleted properties, restorable for 30 days. */
export default function DeletedSection() {
  // Don't fire a request this role will only be 403'd for — the
  // wrapper renders a refusal instead of this content anyway.
  const { session } = useAuth();
  const allowed = canAccess(session?.membership, "admin");
  const deletedProperties = useAsync(() => (allowed ? api.properties.deleted.list() : Promise.resolve([])), [allowed]);
  const properties = useAsync(() => (allowed ? api.properties.list() : Promise.resolve(null)), [allowed]);

  return (
    <ManageSectionPage
      title="Recently deleted"
      access="admin"
      intro={
        <p className="muted">
          Deleted properties (and their activities/sightings) are hidden right away but kept for 30
          days in case that was a mistake — restore one here, or wait and it's removed for good.
        </p>
      }
    >
      {deletedProperties.loading && <p className="muted">Loading…</p>}
      {deletedProperties.error && (
        <p className="form-error">
          Couldn't load recently-deleted properties: {deletedProperties.error}
        </p>
      )}
      <ul className="card-list">
        {deletedProperties.data?.map((p) => (
          <DeletedPropertyRow
            key={p.id}
            property={p}
            onRestored={() => {
              deletedProperties.reload();
              properties.reload();
            }}
          />
        ))}
      </ul>
      {/* This section used to be hidden entirely when empty, because it
          sat in the middle of one long page. On its own route it's
          something you navigate to on purpose, so an empty state beats a
          blank screen. */}
      {!deletedProperties.loading &&
        !deletedProperties.error &&
        (deletedProperties.data?.length ?? 0) === 0 && (
          <p className="muted">Nothing deleted in the last 30 days.</p>
        )}
    </ManageSectionPage>
  );
}
