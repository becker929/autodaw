import { describe, expect, it } from "vitest";
import { analyseFlashes, lumaFromRgba, transitionSign } from "../src/core/flash";

const flat = (v: number, n = 100) => new Float32Array(n).fill(v);

describe("lumaFromRgba", () => {
  it("maps black to 0 and white to 1", () => {
    const l = lumaFromRgba(new Uint8Array([0, 0, 0, 255, 255, 255, 255, 255]));
    expect(l[0]).toBe(0);
    expect(l[1]).toBeCloseTo(1, 6);
  });
});

describe("transitionSign", () => {
  it("needs a quarter of the area to move by more than 0.1", () => {
    const a = flat(0.2);
    const b = flat(0.2);
    for (let i = 0; i < 24; i++) b[i] = 0.5;
    expect(transitionSign(a, b)).toBe(0);
    b[24] = 0.5;
    expect(transitionSign(a, b)).toBe(1);
    expect(transitionSign(b, a)).toBe(-1);
    expect(transitionSign(a, flat(0.29))).toBe(0);
  });
});

describe("analyseFlashes", () => {
  it("passes a steady sequence", () => {
    const r = analyseFlashes(Array.from({ length: 120 }, () => flat(0.3)), 60);
    expect(r.worstFlashesPerSecond).toBe(0);
    expect(r.windowsOverLimit).toBe(0);
  });
  it("counts a 10 Hz strobe as ten flashes a second", () => {
    // 60 fps, 3 frames bright, 3 frames dark: 10 full cycles per second.
    const frames = Array.from({ length: 120 }, (_, f) => flat(f % 6 < 3 ? 0.6 : 0.05));
    const r = analyseFlashes(frames, 60);
    expect(r.worstFlashesPerSecond).toBe(10);
    expect(r.windowsOverLimit).toBe(1);
  });
  it("lets a 2.5 Hz beat flash pass", () => {
    const frames = Array.from({ length: 120 }, (_, f) => flat(f % 24 < 3 ? 0.6 : 0.05));
    expect(analyseFlashes(frames, 60).worstFlashesPerSecond).toBeLessThanOrEqual(3);
  });
  it("reports the share of black pixels", () => {
    const half = flat(0.5);
    for (let i = 0; i < 50; i++) half[i] = 0;
    expect(analyseFlashes([half, half], 60).blackShare).toBeCloseTo(0.5, 6);
  });
});
