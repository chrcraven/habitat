import type { CSSProperties } from "react";
import { API_BASE } from "../api/client";
import type { ThemeFields, ThemeFont } from "../api/types";

/**
 * The "constrained theme controls" feature (owner decision, 2026-08-31 —
 * see /docs/open-questions.md, "Public site storytelling / custom
 * content"): turns an org/property's theme fields into CSS custom
 * property overrides, scoped to the public-site DOM subtree they're
 * applied to (see PublicOrganizationPage/PublicPropertyPage). This is the
 * whole mechanism — no per-component styling logic needed, because
 * index.css's public-site rules already reference these same variable
 * names (falling back to the app's normal --color-* defaults), so
 * overriding them here re-themes buttons/links/cards/backgrounds
 * everywhere in one place. See backend/apps/accounts/theming.py for the
 * matching server-side validation (a 6-digit hex code can't contain
 * anything CSS-meaningful, which is what makes dropping these straight
 * into a style object safe with no extra escaping here).
 */

const FONT_STACKS: Record<Exclude<ThemeFont, "">, string> = {
  sans: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  serif: 'Georgia, Cambria, "Times New Roman", Times, serif',
  rounded: '"Century Gothic", "Trebuchet MS", sans-serif',
  monospace: '"SFMono-Regular", Consolas, "Liberation Mono", monospace',
};

/** Resolves one property's field for a Property, falling back to its
 * Organization's own value when the property left it blank — a property
 * theme overrides its org's per-field, not all-or-nothing. */
function resolve<K extends keyof ThemeFields>(
  key: K,
  theme: ThemeFields,
  fallback?: ThemeFields,
): ThemeFields[K] | undefined {
  if (theme[key]) return theme[key];
  return fallback?.[key];
}

/** React inline-style object (CSS custom properties) for the public-site
 * shell — spread onto the outermost `.app-shell--public` element. Pass
 * `fallback` (the org's own ThemeFields) when theming a *property* page,
 * so a property that hasn't set its own colors still picks up its org's;
 * omit it for the org portfolio page itself, which has nothing above it
 * to fall back to. */
export function publicThemeStyle(theme: ThemeFields, fallback?: ThemeFields): CSSProperties {
  const primary = resolve("theme_primary_color", theme, fallback);
  const background = resolve("theme_background_color", theme, fallback);
  const accent = resolve("theme_accent_color", theme, fallback);
  const font = resolve("theme_font", theme, fallback);

  const style: Record<string, string> = {};
  if (primary) {
    style["--color-primary"] = primary;
    // Derived at CSS-value time (color-mix, already used elsewhere in
    // index.css) rather than computed in JS — one less thing to keep in
    // sync, and it's exactly what --color-primary-dark is for (hover
    // states on primary buttons).
    style["--color-primary-dark"] = `color-mix(in srgb, ${primary} 82%, black)`;
  }
  if (background) style["--color-bg"] = background;
  if (accent) style["--public-accent"] = accent;
  if (font) style["--public-font-family"] = FONT_STACKS[font];
  return style as CSSProperties;
}

/** The header-image URL for an org/property's theme, or null if it hasn't
 * set one (own field checked first, then the org fallback for a property
 * page) — points at the *public*, unauthenticated theme-image endpoint
 * (see backend/apps/public_site/views.py), not the session-authenticated
 * admin-preview one (see api/client.ts's theme.* helpers for that). */
export function publicHeaderImageUrl(
  theme: { id: number; has_theme_header_image: boolean },
  kind: "organization" | "property",
  fallback?: { id: number; has_theme_header_image: boolean },
): string | null {
  if (theme.has_theme_header_image) {
    return `${API_BASE}/public/${kind === "organization" ? "organizations" : "properties"}/${theme.id}/theme-image/`;
  }
  if (kind === "property" && fallback?.has_theme_header_image) {
    return `${API_BASE}/public/organizations/${fallback.id}/theme-image/`;
  }
  return null;
}
