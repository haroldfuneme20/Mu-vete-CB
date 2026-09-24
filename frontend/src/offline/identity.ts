// Identificador anónimo persistente del dispositivo (FR-015, T071). Sin cuenta ni datos personales.
import { getMeta, setMeta } from "./db";

export function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  // respaldo para navegadores antiguos
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export async function getAnonId(): Promise<string> {
  let id = await getMeta<string>("anon_id");
  if (!id) {
    id = uuid();
    await setMeta("anon_id", id);
  }
  return id;
}
