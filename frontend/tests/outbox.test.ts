// T076: outbox y sincronización idempotente (fake-indexeddb).
import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import { _resetDB, getDB } from "../src/offline/db";
import { countPending, listOutbox, recoverInterrupted, saveToOutbox, setStatus } from "../src/offline/outbox";
import { syncNow } from "../src/offline/sync";

const base = (id: string) => ({
  id, anon_id: "anon-1", category: "blockage" as const, location: { lat: 4.55, lng: -74.15 },
  created_at: new Date(2026, 8, 24, 7, 0, Number(id.slice(-1))).toISOString(),
});

beforeEach(async () => {
  const db = await getDB();
  await db.clear("outbox");
  await db.clear("meta");
});

describe("outbox", () => {
  it("guarda como pendiente y persiste al 'reabrir'", async () => {
    await saveToOutbox({ ...base("r1"), photo: new Blob(["x"], { type: "image/jpeg" }) });
    _resetDB(); // simula cerrar y reabrir la app
    const items = await listOutbox();
    expect(items).toHaveLength(1);
    expect(items[0].sync_status).toBe("pending_sync");
    expect(items[0].photo).toBeDefined();
    expect(await countPending()).toBe(1);
  });

  it("un 'syncing' interrumpido vuelve a pendiente", async () => {
    await saveToOutbox(base("r2"));
    await setStatus(["r2"], "syncing");
    expect(await recoverInterrupted()).toBe(1);
    expect((await listOutbox())[0].sync_status).toBe("pending_sync");
  });

  it("accepted/duplicate → synced, rejected → error, y no reenvía lo sincronizado", async () => {
    await saveToOutbox(base("a1"));
    await saveToOutbox(base("a2"));
    await saveToOutbox(base("a3"));
    let calls = 0;
    const send = async () => {
      calls++;
      return {
        results: [
          { id: "a1", status: "accepted" as const },
          { id: "a2", status: "duplicate" as const },
          { id: "a3", status: "rejected" as const, error: { message: "inválido" } },
        ],
        recalculate: true,
      };
    };
    const r = await syncNow(send);
    expect(r).toMatchObject({ sent: 3, accepted: 1, duplicate: 1, rejected: 1, recalculate: true });
    const byId = Object.fromEntries((await listOutbox()).map((x) => [x.id, x]));
    expect(byId.a1.sync_status).toBe("synced");
    expect(byId.a2.sync_status).toBe("synced");
    expect(byId.a3.sync_status).toBe("error");
    expect(byId.a3.last_error).toBe("inválido");
    // segundo intento: solo se reenvía el que quedó con error
    const sent: string[] = [];
    await syncNow(async (form) => {
      const reports = JSON.parse(form.get("reports") as string) as { id: string }[];
      sent.push(...reports.map((x) => x.id));
      return { results: reports.map((x) => ({ id: x.id, status: "duplicate" as const })), recalculate: false };
    });
    expect(sent).toEqual(["a3"]);
    expect(calls).toBe(1);
  });

  it("si falla la red, los reportes vuelven a pendiente", async () => {
    await saveToOutbox(base("n1"));
    await expect(syncNow(async () => { throw new Error("offline"); })).rejects.toThrow();
    expect((await listOutbox())[0].sync_status).toBe("pending_sync");
  });
});
