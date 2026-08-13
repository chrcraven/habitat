import { useCallback, useMemo, useState } from "react";
import type { PolygonGeometry, Position } from "../api/types";

/** Manages the vertex list for a tap-to-draw polygon tool (see
 * ActivityFormPage) — no external drawing library, just plain state plus a
 * derived closed-ring geometry once there are enough points.
 *
 * `initial` seeds the vertex list when editing an existing shape (its
 * closing point is dropped — `geometry` re-closes the ring itself). Only
 * read once, on mount; callers that load the initial geometry
 * asynchronously should key the component (e.g. by record id) rather than
 * expect this to react to a later `initial` change. */
export function usePolygonPoints(initial?: Position[]) {
  const [points, setPoints] = useState<Position[]>(() => {
    if (!initial || initial.length === 0) return [];
    const last = initial[initial.length - 1];
    const first = initial[0];
    const isClosed = initial.length > 1 && last[0] === first[0] && last[1] === first[1];
    return isClosed ? initial.slice(0, -1) : initial;
  });

  const addPoint = useCallback((p: Position) => setPoints((pts) => [...pts, p]), []);
  const undo = useCallback(() => setPoints((pts) => pts.slice(0, -1)), []);
  const reset = useCallback(() => setPoints([]), []);

  const geometry: PolygonGeometry | null = useMemo(() => {
    if (points.length < 3) return null;
    return { type: "Polygon", coordinates: [[...points, points[0]]] };
  }, [points]);

  return { points, addPoint, undo, reset, geometry, canFinish: points.length >= 3 };
}
