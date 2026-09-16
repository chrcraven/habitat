/**
 * Whether one activity or sighting is *actually* on the public site, and
 * how to say so — shared by ActivitiesPage and SightingsPage.
 *
 * This is a shared module rather than two copies of a ternary for the
 * D6/D34 reason: the original D6 defect was one content-type check
 * copy-pasted into four upload sites and wrong in all four, and D34's
 * delete prompts were four words each precisely because nobody had read
 * the two side by side. The next org-wide list screen inherits this rule
 * or opts out deliberately.
 *
 * ## The rule is two conditions, not one
 *
 * A record carries its own `is_public`, and so does its property.
 * `apps/public_site/views.py` gates on **both** — `_public_property_or_404`
 * requires `is_public=True` on the property, and `property_activities` /
 * `property_sightings` then filter `is_public=True` on the record. So a
 * record flagged public on a *private* property is not published; it is
 * merely invisible, and nothing anywhere writes the record's flag when the
 * property's changes (verified 2026-09-16: there is no cascade).
 *
 * **That is why a two-state "Public / Private" badge would be a lie.** It
 * would mark a record "Public" that no anonymous visitor can reach — the
 * D19 class of defect (a caption that misdescribes what it controls),
 * shipped on the very screen built to answer "what of ours is public?".
 * Hence `BLOCKED`: flagged public, not published, and one property
 * checkbox away from being.
 *
 * A sighting's property is nullable (`SET_NULL`), and the public site
 * serves sightings only *per property* — so a property-less sighting has
 * no public route at all and can never be published. That is `ORPHANED`.
 * An activity's property FK is non-null, so activities never reach it.
 *
 * ## Unknown is a real answer
 *
 * Both pages load records and properties in two parallel requests. Until
 * the properties resolve — or if they fail — the second condition is
 * genuinely unknown, and guessing it renders a wrong badge (every public
 * record would briefly read as BLOCKED). `publicVisibility` returns
 * `null` for that, and callers render nothing rather than a guess.
 */

export type PublicVisibility =
  /** Record flag on, property flag on: reachable by anyone, right now. */
  | "public"
  /** Record flag off. Deliberately withheld. */
  | "private"
  /** Record flag on, property flag off: would publish if the property did. */
  | "blocked"
  /** Sighting with no property: no public route exists for it at all. */
  | "orphaned";

/** Just enough of a Property to answer the second condition. */
export interface PropertyVisibility {
  id: number;
  isPublic: boolean;
}

/**
 * `null` means "can't tell yet" — the property list hasn't resolved, or a
 * record names a property that isn't in it. Never guess: see the module
 * comment.
 */
export function publicVisibility(
  recordIsPublic: boolean,
  propertyId: number | null,
  properties: readonly PropertyVisibility[] | null,
): PublicVisibility | null {
  if (!recordIsPublic) return "private";
  // A property-less sighting is decidable without the property list:
  // nothing publishes it either way.
  if (propertyId == null) return "orphaned";
  if (properties == null) return null;
  const property = properties.find((p) => p.id === propertyId);
  if (property === undefined) return null;
  return property.isPublic ? "public" : "blocked";
}

/**
 * Short enough for a pill beside a record's title at 390px. Deliberately
 * names the *reason* a blocked record isn't published rather than lumping
 * it in with "Private" — the distinction is the whole point of the state.
 */
export function visibilityLabel(visibility: PublicVisibility): string {
  switch (visibility) {
    case "public":
      return "Public";
    case "private":
      return "Private";
    case "blocked":
      return "Property private";
    case "orphaned":
      // The row already renders "No property" as the property name, so the
      // badge states the consequence rather than repeating the cause.
      return "Not public";
  }
}

/** The badge's CSS modifier. Public is the one worth seeing at a glance. */
export function visibilityBadgeClass(visibility: PublicVisibility): string {
  return visibility === "public" ? "badge badge--public" : "badge";
}

/** Everything the filter control's "Not public" option should match. */
export type VisibilityFilter = "all" | "public" | "not-public";

export function matchesVisibilityFilter(
  choice: VisibilityFilter,
  visibility: PublicVisibility | null,
): boolean {
  if (choice === "all") return true;
  // With the property list unresolved we can't honestly exclude a row, and
  // silently dropping records would understate what the org has. Keep it.
  if (visibility === null) return true;
  return choice === "public" ? visibility === "public" : visibility !== "public";
}

export interface VisibilityCounts {
  total: number;
  /** Actually reachable by an anonymous visitor. */
  publicCount: number;
  /** Flagged public, held back only by their property's own flag. */
  blockedCount: number;
}

export function countVisibility(
  visibilities: readonly (PublicVisibility | null)[],
): VisibilityCounts {
  return {
    total: visibilities.length,
    publicCount: visibilities.filter((v) => v === "public").length,
    blockedCount: visibilities.filter((v) => v === "blocked").length,
  };
}

interface Noun {
  singular: string;
  plural: string;
}

/**
 * The line that answers the page's actual question. Every branch is here
 * because the naive `${n} of ${total} ${plural} are …` is ungrammatical in
 * it — "Your only activity", "None of your 1 activity are". D30 shipped
 * "Its 1 photos" and only looking caught it; this is the same trap.
 */
export function publicCountSummary(counts: VisibilityCounts, noun: Noun): string {
  const { total, publicCount } = counts;
  if (total === 0) return "";
  if (total === 1) {
    return publicCount === 1
      ? `Your only ${noun.singular} is on the public site.`
      : `Your only ${noun.singular} is not on the public site.`;
  }
  if (publicCount === 0) return `None of your ${total} ${noun.plural} are on the public site.`;
  if (publicCount === total) return `All ${total} ${noun.plural} are on the public site.`;
  return `${publicCount} of ${total} ${noun.plural} are on the public site.`;
}

/**
 * The compounding case, named with a number because a number makes someone
 * stop — D34's shipped precedent ("Its 3 photos are deleted too"), applied
 * to publication instead of deletion. Empty when it doesn't apply, so the
 * page says nothing about a situation the org isn't in.
 */
export function wouldPublishSummary(counts: VisibilityCounts, noun: Noun): string {
  const { blockedCount } = counts;
  if (blockedCount === 0) return "";
  return blockedCount === 1
    ? `1 more ${noun.singular} is marked public and would go online if its property were published.`
    : `${blockedCount} more ${noun.plural} are marked public and would go online if their property were published.`;
}

export const ACTIVITY_NOUN: Noun = { singular: "activity", plural: "activities" };
export const SIGHTING_NOUN: Noun = { singular: "sighting", plural: "sightings" };
