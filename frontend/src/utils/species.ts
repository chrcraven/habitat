import { api } from "../api/client";
import type { Species } from "../api/types";

/**
 * Resolve what the user picked *or typed* into a species id, creating the
 * species if it's genuinely new.
 *
 * Shared by the app's only two sighting-creation sites — SightingFormPage
 * and QuickLogPage — deliberately, rather than copied into each. A
 * sighting's species is a required FK with no default, so whatever this
 * function does is the difference between "I can log what I just saw" and
 * a dead end; the two entry points must not drift on it.
 *
 * **Why quick log needed this at all (D24, 2026-09-12).** A brand-new
 * organization is seeded with 3 workflow states and 8 activity types by
 * `apps/activities/signals.py`, and with **no species** — the empty
 * species list is a decided product stance (owner, 2026-08-28: no starter
 * list), not an oversight. The untraced consequence was that quick log's
 * *activity* path had both of its required reference lists pre-filled on
 * day one while its *sighting* path had its one required list empty and no
 * way to fill it, so the simplest first action in the app — one tap for "I
 * saw a thing" — could not complete on a new account. It refused with
 * "Pick a species for this sighting", an instruction the screen gave no
 * way to follow. The fix is this affordance, **not** seeding a starter
 * list, which would reverse the owner's decision.
 *
 * An existing name is **reused rather than re-created**, case-insensitively.
 * That is deliberately stricter than the database, whose uniqueness
 * constraint on (organization, common_name) is case-*sensitive* and would
 * happily store "crabgrass" next to "Crabgrass". Typing a name you already
 * have should select it, not fail and not quietly fork the list in two —
 * there is no species merge tool to clean that up afterwards.
 *
 * @param speciesId The picker's value; a real id wins over anything typed.
 * @param newSpeciesName Free text from the "or add a new species" field.
 * @param known The org's species list as already loaded by the caller.
 * @returns The species id to save against, or null if the user gave neither.
 */
export async function resolveSpeciesId(
  speciesId: number | "",
  newSpeciesName: string,
  known: Species[],
): Promise<number | null> {
  if (speciesId !== "") return speciesId;
  const typed = newSpeciesName.trim();
  if (!typed) return null;

  const match = known.find(
    (s) => s.common_name.trim().toLowerCase() === typed.toLowerCase(),
  );
  if (match) return match.id;

  return (await api.species.create({ common_name: typed })).id;
}
