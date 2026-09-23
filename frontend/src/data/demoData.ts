export type Urgency = "Critical" | "High" | "Medium" | "Normal";
export type RequestStatus = "Pending" | "Processing" | "Partially Allocated" | "Fulfilled" | "Dispatched" | "Failed";

export const demoNotice = "DEMO MODE - Data shown here is fictional and does not represent live blood availability.";

export const navItems = [
  { label: "Dashboard", path: "/dashboard", icon: "LayoutDashboard" },
  { label: "Blood Requests", path: "/requests", icon: "Siren" },
  { label: "Hospitals", path: "/hospitals", icon: "Building2" },
  { label: "Inventory", path: "/inventory", icon: "Droplets" },
  { label: "Routes & Dispatch", path: "/routes", icon: "Route" },
  { label: "Algorithm Center", path: "/algorithms", icon: "Network" },
  { label: "Reports", path: "/reports", icon: "ChartNoAxesCombined" },
  { label: "Users & Roles", path: "/users", icon: "Users" },
  { label: "Audit Logs", path: "/audit", icon: "ScrollText" },
  { label: "Settings", path: "/settings", icon: "Settings2" },
] as const;

export const bloodGroups = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

export const inventory = bloodGroups.map((group, index) => ({
  group,
  available: [18, 42, 12, 29, 16, 24, 8, 21][index],
  reserved: [4, 8, 2, 5, 3, 7, 1, 4][index],
  threshold: [12, 20, 8, 14, 10, 12, 6, 10][index],
}));

export const hospitals = [
  { id: "H-01", name: "Northbridge Medical Center", city: "New Delhi", connected: 4, availability: "Stable", status: "Operational", lat: 28.642, lng: 77.214 },
  { id: "H-02", name: "St. Anselm Emergency Hospital", city: "New Delhi", connected: 3, availability: "Watch", status: "Operational", lat: 28.615, lng: 77.229 },
  { id: "H-03", name: "Civic Heart Institute", city: "New Delhi", connected: 5, availability: "Stable", status: "Operational", lat: 28.598, lng: 77.187 },
  { id: "H-04", name: "Eastline Trauma Hospital", city: "New Delhi", connected: 3, availability: "Low O-", status: "Operational", lat: 28.628, lng: 77.274 },
  { id: "H-05", name: "Meridian Children’s Hospital", city: "New Delhi", connected: 2, availability: "Stable", status: "Standby", lat: 28.575, lng: 77.242 },
  { id: "H-06", name: "Riverside General", city: "New Delhi", connected: 4, availability: "Stable", status: "Operational", lat: 28.661, lng: 77.254 },
];

export const requests = [
  { id: "REQ-1048", blood: "O+", units: 8, urgency: "Critical" as Urgency, requested: "2 min ago", hospital: "St. Anselm Emergency Hospital", status: "Processing" as RequestStatus, priority: 96 },
  { id: "REQ-1047", blood: "A-", units: 4, urgency: "High" as Urgency, requested: "18 min ago", hospital: "Eastline Trauma Hospital", status: "Partially Allocated" as RequestStatus, priority: 74 },
  { id: "REQ-1046", blood: "B+", units: 6, urgency: "Medium" as Urgency, requested: "41 min ago", hospital: "Civic Heart Institute", status: "Fulfilled" as RequestStatus, priority: 51 },
  { id: "REQ-1045", blood: "AB+", units: 2, urgency: "Normal" as Urgency, requested: "1 hr ago", hospital: "Meridian Children’s Hospital", status: "Dispatched" as RequestStatus, priority: 32 },
  { id: "REQ-1044", blood: "O-", units: 10, urgency: "Critical" as Urgency, requested: "2 hrs ago", hospital: "Northbridge Medical Center", status: "Failed" as RequestStatus, priority: 88 },
];

export const dispatches = [
  { id: "DSP-022", origin: "Northbridge Medical Center", destination: "St. Anselm Emergency Hospital", group: "O+", units: 8, distance: "6.4 km", eta: "14 min", status: "En route" },
  { id: "DSP-021", origin: "Civic Heart Institute", destination: "Meridian Children’s Hospital", group: "AB+", units: 2, distance: "8.1 km", eta: "22 min", status: "Delivered" },
  { id: "DSP-020", origin: "Riverside General", destination: "Eastline Trauma Hospital", group: "A-", units: 4, distance: "5.7 km", eta: "Completed", status: "Delivered" },
];

export const urgencyData = [
  { name: "Critical", value: 18, fill: "#d85b4f" },
  { name: "High", value: 27, fill: "#e39a52" },
  { name: "Medium", value: 36, fill: "#5c9d98" },
  { name: "Normal", value: 19, fill: "#b8c6c7" },
];

export const trendData = [
  { day: "Mon", requests: 18, fulfilled: 14 }, { day: "Tue", requests: 26, fulfilled: 20 },
  { day: "Wed", requests: 22, fulfilled: 19 }, { day: "Thu", requests: 31, fulfilled: 25 },
  { day: "Fri", requests: 28, fulfilled: 23 }, { day: "Sat", requests: 35, fulfilled: 28 },
  { day: "Sun", requests: 29, fulfilled: 24 },
];

export const auditLogs = [
  { time: "09:42:18", user: "A. Mercer", action: "ALLOCATE_BLOOD", resource: "REQ-1048", result: "Success", ip: "10.24.8.14" },
  { time: "09:39:04", user: "Dispatch desk", action: "ROUTE_CALCULATED", resource: "DSP-022", result: "Success", ip: "10.24.8.08" },
  { time: "09:31:52", user: "R. Patel", action: "LOGIN_SUCCESS", resource: "User", result: "Success", ip: "10.24.8.22" },
  { time: "09:18:27", user: "System", action: "INVENTORY_UPDATE", resource: "H-04 / O-", result: "Success", ip: "10.24.8.01" },
];

export const algorithmGraph = {
  H1: ["H2", "H3"], H2: ["H1", "H4", "H5"], H3: ["H1", "H4"], H4: ["H2", "H3", "H6"], H5: ["H2", "H6"], H6: ["H4", "H5"],
};

export const algorithmTreeRows = [
  { key: "Critical · 96", id: "REQ-1048", color: "black", action: "Root" },
  { key: "High · 74", id: "REQ-1047", color: "red", action: "Recolored" },
  { key: "Medium · 51", id: "REQ-1046", color: "black", action: "Left rotation" },
];
