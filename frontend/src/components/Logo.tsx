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
 *
 * `size` picks between the nav-sized mark (the default, what TopBar and
 * PublicHeader use) and a heading-sized one for the unauthenticated auth
 * screens, where the brand is the page's own <h1> rather than a strip
 * along the top — see `.logo--lg` in index.css.
 */
export default function Logo({
  className,
  size = "nav",
}: {
  className?: string;
  size?: "nav" | "lg";
}) {
  const season = currentSeason();
  const classes = ["logo", size === "lg" ? "logo--lg" : null, className].filter(Boolean).join(" ");
  return (
    <span className={classes}>
      {/* The mark is decorative: the wordmark right beside it already
          supplies the name as real text, so giving the image its own
          "Habitat" alt made a screen reader announce the brand twice
          ("Habitat habitat"). Audible anywhere, but most so on the auth
          screens, where this component is the page's own <h1>. */}
      <img src={LOGO_BY_SEASON[season]} alt="" className="logo__mark" width={28} height={28} />
      <span className="logo__wordmark" style={{ color: wordmarkColor(season) }}>
        habitat
      </span>
    </span>
  );
}
