import { apiClient } from "./client";

export const login = (email: string, password: string) => apiClient.post("/auth/login", { email, password });
export const register = (payload: { email: string; password: string; full_name: string }) => apiClient.post("/auth/register", payload);
export const currentUser = () => apiClient.get("/auth/me");
export const logout = (refresh_token?: string) => apiClient.post("/auth/logout", { refresh_token });
export const refresh = () => apiClient.post("/auth/refresh", { refresh_token: localStorage.getItem("bloodroute.refresh_token") });
