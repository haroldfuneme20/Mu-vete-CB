// Reportar incidencia (T073, T083): en línea envía; sin conexión guarda en el outbox.
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import { Alert, Button, Stack, TextField, Typography } from "@mui/material";
import { useState, type ChangeEvent, type FormEvent } from "react";
import { announce } from "../a11y/announce";
import { CategoryPicker } from "../components/CategoryPicker";
import { LocationPicker } from "../components/LocationPicker";
import { getAnonId, uuid } from "../offline/identity";
import { saveToOutbox, setStatus } from "../offline/outbox";
import { compressPhoto } from "../offline/photo";
import { api, ApiError } from "../services/api";
import { recommend } from "../services/recommendations";
import { useApp } from "../state/AppState";
import type { Category } from "../types";

export function Report() {
  const { online, rec, setRec, refreshPending } = useApp();
  const [category, setCategory] = useState<Category | null>(null);
  const [loc, setLoc] = useState<{ lat: number; lng: number } | null>(null);
  const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState<Blob | null>(null);
  const [photoMsg, setPhotoMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);

  const onPhoto = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const b = await compressPhoto(f);
      setPhoto(b);
      setPhotoMsg(`Foto lista (${Math.round(b.size / 1024)} KB, sin datos de ubicación).`);
    } catch (err) {
      setPhoto(null);
      setPhotoMsg(err instanceof Error ? err.message : "No se pudo usar la foto.");
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!category || !loc) {
      setResult({ ok: false, text: "Elige qué ocurrió y dónde." });
      return;
    }
    setBusy(true);
    const report = {
      id: uuid(), anon_id: await getAnonId(), category, location: loc,
      description: description.trim() || undefined, created_at: new Date().toISOString(),
      photo: photo ?? undefined,
    };
    // siempre se guarda primero en el outbox: nunca se pierde un reporte
    await saveToOutbox(report);
    let text: string;
    if (online) {
      try {
        const form = new FormData();
        const { photo: p, ...json } = report;
        form.append("report", JSON.stringify(json));
        if (p) form.append("photo", p, "foto.jpg");
        const r = await api.postReport(form);
        await setStatus([report.id], "synced");
        text = r.confirmations > 1
          ? `Reporte enviado. ${r.confirmations} personas han reportado esto.`
          : "Reporte enviado. Gracias por ayudar a tu comunidad.";
        if (rec) {
          const again = await recommend({
            origin: { lat: rec.request.origin.lat, lng: rec.request.origin.lng, label: rec.request.origin.display_name },
            destination: { lat: rec.request.destination.lat, lng: rec.request.destination.lng, label: rec.request.destination.display_name },
            priority: rec.request.priority,
          }).catch(() => null);
          if (again) {
            setRec(again);
            text += " Actualizamos tu recomendación.";
          }
        }
      } catch (err) {
        text = err instanceof ApiError && err.code !== "OFFLINE"
          ? `No se pudo enviar: ${err.message}`
          : "Guardado localmente. Pendiente de sincronización.";
      }
    } else {
      text = "Guardado localmente. Pendiente de sincronización.";
    }
    refreshPending();
    setResult({ ok: true, text });
    announce(text);
    setBusy(false);
    setCategory(null);
    setDescription("");
    setPhoto(null);
    setPhotoMsg(null);
  };

  return (
    <form onSubmit={submit} aria-label="Reportar incidencia">
      <Stack spacing={2.5}>
        <Typography variant="h1">Reportar incidencia</Typography>
        <Typography variant="body2" color="text.secondary">Tu reporte es anónimo.</Typography>
        <CategoryPicker value={category} onChange={setCategory} />
        <LocationPicker value={loc} onChange={setLoc} />
        <TextField label="Descripción (opcional)" multiline minRows={2} value={description}
          onChange={(e) => setDescription(e.target.value.slice(0, 280))}
          helperText={`${description.length}/280`} />
        <Stack spacing={1}>
          <Button variant="outlined" component="label" startIcon={<PhotoCameraIcon aria-hidden />}>
            Agregar foto (opcional)
            <input hidden type="file" accept="image/*" capture="environment" onChange={onPhoto}
              aria-label="Agregar foto opcional" />
          </Button>
          <Typography variant="body2" color="text.secondary">No incluyas rostros ni placas en la foto.</Typography>
          {photoMsg && <Typography variant="body2" aria-live="polite">{photoMsg}</Typography>}
        </Stack>
        <Button type="submit" variant="contained" color="secondary" size="large" disabled={busy}>
          {busy ? "Guardando…" : online ? "Enviar reporte" : "Guardar reporte"}
        </Button>
        {result && <Alert severity={result.ok ? "success" : "error"} role="alert">{result.text}</Alert>}
      </Stack>
    </form>
  );
}
