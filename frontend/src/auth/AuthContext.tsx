import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError } from "../api/client";
import type { Session } from "../api/types";

interface AuthContextValue {
  session: Session | null;
  status: "loading" | "authenticated" | "anonymous";
  login: (email: string, password: string) => Promise<void>;
  signup: (data: {
    email: string;
    password: string;
    organization_name?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Sets the csrftoken cookie the client needs before any POST — see
      // src/api/client.ts and the module docstring on the backend's
      // apps/accounts/views.py.
      await api.auth.csrf().catch(() => undefined);
      try {
        const me = await api.auth.me();
        if (!cancelled) {
          setSession(me);
          setStatus("authenticated");
        }
      } catch (err) {
        if (!cancelled) {
          if (!(err instanceof ApiError && err.status === 403)) {
            // Unexpected failure (network, 5xx) — still fall back to the
            // login screen rather than spinning forever.
            console.error("Failed to load session", err);
          }
          setStatus("anonymous");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const me = await api.auth.login({ email, password });
    setSession(me);
    setStatus("authenticated");
  }, []);

  const signup = useCallback(
    async (data: { email: string; password: string; organization_name?: string }) => {
      const me = await api.auth.signup(data);
      setSession(me);
      setStatus("authenticated");
    },
    [],
  );

  const logout = useCallback(async () => {
    await api.auth.logout();
    setSession(null);
    setStatus("anonymous");
  }, []);

  return (
    <AuthContext.Provider value={{ session, status, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
