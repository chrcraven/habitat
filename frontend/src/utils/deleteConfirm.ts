/**
 * Confirm-dialog text for deleting a record that takes its photos with it.
 *
 * Why this is one function rather than a string at each call site: the
 * original D6 defect was a single content-type check copy-pasted into four
 * upload sites and wrong in all four, and D34 is that shape one layer up —
 * two delete dialogs that were four words each ("Delete this activity?")
 * precisely because nobody had ever read them side by side. A shared builder
 * means the next record type that grows a delete button either uses this
 * wording or has to deliberately opt out of it.
 *
 * Why it names a *count* instead of a blanket "and any attached photos":
 * photos are the only thing in Habitat that can't be re-typed from memory
 * (`docs/open-questions.md`, D32 — everything else is text a user could
 * enter again), and both `ActivityPhoto.activity` and
 * `SightingPhoto.sighting` are `on_delete=CASCADE`, so this dialog is the
 * last thing standing between a click and the permanent loss of the only
 * unrederivable content in the database. A number is what makes someone
 * stop; "and its photos" reads as boilerplate when there are none and
 * badly understates it when there are twelve.
 *
 * Why the wording is shorter than the property dialog's, not longer: a
 * property delete is recoverable, so its dialog has a 30-day restore path to
 * explain. These have nothing to offer but the warning, and burying
 * "can't be undone" in a third clause is how it stops being read.
 */
export type DeletableKind = "activity" | "sighting";

/**
 * @param photoCount how many photos are attached, or `null` if that couldn't
 *   be determined (the lookup failed). `null` deliberately still warns, using
 *   the hedged wording — a delete must never be blocked, or made to look
 *   safe, just because a count request didn't come back.
 */
export function confirmDeleteMessage(
  kind: DeletableKind,
  photoCount: number | null,
): string {
  const head = `Delete this ${kind}?`;
  const tail = "This can't be undone.";

  if (photoCount === null) {
    return `${head} Any photos attached to it are deleted too. ${tail}`;
  }
  if (photoCount === 0) {
    return `${head} ${tail}`;
  }
  // Singular matters here: "Its 1 photos are deleted too" is exactly the
  // class of slip D30 shipped ("All 1 sightings are plotted…") and that was
  // only caught by looking at a screenshot rather than at an assertion.
  const photos =
    photoCount === 1 ? "Its photo is deleted too." : `Its ${photoCount} photos are deleted too.`;
  return `${head} ${photos} ${tail}`;
}
