// Descripción textual de la ruta: equivalente accesible del mapa (FR-012).
import { List, ListItem, ListItemText, Typography } from "@mui/material";
import type { Alternative } from "../types";
import { SourceBadge } from "./SourceBadge";

const MODE: Record<string, string> = {
  walk: "Caminata", troncal: "TransMilenio", provisional: "Ruta provisional", zonal: "SITP zonal",
  transmicable: "TransMiCable", community: "Ruta comunitaria",
};

export function RouteText({ alt }: { alt: Alternative }) {
  return (
    <section aria-label="Recorrido paso a paso">
      <Typography variant="h3" component="h2" sx={{ mb: 1 }}>Recorrido paso a paso</Typography>
      <List component="ol" sx={{ listStyle: "decimal", pl: 3 }}>
        {alt.legs.filter((l) => l.mode !== "walk" || l.duration_min > 0).map((l, i) => (
          <ListItem key={i} component="li" sx={{ display: "list-item", px: 0 }}>
            <ListItemText
              primary={
                l.mode === "walk"
                  ? `Camina ${l.duration_min} min hasta ${l.to_stop}`
                  : `${MODE[l.mode] ?? l.mode}: ${l.route_name}, de ${l.from_stop} a ${l.to_stop}`
              }
              secondary={
                l.mode === "walk" ? null : (
                  <>
                    Paradas: {l.stops.join(", ")}. Espera aprox. {l.wait_min} min, viaje {l.duration_min} min,
                    costo ${l.cost.toLocaleString("es-CO")}. Confianza {Math.round(l.confidence * 100)}%.
                    {l.last_updated ? ` Actualizado: ${l.last_updated}.` : ""}
                    {l.reports.map((r) => ` ${r.n_confirm === 1 ? "1 persona reportó" : `${r.n_confirm} personas reportaron`} ${r.label}.`).join("")}
                    {" "}<SourceBadge kind={l.source_kind} />
                  </>
                )
              }
              secondaryTypographyProps={{ component: "div" }}
            />
          </ListItem>
        ))}
      </List>
    </section>
  );
}
