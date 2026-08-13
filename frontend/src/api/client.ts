import type {
  Activity,
  ActivityType,
  FeatureCollection,
  Photo,
  PointGeometry,
  PolygonGeometry,
  Property,
  Session,
  Sighting,
  Species,
  WorkflowState,
} from "./types";

// No separate deployed frontend origin yet beyond local dev (see
// backend/config/settings.py CORS_ALLOWED_ORIGINS) — override with
// VITE_API_URL for anything else (staging, a phone on the LAN, etc.).
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/[.$?*|{}()[\]\\/+^]/g, "\\$&") + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

function csrfHeaders(method: string): HeadersInit {
  if (SAFE_METHODS.has(method)) return {};
  // Django's CSRF check needs this on every unsafe request; the cookie is
  // set by GET /auth/csrf/, called once on app start (see AuthContext),
  // and read fresh here on every call rather than cached — login/signup
  // rotate it server-side. See backend/apps/accounts/views.py.
  const csrfToken = getCookie("csrftoken");
  return csrfToken ? { "X-CSRFToken": csrfToken } : {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await response.json() : undefined;

  if (!response.ok) {
    const message =
      (body && (body.detail || JSON.stringify(body))) || response.statusText;
    throw new ApiError(message, response.status);
  }
  return body as T;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  for (const [key, value] of Object.entries(csrfHeaders(method))) {
    headers.set(key, value);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });
  return handleResponse<T>(response);
}

/** Multipart upload (photos) — deliberately NOT routed through `request`,
 * which always sets a JSON Content-Type: the browser needs to set its own
 * multipart boundary, so no Content-Type header can be set here at all. */
async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("image", file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: new Headers(csrfHeaders("POST")),
    credentials: "include",
    body: formData,
  });
  return handleResponse<T>(response);
}

const withQuery = (
  path: string,
  params: Record<string, string | number | boolean | undefined>,
) => {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `${path}?${qs}` : path;
};

interface ListFilter {
  /** Omit for everything; true/false to match the app's own is_public
   * flag. The frontend's default record view passes `true` (public-only,
   * per the requested default) with a toggle to pass nothing (see
   * PropertyMapPage). This is unrelated to the unauthenticated Phase-2
   * public page — every value here still requires being logged into the
   * org. */
  isPublic?: boolean;
}

export const api = {
  auth: {
    csrf: () => request<{ detail: string }>("/auth/csrf/"),
    signup: (data: {
      email: string;
      password: string;
      organization_name?: string;
      first_name?: string;
      last_name?: string;
    }) => request<Session>("/auth/signup/", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<Session>("/auth/login/", { method: "POST", body: JSON.stringify(data) }),
    logout: () => request<void>("/auth/logout/", { method: "POST" }),
    me: () => request<Session>("/auth/me/"),
  },

  properties: {
    list: () => request<FeatureCollection<Property>>("/properties/"),
    get: (id: number) => request<Property>(`/properties/${id}/`),
    create: (data: { name: string; boundary?: PolygonGeometry | null }) =>
      request<Property>("/properties/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<{ name: string; boundary: PolygonGeometry | null }>) =>
      request<Property>(`/properties/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/properties/${id}/`, { method: "DELETE" }),
  },

  species: {
    list: () => request<Species[]>("/species/"),
    create: (data: { common_name: string; scientific_name?: string; notes?: string }) =>
      request<Species>("/species/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{ common_name: string; scientific_name: string; notes: string }>,
    ) => request<Species>(`/species/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/species/${id}/`, { method: "DELETE" }),
  },

  workflowStates: {
    list: () => request<WorkflowState[]>("/workflow-states/"),
  },

  activities: {
    list: (propertyId?: number, filter: ListFilter = {}) =>
      request<FeatureCollection<Activity>>(
        withQuery("/activities/", { property: propertyId, is_public: filter.isPublic }),
      ),
    get: (id: number) => request<Activity>(`/activities/${id}/`),
    create: (data: {
      property: number;
      activity_type: ActivityType;
      status: number;
      geometry: PolygonGeometry;
      date_planned?: string | null;
      date_done?: string | null;
      notes?: string;
      is_public?: boolean;
    }) => request<Activity>("/activities/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{
        activity_type: ActivityType;
        status: number;
        geometry: PolygonGeometry;
        date_planned: string | null;
        date_done: string | null;
        notes: string;
        is_public: boolean;
      }>,
    ) => request<Activity>(`/activities/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/activities/${id}/`, { method: "DELETE" }),
    photos: {
      list: (activityId: number) => request<Photo[]>(`/activities/${activityId}/photos/`),
      upload: (activityId: number, file: File) =>
        uploadFile<Photo>(`/activities/${activityId}/photos/`, file),
      remove: (activityId: number, photoId: number) =>
        request<void>(`/activities/${activityId}/photos/${photoId}/`, { method: "DELETE" }),
    },
  },

  sightings: {
    list: (propertyId?: number, filter: ListFilter = {}) =>
      request<FeatureCollection<Sighting>>(
        withQuery("/sightings/", { property: propertyId, is_public: filter.isPublic }),
      ),
    get: (id: number) => request<Sighting>(`/sightings/${id}/`),
    create: (data: {
      property?: number | null;
      species: number;
      location: PointGeometry;
      observed_at: string;
      notes?: string;
      is_public?: boolean;
    }) => request<Sighting>("/sightings/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{
        species: number;
        location: PointGeometry;
        observed_at: string;
        notes: string;
        is_public: boolean;
      }>,
    ) => request<Sighting>(`/sightings/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/sightings/${id}/`, { method: "DELETE" }),
    photos: {
      list: (sightingId: number) => request<Photo[]>(`/sightings/${sightingId}/photos/`),
      upload: (sightingId: number, file: File) =>
        uploadFile<Photo>(`/sightings/${sightingId}/photos/`, file),
      remove: (sightingId: number, photoId: number) =>
        request<void>(`/sightings/${sightingId}/photos/${photoId}/`, { method: "DELETE" }),
    },
  },
};
