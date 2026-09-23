import { apiClient } from "./client";

export const runBfs = (payload: unknown) => apiClient.post("/algorithms/bfs", payload);
export const runGreedy = (payload: unknown) => apiClient.post("/algorithms/greedy", payload);
export const runAstar = (payload: unknown) => apiClient.post("/algorithms/astar", payload);
export const runPriority = () => apiClient.post("/algorithms/priority", {});
export const processRequest = (request_id: number) => apiClient.post("/algorithms/process-request", { request_id });
