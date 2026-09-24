// Estado de conexión + pendientes (T084, FR-024).
import CloudDoneIcon from "@mui/icons-material/CloudDone";
import CloudOffIcon from "@mui/icons-material/CloudOff";
import { Chip, Stack } from "@mui/material";
import { useApp } from "../state/AppState";

export function ConnectionBadge() {
  const { online, pending, waking } = useApp();
  const label = waking
    ? "Despertando el servicio…"
    : online
      ? "Conectado"
      : "Sin conexión";
  return (
    <Stack direction="row" spacing={1} role="status" aria-live="polite">
      <Chip
        icon={online ? <CloudDoneIcon aria-hidden /> : <CloudOffIcon aria-hidden />}
        label={label}
        color={online ? "secondary" : "warning"}
        size="small"
      />
      {pending > 0 && (
        <Chip
          label={`${pending} ${pending === 1 ? "reporte pendiente" : "reportes pendientes"}`}
          color="warning"
          variant="outlined"
          size="small"
        />
      )}
    </Stack>
  );
}
