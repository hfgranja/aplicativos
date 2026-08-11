import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { api } from "../api/client.js";

const AuthContext = createContext(null);

const STORAGE_KEY = "agroprofit.auth";

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(loadStored);

  const login = useCallback(async (email, password) => {
    const result = await api.login(email, password);
    const session = {
      token: result.access_token,
      userId: result.user_id,
      tenantId: result.tenant_id,
      fullName: result.full_name,
      role: result.role,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    setAuth(session);
    return session;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setAuth(null);
  }, []);

  const value = useMemo(() => ({ auth, login, logout, isAuthenticated: Boolean(auth?.token) }), [auth, login, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
