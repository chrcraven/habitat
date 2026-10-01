import { useEffect } from "react";

/**
 * Per-page document titles — what a reader ends up holding after they
 * visit (D82).
 *
 * `index.html` carries `<title>Habitat</title>` and nothing in the app
 * had ever written `document.title`, so every one of the app's
 * path-carrying routes shared that one string: the browser tab, the
 * default bookmark name, the back/forward history entry and the
 * screen reader's on-load announcement all said "Habitat". Two of an
 * organization's properties open in two tabs were indistinguishable.
 *
 * # Name first, brand last
 *
 * A tab strip gives a title something like fifteen characters before it
 * truncates, so the distinguishing part has to come first:
 * `"Grove Ave · Habitat"` degrades to "Grove Ave…" while
 * `"Habitat — Grove Ave"` degrades to "Habitat — G…", which is the
 * defect again with extra steps. `·` is this repo's existing separator
 * (see `components/AttributionNote.tsx`).
 *
 * # Why each page calls this, rather than one table keyed on the route
 *
 * A central `pathname -> title` map reads as tidier and would need its
 * own copy of the route table's 46 patterns to match against. That is
 * D53's shape exactly: a second structure that has to be kept in step
 * with the first, where falling behind it is silent. It also cannot
 * name what the reader actually came for — a property's title is its
 * *name*, which is fetched, not routed.
 *
 * `useMatches` would give the matched route without re-deriving it, but
 * it needs a data router (`createBrowserRouter`); this app renders
 * `<Routes>` under a plain `BrowserRouter`, so it is not available.
 *
 * # Why there is deliberately no cleanup
 *
 * The obvious companion to "set the title on mount" is "put it back on
 * unmount". It was first left out here on the theory that a restoring
 * cleanup would fire *after* the incoming page had set its own title and
 * clobber it. **Measured, that theory is wrong** — the cleanup version
 * was built and run against the 57-check browser suite and passed every
 * one of them, so on these navigations the restore lands before the next
 * page's write and nothing is clobbered. Recorded as a correction rather
 * than quietly dropped, since the wrong reason is the more memorable one.
 *
 * It stays out for a duller reason that does hold: **there is never
 * anything to restore.** Every route that renders at all sets a title,
 * so the saved `previous` is read by nobody — the cleanup is inert in
 * exactly the case it appears to serve, which is this repo's
 * "configured and does nothing" family in a place that reads as
 * defensive programming. It is also not the safety net it resembles: if
 * a future page forgets the call, restoring gives it the title from
 * *two* pages back instead of one, which is no less wrong and harder to
 * reason about.
 *
 * What actually keeps titles correct is structural: **every route that
 * renders anything calls one of these two hooks.** The four `/admin/*`
 * routes are bare `<Navigate>`s and render nothing, and their targets
 * set a title of their own.
 *
 * That invariant is not self-maintaining — a new page that forgets the
 * call inherits whatever the previous page set, which is a *wrong*
 * title rather than a missing one, and worse than the defect this
 * fixes. There is no frontend test runner in this repo to pin it.
 *
 * # What this deliberately does NOT do
 *
 * It does not inject `<meta name="description">` or Open Graph tags.
 * Those would look like the other half of the same fix and would be
 * inert for precisely the consumers they appear to serve: a
 * link-preview bot does not run JS, so a tag written from an effect is
 * never seen by the thing rendering the preview. (The
 * "configured and does nothing" family — D40's `NUM_PROXIES`, D43's
 * `AnonRateThrottle`, D45's mail variables, D53, D68, D75.) Shareable
 * previews need SSR or prerendering, which is an architecture decision
 * and the owner's: D82b, composed with D39b's Q2.
 */

/** The product name, used as the suffix inside the authenticated app. */
export const APP_NAME = "Habitat";

/** Joins the parts that are actually present. Callers pass a value that
 * may still be loading, so a missing part has to drop out rather than
 * render as an empty segment — `" · Habitat"` with a leading separator
 * reads as a bug, and `"undefined · Habitat"` more so. */
function joinTitle(parts: Array<string | null | undefined>): string {
  const present = parts
    .map((part) => part?.trim())
    .filter((part): part is string => !!part);
  // Nothing known yet: the bare product name is the honest answer, and
  // it is what `index.html` already shows, so there is no flicker.
  return present.length > 0 ? present.join(" · ") : APP_NAME;
}

/**
 * Title a page inside the authenticated app: `"<name> · Habitat"`.
 *
 * `name` is the page's own name — for a page whose name is fetched,
 * pass a generic label as the fallback (`property?.name ?? "Property"`)
 * rather than `null`. Both are honest, but the label says which *kind*
 * of page this is while the fetch is in flight, and it is also what a
 * failed load should leave behind: claiming a name the request never
 * returned would be worse than naming the kind of page.
 */
export function useDocumentTitle(name: string | null | undefined): void {
  const title = joinTitle([name, APP_NAME]);
  useEffect(() => {
    document.title = title;
  }, [title]);
}

/**
 * Title a page on the public site: `"<name> · <organization>"`, or just
 * the organization's name on its own portfolio root.
 *
 * The suffix is the **organization**, not `Habitat`, and that is a
 * decision rather than an oversight. A public page is the
 * organization's — it carries that organization's name, colors, font
 * and header image (see `utils/theme.ts`) — and a visitor saving it has
 * no use for the name of the software it happens to run on. Habitat is
 * the vendor; the land is what they came for.
 *
 * Falls back to the product name only while nothing has loaded, via
 * `joinTitle`, so a visitor never sees an empty or half-formed title.
 */
export function usePublicDocumentTitle(
  name: string | null | undefined,
  organizationName: string | null | undefined,
): void {
  const title = joinTitle([name, organizationName]);
  useEffect(() => {
    document.title = title;
  }, [title]);
}
