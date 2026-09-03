import { Navigate, Route, Routes, useParams } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import AppShell from "./components/AppShell";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import AcceptInvitePage from "./pages/AcceptInvitePage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import QuickLogPage from "./pages/QuickLogPage";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyFormPage from "./pages/PropertyFormPage";
import PropertyMapPage from "./pages/PropertyMapPage";
import ActivityFormPage from "./pages/ActivityFormPage";
import SightingFormPage from "./pages/SightingFormPage";
import SpeciesPage from "./pages/SpeciesPage";
import TasksPage from "./pages/TasksPage";
import ActivitiesPage from "./pages/ActivitiesPage";
import SightingsPage from "./pages/SightingsPage";
import ManagePage from "./pages/manage/ManagePage";
import OrganizationSection from "./pages/manage/OrganizationSection";
import ThemeSection from "./pages/manage/ThemeSection";
import ActivityTypesSection from "./pages/manage/ActivityTypesSection";
import WorkflowStatesSection from "./pages/manage/WorkflowStatesSection";
import PagesSection from "./pages/manage/PagesSection";
import MembersSection from "./pages/manage/MembersSection";
import DeletedSection from "./pages/manage/DeletedSection";
import FeedbackSection from "./pages/manage/FeedbackSection";
import PageFormPage from "./pages/PageFormPage";
import AccountPage from "./pages/AccountPage";
import PublicOrganizationPage from "./pages/PublicOrganizationPage";
import PublicPropertyPage from "./pages/PublicPropertyPage";

/**
 * Phase 1/2/3 route map — the "create property → draw activity/sighting →
 * save" flow from /CLAUDE.md's task log, the account species list, the
 * org admin portal (member/role management, including the org-invite
 * accept flow at /accept-invite/:token — see AcceptInvitePage), and the
 * unauthenticated public site. The `/public/...` routes are deliberately
 * outside RequireAuth/AppShell — no login, no bottom nav, just
 * PublicHeader (see that component) with a link back to /login.
 * /accept-invite/:token, /forgot-password, and /reset-password/:token are
 * outside them for the same reason (no session yet, or intentionally not
 * one — see ForgotPasswordPage/ResetPasswordPage). "/" is the dashboard (DashboardPage) — a summary
 * landing page (tasks, upcoming/recent activities, recent sightings)
 * rather than a redirect straight to /properties.
 */
/** Back-compat for a bookmarked /admin/pages/:pageId/edit — carries the
 * page id across to the /manage route rather than dropping the visitor on
 * the section index, which the plain /admin/* catch-all would do. */
function RedirectPageEdit() {
  const { pageId } = useParams();
  return <Navigate to={`/manage/pages/${pageId}/edit`} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/accept-invite/:token" element={<AcceptInvitePage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
        {/* Numeric-ID public routes, kept for backward compatibility. */}
        <Route path="/public/org/:orgId" element={<PublicOrganizationPage />} />
        <Route path="/public/properties/:propertyId" element={<PublicPropertyPage />} />
        {/* Vanity-slug public routes (see /docs/open-questions.md). The
            static "org"/"properties" segments above rank higher in
            react-router than these single-/double-dynamic-segment routes,
            so a numeric URL still hits its own route; reserved org slugs
            (see backend slugs.py) keep "org"/"properties" from ever being
            an org slug that would shadow them. */}
        {/* Authored-page routes (see /docs/open-questions.md, "Public
            site storytelling") — the literal "explore"/"pages" segments
            here rank higher than the single-dynamic-segment
            :propertySlug route below in react-router's matching, so a
            property can't accidentally shadow these. Explore is rendered
            client-side from the same org/property payload the root route
            already fetches — no separate API call. */}
        <Route path="/public/:orgSlug/explore" element={<PublicOrganizationPage forcePage="explore" />} />
        <Route path="/public/:orgSlug/pages/:pageSlug" element={<PublicOrganizationPage />} />
        <Route
          path="/public/:orgSlug/:propertySlug/explore"
          element={<PublicPropertyPage forcePage="explore" />}
        />
        <Route
          path="/public/:orgSlug/:propertySlug/pages/:pageSlug"
          element={<PublicPropertyPage />}
        />
        <Route path="/public/:orgSlug" element={<PublicOrganizationPage />} />
        <Route path="/public/:orgSlug/:propertySlug" element={<PublicPropertyPage />} />

        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            {/* Quick log — the geometry-first capture flow, reached from
                the dashboard (owner decision, 2026-09-02). Not scoped to a
                property in its URL: which property it lands on is worked
                out from where the points are placed, which is the point of
                the flow. See QuickLogPage. */}
            <Route path="/quick-log" element={<QuickLogPage />} />
            <Route path="/properties" element={<PropertiesPage />} />
            <Route path="/properties/new" element={<PropertyFormPage />} />
            <Route path="/properties/:id" element={<PropertyMapPage />} />
            <Route path="/properties/:id/edit" element={<PropertyFormPage />} />
            <Route path="/properties/:id/activities/new" element={<ActivityFormPage />} />
            <Route
              path="/properties/:id/activities/:activityId/edit"
              element={<ActivityFormPage />}
            />
            <Route path="/properties/:id/sightings/new" element={<SightingFormPage />} />
            <Route
              path="/properties/:id/sightings/:sightingId/edit"
              element={<SightingFormPage />}
            />
            <Route path="/properties/:id/pages/new" element={<PageFormPage />} />
            <Route path="/properties/:id/pages/:pageId/edit" element={<PageFormPage />} />
            <Route path="/species" element={<SpeciesPage />} />
            {/* Org-wide record lists (owner feedback, 2026-09-03) —
                activities and sightings were previously reachable only
                inside a property. The per-property routes above still
                own creating and editing them; these are for finding one
                among many. */}
            <Route path="/activities" element={<ActivitiesPage />} />
            <Route path="/sightings" element={<SightingsPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            {/* "Admin" became "Manage" (owner decision, 2026-09-03): a
                section every member can open, with the admin-only
                surfaces gated per section inside it (see
                pages/manage/sections.ts). The old single /admin route
                that rendered all eight sections at once is gone; each is
                its own sub-route now. */}
            <Route path="/manage" element={<ManagePage />} />
            <Route path="/manage/organization" element={<OrganizationSection />} />
            <Route path="/manage/theme" element={<ThemeSection />} />
            <Route path="/manage/activity-types" element={<ActivityTypesSection />} />
            <Route path="/manage/workflow-states" element={<WorkflowStatesSection />} />
            <Route path="/manage/pages" element={<PagesSection />} />
            <Route path="/manage/members" element={<MembersSection />} />
            <Route path="/manage/deleted" element={<DeletedSection />} />
            <Route path="/manage/feedback" element={<FeedbackSection />} />
            <Route path="/manage/pages/new" element={<PageFormPage />} />
            <Route path="/manage/pages/:pageId/edit" element={<PageFormPage />} />
            {/* Bookmarks and any link already out in the world still
                work — /admin was a real, linkable route for weeks. */}
            <Route path="/admin" element={<Navigate to="/manage" replace />} />
            <Route path="/admin/pages/new" element={<Navigate to="/manage/pages/new" replace />} />
            <Route path="/admin/pages/:pageId/edit" element={<RedirectPageEdit />} />
            <Route path="/admin/*" element={<Navigate to="/manage" replace />} />
            <Route path="/account" element={<AccountPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
