import { useEffect, useState } from "react";
import type { Position } from "../api/types";

interface WatchState {
  position: Position | null;
  accuracy: number | null;
  error: string | null;
}

/** Continuously tracks the device's location while `active` — used for the
 * "drop a pin at my current position" boundary-drawing workflow (walk the
 * property, tap a pin at each corner) and the opt-in "show my location"
 * toggle on the property view page. Unlike utils/geo.ts#getCurrentPosition
 * (a single on-demand fetch, used by the sighting form's "use my
 * location" button), this keeps updating so a marker can follow the user
 * as they move. Stops watching — and releases the location permission
 * indicator — the moment `active` goes false or the component unmounts. */
export function useWatchPosition(active: boolean): WatchState {
  const [state, setState] = useState<WatchState>({
    position: null,
    accuracy: null,
    error: null,
  });

  useEffect(() => {
    if (!active) {
      setState({ position: null, accuracy: null, error: null });
      return;
    }
    if (!navigator.geolocation) {
      setState({
        position: null,
        accuracy: null,
        error: "Geolocation isn't available on this device/browser.",
      });
      return;
    }
    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setState({
          position: [pos.coords.longitude, pos.coords.latitude],
          accuracy: pos.coords.accuracy,
          error: null,
        });
      },
      (err) => {
        setState((s) => ({ ...s, error: err.message }));
      },
      { enableHighAccuracy: true, maximumAge: 5_000, timeout: 15_000 },
    );
    return () => navigator.geolocation.clearWatch(watchId);
  }, [active]);

  return state;
}
