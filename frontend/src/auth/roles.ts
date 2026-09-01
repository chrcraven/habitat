import type { Membership, Role } from "../api/types";

// Mirrors backend/apps/accounts/org_scoping.py's _ROLE_RANK — viewer =
// read only, editor = read/create/update, admin = also delete. Keep the
// two in sync; the backend is what actually enforces this; this is just
// for hiding controls the user isn't allowed to use anyway.
const RANK: Record<Role, number> = { viewer: 0, editor: 1, admin: 2 };

export function roleAtLeast(role: Role | undefined | null, minimum: Role): boolean {
  if (!role) return false;
  return RANK[role] >= RANK[minimum];
}

/** True if the caller's own membership is limited to specific properties
 * rather than account-wide (see backend Membership.properties). Mirrors
 * backend/apps/accounts/org_scoping.py's scoped_property_ids — again,
 * the backend is what actually enforces this (PropertyViewSet.
 * perform_create and friends reject the actions this hides), this is
 * just for not showing a control that would always fail. */
export function isPropertyScoped(membership: Membership | null | undefined): boolean {
  return !!membership && membership.properties.length > 0;
}
