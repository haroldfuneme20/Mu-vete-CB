// Cliente de /api/* con la forma de error común (T033).
import type { ApiErrorBody, PlaceItem, Recommendation, RecommendationRequest } from "../types";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

const WAKING_MS = 2000;
type WakeListener = (waking: boolean) => void;
const wakeListeners = new Set<WakeListener>();
export function onServerWaking(fn: WakeListener): () => void {
  wakeListeners.add(fn);
  return () => wakeListeners.delete(fn);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // si el servidor tarda (plan gratuito dormido), avisar "Despertando el servicio…"
  const timer = setTimeout(() => wakeListeners.forEach((f) => f(true)), WAKING_MS);
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError("OFFLINE", "Sin conexión con el servidor.", 0);
  } finally {
    clearTimeout(timer);
    wakeListeners.forEach((f) => f(false));
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const e = (data as ApiErrorBody).error ?? { code: "INTERNAL", message: "Error inesperado" };
    throw new ApiError(e.code, e.message, res.status, e.details ?? {});
  }
  return data as T;
}

export const api = {
  health: () => request<Record<string, unknown>>("/api/health"),
  places: (q: string, limit = 6) =>
    request<{ items: PlaceItem[] }>(`/api/places?q=${encodeURIComponent(q)}&limit=${limit}`),
  recommend: (body: RecommendationRequest) =>
    request<Recommendation>("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  reports: (bbox?: string) =>
    request<{ items: Array<Record<string, unknown>> }>(
      `/api/reports?active=true${bbox ? `&bbox=${bbox}` : ""}`,
    ),
  postReport: (form: FormData) =>
    request<{ id: string; status: string; confirmations: number }>("/api/reports", {
      method: "POST",
      body: form,
    }),
  sync: (form: FormData) =>
    request<{
      results: { id: string; status: "accepted" | "duplicate" | "rejected"; error?: { message: string } }[];
      recalculate: boolean;
    }>("/api/sync", { method: "POST", body: form }),
  stops: (bbox: string) =>
    request<{ items: Array<{ id: string; name: string; kind: string; lat: number; lng: number; source_kind: string }> }>(
      `/api/stops?bbox=${bbox}`,
    ),
};
