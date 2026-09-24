// Ubicación del reporte: GPS del teléfono o punto en el mapa (T073, reutiliza MapView de T100).
import MyLocationIcon from "@mui/icons-material/MyLocation";
import { Alert, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { announce } from "../a11y/announce";
import { MapView } from "../map/MapView";

interface Props {
  value: { lat: number; lng: number } | null;
  onChange: (v: { lat: number; lng: number }) => void;
}

export function LocationPicker({ value, onChange }: Props) {
  const [error, setError] = useState<string | null>(null);
  const useGps = () => {
    setError(null);
    if (!navigator.geolocation) {
      setError("Tu teléfono no permite obtener la ubicación. Toca el mapa para marcarla.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => {
        onChange({ lat: p.coords.latitude, lng: p.coords.longitude });
        announce("Ubicación actual guardada.");
      },
      () => setError("No pudimos obtener tu ubicación. Toca el mapa para marcarla."),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };
  return (
    <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
      <Typography component="legend" variant="h3" sx={{ mb: 1 }}>¿Dónde?</Typography>
      <Stack spacing={1}>
        <Button variant="outlined" startIcon={<MyLocationIcon aria-hidden />} onClick={useGps}>
          Usar mi ubicación actual
        </Button>
        <Typography variant="body2" color="text.secondary">O toca el mapa para marcar el lugar.</Typography>
        <MapView height={240} label="Mapa para marcar la ubicación del reporte" picked={value}
          layers={{ barrios: true, roads: true, trunk: true, community: true, stops: true, incidents: false }}
          onPick={(lat, lng) => {
            onChange({ lat, lng });
            announce("Ubicación marcada en el mapa.");
          }} />
        {value && (
          <Typography variant="body2" aria-live="polite">
            Ubicación elegida: {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
          </Typography>
        )}
        {error && <Alert severity="warning">{error}</Alert>}
      </Stack>
    </fieldset>
  );
}
