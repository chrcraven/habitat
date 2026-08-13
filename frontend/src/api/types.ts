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
  date_planned: string | null;
  date_done: string | null;
  notes: string;
  is_public: boolean;
  species_names: string[];
  created_at: string;
  updated_at: string;
}
export type Activity = Feature<PolygonGeometry, ActivityFields>;

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
