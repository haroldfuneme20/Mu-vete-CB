// Tipos del contrato REST (specs/001-muevete-cb-mvp/contracts/api.md)

export type Priority = "balanced" | "fast" | "cheap" | "reliable";
export type SourceKind = "institutional" | "community" | "territorial" | "demo_simulated";
export type Category = "blockage" | "delay" | "route_change" | "risk" | "other";

export interface PlaceRef {
  ref_id?: string;
  lat?: number;
  lng?: number;
  label?: string;
  text?: string;
}

export interface PlaceItem {
  ref_id: string;
  kind: "barrio" | "station" | "stop" | "landmark";
  display_name: string;
  localidad: string | null;
  lat: number;
  lng: number;
}

export interface LegReport {
  category: Category;
  label: string;
  n_confirm: number;
  effect: "parcial" | "confirmado";
  report_ids: string[];
}

export interface Leg {
  mode: "walk" | "troncal" | "provisional" | "zonal" | "alimentador" | "transmicable" | "community";
  pattern_id: string | null;
  route_name: string;
  from_stop: string;
  to_stop: string;
  stops: string[];
  duration_min: number;
  wait_min: number;
  cost: number;
  source_kind: SourceKind;
  source_name?: string;
  confidence: number;
  last_updated: string | null;
  reports: LegReport[];
  stop_points?: { name: string; lat: number; lng: number }[];
  geometry: { type: "LineString"; coordinates: [number, number][] };
}

export interface Evidence {
  kind: "source" | "report" | "schedule";
  label: string;
  source_id?: string;
  report_ids?: string[];
  date?: string | null;
}

export interface Alternative {
  id: string;
  rank: number;
  total_time_min: number;
  cost: number;
  transfers: number;
  availability: number;
  reliability: number;
  confidence: number;
  score: number;
  penalized: boolean;
  legs: Leg[];
  text_description: string;
  evidence: Evidence[];
}

export interface Recommendation {
  request: {
    origin: { display_name: string; localidad: string | null; lat: number; lng: number };
    destination: { display_name: string; localidad: string | null; lat: number; lng: number };
    priority: Priority;
    depart_at: string;
    interpreted_from_text: boolean;
  };
  recommended: Alternative;
  alternatives: Alternative[];
  explanation: string;
  explanation_provider: string;
  warning: null | "all_affected";
  confidence: number;
  evidence: Evidence[];
  blocked?: { route_name: string; n_confirm: number }[];
  computed_at: string;
  data_version: string;
  data_mode?: string;
  precomputed?: boolean;
  from_cache?: boolean;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: Record<string, unknown> };
}

export interface RecommendationRequest {
  origin?: PlaceRef;
  destination?: PlaceRef;
  query?: string;
  priority?: Priority;
  depart_at?: string;
}

export type SyncStatus = "draft" | "pending_sync" | "syncing" | "synced" | "error";

export interface OutboxReport {
  id: string;
  anon_id: string;
  category: Category;
  location: { lat: number; lng: number };
  description?: string;
  created_at: string;
  photo?: Blob;
  sync_status: SyncStatus;
  attempts: number;
  last_error?: string;
}

export const PRIORITY_LABEL: Record<Priority, string> = {
  balanced: "Balanceado",
  fast: "Más rápido",
  cheap: "Más económico",
  reliable: "Más confiable",
};

export const CATEGORY_LABEL: Record<Category, string> = {
  blockage: "Bloqueo",
  delay: "Retraso",
  route_change: "Cambio de ruta",
  risk: "Riesgo",
  other: "Otro",
};
