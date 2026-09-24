// Estado compartido mínimo: última recomendación, conexión y pendientes.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { onServerWaking } from "../services/api";
import { countPending, onOutboxChange, recoverInterrupted } from "../offline/outbox";
import { registerBackgroundSync, syncNow } from "../offline/sync";
import { runPendingQueries } from "../services/recommendations";
import { checkPackageVersion } from "../offline/package";
import { getMeta } from "../offline/db";
import type { Recommendation } from "../types";

interface Ctx {
  online: boolean;
  waking: boolean;
  pending: number;
  lastSync: string | null;
  rec: Recommendation | null;
  setRec: (r: Recommendation | null) => void;
  sync: () => Promise<string>;
  refreshPending: () => void;
}

const AppCtx = createContext<Ctx | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [online, setOnline] = useState(navigator.onLine);
  const [waking, setWaking] = useState(false);
  const [pending, setPending] = useState(0);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [rec, setRec] = useState<Recommendation | null>(null);

  const refreshPending = useCallback(() => {
    countPending().then(setPending).catch(() => setPending(0));
    getMeta<string>("last_sync_at").then((v) => setLastSync(v ?? null)).catch(() => undefined);
  }, []);

  const sync = useCallback(async () => {
    const r = await syncNow();
    refreshPending();
    if (r.recalculate) {
      const again = await runPendingQueries();
      if (again) setRec(again);
    }
    if (r.sent === 0) return "No hay reportes pendientes.";
    return `Sincronizados ${r.accepted + r.duplicate} de ${r.sent} reportes.` +
      (r.rejected ? ` ${r.rejected} con error.` : "");
  }, [refreshPending]);

  useEffect(() => {
    recoverInterrupted().finally(refreshPending);
    checkPackageVersion();
    registerBackgroundSync();
    const off1 = onOutboxChange(refreshPending);
    const off2 = onServerWaking(setWaking);
    const up = () => {
      setOnline(true);
      sync().catch(() => undefined);
      runPendingQueries().then((r) => r && setRec(r));
    };
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      off1();
      off2();
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, [refreshPending, sync]);

  const value = useMemo(
    () => ({ online, waking, pending, lastSync, rec, setRec, sync, refreshPending }),
    [online, waking, pending, lastSync, rec, sync, refreshPending],
  );
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp fuera de AppStateProvider");
  return c;
}
