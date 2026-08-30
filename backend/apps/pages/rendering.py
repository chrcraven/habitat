"""
Markdown -> sanitized HTML for a Page's public rendering.

Deliberately two steps, not a hand-rolled one: `markdown` handles the
syntax (headings, lists, links, etc.), then `bleach` strips anything that
slipped through as raw HTML in the source (a `<script>`, an `onerror=`
handler, a `javascript:` link) down to a fixed allowlist — the same
"vetted sanitizer, never a hand-rolled regex" approach recommended for the
still-undecided raw-custom-HTML feature in /build-questions.md, applied
now even though today's input is "just markdown" (Python-Markdown passes
raw inline/block HTML in its source straight through unless something else
strips it, so skipping this step would already be a real stored-XSS hole).
"""

import bleach
import markdown as _markdown

ALLOWED_TAGS = [
    "p", "br", "hr",
    "strong", "em", "b", "i", "del",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "img",
    "blockquote", "code", "pre",
    "table", "thead", "tbody", "tr", "th", "td",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_page_body(markdown_text: str) -> str:
    """Render a Page.body markdown string to sanitized HTML safe to inject
    into the public site verbatim."""
    html = _markdown.markdown(
        markdown_text or "", extensions=["extra", "sane_lists"]
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
