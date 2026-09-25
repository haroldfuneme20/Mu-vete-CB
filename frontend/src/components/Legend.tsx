// Leyenda del mapa (T101): en modo ruta solo muestra los modos que usa esa ruta.
import { Box, Stack, Typography } from "@mui/material";
import { COLORS, MODE_COLOR, MODE_LABEL } from "../map/styles";
import type { Alternative } from "../types";

interface Item { label: string; color: string; dash?: string; dot?: boolean }

function line(mode: string): Item {
  return {
    label: MODE_LABEL[mode] ?? mode,
    color: MODE_COLOR[mode] ?? "#333",
    dash: mode === "walk" ? "dotted" : mode === "community" ? "dashed" : undefined,
  };
}

export function Legend({ route }: { route?: Alternative | null }) {
  const items: Item[] = route
    ? [
        ...Array.from(new Set(route.legs.map((l) => l.mode))).map(line),
        { label: "Salida", color: COLORS.origin, dot: true },
        { label: "Llegada", color: COLORS.destination, dot: true },
      ]
    : [
        line("troncal"),
        { label: "Estación TransMiCable", color: MODE_COLOR.transmicable, dot: true },
        { label: "Estación TransMilenio", color: MODE_COLOR.troncal, dot: true },
        line("community"),
        { label: "Incidente reportado", color: COLORS.incident, dot: true },
      ];
  return (
    <Box component="section" aria-label="Leyenda del mapa"
      sx={{ mt: 1, p: 1.5, borderRadius: 2, bgcolor: "background.paper", border: "1px solid", borderColor: "divider" }}>
      <Typography variant="h3" component="h2" sx={{ mb: 0.5 }}>Leyenda</Typography>
      <Stack component="ul" sx={{ listStyle: "none", p: 0, m: 0, display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 0.75 }}>
        {items.map((i) => (
          <Box component="li" key={i.label} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {i.dot ? (
              <Box aria-hidden sx={{ width: 14, height: 14, borderRadius: "50%", bgcolor: i.color, border: "2px solid #fff", boxShadow: "0 0 0 1px rgba(0,0,0,.25)", mx: "9px" }} />
            ) : (
              <Box aria-hidden sx={{ width: 32, height: 0, borderTop: `5px ${i.dash ?? "solid"} ${i.color}` }} />
            )}
            <Typography variant="body2">{i.label}</Typography>
          </Box>
        ))}
      </Stack>
    </Box>
  );
}
