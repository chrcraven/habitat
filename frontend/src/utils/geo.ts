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
