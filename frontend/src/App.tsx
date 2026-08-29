import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import AppShell from "./components/AppShell";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import AcceptInvitePage from "./pages/AcceptInvitePage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyFormPage from "./pages/PropertyFormPage";
import PropertyMapPage from "./pages/PropertyMapPage";
import ActivityFormPage from "./pages/ActivityFormPage";
import SightingFormPage from "./pages/SightingFormPage";
import SpeciesPage from "./pages/SpeciesPage";
import TasksPage from "./pages/TasksPage";
import OrgAdminPage from "./pages/OrgAdminPage";
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
        <Route path="/public/:orgSlug" element={<PublicOrganizationPage />} />
        <Route path="/public/:orgSlug/:propertySlug" element={<PublicPropertyPage />} />

        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
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
            <Route path="/species" element={<SpeciesPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/admin" element={<OrgAdminPage />} />
            <Route path="/account" element={<AccountPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
