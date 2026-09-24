// Desambiguación accesible de lugares (T096, FR-009).
import { Button, Dialog, DialogActions, DialogContent, DialogTitle, List, ListItemButton, ListItemText } from "@mui/material";
import type { PlaceItem } from "../types";

interface Props {
  open: boolean;
  message: string;
  candidates: PlaceItem[];
  onPick: (p: PlaceItem) => void;
  onClose: () => void;
}

export function DisambiguationDialog({ open, message, candidates, onPick, onClose }: Props) {
  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="disamb-title" fullWidth>
      <DialogTitle id="disamb-title">{message}</DialogTitle>
      <DialogContent>
        {candidates.length === 0 ? (
          "No encontramos coincidencias. Revisa el nombre o usa el formulario."
        ) : (
          <List aria-label="Lugares posibles">
            {candidates.map((c) => (
              <ListItemButton key={c.ref_id} onClick={() => onPick(c)}>
                <ListItemText primary={c.display_name} secondary={c.localidad ?? undefined} />
              </ListItemButton>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cerrar</Button>
      </DialogActions>
    </Dialog>
  );
}
