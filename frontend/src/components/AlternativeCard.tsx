// Tarjeta de alternativa (T058, T074): métricas, fuente y reportes que la afectan.
import WarningIcon from "@mui/icons-material/WarningAmber";
import { Box, Button, Card, CardActions, CardContent, Chip, Stack, Typography } from "@mui/material";
import { Link } from "react-router-dom";
import type { Alternative } from "../types";
import { SourceBadge } from "./SourceBadge";

const MODE: Record<string, string> = {
  troncal: "TransMilenio", provisional: "Provisional", zonal: "SITP", transmicable: "TransMiCable",
  community: "Comunitaria",
};

export function AlternativeCard({ alt, recommended }: { alt: Alternative; recommended?: boolean }) {
  const rides = alt.legs.filter((l) => l.mode !== "walk");
  const kinds = Array.from(new Set(rides.map((l) => l.source_kind)));
  const reports = rides.flatMap((l) => l.reports.map((r) => ({ ...r, route: l.route_name })));
  const title = rides.map((l) => MODE[l.mode] ?? l.mode).join(" + ") || "Caminata";
  return (
    <Card component="article" variant={recommended ? "elevation" : "outlined"} elevation={recommended ? 3 : 0}
      aria-labelledby={`alt-${alt.id}`}
      sx={{ borderLeft: recommended ? "6px solid" : undefined, borderColor: "secondary.main" }}>
      <CardContent>
        {recommended && <Chip label="Recomendada" color="secondary" size="small" sx={{ mb: 1 }} />}
        <Typography id={`alt-${alt.id}`} variant="h3" component="h3">{title}</Typography>
        <Typography variant="body1" sx={{ mt: 0.5 }}>
          <strong>{alt.total_time_min} min</strong> · ${alt.cost.toLocaleString("es-CO")} ·{" "}
          {alt.transfers === 0 ? "sin transbordos" : `${alt.transfers} transbordo${alt.transfers > 1 ? "s" : ""}`}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Confianza {Math.round(alt.confidence * 100)}% · Confiabilidad {Math.round(alt.reliability * 100)}%
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap", rowGap: 1 }}>
          {kinds.map((k) => <SourceBadge key={k} kind={k} />)}
        </Stack>
        {reports.length > 0 && (
          <Box sx={{ mt: 1, display: "flex", gap: 1, alignItems: "flex-start", color: "warning.main" }}>
            <WarningIcon aria-hidden fontSize="small" />
            <Typography variant="body2">
              {reports.map((r) =>
                `${r.n_confirm === 1 ? "1 persona reportó" : `${r.n_confirm} personas reportaron`} ${r.label} en ${r.route}`,
              ).join(". ")}.
            </Typography>
          </Box>
        )}
      </CardContent>
      <CardActions>
        <Button component={Link} to={`/ruta/${alt.id}`} variant={recommended ? "contained" : "outlined"}
          aria-label={`Ver detalles de ${title}, ${alt.total_time_min} minutos`}>
          Ver detalles
        </Button>
      </CardActions>
    </Card>
  );
}
