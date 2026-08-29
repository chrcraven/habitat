/**
 * Season selection for the "four seasons" nav logo — decided 2026-08-29
 * (see /docs/open-questions.md, "Nav logo"): the owner picked the
 * "Habitat — four seasons" set from a published design canvas, refined to
 * display the seasonal variant matching the current date rather than one
 * fixed mark.
 *
 * Two build-session defaults, per that decision (cheap to change,
 * flagged rather than blocking the build):
 *  - **Season boundaries**: meteorological (Mar-May / Jun-Aug / Sep-Nov /
 *    Dec-Feb), not exact solstice/equinox dates.
 *  - **Hemisphere**: Northern (the author's own property/native-
 *    restoration context) — revisit with a location-aware version if
 *    Habitat ever serves Southern-Hemisphere properties.
 */

export type Season = "spring" | "summer" | "fall" | "winter";

export function currentSeason(date: Date = new Date()): Season {
  const month = date.getMonth(); // 0 = January
  if (month >= 2 && month <= 4) return "spring"; // Mar, Apr, May
  if (month >= 5 && month <= 7) return "summer"; // Jun, Jul, Aug
  if (month >= 8 && month <= 10) return "fall"; // Sep, Oct, Nov
  return "winter"; // Dec, Jan, Feb
}

/** The "habitat" wordmark's color for each season, matching the canvas
 * design (the icon and wordmark are styled as separate elements there,
 * not baked into one image) — see components/Logo.tsx. */
const WORDMARK_COLOR: Record<Season, string> = {
  spring: "oklch(0.5 0.09 140)",
  summer: "#2F4A34",
  fall: "oklch(0.48 0.1 55)",
  winter: "oklch(0.55 0.02 240)",
};

export function wordmarkColor(season: Season): string {
  return WORDMARK_COLOR[season];
}
