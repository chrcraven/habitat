import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { ApiError } from "../api/client";
import type { ThemeFields, ThemeFont } from "../api/types";

const FONT_OPTIONS: { value: ThemeFont; label: string }[] = [
  { value: "", label: "Default" },
  { value: "sans", label: "Sans-serif" },
  { value: "serif", label: "Serif" },
  { value: "rounded", label: "Rounded" },
  { value: "monospace", label: "Monospace" },
];

type ThemeColorFields = Pick<
  ThemeFields,
  "theme_primary_color" | "theme_background_color" | "theme_accent_color" | "theme_font"
>;

/**
 * Editor for the "constrained theme controls" feature (owner decision,
 * 2026-08-31 — see /docs/open-questions.md, "Public site storytelling /
 * custom content") — a fixed, safe set of knobs (colors, font, a header
 * image), not a free-text CSS field. Shared by OrgAdminPage (org-level
 * theme) and PropertyMapPage (property-level theme, which overrides the
 * org's per-field on that property's own public page — see
 * frontend/src/utils/theme.ts).
 *
 * Kept generic the same way QrCodePanel is: the caller supplies the save/
 * upload/remove callbacks (which endpoint they hit differs by org vs.
 * property) and this component only owns the form state and the actual
 * controls.
 */
export default function ThemeEditorPanel({
  theme,
  onSave,
  previewImageUrl,
  onUploadImage,
  onRemoveImage,
}: {
  theme: ThemeColorFields & { has_theme_header_image: boolean };
  onSave: (data: ThemeColorFields) => Promise<void>;
  /** Session-authenticated <img src> for the current header image — see
   * api/client.ts's `org.themeImage.previewUrl` / `properties.themeImage.previewUrl`. */
  previewImageUrl: string;
  onUploadImage: (file: File) => Promise<void>;
  onRemoveImage: () => Promise<void>;
}) {
  const [primary, setPrimary] = useState(theme.theme_primary_color);
  const [background, setBackground] = useState(theme.theme_background_color);
  const [accent, setAccent] = useState(theme.theme_accent_color);
  const [font, setFont] = useState<ThemeFont>(theme.theme_font);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageBusy, setImageBusy] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  // The preview URL's path never changes (same endpoint before/after an
  // upload), so the browser would otherwise keep showing a cached image —
  // this cache-busts it after every upload/remove.
  const [imageVersion, setImageVersion] = useState(0);

  useEffect(() => {
    setPrimary(theme.theme_primary_color);
    setBackground(theme.theme_background_color);
    setAccent(theme.theme_accent_color);
    setFont(theme.theme_font);
  }, [theme.theme_primary_color, theme.theme_background_color, theme.theme_accent_color, theme.theme_font]);

  const dirty =
    primary !== theme.theme_primary_color ||
    background !== theme.theme_background_color ||
    accent !== theme.theme_accent_color ||
    font !== theme.theme_font;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave({
        theme_primary_color: primary,
        theme_background_color: background,
        theme_accent_color: accent,
        theme_font: font,
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save the theme.");
    } finally {
      setSaving(false);
    }
  };

  const handleFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setImageBusy(true);
    setImageError(null);
    try {
      await onUploadImage(file);
      setImageVersion((v) => v + 1);
    } catch (err) {
      setImageError(err instanceof ApiError ? err.message : "Couldn't upload that image.");
    } finally {
      setImageBusy(false);
    }
  };

  const handleRemoveImage = async () => {
    setImageBusy(true);
    setImageError(null);
    try {
      await onRemoveImage();
      setImageVersion((v) => v + 1);
    } catch (err) {
      setImageError(err instanceof ApiError ? err.message : "Couldn't remove that image.");
    } finally {
      setImageBusy(false);
    }
  };

  return (
    <div className="theme-editor">
      <p className="muted">
        Brand your public page with a fixed set of safe controls — colors, a font, a header image
        — not free-form CSS. Leave a color at its default to inherit Habitat's normal styling.
      </p>
      <form onSubmit={handleSubmit} className="form form--panel">
        {error && <p className="form-error">{error}</p>}
        <div className="theme-editor__colors">
          <label className="field">
            <span>Primary color</span>
            <input
              type="color"
              value={primary || "#2f6f4f"}
              onChange={(e) => setPrimary(e.target.value)}
            />
            {primary && (
              <button type="button" className="btn-link" onClick={() => setPrimary("")}>
                Reset to default
              </button>
            )}
          </label>
          <label className="field">
            <span>Background color</span>
            <input
              type="color"
              value={background || "#f7f7f5"}
              onChange={(e) => setBackground(e.target.value)}
            />
            {background && (
              <button type="button" className="btn-link" onClick={() => setBackground("")}>
                Reset to default
              </button>
            )}
          </label>
          <label className="field">
            <span>Accent color</span>
            <input
              type="color"
              value={accent || "#2f6f4f"}
              onChange={(e) => setAccent(e.target.value)}
            />
            {accent && (
              <button type="button" className="btn-link" onClick={() => setAccent("")}>
                Reset to default
              </button>
            )}
          </label>
        </div>
        <label className="field">
          <span>Font</span>
          <select value={font} onChange={(e) => setFont(e.target.value as ThemeFont)}>
            {FONT_OPTIONS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="btn btn-secondary btn-small" disabled={saving || !dirty}>
          {saving ? "Saving…" : "Save theme"}
        </button>
      </form>

      <div className="form form--panel">
        <label className="field">
          <span>Header image (optional)</span>
          <span className="field-hint muted">
            A banner image shown at the top of your public page.
          </span>
        </label>
        {imageError && <p className="form-error">{imageError}</p>}
        {theme.has_theme_header_image && (
          <img
            key={imageVersion}
            src={`${previewImageUrl}?v=${imageVersion}`}
            alt=""
            className="theme-editor__image-preview"
          />
        )}
        <div className="qr-panel__actions">
          <label className="btn btn-secondary btn-small">
            {imageBusy
              ? "Working…"
              : theme.has_theme_header_image
                ? "Replace image"
                : "Upload image"}
            <input
              type="file"
              accept="image/*"
              onChange={handleFile}
              disabled={imageBusy}
              hidden
            />
          </label>
          {theme.has_theme_header_image && (
            <button
              type="button"
              className="btn btn-danger btn-small"
              onClick={handleRemoveImage}
              disabled={imageBusy}
            >
              Remove image
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
