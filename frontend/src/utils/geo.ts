import type { PolygonGeometry, Position } from "../api/types";

export type BBox = [number, number, number, number]; // [minLng, minLat, maxLng, maxLat]

/** Bounding box of a Polygon's outer ring (Phase 1 has no multi-part
 * geometries) — enough for MapLibre's fitBounds, no turf dependency. */
export function polygonBounds(geometry: PolygonGeometry): BBox {
  const ring = geometry.coordinates[0] ?? [];
  return positionsBounds(ring);
}

export function positionsBounds(positions: Position[]): BBox {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;
  for (const [lng, lat] of positions) {
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  return [minLng, minLat, maxLng, maxLat];
}

export function pointBounds(position: Position, padDegrees = 0.002): BBox {
  const [lng, lat] = position;
  return [lng - padDegrees, lat - padDegrees, lng + padDegrees, lat + padDegrees];
}

export function mergeBounds(a: BBox, b: BBox): BBox {
  return [
    Math.min(a[0], b[0]),
    Math.min(a[1], b[1]),
    Math.max(a[2], b[2]),
    Math.max(a[3], b[3]),
  ];
}

/**
 * Is this position inside the polygon's outer ring?
 *
 * Standard ray-casting, and deliberately hand-rolled rather than pulling
 * in turf for one predicate — the same "don't add a dependency for one
 * function" reasoning as polygonBounds above. Used by the quick-log flow
 * to work out which property the user just dropped a point on, so they
 * don't have to pick one first (see pages/QuickLogPage.tsx).
 *
 * Treated as planar lng/lat. At a single property's scale that's exact
 * enough — the error from ignoring the earth's curvature is far below the
 * accuracy of a hand-drawn boundary — and a wrong answer here only means
 * the user picks the property manually, which the flow already allows.
 * Holes (inner rings) are ignored: Phase 1 boundaries don't have any.
 */
export function positionInPolygon(position: Position, geometry: PolygonGeometry): boolean {
  const ring = geometry.coordinates[0] ?? [];
  if (ring.length < 3) return false;
  const [x, y] = position;
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const straddles = yi > y !== yj > y;
    if (straddles && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/** Wraps the browser Geolocation API in a Promise — used to capture a
 * sighting at the device's current location (see docs/use-cases.md (b)). */
export function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation isn't available on this device/browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10_000,
    });
  });
}
