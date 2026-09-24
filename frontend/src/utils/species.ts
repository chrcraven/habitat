import { ApiError, api } from "../api/client";
import type { Species } from "../api/types";

/** The one name comparison this module makes, deliberately in one place.
 *
 * Both the pre-create check and the post-refusal re-read below have to
 * match the *same* way, and case-insensitively — the whole point of
 * re-reading is to find a species the caller's snapshot missed, and a
 * case-sensitive re-read would find "Crabgrass" absent when the user
 * retried as "crabgrass" and fork the list on exactly the retry the
 * re-read exists to prevent. Two copies that both happen to call
 * `.toLowerCase()` today is one rename away from being one copy that
 * doesn't; one function can't drift from itself. */
function findByName(list: Species[], typed: string): Species | undefined {
  const wanted = typed.trim().toLowerCase();
  return list.find((s) => s.common_name.trim().toLowerCase() === wanted);
}

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
 * **`known` is a snapshot, and that is what D62 was (2026-09-25).** The
 * contract above held only for the list the caller had loaded *before the
 * user started typing*, and both callers save the species and the record
 * in two separate writes. So when the record write failed after the
 * species write had succeeded — a dropped connection mid-save being the
 * ordinary way, since nothing in the app bounds a request — pressing Save
 * again re-ran this against a `known` that could never contain the species
 * the first attempt had just created. Measured against the real backend,
 * both retries were bad and neither was recoverable without a reload,
 * which in quick log discards the dropped point and the typed notes:
 *
 *   retry with the same text  `validate_common_name` matches exactly, 400,
 *                             and the refusal ("You already have a species
 *                             with that name.") is rendered while saving a
 *                             *sighting*. Every later Save repeats it.
 *                             **Wedged.**
 *   retry with different      D26's guard is deliberately case-sensitive,
 *   casing                    so the create is accepted, 201 — and the
 *                             list is **forked permanently**.
 *
 * Hence the two re-reads below — and **which one does what was measured,
 * not reasoned about, because the obvious answer is wrong.** Four variants
 * were built against a fake backend carrying the real one's semantics
 * (exact-match refusal, so a differently-cased duplicate is *accepted*),
 * over nine cases:
 *
 *   pre-fix                  3 red   both rows above, plus the race
 *   re-read only after a     2 red   **the fork is still live** — and this
 *     refusal                        is the literal reading of the item
 *                                    that queued the fix
 *   re-read only before      1 red   closes both rows; only the race
 *     creating                       survives
 *   re-read, compared        2 red   the fork, *and* the ordinary
 *     case-sensitively               already-in-the-list case
 *
 * The queued build note named case sensitivity as the trap, correctly, and
 * put it in the wrong place: a *catch* block never runs on the casing path
 * at all, because nothing refuses that write. So the re-read *before*
 * creating is what closes both retries, and the one *after* a refusal
 * earns its place only against a genuine two-client race — the reverse of
 * the split this comment first claimed. D46's shape (a correct observation
 * applied to the wrong option), this time in a build note.
 *
 * The fourth row is the shared `findByName` being visibly load-bearing:
 * making the comparison exact breaks a case the re-reads have nothing to
 * do with, because there is only one comparison to break.
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

  const match = findByName(known, typed);
  if (match) return match.id;

  // Not in the caller's snapshot — which is the one case where the
  // snapshot's age matters, so spend a request to ask. Only ever on the
  // "add a new species" path, which already costs a POST.
  const fresh = await api.species.list().catch(() => null);
  if (fresh) {
    const freshMatch = findByName(fresh, typed);
    if (freshMatch) return freshMatch.id;
  }

  try {
    return (await api.species.create({ common_name: typed })).id;
  } catch (err) {
    // A **400 only**. That is the server having been reached and having
    // made a judgement, which is the only case where "the name may already
    // exist" follows. A dropped connection or a 5xx says nothing about the
    // list, and re-reading it would fail too — re-raise those unchanged so
    // the caller reports what actually happened.
    if (!(err instanceof ApiError) || err.status !== 400) throw err;
    const after = await api.species.list().catch(() => null);
    const afterMatch = after && findByName(after, typed);
    if (afterMatch) return afterMatch.id;
    // Refused for some other reason (a blank name, a length cap) — the
    // server's own message is the useful one.
    throw err;
  }
}
