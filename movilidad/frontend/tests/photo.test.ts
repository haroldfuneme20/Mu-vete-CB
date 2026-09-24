// T072: reglas de compresión de fotos (tamaño y calidades).
import { describe, expect, it } from "vitest";
import { encodeWithinLimit, MAX_BYTES, PhotoTooLargeError, targetSize } from "../src/offline/photo";

const blobOf = (n: number) => new Blob([new Uint8Array(n)], { type: "image/jpeg" });

describe("targetSize", () => {
  it("reduce el lado mayor a 1280 px conservando proporción", () => {
    expect(targetSize(4000, 3000)).toEqual({ width: 1280, height: 960 });
    expect(targetSize(1000, 2560)).toEqual({ width: 500, height: 1280 });
  });
  it("no agranda fotos pequeñas", () => {
    expect(targetSize(800, 600)).toEqual({ width: 800, height: 600 });
  });
});

describe("encodeWithinLimit", () => {
  it("usa la primera calidad que cabe en 1 MB", async () => {
    const tried: number[] = [];
    const out = await encodeWithinLimit(async (q) => {
      tried.push(q);
      return blobOf(q > 0.6 ? MAX_BYTES + 1 : 500_000);
    });
    expect(out.size).toBe(500_000);
    expect(tried).toEqual([0.7, 0.6]);
  });
  it("rechaza si ni con calidad 0,5 cabe", async () => {
    await expect(encodeWithinLimit(async () => blobOf(MAX_BYTES + 1))).rejects.toBeInstanceOf(PhotoTooLargeError);
  });
});
