import { apiClient } from "./client";

export const listRequests = () => apiClient.get("/requests");
export const createRequest = (payload: unknown) => apiClient.post("/requests", payload);
export const getRequest = (id: string) => apiClient.get(`/requests/${id}`);
