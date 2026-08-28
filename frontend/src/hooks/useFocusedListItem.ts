import { useEffect, useRef, useState } from "react";

// How far from the top of the scrollable container, and how tall, the
// "focus band" is — the zone a card has to be scrolled into to become the
// one auto-shown on the map. Approximates one card's typical height; real
// cards vary (more/less detail per record), so this is a reasonable
// average rather than a measurement of any specific card — see
// PropertyMapPage/PublicPropertyPage for how the focused card itself is
// then given a colored background at its own (real) height, rather than
// drawing a separate overlay band that would need to be kept in sync with
// that variable height.
const TRIGGER_OFFSET_PX = 12;
const TRIGGER_BAND_PX = 96;

/**
 * Scroll-spy: while `containerRef`'s content scrolls, tracks which item
 * (by id) currently sits in a thin trigger band near the top of the
 * container's visible area, using an IntersectionObserver rather than a
 * scroll-event handler (avoids hand-rolled scroll-position math, and
 * doesn't run on every scroll tick). Used to drive "only the item
 * scrolled into focus shows on the map" — see PropertyMapPage's and
 * PublicPropertyPage's combined activity/sighting list.
 *
 * Returns the focused id (or null if the list is empty) and a ref
 * callback to attach to each list item's DOM node, keyed by that item's
 * id.
 */
export function useFocusedListItem(
  containerRef: React.RefObject<HTMLElement | null>,
  itemIds: string[],
) {
  const [focusedId, setFocusedId] = useState<string | null>(itemIds[0] ?? null);
  const itemNodes = useRef(new Map<string, HTMLElement>());
  // Re-run setup when the *set* of ids changes, not on every render.
  const idsKey = itemIds.join("|");

  useEffect(() => {
    const container = containerRef.current;
    if (!container || itemIds.length === 0) {
      setFocusedId(null);
      return;
    }
    // Keep whatever's already focused if it's still in the list; otherwise
    // fall back to the first item (e.g. after a delete, or on first load).
    setFocusedId((prev) => (prev && itemIds.includes(prev) ? prev : itemIds[0]));

    let observer: IntersectionObserver | null = null;

    const setup = () => {
      observer?.disconnect();
      const height = container.clientHeight;
      const bottomMargin = Math.max(height - TRIGGER_OFFSET_PX - TRIGGER_BAND_PX, 0);
      observer = new IntersectionObserver(
        (entries) => {
          const intersecting = entries.filter((entry) => entry.isIntersecting);
          if (intersecting.length === 0) return;
          // Multiple cards can overlap a tall band at once (a short card,
          // or a fast scroll) — prefer whichever is nearest the top of it.
          intersecting.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
          const id = intersecting[0].target.getAttribute("data-item-id");
          if (id) setFocusedId(id);
        },
        {
          root: container,
          rootMargin: `-${TRIGGER_OFFSET_PX}px 0px -${bottomMargin}px 0px`,
          threshold: 0,
        },
      );
      itemNodes.current.forEach((node) => observer!.observe(node));
    };

    setup();
    // The container's height changes with viewport size/orientation
    // (the map above it is a vh-based height) — recompute the band.
    const resizeObserver = new ResizeObserver(setup);
    resizeObserver.observe(container);

    return () => {
      observer?.disconnect();
      resizeObserver.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idsKey]);

  const registerItem = (id: string) => (node: HTMLElement | null) => {
    if (node) itemNodes.current.set(id, node);
    else itemNodes.current.delete(id);
  };

  return { focusedId, registerItem };
}
