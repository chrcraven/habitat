/** Capturing where a visitor was trying to go, so authenticating can resume it.
 *
 * Why this exists: `RequireAuth` used to answer an anonymous visitor with a
 * bare `<Navigate to="/login" replace />`, discarding the destination
 * entirely, and all four post-auth paths hardcoded `navigate("/")`. So a
 * link shared between org members, or a bookmark followed after a session
 * lapsed, could not resume — you logged in and arrived at the dashboard,
 * with the address you actually wanted gone from history as well (both
 * navigations used `replace`).
 *
 * THE SECURITY PROPERTY, which is the whole reason this is a module rather
 * than an inline template string at each call site: a return target that
 * accepts an absolute URL is an open redirect. `safeReturnPath` is the one
 * gate, and it is refusal-shaped — a value either already looks like a path
 * on this very origin or it is dropped whole. It is never "cleaned up" into
 * something that almost matches, because a sanitizer that rewrites hostile
 * input is how the interesting bypasses get in.
 *
 * It deliberately guards harder than the backend's own `_clean_page_path`
 * (backend/apps/feedback/views.py), whose rationale it otherwise mirrors,
 * because that value is *displayed* where this one is *navigated to*. Three
 * shapes are all genuine off-site redirects, and a leading-"//" check alone
 * catches only the first:
 *
 *   - `//evil.com` is protocol-relative — it resolves to `https://evil.com`.
 *   - `/\evil.com` is the same thing, because a browser normalizes a
 *     backslash in the path of an http(s) URL to a forward slash.
 *   - `/<TAB>/evil.com` is the same thing again, because a browser strips
 *     tab, newline and carriage return from a URL *before* parsing it — so a
 *     control character can assemble a `//` prefix that is not literally
 *     present in the string being checked.
 *
 * The last two are why the control-character and backslash checks below are
 * not belt-and-braces: remove either and this becomes an open redirect.
 */

/** Query parameter carrying the captured destination. */
export const RETURN_PARAM = "next";

/** Where an unauthenticated visitor lands when there is nothing to resume. */
const DEFAULT_RETURN = "/";

/**
 * The value as a usable same-origin path, or `null` if it isn't one.
 *
 * Returns `null` rather than a default so a caller can tell "nothing was
 * captured" from "the dashboard was captured", and so the refusal is never
 * silently indistinguishable from a legitimate `/`.
 */
export function safeReturnPath(raw: string | null | undefined): string | null {
  if (typeof raw !== "string") return null;
  const value = raw.trim();
  // Control characters are checked before anything structural: a browser
  // strips them, and stripping them is what creates the dangerous shape, so
  // a value containing one cannot be judged by its visible prefix.
  //
  // Spelled with explicit char codes rather than a `\uXXXX` regex class on
  // purpose. Written as an escape, one round trip through a tool that
  // interprets it turns this line into real control bytes and the whole file
  // into something git and grep treat as binary — which is exactly what
  // happened when it was first written here.
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i);
    if (code <= 0x1f || code === 0x7f) return null;
  }
  if (value.includes("\\")) return null;
  if (!value.startsWith("/")) return null;
  if (value.startsWith("//")) return null;
  if (value.includes("://")) return null;
  return value;
}

/**
 * The path to resume after authenticating: the captured destination when
 * there is a usable one, the dashboard otherwise.
 *
 * Takes a raw `location.search` string rather than calling `useLocation`
 * itself, so this module stays free of React and directly testable.
 */
export function returnPathFrom(search: string): string {
  return safeReturnPath(new URLSearchParams(search).get(RETURN_PARAM)) ?? DEFAULT_RETURN;
}

/**
 * The `/login` address that will come back to `location` afterwards.
 *
 * A visitor heading for the dashboard needs no return trip, so that case
 * stays a plain `/login` rather than carrying a `?next=/` that reads as
 * clutter and changes nothing.
 */
export function loginPathFor(location: {
  pathname: string;
  search: string;
  hash: string;
}): string {
  const target = `${location.pathname}${location.search}${location.hash}`;
  const safe = safeReturnPath(target);
  if (safe === null || safe === DEFAULT_RETURN) return "/login";
  return `/login?${RETURN_PARAM}=${encodeURIComponent(safe)}`;
}

/**
 * Carry a captured destination across a link *between* the auth screens
 * (login → signup, reset → login, …).
 *
 * Without this the return works from whichever screen `RequireAuth` happened
 * to land on and silently doesn't from the others: a deep-linked visitor with
 * no account yet is bounced to `/login?next=…`, clicks "Create one", and
 * loses it. Assumes `path` carries no query string of its own, which is true
 * of every auth-screen link in this app.
 */
export function withReturn(path: string, search: string): string {
  const target = safeReturnPath(new URLSearchParams(search).get(RETURN_PARAM));
  if (target === null || target === DEFAULT_RETURN) return path;
  return `${path}?${RETURN_PARAM}=${encodeURIComponent(target)}`;
}
