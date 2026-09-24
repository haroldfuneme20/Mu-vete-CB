// Leyenda del mapa (T101).
import { Box, Stack, Typography } from "@mui/material";
import { COLORS } from "../map/styles";

const ITEMS = [
  { label: "Ruta recomendada", color: COLORS.recommended, dash: false, w: 6 },
  { label: "Alternativa", color: COLORS.alternative, dash: true, w: 4 },
  { label: "TransMilenio / troncal (institucional)", color: COLORS.trunk, dash: false, w: 4 },
  { label: "Ruta comunitaria simulada para la demo", color: COLORS.community, dash: true, w: 4 },
  { label: "Incidente reportado", color: COLORS.incident, dash: false, w: 10 },
];

export function Legend() {
  return (
    <Box component="section" aria-label="Leyenda del mapa" sx={{ mt: 1 }}>
      <Typography variant="h3" component="h2">Leyenda</Typography>
      <Stack component="ul" sx={{ listStyle: "none", p: 0, m: 0 }} spacing={0.5}>
        {ITEMS.map((i) => (
          <Box component="li" key={i.label} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box aria-hidden sx={{ width: 32, height: 0, borderTop: `${i.w}px ${i.dash ? "dashed" : "solid"} ${i.color}` }} />
            <Typography variant="body2">{i.label}</Typography>
          </Box>
        ))}
      </Stack>
    </Box>
  );
}
