// Campo de lugar con autocompletar (T057): /api/places en línea, places_index.json sin conexión.
import { Autocomplete, TextField } from "@mui/material";
import { useEffect, useState } from "react";
import { offlinePlaces } from "../offline/package";
import { api } from "../services/api";
import type { PlaceItem } from "../types";

const KIND: Record<PlaceItem["kind"], string> = {
  barrio: "Barrio", station: "Estación", stop: "Paradero", landmark: "Lugar",
};

interface Props {
  id: string;
  label: string;
  value: PlaceItem | null;
  onChange: (p: PlaceItem | null) => void;
}

export function PlaceField({ id, label, value, onChange }: Props) {
  const [input, setInput] = useState("");
  const [options, setOptions] = useState<PlaceItem[]>([]);

  useEffect(() => {
    if (input.trim().length < 2) {
      setOptions([]);
      return;
    }
    let alive = true;
    const t = window.setTimeout(async () => {
      let items: PlaceItem[] = [];
      try {
        items = navigator.onLine ? (await api.places(input)).items : await offlinePlaces(input);
      } catch {
        items = await offlinePlaces(input);
      }
      if (alive) setOptions(items);
    }, 250);
    return () => {
      alive = false;
      window.clearTimeout(t);
    };
  }, [input]);

  return (
    <Autocomplete
      id={id}
      options={options}
      value={value}
      filterOptions={(x) => x}
      getOptionLabel={(o) => o.display_name}
      isOptionEqualToValue={(a, b) => a.ref_id === b.ref_id}
      onChange={(_, v) => onChange(v)}
      onInputChange={(_, v) => setInput(v)}
      noOptionsText={input.length < 2 ? "Escribe al menos 2 letras" : "Sin coincidencias"}
      renderOption={(props, o) => {
        const { key, ...rest } = props as typeof props & { key: string };
        return (
          <li key={key} {...rest}>
            {o.display_name} · {KIND[o.kind]}{o.localidad ? ` · ${o.localidad}` : ""}
          </li>
        );
      }}
      renderInput={(params) => <TextField {...params} label={label} required fullWidth />}
    />
  );
}
