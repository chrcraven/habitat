import { isPropertyScoped, roleAtLeast } from "../../auth/roles";
import type { Membership } from "../../api/types";

/**
 * Who can see which part of Manage.
 *
 * "Admin" became "Manage" — a section every member can open — on owner
 * feedback (2026-09-03: "It should become a manage section"), because
 * Properties, Species and Public site moved under it and gating the whole
 * entry behind `isAdmin` would have left an editor with no way to reach
 * the property they're supposed to be logging work on.
 *
 * **The gate moved inward; it did not disappear.** Two independent
 * filters compose here:
 *
 *  - `access` — the caller's role (viewer/editor/admin).
 *  - the property-scoped-admin narrowing (owner decision, 2026-09-02): an
 *    admin scoped to specific properties administers *those properties*,
 *    not the organization, so the org-level half is hidden from it.
 *
 * These mirror the gates the single-route OrgAdminPage already applied,
 * one for one. As everywhere else in this app, the frontend only hides
 * what a role can't use — `OrganizationRolePermission` / `ensure_role` on
 * the backend are what actually enforce any of this.
 */
export type ManageAccess =
  /** Any member of the organization. */
  | "member"
  /** Any admin, including one scoped to specific properties. */
  | "admin"
  /** An account-wide admin only — the organization-level settings. */
  | "account-admin";

export interface ManageSection {
  id: string;
  label: string;
  /** Route under /manage, or an app route elsewhere for the three
   * sections that are really links to existing pages. */
  to: string;
  icon: string;
  description: string;
  access: ManageAccess;
  /** True for the entries that leave Manage rather than opening a
   * sub-page of it (Properties, Species, Public site). */
  external?: boolean;
}

export const MANAGE_SECTIONS: ManageSection[] = [
  {
    id: "properties",
    label: "Properties",
    to: "/properties",
    icon: "🗺️",
    description: "The land you manage — boundaries, public visibility, and per-property settings.",
    access: "member",
    external: true,
  },
  {
    id: "species",
    label: "Species",
    to: "/species",
    icon: "🌱",
    description: "Your organization's own species list, with descriptions and bloom periods.",
    access: "member",
    external: true,
  },
  {
    id: "organization",
    label: "Organization",
    to: "/manage/organization",
    icon: "🏛️",
    description: "Name, public URL, and a QR code for your public site.",
    access: "account-admin",
  },
  {
    id: "theme",
    label: "Theme",
    to: "/manage/theme",
    icon: "🎨",
    description: "Colors, font, and header image for your public site.",
    access: "account-admin",
  },
  {
    id: "activity-types",
    label: "Activity types",
    to: "/manage/activity-types",
    icon: "🏷️",
    description: "The kinds of work you log — yours to name.",
    access: "account-admin",
  },
  {
    id: "workflow-states",
    label: "Workflow states",
    to: "/manage/workflow-states",
    icon: "🔁",
    description: "The states your activities move through, from planned to finished.",
    access: "account-admin",
  },
  {
    id: "pages",
    label: "Pages",
    to: "/manage/pages",
    icon: "📄",
    description: "Authored pages for your public site, and which one visitors land on.",
    access: "account-admin",
  },
  {
    id: "members",
    label: "Members",
    to: "/manage/members",
    icon: "👥",
    description: "Who's in your organization, their roles, and pending invitations.",
    access: "admin",
  },
  {
    id: "deleted",
    label: "Recently deleted",
    to: "/manage/deleted",
    icon: "♻️",
    description: "Restore a deleted property within 30 days.",
    access: "admin",
  },
  {
    id: "feedback",
    label: "Feedback",
    to: "/manage/feedback",
    icon: "💬",
    description: "What your members have sent about Habitat itself.",
    access: "account-admin",
  },
];

/** Whether a membership may open a section. The single place this rule
 * lives — the index menu and each sub-page's own guard both call it, so a
 * section can't be listed in one and reachable in the other. */
export function canAccess(membership: Membership | null | undefined, access: ManageAccess): boolean {
  const isAdmin = roleAtLeast(membership?.role, "admin");
  switch (access) {
    case "member":
      return !!membership;
    case "admin":
      return isAdmin;
    case "account-admin":
      return isAdmin && !isPropertyScoped(membership);
  }
}

export function visibleSections(membership: Membership | null | undefined): ManageSection[] {
  return MANAGE_SECTIONS.filter((s) => canAccess(membership, s.access));
}
