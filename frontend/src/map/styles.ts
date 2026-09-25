// Estilos del mapa (T101): un color por modo de transporte, capas base discretas.
import type { PathOptions } from "leaflet";

export const MODE_COLOR: Record<string, string> = {
  transmicable: "#7b3fb5",   // morado TransMiCable
  troncal: "#c62828",        // rojo TransMilenio
  zonal: "#1565c0",          // azul SITP
  alimentador: "#2e7d32",    // verde alimentador
  provisional: "#6d4c41",    // café provisional
  community: "#e07b00",      // naranja comunitaria (simulada)
  walk: "#5f6b76",           // gris caminata
};

export const MODE_LABEL: Record<string, string> = {
  transmicable: "TransMiCable",
  troncal: "TransMilenio (troncal)",
  zonal: "SITP zonal",
  alimentador: "Alimentador (gratis)",
  provisional: "Ruta provisional",
  community: "Ruta comunitaria (simulada para la demo)",
  walk: "Caminata",
};

export const COLORS = {
  origin: "#1b6e35",
  destination: "#b3261e",
  barrio: "#0b3d63",
  road: "#b8c0c8",
  incident: "#b3261e",
};

export function legStyle(mode: string): PathOptions {
  if (mode === "walk") return { color: MODE_COLOR.walk, weight: 4, opacity: 0.9, dashArray: "1 8", lineCap: "round" };
  if (mode === "community") return { color: MODE_COLOR.community, weight: 6, opacity: 0.95, dashArray: "12 8" };
  return { color: MODE_COLOR[mode] ?? "#1b6e35", weight: 6, opacity: 0.95, lineCap: "round", lineJoin: "round" };
}

/** Borde blanco bajo cada tramo para que se lea sobre cualquier fondo. */
export const casing: PathOptions = { color: "#ffffff", weight: 10, opacity: 0.9, lineCap: "round", lineJoin: "round" };

// capas base (modo exploración): discretas para no competir con la ruta
export const styleBarrio: PathOptions = { color: COLORS.barrio, weight: 0.8, opacity: 0.35, fillOpacity: 0.03 };
export const styleRoad: PathOptions = { color: COLORS.road, weight: 1.5, opacity: 0.7 };
export const styleTrunk: PathOptions = { color: MODE_COLOR.troncal, weight: 3, opacity: 0.55 };
export const styleCommunity: PathOptions = { color: MODE_COLOR.community, weight: 3, opacity: 0.7, dashArray: "8 6" };

export const CATEGORY_COLOR: Record<string, string> = {
  blockage: "#b3261e", delay: "#8a5300", route_change: "#0b3d63", risk: "#7a3fb0", other: "#454545",
};

export const CATEGORY_LABEL: Record<string, string> = {
  blockage: "Bloqueo", delay: "Retraso", route_change: "Cambio de ruta", risk: "Riesgo", other: "Otro",
};
