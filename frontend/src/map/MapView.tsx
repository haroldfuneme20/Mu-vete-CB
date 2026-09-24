// Mapa reutilizable (T100): Leaflet + teselas OSM en línea, fondo neutro sin conexión.
import "leaflet/dist/leaflet.css";
import { circleMarker, type LatLngExpression, type LeafletMouseEvent } from "leaflet";
import { useEffect, useState, type ReactNode } from "react";
import { CircleMarker, GeoJSON, MapContainer, Polyline, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import type { LayerKey } from "../components/LayerToggle";
import { useApp } from "../state/AppState";
import type { Alternative } from "../types";
import { BOGOTA_CB_CENTER, loadBaseLayers, type BaseLayers } from "./layers";
import { CATEGORY_COLOR, COLORS, styleAlternative, styleBarrio, styleCommunity, styleRecommended, styleRoad, styleTrunk } from "./styles";

export interface Incident { id: string; category: string; lat: number; lng: number; confirmations?: number }

interface Props {
  height?: number | string;
  layers?: Partial<Record<LayerKey, boolean>>;
  recommended?: Alternative | null;
  alternatives?: Alternative[];
  incidents?: Incident[];
  onPick?: (lat: number, lng: number) => void;
  picked?: { lat: number; lng: number } | null;
  label: string;
  children?: ReactNode;
}

function Picker({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e: LeafletMouseEvent) => onPick(e.latlng.lat, e.latlng.lng) });
  return null;
}

function FitTo({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length > 1) map.fitBounds(coords.map(([lng, lat]) => [lat, lng]) as [number, number][], { padding: [24, 24] });
  }, [coords, map]);
  return null;
}

const toLatLng = (c: [number, number][]): LatLngExpression[] => c.map(([lng, lat]) => [lat, lng]);

export function MapView({ height = 360, layers = {}, recommended, alternatives = [], incidents = [], onPick, picked, label, children }: Props) {
  const { online } = useApp();
  const [base, setBase] = useState<BaseLayers | null>(null);
  useEffect(() => {
    loadBaseLayers().then(setBase);
  }, []);
  const on = (k: LayerKey) => layers[k] ?? true;
  const recCoords = recommended?.legs.flatMap((l) => l.geometry.coordinates) ?? [];

  return (
    <div role="region" aria-label={label} style={{ height, borderRadius: 12, overflow: "hidden", background: "#e8edf2" }}>
      <MapContainer center={BOGOTA_CB_CENTER} zoom={13} style={{ height: "100%", width: "100%" }} keyboard>
        {online && (
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        )}
        {base?.barrios && on("barrios") && <GeoJSON data={base.barrios} style={styleBarrio} />}
        {base?.roads && on("roads") && <GeoJSON data={base.roads} style={styleRoad} />}
        {base?.trunk && on("trunk") && <GeoJSON data={base.trunk} style={styleTrunk} />}
        {base?.community && on("community") && <GeoJSON data={base.community} style={styleCommunity} />}
        {base?.stations && on("stops") && (
          <GeoJSON data={base.stations} pointToLayer={(f, ll) =>
            circleMarker(ll, {
              radius: 6, color: f.properties?.kind === "transmicable" ? COLORS.cable : COLORS.trunk, weight: 2, fillOpacity: 0.9,
            })} />
        )}
        {alternatives.map((a) => (
          <Polyline key={a.id} positions={toLatLng(a.legs.flatMap((l) => l.geometry.coordinates))} pathOptions={styleAlternative} />
        ))}
        {recommended && (
          <>
            <Polyline positions={toLatLng(recCoords)} pathOptions={styleRecommended} />
            <FitTo coords={recCoords} />
          </>
        )}
        {on("incidents") && incidents.map((i) => (
          <CircleMarker key={i.id} center={[i.lat, i.lng]} radius={10}
            pathOptions={{ color: CATEGORY_COLOR[i.category] ?? COLORS.incident, weight: 3, fillOpacity: 0.5 }}>
            <Tooltip>{`${i.category}${i.confirmations && i.confirmations > 1 ? ` · ${i.confirmations} reportes` : ""}`}</Tooltip>
          </CircleMarker>
        ))}
        {picked && <CircleMarker center={[picked.lat, picked.lng]} radius={9} pathOptions={{ color: "#0b3d63", fillOpacity: 0.8 }} />}
        {onPick && <Picker onPick={onPick} />}
        {children}
      </MapContainer>
    </div>
  );
}
