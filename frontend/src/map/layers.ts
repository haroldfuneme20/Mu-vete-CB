// Capas base desde el paquete offline (T100): funcionan sin conexión.
import type { FeatureCollection } from "geojson";
import { loadOfflineFile } from "../offline/package";

export interface BaseLayers {
  barrios: FeatureCollection | null;
  roads: FeatureCollection | null;
  community: FeatureCollection | null;
  trunk: FeatureCollection | null;
  stations: FeatureCollection | null;
  stops: FeatureCollection | null;
}

export async function loadBaseLayers(): Promise<BaseLayers> {
  const [barrios, roads, community, trunk, stations, stops] = await Promise.all([
    loadOfflineFile<FeatureCollection>("cb_barrios.geojson"),
    loadOfflineFile<FeatureCollection>("cb_roads_main.geojson"),
    loadOfflineFile<FeatureCollection>("community_routes.geojson"),
    loadOfflineFile<FeatureCollection>("tm_trunk.geojson"),
    loadOfflineFile<FeatureCollection>("tm_stations.geojson"),
    loadOfflineFile<FeatureCollection>("cb_stops.geojson"),
  ]);
  return { barrios, roads, community, trunk, stations, stops };
}

export const BOGOTA_CB_CENTER: [number, number] = [4.565, -74.13];
