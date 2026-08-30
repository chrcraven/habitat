import { Link } from "react-router-dom";
import type { PublicPageSummary } from "../api/types";

/**
 * Page nav for the public org/property pages — "Explore" (the built-in
 * auto-generated view, always first) plus every authored public page, in
 * position order. Only rendered at all when at least one authored page
 * exists (see PublicOrganizationPage/PublicPropertyPage) — an org/
 * property that's never authored a page still looks exactly like it did
 * before this feature existed. See /docs/open-questions.md, "Public site
 * storytelling / custom content".
 */
export default function PublicPageNav({
  basePath,
  pages,
  activeSlug,
}: {
  /** e.g. `/public/<org-slug>` or `/public/<org-slug>/<property-slug>`. */
  basePath: string;
  pages: PublicPageSummary[];
  /** null means Explore is the one currently shown. */
  activeSlug: string | null;
}) {
  return (
    <nav className="page-nav">
      <Link
        to={`${basePath}/explore`}
        className={`page-nav__link${activeSlug === null ? " page-nav__link--active" : ""}`}
      >
        Explore
      </Link>
      {pages.map((page) => (
        <Link
          key={page.id}
          to={`${basePath}/pages/${page.slug}`}
          className={`page-nav__link${activeSlug === page.slug ? " page-nav__link--active" : ""}`}
        >
          {page.title}
        </Link>
      ))}
    </nav>
  );
}
