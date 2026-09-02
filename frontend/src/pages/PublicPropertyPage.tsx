import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import type { Map as MapLibreMap } from "maplibre-gl";
import MapCanvas from "../components/MapCanvas";
import PublicHeader from "../components/PublicHeader";
import PublicPageNav from "../components/PublicPageNav";
import PublicPageBody from "../components/PublicPageBody";
import PublicPhotoGrid from "../components/PublicPhotoGrid";
import ActivityStatusLegend from "../components/ActivityStatusLegend";
import {
  ensureActivityStatusLayers,
  ensureCircleLayer,
  ensureFillLayer,
  ensureLineLayer,
  setGeoJsonSource,
} from "../components/mapLayers";
import { api } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import { useFocusedListItem } from "../hooks/useFocusedListItem";
import { polygonBounds } from "../utils/geo";
import { publicHeaderImageUrl, publicThemeStyle } from "../utils/theme";
import type { PublicActivity, PublicSighting } from "../api/types";

const PROPERTY_SOURCE = "property-boundary";
const ACTIVITIES_SOURCE = "activities";
const SIGHTINGS_SOURCE = "sightings";

/** Same combined-row shape as PropertyMapPage's list — see that file's
 * comment. Kept as a separate type here rather than shared, same as the
 * rest of this page's relationship to PropertyMapPage (visually modeled
 * on it but deliberately not sharing code, since the public page is
 * read-only and has no role-gated actions). Uses the Public* feature
 * types (not plain Activity/Sighting) since they carry each record's
 * linked_sighting_ids/linked_activity_ids — see below. */
type CombinedItem =
  | { key: string; kind: "activity"; id: number; sortDate: string | null; data: PublicActivity }
  | { key: string; kind: "sighting"; id: number; sortDate: string | null; data: PublicSighting };

/**
 * The per-property public page — the other of the two public-site shapes
 * requested (see PublicOrganizationPage for the org-portfolio one). Read
 * only: no edit/delete controls, no FABs, no private-records toggle
 * (there's nothing to toggle — the public API only ever returns
 * is_public=true records in the first place, see
 * backend/apps/public_site/views.py). Visually modeled on
 * PropertyMapPage, including its combined activity/sighting list and
 * scroll-to-focus map selection — the map-visibility pin/clear controls
 * are a client-only viewing preference, so they're offered here too even
 * though nothing else on this page is interactive.
 *
 * This is also the built-in **Explore** page in the "public site
 * storytelling" feature (see /docs/open-questions.md) — a property can
 * author its own pages and pick one as the landing page instead, in which
 * case this same component renders that page's content at the URL root,
 * with Explore (the map + record list below) still reachable via the
 * page nav / `/explore`. `forcePage="explore"` (passed by the `/explore`
 * route in App.tsx) always shows Explore regardless of the landing-page
 * pick.
 */
export default function PublicPropertyPage({ forcePage }: { forcePage?: "explore" }) {
  // Reachable via both the vanity-slug route (/public/:orgSlug/:propertySlug)
  // and the legacy numeric route (/public/properties/:propertyId), plus the
  // authored-page routes (/public/:orgSlug/:propertySlug/pages/:pageSlug,
  // .../explore). The slug route doesn't carry the numeric id, so we
  // resolve the property first (its response includes the id) and drive
  // the activity/sighting/photo sub-resources — which stay numeric — off
  // that. See App.tsx.
  const { orgSlug, propertySlug, propertyId, pageSlug: routePageSlug } = useParams<{
    orgSlug?: string;
    propertySlug?: string;
    propertyId?: string;
    pageSlug?: string;
  }>();
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const property = useAsync(
    () =>
      orgSlug && propertySlug
        ? api.public.propertyBySlug(orgSlug, propertySlug)
        : api.public.property(Number(propertyId)),
    [orgSlug, propertySlug, propertyId],
  );
  const id = property.data?.id ?? null;

  // Which page to actually show, most-specific first: an explicit
  // /pages/:slug route, then an explicit /explore route, then this
  // property's own landing-page pick (null = Explore, the map/list
  // below). See /docs/open-questions.md, "Public site storytelling /
  // custom content".
  const activeSlug =
    routePageSlug ?? (forcePage === "explore" ? null : property.data?.landing_page_slug ?? null);
  const resolvedOrgSlug = property.data?.organization.slug ?? orgSlug;
  const resolvedPropertySlug = property.data?.properties.slug ?? propertySlug;
  const authoredPage = useAsync(
    () =>
      activeSlug && resolvedOrgSlug && resolvedPropertySlug
        ? api.public.propertyPage(resolvedOrgSlug, resolvedPropertySlug, activeSlug)
        : Promise.resolve(null),
    [resolvedOrgSlug, resolvedPropertySlug, activeSlug],
  );

  const emptyCollection = <T,>() =>
    Promise.resolve({ type: "FeatureCollection" as const, features: [] as T[] });
  const activities = useAsync(
    () => (id != null ? api.public.activities(id) : emptyCollection<PublicActivity>()),
    [id],
  );
  const sightings = useAsync(
    () => (id != null ? api.public.sightings(id) : emptyCollection<PublicSighting>()),
    [id],
  );

  const bounds = useMemo(
    () => (property.data?.geometry ? polygonBounds(property.data.geometry) : null),
    [property.data],
  );

  const combinedItems = useMemo<CombinedItem[]>(() => {
    const activityItems: CombinedItem[] = (activities.data?.features ?? []).map((a) => ({
      key: `activity-${a.id}`,
      kind: "activity",
      id: a.id,
      sortDate: a.properties.date_done ?? a.properties.date_planned,
      data: a,
    }));
    const sightingItems: CombinedItem[] = (sightings.data?.features ?? []).map((s) => ({
      key: `sighting-${s.id}`,
      kind: "sighting",
      id: s.id,
      sortDate: s.properties.observed_at,
      data: s,
    }));
    return [...activityItems, ...sightingItems].sort((a, b) => {
      if (!a.sortDate && !b.sortDate) return 0;
      if (!a.sortDate) return 1;
      if (!b.sortDate) return -1;
      return b.sortDate.localeCompare(a.sortDate);
    });
  }, [activities.data, sightings.data]);

  const itemIds = useMemo(() => combinedItems.map((item) => item.key), [combinedItems]);
  const { focusedId, registerItem } = useFocusedListItem(scrollContainerRef, itemIds);

  // Looked up by id to render each item's linked_sighting_ids/
  // linked_activity_ids as something readable (see property_activities/
  // property_sightings in backend/apps/public_site/views.py) — e.g.
  // "reported by a visitor, treated on this date" (docs/open-questions.md,
  // "Public-facing behavior"). Both lists only ever contain ids that are
  // themselves public, so every lookup here is guaranteed to resolve.
  const activityById = useMemo(() => {
    const map = new Map<number, PublicActivity>();
    (activities.data?.features ?? []).forEach((a) => map.set(a.id, a));
    return map;
  }, [activities.data]);
  const sightingById = useMemo(() => {
    const map = new Map<number, PublicSighting>();
    (sightings.data?.features ?? []).forEach((s) => map.set(s.id, s));
    return map;
  }, [sightings.data]);

  const shownIds = useMemo(() => {
    const next = new Set(pinnedIds);
    if (focusedId) next.add(focusedId);
    return next;
  }, [pinnedIds, focusedId]);

  const togglePinned = (key: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const visibleActivityFeatures = useMemo(
    () => (activities.data?.features ?? []).filter((a) => shownIds.has(`activity-${a.id}`)),
    [activities.data, shownIds],
  );
  const visibleSightingFeatures = useMemo(
    () => (sightings.data?.features ?? []).filter((s) => shownIds.has(`sighting-${s.id}`)),
    [sightings.data, shownIds],
  );

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(
      map,
      PROPERTY_SOURCE,
      property.data?.geometry ?? { type: "Polygon", coordinates: [] },
    );
    ensureFillLayer(map, "property-boundary-fill", PROPERTY_SOURCE, "#2f6f4f", 0.08);
    ensureLineLayer(map, "property-boundary-line", PROPERTY_SOURCE, "#2f6f4f", 2);
  }, [map, property.data]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, ACTIVITIES_SOURCE, {
      type: "FeatureCollection",
      features: visibleActivityFeatures,
    });
    ensureActivityStatusLayers(map, ACTIVITIES_SOURCE);
  }, [map, visibleActivityFeatures]);

  useEffect(() => {
    if (!map) return;
    setGeoJsonSource(map, SIGHTINGS_SOURCE, {
      type: "FeatureCollection",
      features: visibleSightingFeatures,
    });
    ensureCircleLayer(map, "sightings-circle", SIGHTINGS_SOURCE, "#2f5fc9");
  }, [map, visibleSightingFeatures]);

  const loading = activities.loading || sightings.loading;

  if (property.loading) {
    return (
      <div className="app-shell app-shell--public">
        <PublicHeader />
        <main className="app-main">
          <div className="full-page-status">Loading…</div>
        </main>
      </div>
    );
  }

  if (property.error || !property.data) {
    return (
      <div className="app-shell app-shell--public">
        <PublicHeader />
        <main className="app-main">
          <p className="form-error" style={{ padding: "1rem" }}>
            This property isn't public, or doesn't exist.
          </p>
        </main>
      </div>
    );
  }

  const headerImageUrl = publicHeaderImageUrl(
    { id: property.data.id, has_theme_header_image: property.data.properties.has_theme_header_image },
    "property",
    property.data.organization,
  );

  return (
    <div
      className="app-shell app-shell--public"
      style={publicThemeStyle(property.data.properties, property.data.organization)}
    >
      <PublicHeader
        back={{
          to: `/public/${property.data.organization.slug}`,
          label: `← ${property.data.organization.name}`,
        }}
      />
      <main className="app-main">
        {activeSlug ? (
          <div className="page page--public">
            {/* Only shown on an authored page, not the Explore/map view
                below — .page--map is a fixed-height split-scroll layout
                (see its own comment further down) that a banner image
                would need real layout rework to fit above cleanly, out of
                scope for this pass. */}
            {headerImageUrl && <img src={headerImageUrl} alt="" className="public-header-image" />}
            <div className="page__header">
              <h1>{property.data.properties.name}</h1>
            </div>
            {property.data.pages.length > 0 && (
              <PublicPageNav
                basePath={`/public/${property.data.organization.slug}/${property.data.properties.slug}`}
                pages={property.data.pages}
                activeSlug={activeSlug}
              />
            )}
            {authoredPage.loading && <p className="muted">Loading…</p>}
            {(authoredPage.error || (!authoredPage.loading && !authoredPage.data)) && (
              <p className="form-error">Couldn't load this page.</p>
            )}
            {authoredPage.data && <PublicPageBody page={authoredPage.data} />}
          </div>
        ) : (
        <div className="page page--map">
          <div className="page__header">
            <h1>{property.data.properties.name}</h1>
          </div>
          {property.data.pages.length > 0 && (
            <PublicPageNav
              basePath={`/public/${property.data.organization.slug}/${property.data.properties.slug}`}
              pages={property.data.pages}
              activeSlug={activeSlug}
            />
          )}

          <div className="map-panel">
            <MapCanvas onReady={setMap} bounds={bounds} />
            <ActivityStatusLegend />
          </div>

          <div className="map-page-scroll" ref={scrollContainerRef}>
          <p className="muted map-selection-hint">
            Showing {shownIds.size} of {combinedItems.length} on the map — scroll to bring one
            into focus (highlighted below), or tap a card to pin more at once.
          </p>

          <div className="record-list">
            <div className="page__header">
              <h2>Activities &amp; sightings</h2>
              {pinnedIds.size > 0 && (
                <div className="card__actions">
                  <button
                    type="button"
                    className="btn btn-ghost btn-small"
                    onClick={() => setPinnedIds(new Set())}
                  >
                    Clear all
                  </button>
                </div>
              )}
            </div>
            {loading && <p className="muted">Loading…</p>}
            {!loading && combinedItems.length === 0 && (
              <p className="muted">Nothing to show yet.</p>
            )}
            <ul className="card-list">
              {combinedItems.map((item) => {
                const isFocused = focusedId === item.key;
                const isPinned = pinnedIds.has(item.key);
                const label =
                  item.kind === "activity"
                    ? item.data.properties.activity_type
                    : item.data.properties.species_detail.common_name;
                return (
                  <li
                    key={item.key}
                    ref={registerItem(item.key)}
                    data-item-id={item.key}
                    className={`card card--pinnable${isFocused ? " card--focused" : ""}${
                      isPinned ? " card--pinned" : ""
                    }`}
                    tabIndex={0}
                    aria-label={`${isPinned ? "Unpin" : "Pin"} ${label} ${
                      isPinned ? "from" : "to"
                    } the map`}
                    onClick={() => togglePinned(item.key)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        togglePinned(item.key);
                      }
                    }}
                  >
                    <div className="card__row">
                      <div className="card__main">
                        <div>
                          <span className={`type-badge type-badge--${item.kind}`}>
                            {item.kind === "activity" ? "Activity" : "Sighting"}
                          </span>
                          {item.kind === "activity" ? (
                            <>
                              <strong>{item.data.properties.activity_type}</strong>
                              <span className="muted"> — {item.data.properties.status_name}</span>
                            </>
                          ) : (
                            <strong>{item.data.properties.species_detail.common_name}</strong>
                          )}
                          {isPinned && <span className="badge badge--pin">📌 Pinned</span>}
                        </div>
                      </div>
                    </div>
                    {item.kind === "activity" ? (
                      <>
                        {item.data.properties.date_planned && (
                          <span className="muted">Planned: {item.data.properties.date_planned}</span>
                        )}
                        {item.data.properties.date_done && (
                          <span className="muted">Done: {item.data.properties.date_done}</span>
                        )}
                      </>
                    ) : (
                      <span className="muted">
                        {new Date(item.data.properties.observed_at).toLocaleDateString()}
                      </span>
                    )}
                    {item.data.properties.notes && <p>{item.data.properties.notes}</p>}
                    {item.kind === "activity" && item.data.properties.linked_sighting_ids.length > 0 && (
                      <p className="muted">
                        Reported sightings:{" "}
                        {item.data.properties.linked_sighting_ids
                          .map((sightingId) => sightingById.get(sightingId))
                          .filter((s): s is PublicSighting => Boolean(s))
                          .map((s) => s.properties.species_detail.common_name)
                          .join(", ")}
                      </p>
                    )}
                    {item.kind === "sighting" && item.data.properties.linked_activity_ids.length > 0 && (
                      <p className="muted">
                        Treated by:{" "}
                        {item.data.properties.linked_activity_ids
                          .map((activityId) => activityById.get(activityId))
                          .filter((a): a is PublicActivity => Boolean(a))
                          .map(
                            (a) =>
                              `${a.properties.activity_type}${
                                a.properties.date_done ? ` (${a.properties.date_done})` : ""
                              }`,
                          )
                          .join(", ")}
                      </p>
                    )}
                    <PublicPhotoGrid
                      kind={item.kind}
                      id={item.id}
                    />
                  </li>
                );
              })}
            </ul>
          </div>
          </div>
        </div>
        )}
      </main>
    </div>
  );
}
