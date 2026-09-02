import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import type { Page, PageContentFormat } from "../api/types";

/**
 * Authoring form for a Page — handles four routes from one component,
 * same "outer data-loading wrapper + inner form" split as
 * PropertyFormPage/ActivityFormPage:
 *   /admin/pages/new                     — new org-level page
 *   /admin/pages/:pageId/edit            — edit an org-level page
 *   /properties/:id/pages/new            — new page scoped to property :id
 *   /properties/:id/pages/:pageId/edit   — edit that property's page
 *
 * Content is a plain textarea either way, not a rich-text/WYSIWYG editor,
 * in both of the formats a page can have (see backend/apps/pages/models.py):
 * markdown, rendered to sanitized HTML server-side, or — where the
 * deployment and the organization both allow it — the author's own HTML
 * document, which the public site loads into a sandboxed frame rather than
 * inlining. The content-type picker only appears when custom HTML is
 * actually available; otherwise this is markdown-only exactly as before.
 * See /docs/open-questions.md, "Public site storytelling / custom content".
 */
function PageForm({
  propertyId,
  existing,
  onSaved,
}: {
  propertyId: number | null;
  existing: Page | null;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(existing?.title ?? "");
  const [slug, setSlug] = useState(existing?.slug ?? "");
  const [body, setBody] = useState(existing?.body ?? "");
  const [contentFormat, setContentFormat] = useState<PageContentFormat>(
    existing?.content_format ?? "markdown",
  );
  const [isPublic, setIsPublic] = useState(existing?.is_public ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Both custom-HTML gates, already resolved server-side onto the org in
  // the session payload (see backend/apps/pages/custom_html.py). When it's
  // off there's no content-type picker at all and every page is markdown,
  // exactly as before the feature existed — the backend rejects an `html`
  // write independently, this only avoids offering a control that would
  // always fail.
  const { session } = useAuth();
  const customHtmlEnabled = session?.membership?.organization.custom_html_enabled ?? false;

  const backTo = propertyId != null ? `/properties/${propertyId}` : "/admin";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (existing) {
        await api.pages.update(existing.id, {
          title,
          slug,
          content_format: contentFormat,
          body,
          is_public: isPublic,
        });
      } else {
        await api.pages.create({
          property: propertyId ?? undefined,
          title,
          slug: slug || undefined,
          content_format: contentFormat,
          body,
          is_public: isPublic,
        });
      }
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save that page.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div className="page__header">
        <h1>{existing ? "Edit page" : "New page"}</h1>
        <Link to={backTo} className="btn-link">
          ← Back
        </Link>
      </div>
      <form onSubmit={handleSubmit} className="form">
        {error && <p className="form-error">{error}</p>}
        <label className="field">
          <span>Title</span>
          <input
            type="text"
            autoFocus
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Our Story"
          />
        </label>
        <label className="field">
          <span>URL name</span>
          <input
            type="text"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="e.g. our-story"
          />
          <span className="field-hint muted">
            Public link ends in <code>/pages/{slug || "…"}</code>. Lowercase letters, numbers, and
            hyphens; leave blank to generate it from the title. "explore" is reserved for the
            built-in Explore page.
          </span>
        </label>
        {customHtmlEnabled && (
          <label className="field">
            <span>Content type</span>
            <select
              value={contentFormat}
              onChange={(e) => setContentFormat(e.target.value as PageContentFormat)}
            >
              <option value="markdown">Markdown (formatted text)</option>
              <option value="html">Custom HTML (your own page)</option>
            </select>
          </label>
        )}
        {contentFormat === "html" ? (
          <label className="field">
            <span>Page HTML</span>
            <textarea
              rows={20}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              spellCheck={false}
              placeholder={
                "<!doctype html>\n<html>\n  <body>\n    <h1>Our Story</h1>\n  </body>\n</html>"
              }
            />
            <span className="field-hint muted">
              Your own HTML, CSS, and JavaScript, used exactly as written. It runs in a sandbox on
              the public site — isolated from the rest of Habitat, with no access to anyone's login
              — so it can't reach your account, but it <strong>can</strong> affect whoever visits
              this page. Only put content here you'd stand behind publicly.
            </span>
          </label>
        ) : (
          <label className="field">
            <span>Body (Markdown)</span>
            <textarea
              rows={16}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={"# A heading\n\nA paragraph, a [link](https://example.com), a list:\n\n- one\n- two"}
            />
            <span className="field-hint muted">
              Formatted with Markdown — headings, bold/italics, links, lists, images. Rendered and
              sanitized on the server before anyone sees it publicly; raw HTML/scripts aren't
              supported.
            </span>
          </label>
        )}
        <label className="field field--checkbox">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
          <span>Visible on the public site</span>
        </label>
        <button type="submit" className="btn btn-primary" disabled={submitting || !title}>
          {submitting ? "Saving…" : "Save page"}
        </button>
      </form>
    </div>
  );
}

export default function PageFormPage() {
  const { id, pageId } = useParams<{ id?: string; pageId?: string }>();
  const navigate = useNavigate();
  const propertyId = id !== undefined ? Number(id) : null;
  const isEdit = pageId !== undefined;

  const existing = useAsync(
    () => (isEdit ? api.pages.get(Number(pageId)) : Promise.resolve(null)),
    [pageId],
  );

  if (isEdit && existing.loading) {
    return <div className="full-page-status">Loading…</div>;
  }
  if (isEdit && (existing.error || !existing.data)) {
    return (
      <p className="form-error" style={{ padding: "1rem" }}>
        Couldn't load that page.
      </p>
    );
  }

  const backTo = propertyId != null ? `/properties/${propertyId}` : "/admin";

  return (
    <PageForm
      propertyId={propertyId}
      existing={existing.data}
      onSaved={() => navigate(backTo)}
    />
  );
}
