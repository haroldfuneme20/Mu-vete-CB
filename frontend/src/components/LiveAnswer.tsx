// Respuesta del agente anunciada automáticamente al lector de pantalla (T097, FR-011).
import SmartToyIcon from "@mui/icons-material/SmartToy";
import { Alert, AlertTitle } from "@mui/material";

export function LiveAnswer({ text, cached }: { text: string; cached?: string | null }) {
  return (
    <Alert icon={<SmartToyIcon aria-hidden />} severity="info" role="status" aria-live="polite" aria-atomic="true"
      sx={{ fontSize: "1rem" }}>
      <AlertTitle>¿Por qué esta ruta?</AlertTitle>
      {text}
      {cached ? ` (Resultado guardado del ${cached}.)` : ""}
    </Alert>
  );
}
