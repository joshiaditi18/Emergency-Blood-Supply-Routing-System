import { apiClient } from "./client";

export const listRoutes = () => apiClient.get("/routes");
export const getRequestRoute = (requestId: string) => apiClient.get(`/routes/${requestId}`);
