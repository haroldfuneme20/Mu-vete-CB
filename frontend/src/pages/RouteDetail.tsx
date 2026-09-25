// Detalle de ruta (T059, T074): recorrido textual, explicación, evidencia y "Ver en mapa".
import MapIcon from "@mui/icons-material/Map";
import { Alert, Button, List, ListItem, ListItemText, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Legend } from "../components/Legend";
import { RouteText } from "../components/RouteText";
import { MapView } from "../map/MapView";
import { useApp } from "../state/AppState";

export function RouteDetail() {
  const { id } = useParams();
  const { rec } = useApp();
  const [showMap, setShowMap] = useState(true);
  const all = rec ? [rec.recommended, ...rec.alternatives] : [];
  const alt = all.find((a) => a.id === id);
  if (!rec || !alt) {
    return <Alert severity="info">Esta ruta ya no está disponible. <Link to="/">Busca de nuevo</Link>.</Alert>;
  }
  const isRec = alt.id === rec.recommended.id;
  return (
    <Stack spacing={2}>
      <Typography variant="h1">{isRec ? "Ruta recomendada" : `Alternativa ${alt.rank}`}</Typography>
      <Typography variant="body1">
        <strong>{alt.total_time_min} min</strong> · ${alt.cost.toLocaleString("es-CO")} · confianza {Math.round(alt.confidence * 100)}%
      </Typography>
      <Typography variant="body1">{alt.text_description}</Typography>
      {isRec && (
        <Alert severity="info" role="note">
          <strong>¿Por qué esta ruta?</strong> {rec.explanation}
        </Alert>
      )}
      <Button variant="contained" startIcon={<MapIcon aria-hidden />} onClick={() => setShowMap((v) => !v)}
        aria-expanded={showMap} aria-controls="route-map">
        {showMap ? "Ocultar mapa" : "Ver en mapa"}
      </Button>
      {showMap && (
        <div id="route-map">
          <MapView label={`Mapa de la ruta de ${alt.total_time_min} minutos`} route={alt} height={380} />
          <Legend route={alt} />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            El recorrido completo está descrito en texto abajo.
          </Typography>
        </div>
      )}
      <RouteText alt={alt} />
      <section aria-label="Evidencia">
        <Typography variant="h3" component="h2">¿De dónde sale esta información?</Typography>
        <List dense>
          {alt.evidence.map((e, i) => (
            <ListItem key={i} sx={{ px: 0 }}>
              <ListItemText primary={e.label} secondary={e.date ? `Fecha: ${e.date}` : null} />
            </ListItem>
          ))}
        </List>
      </section>
      <Button component={Link} to="/resultados" variant="outlined">Volver a las opciones</Button>
    </Stack>
  );
}
