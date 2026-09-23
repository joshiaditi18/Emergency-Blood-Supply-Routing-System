import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000/api",
  timeout: 8000,
});

export const isDemoMode = !import.meta.env.VITE_API_BASE_URL;

export class ApiClientError extends Error {
  status?: number;
  code?: string;
  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
  }
}

let refreshing: Promise<string | null> | null = null;

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("bloodroute.access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  if (error.response?.status === 401 && original && !original._retry && !original.url?.includes("/auth/")) {
    original._retry = true;
    refreshing ??= import("./authApi").then(({ refresh }) => refresh()).then((response) => {
      const token = response.data?.access_token ?? null;
      if (token) localStorage.setItem("bloodroute.access_token", token);
      return token;
    }).catch(() => null).finally(() => { refreshing = null; });
    const token = await refreshing;
    if (token) {
      original.headers.Authorization = `Bearer ${token}`;
      return apiClient(original);
    }
    localStorage.removeItem("bloodroute.access_token");
    localStorage.removeItem("bloodroute.refresh_token");
  }
  const body = error.response?.data?.error;
  throw new ApiClientError(body?.message ?? "Unable to complete the request", error.response?.status, body?.code);
});
