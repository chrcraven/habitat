import { publicSiteUrl } from "../utils/publicSite";
import type {
  Activity,
  ActivitySpeciesLink,
  ActivitySpeciesRole,
  ActivityType,
  DeletedProperty,
  FeatureCollection,
  Feedback,
  Invitation,
  InvitationPreview,
  MembershipDetail,
  Notification,
  Organization,
  Page,
  PageContentFormat,
  Photo,
  PointGeometry,
  PolygonGeometry,
  Property,
  PublicActivity,
  PublicOrganization,
  PublicPage,
  PublicProperty,
  PublicSighting,
  Role,
  Session,
  Sighting,
  SightingActivityLink,
  Species,
  Task,
  TaskStatus,
  ThemeFont,
  WorkflowState,
} from "./types";

// No separate deployed frontend origin yet beyond local dev (see
// backend/config/settings.py CORS_ALLOWED_ORIGINS) — override with
// VITE_API_URL for anything else (staging, a phone on the LAN, etc.).
// Exported so a plain <img src> (theme header images — see
// utils/theme.ts) can point straight at a public endpoint without going
// through `request`/fetch itself.
export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

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

/** POST a FormData and get raw bytes back (the QR-code endpoints return an
 * image/png, not JSON). Throws ApiError with the endpoint's detail message
 * on a non-2xx, same contract as `request`. */
async function postForBlob(path: string, formData: FormData): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: new Headers(csrfHeaders("POST")),
    credentials: "include",
    body: formData,
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || JSON.stringify(body);
    } catch {
      /* non-JSON error body; keep statusText */
    }
    throw new ApiError(message, response.status);
  }
  return response.blob();
}

/** Builds the FormData every QR endpoint takes: the public site's origin
 * plus an optional center-logo image. The backend prefers its own
 * PUBLIC_SITE_URL when the public site has an origin of its own and only
 * falls back to this, but it can't infer the same-origin case (the SPA is
 * on a different origin from the API), so it's still sent. */
function qrForm(logo?: File | null): FormData {
  const form = new FormData();
  form.append("base_url", publicSiteUrl(""));
  if (logo) form.append("logo", logo);
  return form;
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
    changePassword: (data: { current_password: string; new_password: string }) =>
      request<{ detail: string }>("/auth/change-password/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    /** "Forgot password" — always resolves with the same generic message
     * regardless of whether the email has an account (see
     * backend/apps/accounts/views.py#password_reset_request), so the
     * frontend should show that message as-is rather than branching on
     * success/failure. */
    requestPasswordReset: (data: { email: string }) =>
      request<{ detail: string }>("/auth/password-reset/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    confirmPasswordReset: (data: { token: string; new_password: string }) =>
      request<Session>("/auth/password-reset/confirm/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  /** The (unauthenticated) org-invite accept flow — see
   * backend/apps/accounts/views.py#invitation_detail/invitation_accept.
   * Distinct from `org.invitations` below, which is the admin-only
   * management side (list/revoke) of the *same* Invitation model. */
  invitations: {
    get: (token: string) => request<InvitationPreview>(`/invitations/${token}/`),
    accept: (
      token: string,
      data: { password: string; first_name?: string; last_name?: string },
    ) =>
      request<Session>(`/invitations/${token}/accept/`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  org: {
    get: () => request<Organization>("/org/"),
    update: (
      data: Partial<{
        name: string;
        slug: string;
        landing_page: number | null;
        theme_primary_color: string;
        theme_background_color: string;
        theme_accent_color: string;
        theme_font: ThemeFont;
      }>,
    ) => request<Organization>("/org/", { method: "PATCH", body: JSON.stringify(data) }),
    /** PNG QR code pointing at this org's public portfolio page. Pass a
     * logo File to embed it in the center. */
    qrCode: (logo?: File | null) => postForBlob("/org/qr/", qrForm(logo)),
    /** The org's public-site theme header banner image (see
     * backend/apps/accounts/theming.py) — `previewUrl` is a plain
     * session-authenticated <img src> (same "same-site cookies just
     * work" convention as an activity/sighting photo — see
     * PhotoUploader), so it renders even for admin preview; the actual
     * public-site rendering uses the unauthenticated equivalent instead
     * (see utils/theme.ts#publicHeaderImageUrl). */
    themeImage: {
      previewUrl: `${API_BASE}/org/theme-image/`,
      upload: (file: File) => uploadFile<Organization>("/org/theme-image/", file),
      remove: () => request<void>("/org/theme-image/", { method: "DELETE" }),
    },
    members: {
      list: () => request<MembershipDetail[]>("/org/members/"),
      /** Attaches an existing Habitat user to this org immediately (returns
       * a MembershipDetail), or — for a brand-new email — creates a
       * pending Invitation and emails an accept link instead (returns an
       * Invitation). Which one comes back is only used to decide what to
       * tell the admin; either way the members/invitations lists should
       * be reloaded. See backend/apps/accounts/views.py's
       * MembershipViewSet.create. */
      create: (data: {
        email: string;
        first_name?: string;
        last_name?: string;
        role: Role;
        properties?: number[];
      }) =>
        request<MembershipDetail | Invitation>("/org/members/", {
          method: "POST",
          body: JSON.stringify(data),
        }),
      update: (id: number, data: Partial<{ role: Role; properties: number[] }>) =>
        request<MembershipDetail>(`/org/members/${id}/`, {
          method: "PATCH",
          body: JSON.stringify(data),
        }),
      remove: (id: number) => request<void>(`/org/members/${id}/`, { method: "DELETE" }),
    },
    invitations: {
      list: () => request<Invitation[]>("/org/invitations/"),
      remove: (id: number) => request<void>(`/org/invitations/${id}/`, { method: "DELETE" }),
      resend: (id: number) =>
        request<Invitation>(`/org/invitations/${id}/resend/`, { method: "POST" }),
    },
  },

  /** Unauthenticated public-site endpoints (see
   * backend/apps/public_site) — no CSRF/credentials needed since these
   * are all reads with no session involved, but `request` sends
   * `credentials: "include"` regardless, which is harmless here. */
  public: {
    organization: (orgId: number) => request<PublicOrganization>(`/public/organizations/${orgId}/`),
    /** Vanity-slug entry point — `/public/<org-slug>`. */
    organizationBySlug: (orgSlug: string) =>
      request<PublicOrganization>(`/public/o/${encodeURIComponent(orgSlug)}/`),
    property: (propertyId: number) =>
      request<PublicProperty>(`/public/properties/${propertyId}/`),
    /** Vanity-slug entry point — `/public/<org-slug>/<property-slug>`. */
    propertyBySlug: (orgSlug: string, propertySlug: string) =>
      request<PublicProperty>(
        `/public/o/${encodeURIComponent(orgSlug)}/${encodeURIComponent(propertySlug)}/`,
      ),
    activities: (propertyId: number) =>
      request<FeatureCollection<PublicActivity>>(`/public/properties/${propertyId}/activities/`),
    sightings: (propertyId: number) =>
      request<FeatureCollection<PublicSighting>>(`/public/properties/${propertyId}/sightings/`),
    activityPhotos: (activityId: number) =>
      request<Photo[]>(`/public/activities/${activityId}/photos/`),
    sightingPhotos: (sightingId: number) =>
      request<Photo[]>(`/public/sightings/${sightingId}/photos/`),
    /** One of an org's own authored pages — see PublicOrganization.pages
     * for the nav-list shape this fetches the full content of. */
    organizationPage: (orgSlug: string, pageSlug: string) =>
      request<PublicPage>(
        `/public/o/${encodeURIComponent(orgSlug)}/pages/${encodeURIComponent(pageSlug)}/`,
      ),
    /** Mirror of organizationPage, for one property's own authored pages. */
    propertyPage: (orgSlug: string, propertySlug: string, pageSlug: string) =>
      request<PublicPage>(
        `/public/o/${encodeURIComponent(orgSlug)}/${encodeURIComponent(propertySlug)}/pages/${encodeURIComponent(pageSlug)}/`,
      ),
  },

  /** Authoring/management API for Page (see backend/apps/pages) —
   * distinct from `public.organizationPage`/`propertyPage` above, which
   * are the unauthenticated public-site reads. `list`/`create` without a
   * `propertyId` operate on this org's own org-level pages; pass one to
   * scope to that property's pages instead — see backend/apps/pages/
   * views.py's PageViewSet.get_queryset. */
  pages: {
    list: (propertyId?: number) =>
      request<Page[]>(withQuery("/pages/", { property: propertyId })),
    get: (id: number) => request<Page>(`/pages/${id}/`),
    create: (data: {
      property?: number | null;
      title: string;
      slug?: string;
      content_format?: PageContentFormat;
      body?: string;
      is_public?: boolean;
      position?: number;
    }) => request<Page>("/pages/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{
        title: string;
        slug: string;
        content_format: PageContentFormat;
        body: string;
        is_public: boolean;
        position: number;
      }>,
    ) => request<Page>(`/pages/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/pages/${id}/`, { method: "DELETE" }),
  },

  properties: {
    list: () => request<FeatureCollection<Property>>("/properties/"),
    get: (id: number) => request<Property>(`/properties/${id}/`),
    create: (data: {
      name: string;
      slug?: string;
      boundary?: PolygonGeometry | null;
      is_public?: boolean;
      sightings_public_by_default?: boolean;
    }) => request<Property>("/properties/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{
        name: string;
        slug: string;
        boundary: PolygonGeometry | null;
        is_public: boolean;
        sightings_public_by_default: boolean;
        landing_page: number | null;
        theme_primary_color: string;
        theme_background_color: string;
        theme_accent_color: string;
        theme_font: ThemeFont;
      }>,
    ) => request<Property>(`/properties/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    /** Soft delete — the property (and its activities/sightings) drops out
     * of every normal view immediately, but is recoverable via `restore`
     * for 30 days (see `deleted` below and backend/apps/accounts/
     * views.py's PropertyViewSet). */
    remove: (id: number) => request<void>(`/properties/${id}/`, { method: "DELETE" }),
    /** PNG QR code pointing at this property's public page. Pass a logo
     * File to embed it in the center. */
    qrCode: (id: number, logo?: File | null) =>
      postForBlob(`/properties/${id}/qr/`, qrForm(logo)),
    /** Mirror of `org.themeImage` above, for one property's own header
     * banner image. */
    themeImage: {
      previewUrl: (id: number) => `${API_BASE}/properties/${id}/theme-image/`,
      upload: (id: number, file: File) =>
        uploadFile<Property>(`/properties/${id}/theme-image/`, file),
      remove: (id: number) => request<void>(`/properties/${id}/theme-image/`, { method: "DELETE" }),
    },
    /** Admin-only "Recently deleted" list/restore — see the DELETE note
     * above. */
    deleted: {
      list: () => request<DeletedProperty[]>("/properties/deleted/"),
      restore: (id: number) =>
        request<Property>(`/properties/${id}/restore/`, { method: "POST" }),
    },
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
    links: {
      list: (activityId: number) =>
        request<SightingActivityLink[]>(`/activities/${activityId}/links/`),
      create: (activityId: number, sightingId: number) =>
        request<SightingActivityLink>(`/activities/${activityId}/links/`, {
          method: "POST",
          body: JSON.stringify({ sighting: sightingId }),
        }),
      remove: (activityId: number, linkId: number) =>
        request<void>(`/activities/${activityId}/links/${linkId}/`, { method: "DELETE" }),
    },
    species: {
      list: (activityId: number) =>
        request<ActivitySpeciesLink[]>(`/activities/${activityId}/species/`),
      create: (
        activityId: number,
        data: { species: number; role?: ActivitySpeciesRole | ""; quantity?: number | null; detail?: string },
      ) =>
        request<ActivitySpeciesLink>(`/activities/${activityId}/species/`, {
          method: "POST",
          body: JSON.stringify(data),
        }),
      update: (
        activityId: number,
        linkId: number,
        data: Partial<{ role: ActivitySpeciesRole | ""; quantity: number | null; detail: string }>,
      ) =>
        request<ActivitySpeciesLink>(`/activities/${activityId}/species/${linkId}/`, {
          method: "PATCH",
          body: JSON.stringify(data),
        }),
      remove: (activityId: number, linkId: number) =>
        request<void>(`/activities/${activityId}/species/${linkId}/`, { method: "DELETE" }),
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
    links: {
      list: (sightingId: number) =>
        request<SightingActivityLink[]>(`/sightings/${sightingId}/links/`),
      create: (sightingId: number, activityId: number) =>
        request<SightingActivityLink>(`/sightings/${sightingId}/links/`, {
          method: "POST",
          body: JSON.stringify({ activity: activityId }),
        }),
      remove: (sightingId: number, linkId: number) =>
        request<void>(`/sightings/${sightingId}/links/${linkId}/`, { method: "DELETE" }),
    },
  },

  tasks: {
    list: (filter: { status?: TaskStatus; assignedTo?: number } = {}) =>
      request<Task[]>(withQuery("/tasks/", { status: filter.status, assigned_to: filter.assignedTo })),
    get: (id: number) => request<Task>(`/tasks/${id}/`),
    create: (data: {
      title: string;
      description?: string;
      origin_sighting?: number | null;
      origin_activity?: number | null;
      assigned_to?: number | null;
      status?: TaskStatus;
    }) => request<Task>("/tasks/", { method: "POST", body: JSON.stringify(data) }),
    update: (
      id: number,
      data: Partial<{
        title: string;
        description: string;
        origin_sighting: number | null;
        origin_activity: number | null;
        assigned_to: number | null;
        status: TaskStatus;
      }>,
    ) => request<Task>(`/tasks/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: number) => request<void>(`/tasks/${id}/`, { method: "DELETE" }),
  },

  /** The current user's own in-app notifications — see
   * backend/apps/notifications. Scoped to the recipient, not an active
   * organization. */
  notifications: {
    list: () => request<Notification[]>("/notifications/"),
    markRead: (id: number) =>
      request<Notification>(`/notifications/${id}/read/`, { method: "POST" }),
    markAllRead: () => request<void>("/notifications/mark-all-read/", { method: "POST" }),
  },

  /** In-app feedback on Habitat itself — see backend/apps/feedback and
   * that app's module docstring for why this is separate from Phase 5
   * public input. The cross-org `pull`/`mark-synced` endpoints an external
   * routine uses aren't exposed here — they're bearer-token authenticated,
   * not something this session-cookie client ever calls. */
  feedback: {
    config: () => request<{ enabled: boolean }>("/feedback/config/"),
    submit: (message: string) =>
      request<Feedback>("/feedback/", { method: "POST", body: JSON.stringify({ message }) }),
    /** Admin-only: this org's own submitted feedback. */
    list: () => request<Feedback[]>("/feedback/"),
    resolve: (id: number) => request<Feedback>(`/feedback/${id}/resolve/`, { method: "POST" }),
  },
};
