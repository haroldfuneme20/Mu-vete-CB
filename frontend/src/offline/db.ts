// IndexedDB (T071): outbox, results, meta, prefs.
import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { OutboxReport, Recommendation } from "../types";

interface MueveteDB extends DBSchema {
  outbox: { key: string; value: OutboxReport; indexes: { by_status: string } };
  results: { key: string; value: { query_key: string; saved_at: string; rec: Recommendation } };
  meta: { key: string; value: unknown };
  prefs: { key: string; value: unknown };
  pending_queries: { key: string; value: { query_key: string; body: unknown; saved_at: string } };
}

let dbPromise: Promise<IDBPDatabase<MueveteDB>> | null = null;

export function getDB(): Promise<IDBPDatabase<MueveteDB>> {
  if (!dbPromise) {
    dbPromise = openDB<MueveteDB>("muevete-cb", 1, {
      upgrade(db) {
        const outbox = db.createObjectStore("outbox", { keyPath: "id" });
        outbox.createIndex("by_status", "sync_status");
        db.createObjectStore("results", { keyPath: "query_key" });
        db.createObjectStore("meta");
        db.createObjectStore("prefs");
        db.createObjectStore("pending_queries", { keyPath: "query_key" });
      },
    });
  }
  return dbPromise;
}

/** Solo para pruebas: reinicia la conexión. */
export function _resetDB(): void {
  dbPromise = null;
}

export async function getMeta<T>(key: string): Promise<T | undefined> {
  return (await (await getDB()).get("meta", key)) as T | undefined;
}

export async function setMeta(key: string, value: unknown): Promise<void> {
  await (await getDB()).put("meta", value, key);
}
