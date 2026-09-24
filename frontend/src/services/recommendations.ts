// Recomendaciones con caché offline y cola de consultas pendientes (T086, FR-010).
import { getDB } from "../offline/db";
import { demoRecommendation } from "../offline/package";
import type { Recommendation, RecommendationRequest } from "../types";
import { ApiError, api } from "./api";

export class OfflineNoResultError extends Error {
  constructor(public queued: boolean) {
    super(
      "Sin conexión no podemos calcular esta ruta nueva. " +
        (queued ? "Guardamos la consulta y la haremos apenas vuelva la conexión." : ""),
    );
  }
}

export function queryKey(req: RecommendationRequest, labels?: { o?: string; d?: string }): string {
  if (req.query) return `q|${req.query.trim().toLowerCase()}`;
  const k = (p?: RecommendationRequest["origin"], label?: string) =>
    label ?? p?.ref_id ?? p?.text ?? `${p?.lat?.toFixed(4)},${p?.lng?.toFixed(4)}`;
  return `f|${k(req.origin, labels?.o)}|${k(req.destination, labels?.d)}|${req.priority ?? "balanced"}`;
}

export async function recommend(
  req: RecommendationRequest,
  labels: { o?: string; d?: string } = {},
): Promise<Recommendation> {
  const key = queryKey(req, labels);
  const db = await getDB();
  try {
    const rec = await api.recommend(req);
    await db.put("results", { query_key: key, saved_at: new Date().toISOString(), rec });
    return rec;
  } catch (e) {
    if (!(e instanceof ApiError) || e.code !== "OFFLINE") throw e;
    const saved = await db.get("results", key);
    if (saved) return { ...saved.rec, from_cache: true, computed_at: saved.saved_at };
    if (!req.query && labels.o && labels.d) {
      const demo = await demoRecommendation(labels.o, labels.d, req.priority ?? "balanced");
      if (demo) return { ...demo, from_cache: true };
    }
    if (req.query) throw new OfflineNoResultError(false);
    await db.put("pending_queries", { query_key: key, body: { req, labels }, saved_at: new Date().toISOString() });
    throw new OfflineNoResultError(true);
  }
}

/** Ejecuta al reconectar las consultas que se guardaron sin conexión. */
export async function runPendingQueries(): Promise<Recommendation | null> {
  const db = await getDB();
  const pending = await db.getAll("pending_queries");
  let last: Recommendation | null = null;
  for (const p of pending) {
    const { req, labels } = p.body as { req: RecommendationRequest; labels: { o?: string; d?: string } };
    try {
      last = await recommend(req, labels);
      await db.delete("pending_queries", p.query_key);
    } catch {
      /* se reintenta en la próxima reconexión */
    }
  }
  return last;
}
