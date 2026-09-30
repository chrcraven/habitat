import RelativeTime from "./RelativeTime";
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
 *
 * # "Last updated" (D79)
 *
 * `PublicPageDetailSerializer.Meta.fields` is a hand-written list of seven
 * fields — not `__all__` — and `updated_at` is one of them. So somebody
 * deliberately put this page's own age on the public wire, it was typed on
 * the client (`PublicPage.updated_at`), and until now it was read by
 * nothing: the whole public site rendered no sense of time anywhere. An
 * authored page is a land trust's own prose, which makes it the most
 * staleness-sensitive thing the public site serves and the reason D79
 * ranked it first.
 *
 * It renders here rather than at the two call sites so the org portfolio
 * and a property's own pages cannot drift apart over the wording — the
 * same reason the security-relevant half of this component is shared.
 *
 * It renders for **both** formats, including the sandboxed html one. The
 * timestamp is the `Page` row's, so it is equally true either way, and the
 * line sits outside the frame where the author's own document cannot
 * restyle or hide it.
 *
 * Deliberately no person: see `RelativeTime`, and D38 on why a member's
 * email must never reach an anonymous visitor.
 */
export default function PublicPageBody({ page }: { page: PublicPage }) {
  return (
    <>
      {page.content_format === "html" ? (
        page.document_url ? (
          <iframe
            className="page-content-frame"
            title={page.title}
            src={page.document_url}
            sandbox="allow-scripts"
          />
        ) : (
          <p className="muted">This page isn't available right now.</p>
        )
      ) : (
        <article className="page-content" dangerouslySetInnerHTML={{ __html: page.body_html }} />
      )}
      <p className="public-record-age">
        Last updated <RelativeTime at={page.updated_at} />
      </p>
    </>
  );
}
