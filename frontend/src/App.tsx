import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import AppShell from "./components/AppShell";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyFormPage from "./pages/PropertyFormPage";
import PropertyMapPage from "./pages/PropertyMapPage";
import ActivityFormPage from "./pages/ActivityFormPage";
import SightingFormPage from "./pages/SightingFormPage";
import SpeciesPage from "./pages/SpeciesPage";

/**
 * Phase 1 route map — the "create property → draw activity/sighting →
 * save" flow from /CLAUDE.md's task log, plus the account species list.
 * No public view (that's Phase 2) and no org-settings UI beyond signup —
 * see /docs/roadmap.md.
 */
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<Navigate to="/properties" replace />} />
            <Route path="/properties" element={<PropertiesPage />} />
            <Route path="/properties/new" element={<PropertyFormPage />} />
            <Route path="/properties/:id" element={<PropertyMapPage />} />
            <Route path="/properties/:id/activities/new" element={<ActivityFormPage />} />
            <Route path="/properties/:id/sightings/new" element={<SightingFormPage />} />
            <Route path="/species" element={<SpeciesPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
