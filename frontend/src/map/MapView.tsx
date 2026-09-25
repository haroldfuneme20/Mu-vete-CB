// Mapa reutilizable (T100).
// - Modo ruta (`route`): SOLO la ruta elegida, cada tramo con el color de su modo, con marcas de
//   origen, destino, abordajes/transbordos y las paradas del recorrido.
// - Modo exploración: capas base discretas (barrios, troncales, estaciones, comunitarias).
// Fondo OpenStreetMap (libre) atenuado con CSS para que la ruta resalte; sin conexión, fondo
// neutro con las capas del paquete offline.
import "leaflet/dist/leaflet.css";
import { circleMarker, type LatLngExpression, type LeafletMouseEvent } from "leaflet";
import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CircleMarker, GeoJSON, MapContainer, Polyline, ScaleControl, TileLayer, Tooltip, useMap, useMapEvents,
} from "react-leaflet";
import type { LayerKey } from "../components/LayerToggle";
import { useApp } from "../state/AppState";
import type { Alternative } from "../types";
import { BOGOTA_CB_CENTER, loadBaseLayers, type BaseLayers } from "./layers";
import {
  casing, CATEGORY_COLOR, CATEGORY_LABEL, COLORS, legStyle, MODE_COLOR, styleBarrio, styleCommunity, styleRoad,
  styleTrunk,
} from "./styles";

export interface Incident { id: string; category: string; lat: number; lng: number; confirmations?: number }

interface Props {
  height?: number | string;
  /** Si se da, el mapa muestra solo esta ruta (sin capas base). */
  route?: Alternative | null;
  /** Capas base del modo exploración. */
  layers?: Partial<Record<LayerKey, boolean>>;
  incidents?: Incident[];
  onPick?: (lat: number, lng: number) => void;
  picked?: { lat: number; lng: number } | null;
  label: string;
  children?: ReactNode;
}

const DEFAULT_LAYERS: Record<LayerKey, boolean> = {
  barrios: true, roads: false, trunk: true, community: true, stops: true, incidents: true,
};

function Picker({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e: LeafletMouseEvent) => onPick(e.latlng.lat, e.latlng.lng) });
  return null;
}

function FitTo({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) map.fitBounds(points, { padding: [32, 32], maxZoom: 16 });
  }, [points, map]);
  return null;
}

const toLatLng = (c: [number, number][]): LatLngExpression[] => c.map(([lng, lat]) => [lat, lng]);

function RouteLayer({ route }: { route: Alternative }) {
  const legs = route.legs.filter((l) => l.geometry.coordinates.length > 1);
  const rides = legs.filter((l) => l.mode !== "walk");
  const all = legs.flatMap((l) => l.geometry.coordinates);
  const start = all[0];
  const end = all[all.length - 1];
  const points = useMemo(
    () => route.legs.flatMap((l) => l.geometry.coordinates).map(([lng, lat]) => [lat, lng] as [number, number]),
    [route],
  );
  return (
    <>
      {legs.map((l, i) => (
        <Fragment key={`leg-${i}`}>
          {l.mode !== "walk" && <Polyline positions={toLatLng(l.geometry.coordinates)} pathOptions={casing} />}
          <Polyline positions={toLatLng(l.geometry.coordinates)} pathOptions={legStyle(l.mode)}>
            <Tooltip sticky>{l.mode === "walk" ? `Caminata ${l.duration_min} min` : `${l.route_name} · ${l.duration_min} min`}</Tooltip>
          </Polyline>
        </Fragment>
      ))}
      {rides.map((l, i) =>
        (l.stop_points ?? []).slice(1, -1).map((s, j) => (
          <CircleMarker key={`st-${i}-${j}`} center={[s.lat, s.lng]} radius={3.5}
            pathOptions={{ color: MODE_COLOR[l.mode] ?? "#333", weight: 2, fillColor: "#fff", fillOpacity: 1 }}>
            <Tooltip>{s.name}</Tooltip>
          </CircleMarker>
        )),
      )}
      {rides.map((l, i) => {
        const sp = l.stop_points ?? [];
        return [sp[0], sp[sp.length - 1]].filter(Boolean).map((s, j) => (
          <CircleMarker key={`tr-${i}-${j}`} center={[s.lat, s.lng]} radius={7}
            pathOptions={{ color: MODE_COLOR[l.mode] ?? "#333", weight: 3, fillColor: "#fff", fillOpacity: 1 }}>
            <Tooltip>{`${j === 0 ? "Toma" : "Bájate de"} ${l.route_name} en ${s.name}`}</Tooltip>
          </CircleMarker>
        ));
      })}
      {start && (
        <CircleMarker center={[start[1], start[0]]} radius={10}
          pathOptions={{ color: "#fff", weight: 3, fillColor: COLORS.origin, fillOpacity: 1 }}>
          <Tooltip permanent direction="top" offset={[0, -8]}>Salida</Tooltip>
        </CircleMarker>
      )}
      {end && (
        <CircleMarker center={[end[1], end[0]]} radius={10}
          pathOptions={{ color: "#fff", weight: 3, fillColor: COLORS.destination, fillOpacity: 1 }}>
          <Tooltip permanent direction="top" offset={[0, -8]}>Llegada</Tooltip>
        </CircleMarker>
      )}
      <FitTo points={points} />
    </>
  );
}

export function MapView({ height = 360, route, layers = {}, incidents = [], onPick, picked, label, children }: Props) {
  const { online } = useApp();
  const [base, setBase] = useState<BaseLayers | null>(null);
  useEffect(() => {
    loadBaseLayers().then(setBase);
  }, []);
  const on = (k: LayerKey) => (route ? false : layers[k] ?? DEFAULT_LAYERS[k]);

  return (
    <div role="region" aria-label={label}
      style={{ height, borderRadius: 16, overflow: "hidden", background: "#eef1f4", boxShadow: "0 1px 4px rgba(0,0,0,.15)" }}>
      <MapContainer center={BOGOTA_CB_CENTER} zoom={13} style={{ height: "100%", width: "100%" }} keyboard
        zoomSnap={0.5}>
        {online && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} className="basemap-muted" />
        )}
        <ScaleControl position="bottomleft" imperial={false} />
        {base?.barrios && on("barrios") && <GeoJSON data={base.barrios} style={styleBarrio} />}
        {base?.roads && on("roads") && <GeoJSON data={base.roads} style={styleRoad} />}
        {base?.trunk && on("trunk") && <GeoJSON data={base.trunk} style={styleTrunk} />}
        {base?.community && on("community") && <GeoJSON data={base.community} style={styleCommunity} />}
        {base?.stations && on("stops") && (
          <GeoJSON data={base.stations} pointToLayer={(f, ll) =>
            circleMarker(ll, {
              radius: 4.5, weight: 2, fillColor: "#fff", fillOpacity: 1,
              color: f.properties?.kind === "transmicable" ? MODE_COLOR.transmicable : MODE_COLOR.troncal,
            }).bindTooltip(String(f.properties?.name ?? ""))} />
        )}
        {route && <RouteLayer route={route} />}
        {(route || on("incidents")) && incidents.map((i) => (
          <CircleMarker key={i.id} center={[i.lat, i.lng]} radius={9}
            pathOptions={{ color: "#fff", weight: 2, fillColor: CATEGORY_COLOR[i.category] ?? COLORS.incident, fillOpacity: 0.95 }}>
            <Tooltip>{`${CATEGORY_LABEL[i.category] ?? i.category}${i.confirmations && i.confirmations > 1 ? ` · ${i.confirmations} reportes` : ""}`}</Tooltip>
          </CircleMarker>
        ))}
        {picked && (
          <CircleMarker center={[picked.lat, picked.lng]} radius={10}
            pathOptions={{ color: "#fff", weight: 3, fillColor: "#0b3d63", fillOpacity: 1 }} />
        )}
        {onPick && <Picker onPick={onPick} />}
        {children}
      </MapContainer>
    </div>
  );
}
