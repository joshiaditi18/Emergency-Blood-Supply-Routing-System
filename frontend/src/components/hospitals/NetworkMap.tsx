import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { hospitals } from "../../data/demoData";

const markerIcon = new L.Icon({ iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png", iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png", shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png", iconSize: [25, 41], iconAnchor: [12, 41] });
const lines = hospitals.slice(0, -1).map((hospital, index) => [[hospital.lat, hospital.lng], [hospitals[index + 1].lat, hospitals[index + 1].lng]] as [number, number][]);

export function NetworkMap({ compact = false }: { compact?: boolean }) {
  return <div className={`network-map ${compact ? "compact" : ""}`}><MapContainer center={[28.62, 77.23]} zoom={12} scrollWheelZoom={false}><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{lines.map((line, index) => <Polyline key={index} positions={line} pathOptions={{ color: "#78aaa5", weight: 2, dashArray: "5 7" }} />)}{hospitals.map((hospital) => <Marker key={hospital.id} position={[hospital.lat, hospital.lng]} icon={markerIcon}><Popup><strong>{hospital.id} · {hospital.name}</strong><br />{hospital.availability} availability</Popup></Marker>)}</MapContainer><span className="map-label">DEMO NETWORK · NOT LIVE GPS</span></div>;
}
