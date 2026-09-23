import { apiClient } from "./client";

export const listHospitals = () => apiClient.get("/hospitals");
export const getHospital = (id: string) => apiClient.get(`/hospitals/${id}`);
