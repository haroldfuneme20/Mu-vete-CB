// Anuncios para lectores de pantalla (región aria-live global, FR-011).
let region: HTMLElement | null = null;

function ensureRegion(): HTMLElement {
  if (region && document.body.contains(region)) return region;
  region = document.createElement("div");
  region.setAttribute("aria-live", "polite");
  region.setAttribute("role", "status");
  Object.assign(region.style, {
    position: "absolute", width: "1px", height: "1px", overflow: "hidden",
    clip: "rect(0 0 0 0)", whiteSpace: "nowrap",
  });
  document.body.appendChild(region);
  return region;
}

export function announce(message: string): void {
  const r = ensureRegion();
  r.textContent = "";
  // pequeño retraso para que el lector detecte el cambio
  window.setTimeout(() => (r.textContent = message), 50);
}
