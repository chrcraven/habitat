/**
 * Where the public site is served from.
 *
 * The public site can live on its own origin, isolated from the
 * authenticated app (see /docs/open-questions.md, "Public site
 * storytelling / custom content") — author-supplied content on a separate
 * origin can't reach the app's session cookies, which are host-only. Which
 * origin that is belongs to the deployment, not the code: it comes from
 * VITE_PUBLIC_SITE_URL, the frontend sibling of the backend's
 * PUBLIC_SITE_URL setting, the same way VITE_API_URL already supplies the
 * API's origin.
 *
 * Unset (the default) means the public pages are served from the same
 * origin as the app, exactly as they are today — every link below then
 * resolves against window.location.origin, unchanged.
 */
const CONFIGURED = (import.meta.env.VITE_PUBLIC_SITE_URL ?? "").trim().replace(/\/+$/, "");

/** True when the public site is deployed on an origin of its own. */
export function publicSiteIsIsolated(): boolean {
  return CONFIGURED !== "" && CONFIGURED !== window.location.origin;
}

/** Absolute URL for a public-site path (e.g. `/public/<org-slug>`). Always
 * absolute rather than relative, because these are links the app hands
 * *out* — a QR code, a "view your public site" link, something a person
 * copies and sends — and those have to keep working off-origin. Links
 * *within* the public pages themselves stay relative: they're already on
 * whichever origin is serving them. */
export function publicSiteUrl(path = ""): string {
  const base = CONFIGURED || window.location.origin;
  if (!path) return base;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}
