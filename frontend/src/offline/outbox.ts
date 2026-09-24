// Outbox de reportes (T081): draft → pending_sync → syncing → synced | error.
import type { OutboxReport, SyncStatus } from "../types";
import { getDB } from "./db";

type Listener = () => void;
const listeners = new Set<Listener>();
export function onOutboxChange(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
function notify() {
  listeners.forEach((f) => f());
}

export class StorageFullError extends Error {
  constructor() {
    super("El teléfono no tiene espacio para guardar el reporte. Libera espacio e inténtalo de nuevo.");
  }
}

export async function saveToOutbox(
  r: Omit<OutboxReport, "sync_status" | "attempts">,
): Promise<OutboxReport> {
  const item: OutboxReport = { ...r, sync_status: "pending_sync", attempts: 0 };
  try {
    await (await getDB()).put("outbox", item);
  } catch (e) {
    if (e instanceof DOMException && e.name === "QuotaExceededError") throw new StorageFullError();
    throw e;
  }
  notify();
  return item;
}

export async function listOutbox(): Promise<OutboxReport[]> {
  const all = await (await getDB()).getAll("outbox");
  return all.sort((a, b) => a.created_at.localeCompare(b.created_at));
}

export async function pendingReports(): Promise<OutboxReport[]> {
  return (await listOutbox()).filter((r) => r.sync_status === "pending_sync" || r.sync_status === "error");
}

export async function setStatus(ids: string[], status: SyncStatus, error?: string): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("outbox", "readwrite");
  for (const id of ids) {
    const item = await tx.store.get(id);
    if (!item) continue;
    item.sync_status = status;
    if (status === "syncing") item.attempts += 1;
    item.last_error = status === "error" ? error : undefined;
    await tx.store.put(item);
  }
  await tx.done;
  notify();
}

/** Al abrir la app: un `syncing` interrumpido vuelve a `pending_sync`. */
export async function recoverInterrupted(): Promise<number> {
  const stuck = (await listOutbox()).filter((r) => r.sync_status === "syncing").map((r) => r.id);
  if (stuck.length) await setStatus(stuck, "pending_sync");
  return stuck.length;
}

export async function countPending(): Promise<number> {
  return (await pendingReports()).length;
}
