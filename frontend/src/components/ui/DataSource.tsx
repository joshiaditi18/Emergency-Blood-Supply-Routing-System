export function DataSource({ live, error }: { live: boolean; error?: string }) {
  return <span className={`data-source ${live ? "live" : "fallback"}`}><i />{live ? "Backend data" : "Demo fallback"}{error && <small>{error}</small>}</span>;
}
