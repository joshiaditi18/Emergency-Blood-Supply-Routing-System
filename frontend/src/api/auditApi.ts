import { apiClient } from "./client";

export const listAuditLogs = () => apiClient.get("/audit-logs");
