/**
 * Shapes returned by the Phase 1 API (see backend/apps, each app's
 * serializers.py). Geometry fields come back as GeoJSON (see
 * rest_framework_gis's GeoFeatureModelSerializer) — plain [lng, lat]
 * tuples, EPSG:4326, matching what MapLibre expects directly.
 */

export type Position = [number, number];

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: Position[][];
}

export interface PointGeometry {
  type: "Point";
  coordinates: Position;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Organization {
  id: number;
  name: string;
  // Vanity slug for the org's public URL (`/public/<slug>`). Always
  // present on a persisted org (auto-generated from the name); admin can
  // override it in the org admin portal. See /docs/open-questions.md.
  slug: string;
  created_at: string;
}

export type Role = "admin" | "editor" | "viewer";

export interface Membership {
  id: number;
  organization: Organization;
  role: Role;
}

export interface Session {
  user: User;
  membership: Membership | null;
}

/** A GeoJSON Feature as GeoFeatureModelSerializer emits it: id/geometry at
 * the top level, everything else nested under `properties`. */
export interface Feature<G, P> {
  id: number;
  type: "Feature";
  geometry: G | null;
  properties: P;
}

export interface FeatureCollection<F> {
  type: "FeatureCollection";
  features: F[];
}

export interface PropertyFields {
  name: string;
  // Vanity sub-slug under the org's slug (`/public/<org-slug>/<slug>`),
  // unique within the org. Auto-generated from the name; admin-editable on
  // the property form. See /docs/open-questions.md ("Vanity slug URLs").
  slug: string;
  is_public: boolean;
  // Per-property default for a *new* sighting's own is_public flag — see
  // Property.sightings_public_by_default's docstring in the backend
  // model. SightingFormPage seeds its own checkbox from this for a
  // brand-new sighting on this property.
  sightings_public_by_default: boolean;
  created_at: string;
  updated_at: string;
}
export type Property = Feature<PolygonGeometry, PropertyFields>;

export interface Species {
  id: number;
  common_name: string;
  scientific_name: string;
  notes: string;
  created_at: string;
}

export interface WorkflowState {
  id: number;
  name: string;
  is_planned: boolean;
  is_done: boolean;
  order: number;
}

export type ActivityType =
  | "seeding"
  | "planting"
  | "treatment"
  | "removal"
  | "monitoring"
  | "maintenance"
  | "intervention"
  | "other";

export interface ActivityFields {
  property: number;
  activity_type: ActivityType;
  status: number;
  status_name: string;
  is_done: boolean;
  date_planned: string | null;
  date_done: string | null;
  notes: string;
  is_public: boolean;
  species_names: string[];
  created_at: string;
  updated_at: string;
}
export type Activity = Feature<PolygonGeometry, ActivityFields>;

/** The public property page's activity feature — same fields as the
 * authenticated Activity, plus which of this property's public sightings
 * this activity is linked to (see backend/apps/public_site/views.py's
 * property_activities — only links where the *other* side is also public
 * are ever included, so a public visitor can't infer the existence of a
 * private sighting this way). Empty rather than omitted when there are no
 * (visible) links. */
export type PublicActivity = Feature<
  PolygonGeometry,
  ActivityFields & { linked_sighting_ids: number[] }
>;

export type ActivitySpeciesRole = "planted" | "treated_target" | "other";

/** The Activity↔Species through-model (role/quantity/detail per species —
 * see backend/apps/activities/models.py's ActivitySpecies), surfaced via
 * /api/activities/<id>/species/ rather than as a writable field on
 * `Activity` itself (Django M2M `.set()` doesn't work against a custom
 * `through` model). `Activity.species_names` stays a read-only summary of
 * the same relationship for display where the full detail isn't needed. */
export interface ActivitySpeciesLink {
  id: number;
  activity: number;
  species: number;
  species_name: string;
  role: ActivitySpeciesRole | "";
  quantity: number | null;
  detail: string;
}

export interface SightingFields {
  property: number | null;
  species: number;
  species_detail: Species;
  observed_at: string;
  notes: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}
export type Sighting = Feature<PointGeometry, SightingFields>;

/** The public property page's sighting feature — mirror of PublicActivity
 * above, but for which public activities this sighting is linked to
 * (e.g. "reported by a visitor, treated on this date" — see
 * /docs/open-questions.md, "Public-facing behavior"). */
export type PublicSighting = Feature<
  PointGeometry,
  SightingFields & { linked_activity_ids: number[] }
>;

export interface Photo {
  id: number;
  /** Absolute URL to the raw image bytes — use directly as an <img src>.
   * Session-cookie authenticated, same as any other endpoint (see
   * backend/apps/activities/views.py's activity_photo_image docstring). */
  url: string;
  content_type: string;
  captured_at: string | null;
  uploaded_at: string;
}

/** One row in the org admin portal's member list — see
 * backend/apps/accounts/serializers.py's MembershipDetailSerializer.
 * Distinct from the plain Membership used in Session (that one only needs
 * the caller's own role; this needs the full roster + property scope). */
export interface MembershipDetail {
  id: number;
  user: User;
  role: Role;
  properties: number[];
  property_names: string[];
  created_at: string;
}

/** A pending, not-yet-accepted org invite — see
 * backend/apps/accounts/serializers.py's InvitationSerializer.
 * `accept_url` is always present (not just when email delivery works) so
 * the org admin portal can show/copy it as a fallback — see
 * backend/apps/accounts/invitations.py. */
export interface Invitation {
  id: number;
  email: string;
  role: Role;
  property_names: string[];
  invited_by_email: string | null;
  accept_url: string;
  created_at: string;
  is_expired: boolean;
}

/** What POST /invitations/:token/ returns for the (unauthenticated)
 * accept-invite page to greet the invitee with before showing the form. */
export interface InvitationPreview {
  email: string;
  organization_name: string;
  role: Role;
}

/** The public (unauthenticated) org portfolio page's response shape —
 * see backend/apps/public_site/views.py#organization_detail. */
export interface PublicOrganization {
  organization: Organization;
  properties: FeatureCollection<Property>;
}

/** The public property detail page's response — a Property Feature with
 * an extra `organization` key for the "back to org" link. */
export type PublicProperty = Property & { organization: Organization };

/** The direct Sighting↔Activity link (see
 * backend/apps/sightings/models.py's SightingActivityLink) — surfaced
 * from both the sighting's and the activity's edit page, same shape
 * either way (see backend/apps/sightings/serializers.py). */
export interface SightingActivityLink {
  id: number;
  sighting: number;
  activity: number;
  activity_type: ActivityType;
  activity_property_name: string;
  sighting_species: string;
  sighting_observed_at: string;
  linked_at: string;
}

export type TaskStatus = "open" | "assigned" | "resolved" | "dismissed";

export interface Task {
  id: number;
  title: string;
  description: string;
  origin_sighting: number | null;
  origin_sighting_species: string | null;
  origin_activity: number | null;
  origin_activity_type: ActivityType | null;
  assigned_to: number | null;
  assigned_to_email: string | null;
  status: TaskStatus;
  created_by: number | null;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
}
