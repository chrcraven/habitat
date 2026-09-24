import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

/**
 * The application's one live region, and the hook that feeds it (D57a,
 * 2026-09-24).
 *
 * Why this exists at all: there are 72 `form-error` render sites across 37
 * files and, before this, **zero** `aria-live`, `role="alert"` or
 * `role="status"` anywhere in the app. D21 (2026-09-11) made every failure
 * carry a non-empty message; D55a (2026-09-23) made the five destructive
 * deletes that destroy the user's own records stop failing silently. For
 * someone who cannot see the screen neither changed anything — the text
 * mounted into the DOM unannounced. The app's entire recovery story was
 * measured as "one undo and an error message", and that story was
 * visual-only.
 *
 * ## The attractive wrong fix, and why this is not it
 *
 * Adding `role="alert"` to each of those 72 conditionally-mounted
 * `<p className="form-error">` elements *looks* exactly like the fix and is
 * unreliable at most of them: a live region inserted into the DOM in the
 * same moment its text arrives is missed by many screen-reader/browser
 * pairs, because there is no prior empty region for them to have been
 * watching. **The region has to already be in the document and have its
 * text change.** Hence one always-mounted region, fed by a hook, rather
 * than 72 edits that work on the implementer's machine and not a user's.
 *
 * ## Why there are two regions rather than one
 *
 * A screen reader generally does not re-announce a region whose text is
 * set to the value it already holds — so pressing Delete twice and failing
 * identically twice would announce once. Writing alternately into two
 * regions (and blanking the other) guarantees a real text *change* every
 * time, whatever the message. This is the standard double-buffer for live
 * regions and it is the reason `announce` is not simply `setState`.
 *
 * ## Scope
 *
 * Deliberately failures only, and deliberately `assertive`: the caller has
 * just pressed a destructive button and needs to know it did not happen.
 * Whether *success* and status messages ("Saved", "Copied!", "Resent")
 * should announce too is D57b's Q1 and is the owner's — an over-eager live
 * region is its own accessibility defect, so this does not pre-empt it by
 * quietly announcing everything.
 *
 * Mounted in App.tsx outside the route table, so it covers the public
 * pages as well as the authenticated app, and so it survives navigation
 * (a region torn down and rebuilt per route is the mounting problem again).
 */
const AnnouncerContext = createContext<(message: string) => void>(() => {});

/**
 * Announce a message to assistive technology. Pass the **same string the
 * user sees**, not a paraphrase of it — on almost every real failure that
 * string is D21's `statusFallback` or the server's own `detail` rather
 * than a hand-written fallback (see D55a's own correction), and a
 * summary invented here would disagree with what is on screen.
 *
 * A falsy message is ignored, so `announce(err.message)` is safe where the
 * message may be empty.
 */
export function useAnnounce() {
  return useContext(AnnouncerContext);
}

export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [slots, setSlots] = useState<[string, string]>(["", ""]);
  const nextSlot = useRef(0);

  const announce = useCallback((message: string) => {
    if (!message) return;
    const slot = nextSlot.current;
    nextSlot.current = slot === 0 ? 1 : 0;
    // Blanking the other slot is what makes the next call to this one a
    // change rather than a no-op. Blanking is not itself announced.
    setSlots(slot === 0 ? [message, ""] : ["", message]);
  }, []);

  const value = useMemo(() => announce, [announce]);

  return (
    <AnnouncerContext.Provider value={value}>
      {children}
      {/* `role="alert"` already implies assertive + atomic; both are
          restated because the combination is what is actually supported
          consistently across screen readers, and because an `aria-live`
          a later edit removes would silently downgrade this to nothing.
          .visually-hidden clips rather than hides — see its own comment in
          index.css for why `display: none` would break this outright. */}
      <div
        className="visually-hidden"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        data-announcer-slot="0"
      >
        {slots[0]}
      </div>
      <div
        className="visually-hidden"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        data-announcer-slot="1"
      >
        {slots[1]}
      </div>
    </AnnouncerContext.Provider>
  );
}
