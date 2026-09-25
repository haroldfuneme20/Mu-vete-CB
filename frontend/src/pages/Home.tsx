// Pantalla Inicio (T057, T096): formulario siempre disponible + consulta en lenguaje natural.
import { Alert, Box, Button, Divider, Stack, Tab, Tabs, Typography } from "@mui/material";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { announce } from "../a11y/announce";
import { AskBox } from "../components/AskBox";
import { DisambiguationDialog } from "../components/DisambiguationDialog";
import { PlaceField } from "../components/PlaceField";
import { PriorityPicker } from "../components/PriorityPicker";
import { ApiError } from "../services/api";
import { recommend } from "../services/recommendations";
import { useApp } from "../state/AppState";
import type { PlaceItem, Priority, RecommendationRequest } from "../types";

export function Home() {
  const nav = useNavigate();
  const { setRec } = useApp();
  const [tab, setTab] = useState(0); // 0 = Formulario (por defecto), 1 = Pregunta con tus palabras
  const [origin, setOrigin] = useState<PlaceItem | null>(null);
  const [dest, setDest] = useState<PlaceItem | null>(null);
  const [priority, setPriority] = useState<Priority>("balanced");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disamb, setDisamb] = useState<{ message: string; candidates: PlaceItem[]; field: string; query: string } | null>(null);

  async function run(req: RecommendationRequest, labels?: { o?: string; d?: string }) {
    setBusy(true);
    setError(null);
    announce("Buscando rutas…");
    try {
      const rec = await recommend(req, labels);
      setRec(rec);
      nav("/resultados");
    } catch (e) {
      if (e instanceof ApiError && e.code === "AMBIGUOUS_PLACE" && req.query) {
        setDisamb({
          message: e.message,
          candidates: (e.details.candidates as PlaceItem[]) ?? [],
          field: (e.details.field as string) ?? "destino",
          query: req.query,
        });
      } else {
        const msg = e instanceof Error ? e.message : "Algo salió mal.";
        setError(msg);
        announce(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  const submitForm = (e: FormEvent) => {
    e.preventDefault();
    if (!origin || !dest) {
      setError("Elige el origen y el destino.");
      return;
    }
    run(
      { origin: { ref_id: origin.ref_id }, destination: { ref_id: dest.ref_id }, priority },
      { o: origin.display_name, d: dest.display_name },
    );
  };

  return (
    <Stack spacing={2}>
      <Typography variant="h1">¿A dónde vas hoy?</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} aria-label="Forma de buscar" variant="fullWidth">
        <Tab label="Formulario" id="tab-form" aria-controls="panel-form" />
        <Tab label="Pregunta con tus palabras" id="tab-ask" aria-controls="panel-ask" />
      </Tabs>

      <Box role="tabpanel" id="panel-form" aria-labelledby="tab-form" hidden={tab !== 0}>
        <form onSubmit={submitForm} aria-label="Buscar ruta con formulario">
          <Stack spacing={2}>
            <PlaceField id="origin" label="Origen" value={origin} onChange={setOrigin} />
            <PlaceField id="destination" label="Destino" value={dest} onChange={setDest} />
            <PriorityPicker value={priority} onChange={setPriority} />
            <Button type="submit" variant="contained" color="secondary" size="large" disabled={busy}>
              {busy ? "Buscando…" : "Buscar rutas"}
            </Button>
          </Stack>
        </form>
      </Box>

      <Box role="tabpanel" id="panel-ask" aria-labelledby="tab-ask" hidden={tab !== 1}>
        <AskBox busy={busy} onAsk={(q) => run({ query: q })} onUseForm={() => setTab(0)} />
      </Box>

      {error && (
        <Alert severity={error.includes("Sin conexión") ? "warning" : "error"} role="alert">
          {error}
        </Alert>
      )}
      <Divider />
      <Typography variant="body2" color="text.secondary">
        Cubrimos viajes que empiezan o terminan en Ciudad Bolívar. Las rutas comunitarias de esta demo son simuladas.
      </Typography>

      <DisambiguationDialog
        open={!!disamb}
        message={disamb?.message ?? ""}
        candidates={disamb?.candidates ?? []}
        onClose={() => setDisamb(null)}
        onPick={(p) => {
          const d = disamb!;
          setDisamb(null);
          // se completa la consulta con el lugar elegido usando el formulario
          if (d.field === "origen") setOrigin(p);
          else setDest(p);
          setTab(0);
          announce(`${p.display_name} elegido como ${d.field}. Completa el formulario y busca.`);
        }}
      />
    </Stack>
  );
}
