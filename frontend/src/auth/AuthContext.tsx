import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { currentUser, login as loginRequest, logout as logoutRequest } from "../api/authApi";

export type CurrentUser = { id: number; email: string; full_name: string; role: string };
type AuthState = { user: CurrentUser | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => Promise<void> };
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!localStorage.getItem("bloodroute.access_token")) { setLoading(false); return; }
    currentUser().then((response) => setUser(response.data.user)).catch(() => { localStorage.removeItem("bloodroute.access_token"); localStorage.removeItem("bloodroute.refresh_token"); }).finally(() => setLoading(false));
  }, []);
  const login = async (email: string, password: string) => { const response = await loginRequest(email, password); localStorage.setItem("bloodroute.access_token", response.data.access_token); localStorage.setItem("bloodroute.refresh_token", response.data.refresh_token); setUser(response.data.user); };
  const logout = async () => { try { await logoutRequest(localStorage.getItem("bloodroute.refresh_token") ?? undefined); } finally { localStorage.removeItem("bloodroute.access_token"); localStorage.removeItem("bloodroute.refresh_token"); setUser(null); } };
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used within AuthProvider"); return context; }