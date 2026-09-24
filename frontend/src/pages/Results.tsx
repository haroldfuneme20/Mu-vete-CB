// Resultados (T058, T097): explicación anunciada + alternativas.
import { Alert, Button, Stack, Typography } from "@mui/material";
import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { AlternativeCard } from "../components/AlternativeCard";
import { LiveAnswer } from "../components/LiveAnswer";
import { useApp } from "../state/AppState";
import { PRIORITY_LABEL } from "../types";

export function Results() {
  const { rec } = useApp();
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), [rec]);

  if (!rec) {
    return (
      <Stack spacing={2}>
        <Typography variant="h1">Rutas disponibles</Typography>
        <Alert severity="info">Aún no has buscado una ruta.</Alert>
        <Button component={Link} to="/" variant="contained">Buscar ruta</Button>
      </Stack>
    );
  }
  const cached = rec.from_cache ? new Date(rec.computed_at).toLocaleString("es-CO") : null;
  return (
    <Stack spacing={2}>
      <Typography variant="h1" ref={heading} tabIndex={-1}>Rutas disponibles</Typography>
      <Typography variant="body1">
        De <strong>{rec.request.origin.display_name}</strong> a <strong>{rec.request.destination.display_name}</strong>
        {" · "}{PRIORITY_LABEL[rec.request.priority]}
      </Typography>
      {rec.request.interpreted_from_text && (
        <Typography variant="body2" color="text.secondary">Entendimos tu pregunta así.</Typography>
      )}
      {rec.from_cache && (
        <Alert severity="warning" role="status">
          Sin conexión: mostramos un resultado guardado ({cached}). Puede no incluir reportes recientes.
        </Alert>
      )}
      {rec.warning === "all_affected" && (
        <Alert severity="warning" role="alert">
          Todas las opciones tienen reportes recientes. Te mostramos la mejor disponible.
        </Alert>
      )}
      <LiveAnswer text={rec.explanation} cached={cached} />
      <AlternativeCard alt={rec.recommended} recommended />
      {rec.alternatives.length > 0 && (
        <Typography variant="h2" component="h2">Otras opciones</Typography>
      )}
      {rec.alternatives.map((a) => <AlternativeCard key={a.id} alt={a} />)}
      {rec.data_mode === "mock" && (
        <Typography variant="body2" color="text.secondary">
          Datos de prueba (mock) mientras se cargan los archivos oficiales.
        </Typography>
      )}
    </Stack>
  );
}
