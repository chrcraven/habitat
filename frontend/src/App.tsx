import MapView from "./MapView";

/**
 * Phase 1 shell: just the map view, no auth/routing/API integration yet.
 * See /CLAUDE.md and /docs/roadmap.md — this is the starting point for the
 * activity-logging flow (draw a property boundary, log an activity
 * against it), not a finished screen.
 */
export default function App() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <header style={{ padding: "0.5rem 1rem", borderBottom: "1px solid #ddd" }}>
        <strong>Habitat</strong>
      </header>
      <MapView />
    </div>
  );
}
