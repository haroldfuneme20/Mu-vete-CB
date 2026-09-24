// Compresión de fotos en el teléfono (T072, FR-016, research R-10).
// Dibujar en un canvas y re-codificar a JPEG elimina TODOS los metadatos EXIF (incluido el GPS).

export const MAX_SIDE = 1280;
export const MAX_BYTES = 1024 * 1024;
export const QUALITIES = [0.7, 0.6, 0.5];

export class PhotoTooLargeError extends Error {
  constructor() {
    super("La foto es muy pesada incluso comprimida. Puedes enviar el reporte sin foto.");
  }
}

export function targetSize(width: number, height: number, maxSide = MAX_SIDE) {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  return { width: Math.round(width * scale), height: Math.round(height * scale) };
}

/** Prueba calidades decrecientes hasta que el JPEG quepa en MAX_BYTES. */
export async function encodeWithinLimit(
  encode: (quality: number) => Promise<Blob>,
  maxBytes = MAX_BYTES,
): Promise<Blob> {
  for (const q of QUALITIES) {
    const blob = await encode(q);
    if (blob.size <= maxBytes) return blob;
  }
  throw new PhotoTooLargeError();
}

export async function compressPhoto(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const { width, height } = targetSize(bitmap.width, bitmap.height);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("No se pudo procesar la foto");
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close?.();
  return encodeWithinLimit(
    (q) =>
      new Promise<Blob>((resolve, reject) =>
        canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob falló"))), "image/jpeg", q),
      ),
  );
}
