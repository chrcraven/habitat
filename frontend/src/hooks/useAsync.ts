import { useCallback, useEffect, useState } from "react";
import type { DependencyList } from "react";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** Small fetch-on-mount-and-when-deps-change helper — Phase 1 has few
 * enough data-fetching pages that a full library (react-query etc.) isn't
 * worth the dependency yet; revisit if this starts getting duplicated
 * awkwardly. */
export function useAsync<T>(
  fn: () => Promise<T>,
  deps: DependencyList,
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            data: null,
            loading: false,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      });
    return () => {
      cancelled = true;
    };
    // `fn` is intentionally excluded — callers pass their own `deps` to
    // control when this re-runs, same contract as useEffect itself.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey]);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);
  return { ...state, reload };
}
