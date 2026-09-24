// Distingue la fuente del dato (FR-028): nunca se presenta lo simulado como oficial.
import { Chip } from "@mui/material";
import type { SourceKind } from "../types";

const LABEL: Record<SourceKind, string> = {
  institutional: "Dato institucional",
  community: "Dato comunitario",
  territorial: "Dato territorial",
  demo_simulated: "Simulada para la demo",
};

export function SourceBadge({ kind }: { kind: SourceKind }) {
  return (
    <Chip
      size="small"
      label={LABEL[kind]}
      variant={kind === "institutional" ? "outlined" : "filled"}
      color={kind === "demo_simulated" ? "warning" : kind === "community" ? "secondary" : "default"}
    />
  );
}
