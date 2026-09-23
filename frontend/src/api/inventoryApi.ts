import { apiClient } from "./client";

export const listInventory = () => apiClient.get("/inventory");
export const getHospitalInventory = (hospitalId: string) => apiClient.get(`/inventory/${hospitalId}`);
