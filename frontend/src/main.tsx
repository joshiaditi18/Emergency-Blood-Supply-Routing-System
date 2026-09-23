import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Algorithms from "./pages/Algorithms";
import LiveAlgorithms from "./pages/LiveAlgorithms";
import { Reports, Settings, Users } from "./pages/Operations";
import { LiveAudit, LiveHospitals, LiveInventory, LiveRequests, LiveRoutes } from "./pages/LiveOperations";
import Login from "./pages/Login";
import "./styles.css";

function App() { return <AuthProvider><BrowserRouter><Routes><Route path="/login" element={<Login />} /><Route element={<ProtectedRoute />}><Route element={<AppLayout />}><Route path="/" element={<Navigate to="/dashboard" replace />} /><Route path="/dashboard" element={<Dashboard />} /><Route path="/requests" element={<LiveRequests />} /><Route path="/hospitals" element={<LiveHospitals />} /><Route path="/inventory" element={<LiveInventory />} /><Route path="/routes" element={<LiveRoutes />} /><Route path="/algorithms" element={<LiveAlgorithms />} /><Route path="/reports" element={<Reports />} /><Route path="/users" element={<Users />} /><Route path="/audit" element={<LiveAudit />} /><Route path="/settings" element={<Settings />} /></Route></Route><Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes></BrowserRouter></AuthProvider>; }

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
