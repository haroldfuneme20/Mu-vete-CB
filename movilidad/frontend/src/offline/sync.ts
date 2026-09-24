// Sincronización del outbox (T082): lotes de 20, botón, evento `online` y Background Sync opcional.
import { api } from "../services/api";
import type { OutboxReport } from "../types";
import { setMeta } from "./db";
import { pendingReports, setStatus } from "./outbox";

export const BATCH = 20;
let running: Promise<SyncResult> | null = null;

export interface SyncResult {
  sent: number;
  accepted: number;
  duplicate: number;
  rejected: number;
  recalculate: boolean;
}

type Sender = (form: FormData) => ReturnType<typeof api.sync>;

function toForm(batch: OutboxReport[]): FormData {
  const form = new FormData();
  form.append(
    "reports",
    JSON.stringify(
      batch.map(({ id, anon_id, category, location, description, created_at }) => ({
        id, anon_id, category, location, description, created_at,
      })),
    ),
  );
  for (const r of batch) if (r.photo) form.append(`photo_${r.id}`, r.photo, `${r.id}.jpg`);
  return form;
}

export async function syncNow(send: Sender = api.sync): Promise<SyncResult> {
  if (running) return running;
  running = (async () => {
    const total: SyncResult = { sent: 0, accepted: 0, duplicate: 0, rejected: 0, recalculate: false };
    const pending = await pendingReports();
    for (let i = 0; i < pending.length; i += BATCH) {
      const batch = pending.slice(i, i + BATCH);
      const ids = batch.map((r) => r.id);
      await setStatus(ids, "syncing");
      try {
        const res = await send(toForm(batch));
        for (const r of res.results) {
          if (r.status === "rejected") {
            total.rejected++;
            await setStatus([r.id], "error", r.error?.message ?? "Rechazado");
          } else {
            total[r.status]++;
            await setStatus([r.id], "synced");
          }
        }
        total.sent += batch.length;
        total.recalculate ||= res.recalculate;
      } catch (e) {
        await setStatus(ids, "pending_sync");
        throw e;
      }
    }
    await setMeta("last_sync_at", new Date().toISOString());
    return total;
  })();
  try {
    return await running;
  } finally {
    running = null;
  }
}

/** Registra Background Sync donde exista (Chromium); iOS usa el botón y el evento `online`. */
export async function registerBackgroundSync(): Promise<boolean> {
  try {
    const reg = await navigator.serviceWorker?.ready;
    const syncMgr = (reg as ServiceWorkerRegistration & { sync?: { register(tag: string): Promise<void> } })?.sync;
    if (!syncMgr) return false;
    await syncMgr.register("muevete-outbox");
    return true;
  } catch {
    return false;
  }
}
