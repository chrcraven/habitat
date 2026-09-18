import { useCallback, useEffect, useRef } from "react";
import type { ReactNode } from "react";
import type { Photo } from "../api/types";

/**
 * Click a photo to see it at full size (F1, requested by a user on
 * 2026-09-18: "I should be able to click on photos to view a larger
 * version").
 *
 * Both the thumbnail trigger and the overlay live in this one module
 * rather than being written twice, for the reason D6 and D34 record: the
 * original D6 defect was one content-type check copy-pasted into four
 * upload sites and wrong in all four. The two grids that render photos
 * (PhotoUploader, PublicPhotoGrid) differ only in their chrome — a delete
 * button and an upload control on one, nothing on the other — so the
 * chrome stays local and the decision-bearing part is here.
 *
 * Why this is free, which is why it outranked everything else in the
 * queue: nothing resizes an upload and no derivative is ever generated
 * (D32), so `photo.url` is already the full-size image and the thumbnail
 * has already downloaded every byte of it — measured at 1,899,250 B for a
 * real photo, into an 84x84 box that needs ~17 KB. The lightbox re-uses
 * that same URL, so it costs **zero additional image bytes**: the browser
 * serves it from cache, and D33's validator (`ETag` +
 * `Cache-Control: private, no-cache`) turns any revalidation into a 304
 * with an empty body. Confirmed against the live host, not assumed.
 *
 * This deliberately does NOT settle D32 (derive-and-keep vs.
 * downscale-on-upload). That is a decision about what is *stored*; this
 * only changes what is *displayed* — no derivative, no migration, no new
 * endpoint. D6 also declined `Content-Disposition: attachment`, so the
 * bytes were already reachable by "open image in new tab" on both the
 * authenticated and public paths and this exposes nothing new.
 */

/** Presentation: this is the app's first overlay of any kind — there was
 * no `<dialog>`, `showModal`, modal or lightbox anywhere in `frontend/src`
 * before it, so there was no precedent to copy and the choice had to be
 * made rather than inherited.
 *
 * Native `<dialog>` + `showModal()` rather than a hand-rolled div, because
 * the browser then owns the three things that are easy to get subtly
 * wrong: Escape closes it, focus is trapped inside it and restored to the
 * trigger on close, and it renders in the **top layer** — above every
 * `z-index` on the page. That last one is not theoretical here: the app
 * has a `position: fixed` feedback widget on every authenticated screen,
 * and a 2026-09-02 session already had to fix that same widget clipping a
 * primary action. A `z-index: 31` div would be one future stacking
 * context away from the same bug; the top layer cannot be out-stacked.
 */
export function PhotoLightbox({
  photos,
  index,
  onNavigate,
  onClose,
}: {
  photos: Photo[];
  index: number;
  onNavigate: (index: number) => void;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  // Everything closes through the element's own close(), never by calling
  // props.onClose directly, so the Escape key and our own buttons take
  // exactly one path. `onClose` on the element is what tells the parent to
  // unmount us, and Escape fires it without asking us first.
  const requestClose = useCallback(() => dialogRef.current?.close(), []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || dialog.open) return;
    // showModal() is imperative because there is no declarative equivalent:
    // rendering `<dialog open>` opens it *non*-modally — no top layer, no
    // backdrop, no focus trap, no Escape. Every property this component
    // relies on comes from this call, not from the element.
    dialog.showModal();
  }, []);

  // A photo can leave the list underneath us (an upload finishing, a
  // delete on some other tab). Clamp rather than render a blank frame.
  const safeIndex = Math.min(Math.max(index, 0), photos.length - 1);
  useEffect(() => {
    // onClose directly rather than requestClose: with no photos left the
    // render below returns null, so there is no <dialog> for close() to act
    // on and the parent would otherwise stay stuck in its "open" state.
    if (photos.length === 0) onClose();
  }, [photos.length, onClose]);

  const photo = photos[safeIndex];
  const total = photos.length;
  const hasPrev = safeIndex > 0;
  const hasNext = safeIndex < total - 1;

  // Deliberately clamped at both ends rather than wrapping. With the
  // "2 of 3" counter right there, a disabled arrow says "that's all of
  // them" in a way a silent wrap back to the first photo does not.
  const go = useCallback(
    (delta: number) => {
      const next = safeIndex + delta;
      if (next >= 0 && next < total) onNavigate(next);
    },
    [safeIndex, total, onNavigate],
  );

  // The bug both this effect and the next one exist for, because it is not
  // obvious and it shipped in the first draft: clicking Next until the last
  // photo *disables* Next, a disabled <button> cannot keep focus, and the
  // browser therefore drops focus to <body> — which is outside the dialog.
  // A keydown there never bubbles through the dialog, so the arrow keys
  // silently died and the only way back was to Tab. Escape kept working
  // throughout, which is exactly what makes it easy to miss: that one is
  // the browser's, handled on the dialog itself rather than by us.
  //
  // Binding the keys on the *document* removes the dependency on where
  // focus happens to be. It is safe precisely because the dialog is modal:
  // everything else on the page is inert while it is open.
  //
  // Be honest about what this line is worth, because it was measured
  // rather than assumed (the D38/D40 rule). Built alone, it fixes the keys
  // and leaves focus stranded — 3 tests red. The focus effect below, built
  // alone, passes **all 40**, including every key test, because restoring
  // focus also restores the bubbling path. So *nothing catches this
  // listener on its own*: two guesses at a case that would (clicking the
  // photo, clicking the bar) both came back green, since Chromium keeps
  // focus inside a modal when you click a non-focusable child — the strand
  // is specific to an element leaving the focus order.
  //
  // It stays anyway, for a reason specific to this repo: there is no
  // frontend test runner, so those 3 red tests are a one-off measurement
  // and not a standing guard. Without this listener the arrow keys work
  // only as a side effect of the focus effect below — the exact coupling
  // that produced the bug — and the next person to read that effect as an
  // optional a11y nicety would silently break them again with nothing to
  // catch it.
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        go(1);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [go]);

  // The other half of the same defect, and the half every test catches:
  // leaving focus on <body> inside an open modal strands anyone navigating
  // by keyboard or screen reader — their next Tab restarts from the top of
  // the document. Hand focus back to whichever arrow is still live, which
  // is also where someone stepping through the photos wants to be.
  //
  // Keyed on the index because that is when a button's disabled state
  // changes, which is the only way measured so far for focus to escape.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || dialog.contains(document.activeElement)) return;
    const fallback = dialog.querySelector<HTMLButtonElement>(
      ".photo-lightbox__nav:not(:disabled), .photo-lightbox__close",
    );
    fallback?.focus();
  }, [safeIndex]);

  if (!photo) return null;

  return (
    <dialog
      ref={dialogRef}
      className="photo-lightbox"
      aria-label="Photo viewer"
      onClose={onClose}
      // Clicking the darkened surround closes. The ::backdrop pseudo-element
      // is not a child and never receives clicks, so the element that
      // actually gets them is the dialog box itself — which is why the
      // stylesheet sizes it to the whole viewport and centres its contents
      // with flex. An `e.target === currentTarget` test therefore means
      // "clicked the surround, not the photo or a control".
      onClick={(e) => {
        if (e.target === e.currentTarget) requestClose();
      }}
    >
      <img
        className="photo-lightbox__image"
        src={photo.url}
        // Positional, not descriptive. Nothing in Habitat describes what is
        // in a photo — there is no caption or alt-text field on either photo
        // model — so a real description would have to be invented here.
        // Naming the position at least distinguishes this image from the
        // others; the missing description is recorded in the manual's
        // limitations rather than papered over.
        alt={total > 1 ? `Photo ${safeIndex + 1} of ${total}` : "Photo"}
      />

      <div className="photo-lightbox__bar">
        {total > 1 && (
          <>
            <button
              type="button"
              className="photo-lightbox__nav"
              onClick={() => go(-1)}
              disabled={!hasPrev}
              aria-label="Previous photo"
            >
              ‹
            </button>
            <span className="photo-lightbox__count">
              {safeIndex + 1} of {total}
            </span>
            <button
              type="button"
              className="photo-lightbox__nav"
              onClick={() => go(1)}
              disabled={!hasNext}
              aria-label="Next photo"
            >
              ›
            </button>
          </>
        )}
        <button
          type="button"
          className="photo-lightbox__close"
          onClick={requestClose}
        >
          Close
        </button>
      </div>
    </dialog>
  );
}

/** One photo in a grid, as a button that opens the lightbox.
 *
 * `children` is the thumbnail's own chrome — today that is
 * PhotoUploader's delete button, which must stay a **sibling** of the
 * open-button rather than sitting inside it. Nesting one button in
 * another is invalid HTML, and this repo has already paid for the
 * equivalent mistake once: a `<form>` nested in a `<form>` (2026-08-14)
 * that browsers silently reparented, which broke the control in practice
 * while looking fine in the diff.
 *
 * The `<img>` keeps `alt=""` because the button carries the accessible
 * name; labelling both would announce the same photo twice. */
export function PhotoThumb({
  photo,
  position,
  total,
  onOpen,
  children,
}: {
  photo: Photo;
  position: number;
  total: number;
  onOpen: () => void;
  children?: ReactNode;
}) {
  return (
    <div className="photo-thumb">
      <button
        type="button"
        className="photo-thumb__open"
        onClick={onOpen}
        aria-label={total > 1 ? `View photo ${position} of ${total}` : "View photo"}
      >
        <img src={photo.url} alt="" loading="lazy" />
      </button>
      {children}
    </div>
  );
}
