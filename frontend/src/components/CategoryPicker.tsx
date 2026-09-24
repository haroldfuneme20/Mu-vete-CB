// Categoría del reporte (T073).
import { ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { CATEGORY_LABEL, type Category } from "../types";

export function CategoryPicker({ value, onChange }: { value: Category | null; onChange: (c: Category) => void }) {
  return (
    <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
      <Typography component="legend" variant="h3" sx={{ mb: 1 }}>¿Qué ocurrió?</Typography>
      <ToggleButtonGroup exclusive color="primary" value={value} aria-label="Categoría del reporte"
        onChange={(_, v: Category | null) => v && onChange(v)}
        sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
        {(Object.keys(CATEGORY_LABEL) as Category[]).map((c) => (
          <ToggleButton key={c} value={c} sx={{ border: "1px solid !important", borderRadius: "12px !important" }}>
            {CATEGORY_LABEL[c]}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </fieldset>
  );
}
