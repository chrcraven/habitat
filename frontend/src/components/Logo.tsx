import logoFall from "../assets/logo-fall.svg";
import logoSpring from "../assets/logo-spring.svg";
import logoSummer from "../assets/logo-summer.svg";
import logoWinter from "../assets/logo-winter.svg";
import { currentSeason, wordmarkColor } from "../utils/logo";

const LOGO_BY_SEASON = {
  spring: logoSpring,
  summer: logoSummer,
  fall: logoFall,
  winter: logoWinter,
};

/**
 * The "four seasons" nav brand — replaces the placeholder "🌿 Habitat"
 * emoji+text mark in TopBar and PublicHeader (decided 2026-08-29, see
 * /docs/open-questions.md, "Nav logo"). Picks the season from today's
 * date (see utils/logo.ts) rather than showing one fixed variant.
 *
 * `className` is applied to the outer wrapper so callers can reuse
 * whatever brand-slot styling already existed (e.g. `.top-bar__brand`)
 * without this component needing to know about it.
 */
export default function Logo({ className }: { className?: string }) {
  const season = currentSeason();
  return (
    <span className={"logo" + (className ? ` ${className}` : "")}>
      <img src={LOGO_BY_SEASON[season]} alt="Habitat" className="logo__mark" width={28} height={28} />
      <span className="logo__wordmark" style={{ color: wordmarkColor(season) }}>
        habitat
      </span>
    </span>
  );
}
