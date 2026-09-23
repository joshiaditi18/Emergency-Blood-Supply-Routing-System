import type { ReactNode } from "react";

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "critical" | "success" | "warning" | "info" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function urgencyTone(value: string) {
  return value === "Critical" ? "critical" : value === "High" ? "warning" : value === "Fulfilled" || value === "Dispatched" || value === "Operational" || value === "Success" ? "success" : value === "Processing" || value === "Partially Allocated" || value === "En route" ? "info" : "neutral";
}
