import { apiClient } from "./client";

export const currentUser = () => apiClient.get("/auth/me");