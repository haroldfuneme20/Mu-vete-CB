// Prioridad del viaje (T057). Sin selección = "Balanceado" (I5), anunciado al lector de pantalla.
import BoltIcon from "@mui/icons-material/Bolt";
import SavingsIcon from "@mui/icons-material/Savings";
import VerifiedIcon from "@mui/icons-material/VerifiedUser";
import { ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import type { Priority } from "../types";

interface Props {
  value: Priority;
  onChange: (p: Priority) => void;
}

export function PriorityPicker({ value, onChange }: Props) {
  return (
    <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
      <Typography component="legend" variant="h3" sx={{ mb: 1 }}>
        ¿Qué priorizas en tu viaje?
      </Typography>
      <ToggleButtonGroup
        exclusive
        fullWidth
        color="primary"
        value={value === "balanced" ? null : value}
        onChange={(_, v: Priority | null) => onChange(v ?? "balanced")}
        aria-label="Prioridad del viaje"
      >
        <ToggleButton value="fast" aria-label="Más rápido"><BoltIcon aria-hidden sx={{ mr: 0.5 }} />Más rápido</ToggleButton>
        <ToggleButton value="cheap" aria-label="Más económico"><SavingsIcon aria-hidden sx={{ mr: 0.5 }} />Más económico</ToggleButton>
        <ToggleButton value="reliable" aria-label="Más confiable"><VerifiedIcon aria-hidden sx={{ mr: 0.5 }} />Más confiable</ToggleButton>
      </ToggleButtonGroup>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }} aria-live="polite">
        {value === "balanced" ? "Sin elegir: balanceado entre tiempo, costo y confiabilidad." : null}
      </Typography>
    </fieldset>
  );
}
