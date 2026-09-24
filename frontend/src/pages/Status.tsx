// Estado de conexión y sincronización (T085).
import SyncIcon from "@mui/icons-material/Sync";
import { Alert, Button, Chip, List, ListItem, ListItemText, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { announce } from "../a11y/announce";
import { listOutbox, onOutboxChange } from "../offline/outbox";
import { useApp } from "../state/AppState";
import { CATEGORY_LABEL, type OutboxReport } from "../types";

const STATUS: Record<OutboxReport["sync_status"], string> = {
  draft: "Borrador", pending_sync: "Pendiente", syncing: "Enviando…", synced: "Sincronizado", error: "Con error",
};

export function Status() {
  const { online, pending, lastSync, sync } = useApp();
  const [items, setItems] = useState<OutboxReport[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const load = () => listOutbox().then((l) => setItems(l.reverse()));
    load();
    return onOutboxChange(load);
  }, []);

  const doSync = async () => {
    setBusy(true);
    try {
      const m = await sync();
      setMsg(m);
      announce(m);
    } catch {
      const m = "No se pudo sincronizar. Revisa tu conexión e inténtalo de nuevo.";
      setMsg(m);
      announce(m);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h1">Estado</Typography>
      <Alert severity={online ? "success" : "warning"} role="status">
        {online ? "Conectado" : "Sin conexión"}
        {lastSync ? ` · Última sincronización: ${new Date(lastSync).toLocaleTimeString("es-CO")}` : ""}
      </Alert>
      <Typography variant="body1">
        {pending === 0 ? "No tienes reportes pendientes." : `${pending} ${pending === 1 ? "reporte pendiente" : "reportes pendientes"} de sincronización.`}
      </Typography>
      <Button variant="contained" size="large" startIcon={<SyncIcon aria-hidden />} onClick={doSync}
        disabled={!online || busy}>
        {busy ? "Sincronizando…" : "Sincronizar ahora"}
      </Button>
      {msg && <Alert severity="info" role="status">{msg}</Alert>}
      <Typography variant="h2" component="h2">Mis reportes en este teléfono</Typography>
      <List aria-label="Reportes guardados">
        {items.length === 0 && <ListItem><ListItemText primary="Todavía no has hecho reportes." /></ListItem>}
        {items.map((r) => (
          <ListItem key={r.id} divider secondaryAction={
            <Chip size="small" label={STATUS[r.sync_status]}
              color={r.sync_status === "synced" ? "secondary" : r.sync_status === "error" ? "error" : "warning"} />
          }>
            <ListItemText primary={`${CATEGORY_LABEL[r.category]}${r.photo ? " · con foto" : ""}`}
              secondary={`${new Date(r.created_at).toLocaleString("es-CO")}${r.last_error ? ` · ${r.last_error}` : ""}`} />
          </ListItem>
        ))}
      </List>
    </Stack>
  );
}
