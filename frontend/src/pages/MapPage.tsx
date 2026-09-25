// Mapa interactivo (T100–T102): territorio con capas discretas, o solo la ruta elegida.
import { Alert, Button, Stack, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LayerToggle, type LayerKey } from "../components/LayerToggle";
import { Legend } from "../components/Legend";
import { MapView, type Incident } from "../map/MapView";
import { api } from "../services/api";
import { useApp } from "../state/AppState";

export function MapPage() {
  const { rec, online } = useApp();
  const [view, setView] = useState<"route" | "territory">(rec ? "route" : "territory");
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    barrios: true, roads: false, trunk: true, community: true, stops: true, incidents: true,
  });
  const [incidents, setIncidents] = useState<Incident[]>([]);
  useEffect(() => {
    if (!online) return;
    api.reports().then((r) => setIncidents(r.items as unknown as Incident[])).catch(() => undefined);
  }, [online]);
  const showRoute = view === "route" && !!rec;

  return (
    <Stack spacing={2}>
      <Typography variant="h1">Mapa</Typography>
      {!online && <Alert severity="warning">Sin conexión: se muestran los datos guardados, sin fondo de mapa.</Alert>}
      {rec && (
        <ToggleButtonGroup exclusive fullWidth color="primary" value={view} aria-label="Qué mostrar en el mapa"
          onChange={(_, v) => v && setView(v)}>
          <ToggleButton value="route">Mi ruta</ToggleButton>
          <ToggleButton value="territory">Territorio</ToggleButton>
        </ToggleButtonGroup>
      )}
      <MapView label={showRoute ? "Mapa de la ruta recomendada" : "Mapa de Ciudad Bolívar con estaciones e incidentes"}
        route={showRoute ? rec!.recommended : null} layers={layers} incidents={incidents} height={440} />
      {!showRoute && <LayerToggle value={layers} onChange={setLayers} />}
      <Legend route={showRoute ? rec!.recommended : null} />
      <Typography variant="body2">
        {incidents.length === 0 ? "No hay incidentes activos." : `${incidents.length} incidente(s) activo(s) en el mapa.`}
      </Typography>
      {rec && (
        <Button component={Link} to={`/ruta/${rec.recommended.id}`} variant="outlined">
          Leer la ruta recomendada en texto
        </Button>
      )}
    </Stack>
  );
}
