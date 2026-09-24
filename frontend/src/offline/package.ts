// Paquete offline por niveles (T080, contracts/offline-package.md).
import type { PlaceItem, Recommendation } from "../types";
import { getMeta, setMeta } from "./db";

export interface Manifest {
  version: string;
  files: { path: string; level: "a" | "b" | "c"; bytes: number }[];
}

const cache = new Map<string, unknown>();

export async function loadOfflineFile<T>(path: string): Promise<T | null> {
  if (cache.has(path)) return cache.get(path) as T;
  try {
    const res = await fetch(`/offline/${path}`);
    if (!res.ok) return null;
    const data = (await res.json()) as T;
    cache.set(path, data);
    return data;
  } catch {
    return null;
  }
}

/** Registra la versión del paquete; el Service Worker actualiza el precache sin tocar el outbox. */
export async function checkPackageVersion(): Promise<string | null> {
  const m = await loadOfflineFile<Manifest>("manifest.json");
  if (!m) return null;
  const prev = await getMeta<string>("offline_package_version");
  if (prev !== m.version) await setMeta("offline_package_version", m.version);
  return m.version;
}

interface CompactPlace { n: string; k: PlaceItem["kind"]; r: string; lat: number; lng: number; l: string | null }

export async function offlinePlaces(q: string, limit = 6): Promise<PlaceItem[]> {
  const idx = (await loadOfflineFile<CompactPlace[]>("places_index.json")) ?? [];
  const norm = (s: string) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  const nq = norm(q);
  if (!nq) return [];
  return idx
    .filter((p) => norm(p.n).includes(nq))
    .sort((a, b) => Number(!norm(a.n).startsWith(nq)) - Number(!norm(b.n).startsWith(nq)))
    .slice(0, limit)
    .map((p) => ({ ref_id: p.r, kind: p.k, display_name: p.n, localidad: p.l, lat: p.lat, lng: p.lng }));
}

interface DemoFile {
  results: { scenario: string; priority: string; query_key: string; recommendation: Recommendation }[];
}

export async function demoRecommendation(origin: string, destination: string, priority: string) {
  const f = await loadOfflineFile<DemoFile>("demo_scenarios.json");
  const norm = (s: string) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\(.*\)/, "").trim();
  const hit = f?.results.find(
    (r) =>
      r.priority === priority &&
      norm(r.recommendation.request.origin.display_name).startsWith(norm(origin)) &&
      norm(r.recommendation.request.destination.display_name).startsWith(norm(destination)),
  );
  return hit?.recommendation ?? null;
}
