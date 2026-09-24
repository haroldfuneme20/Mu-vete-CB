// Consulta en lenguaje natural (T096). Compatible con el dictado del teclado del teléfono.
import SendIcon from "@mui/icons-material/Send";
import { Alert, Button, Stack, TextField } from "@mui/material";
import { useState, type FormEvent } from "react";
import { useApp } from "../state/AppState";

interface Props {
  busy: boolean;
  onAsk: (text: string) => void;
  onUseForm: () => void;
}

export function AskBox({ busy, onAsk, onUseForm }: Props) {
  const { online } = useApp();
  const [text, setText] = useState("");
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (text.trim()) onAsk(text.trim());
  };
  return (
    <form onSubmit={submit} aria-label="Pregunta en lenguaje natural">
      <Stack spacing={1.5}>
        <TextField
          id="ask"
          label="¿A dónde quieres ir?"
          placeholder="Ej.: Necesito ir del barrio Paraíso al Portal Tunal, lo más seguro"
          helperText="Escribe o dicta con el micrófono del teclado."
          multiline
          minRows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={!online}
          fullWidth
        />
        {!online && (
          <Alert severity="warning" role="alert"
            action={<Button color="inherit" onClick={onUseForm}>Usar formulario</Button>}>
            Preguntar con tus palabras necesita conexión. Puedes usar el formulario.
          </Alert>
        )}
        <Button type="submit" variant="contained" size="large" endIcon={<SendIcon aria-hidden />}
          disabled={!online || busy || !text.trim()}>
          {busy ? "Buscando…" : "Preguntar"}
        </Button>
      </Stack>
    </form>
  );
}
