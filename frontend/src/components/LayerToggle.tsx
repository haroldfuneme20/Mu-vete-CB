// Capas activables (T101).
import { Checkbox, FormControlLabel, FormGroup } from "@mui/material";

export type LayerKey = "barrios" | "roads" | "trunk" | "community" | "stops" | "incidents";
export const LAYER_LABEL: Record<LayerKey, string> = {
  barrios: "Barrios", roads: "Vías principales", trunk: "TransMilenio", community: "Rutas comunitarias",
  stops: "Estaciones", incidents: "Incidentes",
};

export function LayerToggle({ value, onChange }: { value: Record<LayerKey, boolean>; onChange: (v: Record<LayerKey, boolean>) => void }) {
  return (
    <FormGroup row aria-label="Capas del mapa">
      {(Object.keys(LAYER_LABEL) as LayerKey[]).map((k) => (
        <FormControlLabel key={k} label={LAYER_LABEL[k]}
          control={<Checkbox checked={value[k]} onChange={(e) => onChange({ ...value, [k]: e.target.checked })} />} />
      ))}
    </FormGroup>
  );
}
