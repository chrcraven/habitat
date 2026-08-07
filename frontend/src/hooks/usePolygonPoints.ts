import { useCallback, useMemo, useState } from "react";
import type { PolygonGeometry, Position } from "../api/types";

/** Manages the vertex list for a tap-to-draw polygon tool (see
 * ActivityFormPage) — no external drawing library, just plain state plus a
 * derived closed-ring geometry once there are enough points. */
export function usePolygonPoints() {
  const [points, setPoints] = useState<Position[]>([]);

  const addPoint = useCallback((p: Position) => setPoints((pts) => [...pts, p]), []);
  const undo = useCallback(() => setPoints((pts) => pts.slice(0, -1)), []);
  const reset = useCallback(() => setPoints([]), []);

  const geometry: PolygonGeometry | null = useMemo(() => {
    if (points.length < 3) return null;
    return { type: "Polygon", coordinates: [[...points, points[0]]] };
  }, [points]);

  return { points, addPoint, undo, reset, geometry, canFinish: points.length >= 3 };
}
