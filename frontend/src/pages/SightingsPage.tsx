import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../auth/AuthContext";
import { roleAtLeast } from "../auth/roles";
import MapCanvas from "../components/MapCanvas";
import { ensureCircleLayer, setGeoJsonSource } from "../components/mapLayers";
import { pointBounds, positionsBounds } from "../utils/geo";
import type { Position, Sighting } from "../api/types";
import {
  SIGHTING_NOUN,
  countVisibility,
  matchesVisibilityFilter,
  publicCountSummary,
  publicVisibility,
  visibilityBadgeClass,
  visibilityLabel,
  wouldPublishSummary,
  type PropertyVisibility,
  type VisibilityFilter,
} from "../utils/publicVisibility";
import { LoadError } from "../components/LoadError";
import { withReturnTo } from "../utils/returnTo";

const SIGHTINGS_SOURCE = "org-sightings";

/**
 * Org-wide list of every sighting the caller can see, with a search box and
 * a map of whatever that search currently matches.
 *
 * The list half came from 2026-09-03 feedback; see ActivitiesPage for why
 * it filters client-side over the existing list endpoint rather than adding
 * API surface. The **map** half came from user feedback 2026-09-11 (item
 * 14, submitted from a sighting's edit page): *"I want to see all crabgrass
 * sightings, as points."*
 *
 * Reading that request precisely is what kept this small. A species filter
 * already existed — the search box below matches common and scientific name
 * — so the missing piece was never filtering, it was that **sightings could
 * only be seen as points inside a single property** (PropertyMapPage). One
 * species growing across three properties had nowhere it could be seen at
 * once. So the map plots `filtered`, not `all`: typing "crabgrass" is what
 * makes this "all crabgrass sightings, as points", and the search box the
 * page already had becomes the control for the map.
 *
 * The same feedback also floated *"some sort of super sighting"* — a way to
 * group sightings into one thing. That is a data-model question (what a
 * group is, whether it is user-made or derived from species, what happens
 * to it when a member sighting is deleted) and is deliberately **not**
 * answered here; it is queued in /docs/open-questions.md. Nothing on this
 * page forecloses it.
 *
 * The **Visibility** filter (D39, 2026-09-16) is client-side for the reason
 * ActivitiesPage's comment gives — a server-side `?is_public=` would
 * collapse the denominator the exposure summary depends on. Here it has a
 * second payoff the sibling page can't have: the map plots `filtered`, so
 * choosing "On the public site" draws exactly the points an anonymous
 * visitor can see.
 */
export default function SightingsPage() {
  // The address to come back to after editing a row (D66a). Built from the
  // live location rather than a literal so that if these filters ever move
  // into the URL, the origin carries them with no further change here.
  const { pathname, search } = useLocation();
  const origin = `${pathname}${search}`;
  const { session } = useAuth();
  const canEdit = roleAtLeast(session?.membership?.role, "editor");
  const { data, loading, error, reload } = useAsync(() => api.sightings.list(), []);
  const properties = useAsync(() => api.properties.listWithoutGeometry(), []);
  const [filter, setFilter] = useState("");
  const [visibility, setVisibility] = useState<VisibilityFilter>("all");
  // D71b — see ActivitiesPage's own comment for why the search box was
  // never a property filter. "all", a property id as a string, or "none":
  // Sighting.property is nullable (SET_NULL, and a point may fall outside
  // every drawn boundary), unlike Activity.property, so this page needs
  // the third option its sibling doesn't.
  const [propertyFilter, setPropertyFilter] = useState("all");
  const [map, setMap] = useState<MapLibreMap | null>(null);

  const propertyName = (propertyId: number | null): string => {
    if (propertyId == null) return "No property";
    return (
      properties.data?.features.find((p) => p.id === propertyId)?.properties.name ?? "Unknown property"
    );
  };

  const all = useMemo(() => data?.features ?? [], [data]);

  // null until the property list resolves (or if it fails): the second half
  // of the two-condition public rule is unknown until then, and it must not
  // be guessed. See utils/publicVisibility.ts.
  const propertyVisibility = useMemo<PropertyVisibility[] | null>(
    () =>
      properties.data?.features.map((p) => ({
        id: p.id,
        isPublic: p.properties.is_public,
      })) ?? null,
    [properties.data],
  );

  const visibilityOf = (sighting: Sighting) =>
    publicVisibility(sighting.properties.is_public, sighting.properties.property, propertyVisibility);

  const counts = useMemo(() => countVisibility(all.map(visibilityOf)), [all, propertyVisibility]);

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    return all.filter((s: Sighting) => {
      if (!matchesVisibilityFilter(visibility, visibilityOf(s))) return false;
      if (propertyFilter === "none") {
        if (s.properties.property != null) return false;
      } else if (propertyFilter !== "all" && String(s.properties.property) !== propertyFilter) {
        return false;
      }
      if (!query) return true;
      // Deliberately not the visibility badge's own words — see
      // ActivitiesPage's haystack comment for why the select owns that.
      // The property name left this list on the same principle once the
      // Property select existed to own it exactly (D71b).
      const haystack = [
        s.properties.species_detail.common_name,
        s.properties.species_detail.scientific_name,
        s.properties.notes,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [all, filter, visibility, propertyFilter, properties.data]);

  const narrowed = filter.trim() !== "" || visibility !== "all" || propertyFilter !== "all";

  // Sighting.location is a non-null PointField (backend/apps/sightings/
  // models.py), so in practice every sighting has one. The shared Feature
  // type is permissive about geometry, though, and a feature with a null
  // geometry makes MapLibre's source data invalid rather than just
  // plotting nothing — so filter defensively instead of trusting the
  // model through a type that doesn't promise it.
  const plottable = useMemo(
    () => filtered.filter((s): s is Sighting & { geometry: { coordinates: Position } } =>
      s.geometry != null,
    ),
    [filtered],
  );

  // Fit to whatever is currently matched, so narrowing the search zooms to
  // the results rather than leaving them as specks in a world view. A
  // single match gets pointBounds' small pad rather than a degenerate
  // zero-area box — same call SightingFormPage makes for one point.
  const bounds = useMemo(() => {
    if (plottable.length === 0) return null;
    if (plottable.length === 1) return pointBounds(plottable[0].geometry.coordinates);
    return positionsBounds(plottable.map((s) => s.geometry.coordinates));
  }, [plottable]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, SIGHTINGS_SOURCE, {
      type: "FeatureCollection",
      features: plottable,
    });
    // Same blue as a sighting on its own property's map (PropertyMapPage),
    // so a point means the same thing on both screens.
    ensureCircleLayer(map, "org-sightings-circle", SIGHTINGS_SOURCE, "#2f5fc9");
  }, [map, plottable]);

  const observed = (sighting: Sighting): string =>
    new Date(sighting.properties.observed_at).toLocaleDateString();

  const list = (
    <ul className="card-list">
      {filtered.map((sighting) => {
        const state = visibilityOf(sighting);
        const label = (
          <>
            <strong>
              {sighting.properties.species_detail.common_name}
              {/* Both states marked, not just the exception — see
                  ActivitiesPage's row comment. A sighting's property is
                  nullable and the public site serves sightings only per
                  property, so one with no property reads "Not public":
                  true, and not the same fact as "Private". */}
              {propertyVisibility != null && state && (
                <span className={visibilityBadgeClass(state)}>{visibilityLabel(state)}</span>
              )}
            </strong>
            <span className="muted">
              {propertyName(sighting.properties.property)} — {observed(sighting)}
            </span>
          </>
        );
        // A sighting can have no property (it's a nullable FK), and the
        // edit form lives at /properties/:id/sightings/:id/edit — so
        // there's nowhere to link one that isn't on a property. Render
        // it as a plain row rather than a dead link, the same way
        // DashboardPage handles the case.
        return sighting.properties.property != null ? (
          <li key={sighting.id} className="card card--row">
            <Link
              to={withReturnTo(`/properties/${sighting.properties.property}/sightings/${sighting.id}/edit`, origin)}
              className="card__link"
            >
              {label}
            </Link>
          </li>
        ) : (
          <li key={sighting.id} className="card card--row">
            <div className="card__stack">{label}</div>
          </li>
        );
      })}
    </ul>
  );

  // No sightings at all (or still loading/failed): plain page, no map. A
  // 50vh map panel showing nothing but basemap would crowd out the empty
  // state's "log your first one" call to action, and on a failed load it
  // would sit there implying the org genuinely has no sightings anywhere —
  // which is the exact misattribution D21 fixed elsewhere in this app.
  if (loading || error || all.length === 0) {
    return (
      <div className="page">
        <div className="page__header">
          <h1>Sightings</h1>
        </div>
        <p className="muted">Every sighting across your properties. Select one to view or edit it.</p>

        {loading && <p className="muted">Loading…</p>}
        {error && <LoadError what="sightings" error={error} onRetry={reload} />}

        {!loading && !error && (
          <div className="empty-state">
            {/* The prose follows the gate for the same reason the button
                does: "Log one from a property's page" is an instruction, and a viewer has no way to
                follow either route. Swept across all four empty states
                rather than fixed only where it was noticed — D25 fixing
                one of three quick-log links and recording the class as
                closed is exactly what produced D76. */}
            <p>
              {canEdit
                ? "No sightings yet. Log one from a property's page, or use Quick log."
                : "No sightings to show yet."}
            </p>
            {/* Gated on editor+ (D76, 2026-09-29) — the twin of
                ActivitiesPage's, and the same reasoning: this renders
                only when the list is empty, so it landed on a member
                invited before much had been logged. The flow itself
                (QuickLogPage) now refuses a viewer as well, so this is
                about not offering work that ends in a refusal. */}
            {canEdit && (
              <Link to="/quick-log" className="btn btn-primary">
                ⊕ Quick log
              </Link>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="page page--map">
      <div className="page__header">
        <h1>Sightings</h1>
      </div>

      <div className="map-panel">
        <MapCanvas onReady={setMap} bounds={bounds} />
      </div>

      <div className="map-page-scroll">
        <div className="list-page-body">
          {/* Above the controls, same reasoning as ActivitiesPage: the line
              answering "what of ours is public?" shouldn't sit below a
              stack of filter fields on a phone. */}
          {propertyVisibility != null && (
            <>
              <p className="muted">{publicCountSummary(counts, SIGHTING_NOUN)}</p>
              {wouldPublishSummary(counts, SIGHTING_NOUN) && (
                <p className="muted">{wouldPublishSummary(counts, SIGHTING_NOUN)}</p>
              )}
            </>
          )}
          {properties.error && (
            <p className="muted">
              Couldn't load your properties, so public/private status isn't shown here.
            </p>
          )}

          <label className="field">
            <span>Search</span>
            <input
              type="search"
              placeholder="Filter by species or notes…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </label>
          <div className="filter-selects">
            {/* Same gate as ActivitiesPage: with one property this control
                could only say "All" or the same thing again. The "No
                property" option is offered whenever any sighting actually
                has none, independently of the count — a sighting dropped
                outside every boundary is otherwise findable only by
                scrolling. */}
            {((properties.data?.features.length ?? 0) > 1 ||
              all.some((s) => s.properties.property == null)) && (
              <label className="field">
                <span>Property</span>
                <select value={propertyFilter} onChange={(e) => setPropertyFilter(e.target.value)}>
                  <option value="all">All properties</option>
                  {/* Server order — alphabetical by name as of D70. */}
                  {properties.data?.features.map((p) => (
                    <option key={p.id} value={String(p.id)}>
                      {p.properties.name}
                    </option>
                  ))}
                  {all.some((s) => s.properties.property == null) && (
                    <option value="none">No property</option>
                  )}
                </select>
              </label>
            )}
            <label className="field">
              <span>Visibility</span>
              <select
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as VisibilityFilter)}
              >
                <option value="all">All</option>
                <option value="public">On the public site</option>
                <option value="not-public">Not on the public site</option>
              </select>
            </label>
          </div>

          {/* The unfiltered line has a singular case and the plural wording
              reads as broken in it ("All 1 sightings are plotted"), which is
              the state a brand-new account is actually in — so it is the
              first thing many users would see here, not an edge case.
              "Search to narrow them down" is dropped there too: there is
              nothing to narrow. The filtered line needs no such split —
              "Showing 1 of 4" is already correct. Keyed on `narrowed`, not
              on the search box alone: with the Visibility select set, "All
              N sightings are plotted" would be false. */}
          <p className="muted">
            {narrowed
              ? `Showing ${filtered.length} of ${all.length}, plotted on the map above.`
              : all.length === 1
                ? "Your only sighting is plotted on the map above."
                : `All ${all.length} sightings are plotted on the map above. Search to narrow them down.`}
          </p>

          {list}

          {filtered.length === 0 && (
            <p className="muted">
              {filter.trim() ? `No sightings match "${filter}".` : "No sightings match these filters."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
