import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useAsync } from "../hooks/useAsync";
import type { Page } from "../api/types";

/**
 * Authoring form for a Page — handles four routes from one component,
 * same "outer data-loading wrapper + inner form" split as
 * PropertyFormPage/ActivityFormPage:
 *   /admin/pages/new                     — new org-level page
 *   /admin/pages/:pageId/edit            — edit an org-level page
 *   /properties/:id/pages/new            — new page scoped to property :id
 *   /properties/:id/pages/:pageId/edit   — edit that property's page
 *
 * Content is markdown (rendered to sanitized HTML server-side for the
 * public site — see backend/apps/pages/rendering.py) rather than raw
 * HTML, so there's a plain textarea here, not a rich-text/HTML editor —
 * see /docs/open-questions.md, "Public site storytelling / custom
 * content" for why (the custom-HTML/CSS/JS layer is a separate,
 * still-undecided feature).
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
  const [isPublic, setIsPublic] = useState(existing?.is_public ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const backTo = propertyId != null ? `/properties/${propertyId}` : "/admin";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (existing) {
        await api.pages.update(existing.id, { title, slug, body, is_public: isPublic });
      } else {
        await api.pages.create({
          property: propertyId ?? undefined,
          title,
          slug: slug || undefined,
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
