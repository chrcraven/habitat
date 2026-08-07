import type {
  Activity,
  ActivityType,
  FeatureCollection,
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

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!SAFE_METHODS.has(method)) {
    // Django's CSRF check needs this on every unsafe request; the cookie
    // is set by GET /auth/csrf/, called once on app start (see
    // AuthContext). See backend/apps/accounts/views.py's module docstring.
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) headers.set("X-CSRFToken", csrfToken);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
  });

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

const withQuery = (path: string, params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `${path}?${qs}` : path;
};

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
  },

  species: {
    list: () => request<Species[]>("/species/"),
    create: (data: { common_name: string; scientific_name?: string; notes?: string }) =>
      request<Species>("/species/", { method: "POST", body: JSON.stringify(data) }),
  },

  workflowStates: {
    list: () => request<WorkflowState[]>("/workflow-states/"),
  },

  activities: {
    list: (propertyId?: number) =>
      request<FeatureCollection<Activity>>(withQuery("/activities/", { property: propertyId })),
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
  },

  sightings: {
    list: (propertyId?: number) =>
      request<FeatureCollection<Sighting>>(withQuery("/sightings/", { property: propertyId })),
    create: (data: {
      property?: number | null;
      species: number;
      location: PointGeometry;
      observed_at: string;
      notes?: string;
      is_public?: boolean;
    }) => request<Sighting>("/sightings/", { method: "POST", body: JSON.stringify(data) }),
  },
};
