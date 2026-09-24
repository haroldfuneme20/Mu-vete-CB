// Mapa interactivo (T100–T102): capas base offline, ruta recomendada e incidentes activos.
import { Alert, Button, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LayerToggle, type LayerKey } from "../components/LayerToggle";
import { Legend } from "../components/Legend";
import { MapView, type Incident } from "../map/MapView";
import { api } from "../services/api";
import { useApp } from "../state/AppState";

export function MapPage() {
  const { rec, online } = useApp();
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    barrios: true, roads: true, trunk: true, community: true, stops: true, incidents: true,
  });
  const [incidents, setIncidents] = useState<Incident[]>([]);
  useEffect(() => {
    if (!online) return;
    api.reports().then((r) => setIncidents(r.items as unknown as Incident[])).catch(() => undefined);
  }, [online]);

  return (
    <Stack spacing={2}>
      <Typography variant="h1">Mapa del territorio</Typography>
      {!online && <Alert severity="warning">Sin conexión: se muestran los datos guardados, sin fondo de mapa.</Alert>}
      <MapView label="Mapa de Ciudad Bolívar con rutas e incidentes" layers={layers}
        recommended={rec?.recommended} alternatives={rec?.alternatives ?? []} incidents={incidents} height={420} />
      <LayerToggle value={layers} onChange={setLayers} />
      <Legend />
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
