// Estilos del mapa (T101): formal, comunitaria simulada (discontinua), incidentes, recomendada.
import type { PathOptions } from "leaflet";

export const COLORS = {
  recommended: "#1b6e35",
  alternative: "#5a6b7b",
  trunk: "#b3261e",
  cable: "#7a3fb0",
  community: "#8a5300",
  road: "#9aa5b1",
  barrio: "#0b3d63",
  incident: "#b3261e",
};

export const styleRecommended: PathOptions = { color: COLORS.recommended, weight: 7, opacity: 0.95 };
export const styleAlternative: PathOptions = { color: COLORS.alternative, weight: 4, opacity: 0.8, dashArray: "2 6" };
export const styleTrunk: PathOptions = { color: COLORS.trunk, weight: 4, opacity: 0.8 };
export const styleCommunity: PathOptions = { color: COLORS.community, weight: 4, opacity: 0.9, dashArray: "10 8" };
export const styleRoad: PathOptions = { color: COLORS.road, weight: 2, opacity: 0.8 };
export const styleBarrio: PathOptions = { color: COLORS.barrio, weight: 1, fillOpacity: 0.06 };

export const CATEGORY_COLOR: Record<string, string> = {
  blockage: "#b3261e", delay: "#8a5300", route_change: "#0b3d63", risk: "#7a3fb0", other: "#454545",
};
