import type { ReactNode } from "react";

export function SectionHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="section-header"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h2>{title}</h2>{description && <p className="section-description">{description}</p>}</div>{action}</div>;
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

export function DemoBanner() {
  return <div className="demo-banner"><span className="demo-pulse" /><strong>DEMO MODE</strong><span>Data shown here is fictional and does not represent live blood availability.</span></div>;
}
