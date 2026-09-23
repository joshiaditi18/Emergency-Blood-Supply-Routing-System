import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Bell, ChevronDown, CircleHelp, Droplets, Menu, Search, ShieldCheck, X } from "lucide-react";
import { navItems } from "../../data/demoData";
import { DemoBanner } from "../ui/Panel";
import { useAuth } from "../../auth/AuthContext";

const icons = { LayoutDashboard: "▦", Siren: "!", Building2: "▥", Droplets: "◌", Route: "↗", Network: "⌘", ChartNoAxesCombined: "⌁", Users: "♙", ScrollText: "≡", Settings2: "⚙" };

export function AppLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const current = navItems.find((item) => location.pathname.startsWith(item.path));
  return <div className="app-frame">
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="brand"><div className="brand-mark"><Droplets size={20} /></div><div><strong>BloodRoute</strong><span>Emergency logistics</span></div><button className="icon-button mobile-only" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={18} /></button></div>
      <div className="nav-label">Workspace</div>
      <nav>{navItems.map((item) => <NavLink key={item.path} to={item.path} onClick={() => setOpen(false)} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}><span className="nav-icon">{icons[item.icon]}</span>{item.label}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="nav-label">System status</div><div className="system-status"><span className="online-dot" /> API Online</div><div className="system-status"><ShieldCheck size={14} /> Database Connected</div><button className="sidebar-user" onClick={() => void logout()}><div className="avatar">{user?.full_name.slice(0, 2).toUpperCase() ?? "US"}</div><div><strong>{user?.full_name ?? "User"}</strong><span>{user?.role ?? "USER"}</span></div><ChevronDown size={14} /></button></div>
    </aside>
    {open && <button className="sidebar-scrim mobile-only" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}
    <main className="main-shell">
      <header className="topbar"><button className="icon-button mobile-only" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div className="breadcrumb"><span>Workspace</span><b>/</b><strong>{current?.label ?? "Dashboard"}</strong></div><div className="top-actions"><label className="search-box"><Search size={16} /><input placeholder="Search requests, hospitals..." aria-label="Search" /></label><button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button><div className="top-profile"><div className="avatar small">{user?.full_name.slice(0, 2).toUpperCase() ?? "US"}</div><span>{user?.full_name ?? "User"}</span><ChevronDown size={14} /></div></div></header>
      <div className="page-content"><DemoBanner /><Outlet /></div>
    </main>
  </div>;
}
