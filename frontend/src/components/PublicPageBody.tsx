import type { PublicPage } from "../api/types";

/**
 * Renders one authored page's content on the public site. Shared by
 * PublicOrganizationPage and PublicPropertyPage so the two can't drift
 * apart on the security-relevant half of this.
 *
 * The two content formats are rendered in deliberately different ways,
 * and the difference is the whole point:
 *
 * - **markdown** — `body_html` is server-rendered and sanitized (see
 *   backend/apps/pages/rendering.py), so it's inlined into this page's own
 *   DOM. Never render author-supplied text here any other way.
 * - **html** — the author's own document, scripts included. It is NEVER
 *   inlined; it's loaded as a separate document in a sandboxed iframe.
 *   `sandbox="allow-scripts"` deliberately omits `allow-same-origin`,
 *   which gives the frame a unique opaque origin (no cookies, no access to
 *   this page's DOM). Adding `allow-same-origin` alongside `allow-scripts`
 *   would let the framed document remove its own sandbox — so don't. The
 *   server sets the equivalent sandbox as a CSP header on the document
 *   itself too (see apps/public_site/views.py#_page_document), so the
 *   protection doesn't depend on this attribute alone.
 *
 * A null `document_url` on an html page means the organization's custom
 * content has been switched off (the per-tenant kill-switch) — there's
 * nothing to frame, so say so rather than showing an empty box.
 */
export default function PublicPageBody({ page }: { page: PublicPage }) {
  if (page.content_format === "html") {
    if (!page.document_url) {
      return <p className="muted">This page isn't available right now.</p>;
    }
    return (
      <iframe
        className="page-content-frame"
        title={page.title}
        src={page.document_url}
        sandbox="allow-scripts"
      />
    );
  }
  return <article className="page-content" dangerouslySetInnerHTML={{ __html: page.body_html }} />;
}
