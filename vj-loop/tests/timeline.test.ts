import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { layoutTrack, ZONES } from "../src/core/layout";
import { cycle, deriveLoop, hash01, LoopSpec, relAhead, rng, stepNoise, timeAt, wave } from "../src/core/timeline";

const loop = deriveLoop(LoopSpec.parse({}));

describe("deriveLoop", () => {
  it("gives 20 bars at 160 bpm as exactly 30 seconds and 1800 frames", () => {
    expect(loop.beats).toBe(80);
    expect(loop.seconds).toBe(30);
    expect(loop.frames).toBe(1800);
  });

  it("refuses a loop that is not a whole number of frames", () => {
    expect(() => deriveLoop(LoopSpec.parse({ bpm: 140, bars: 16 }))).toThrow(/whole number/);
  });

  it("rejects unknown spec keys", () => {
    expect(() => LoopSpec.parse({ bmp: 160 })).toThrow();
  });
});

describe("relAhead", () => {
  it("stays inside [-behind, length - behind)", () => {
    fc.assert(
      fc.property(fc.double({ min: -5000, max: 5000, noNaN: true }), fc.double({ min: -5000, max: 5000, noNaN: true }), (o, c) => {
        const r = relAhead(o, c, loop.length, 30);
        return r >= -30 && r < loop.length - 30;
      }),
    );
  });

  it("is the same after the camera travels one full lap", () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 79 }), fc.double({ min: -720, max: 0, noNaN: true }), (i, cam) => {
        const z = -i * loop.spec.unitsPerBeat;
        return Math.abs(relAhead(z, cam, loop.length, 30) - relAhead(z, cam - loop.length, loop.length, 30)) < 1e-6;
      }),
    );
  });
});

describe("cycle", () => {
  it("accepts cycles that divide the loop and refuses the rest", () => {
    for (const n of [1, 2, 4, 5, 8, 10, 16, 20, 40, 80]) expect(() => cycle(loop, 3, n)).not.toThrow();
    for (const n of [3, 6, 7, 12, 32]) expect(() => cycle(loop, 3, n)).toThrow(/does not divide/);
  });
});

describe("loop closure", () => {
  // The end of the loop (frame index = frame count, phase exactly 1) must give the same state as frame 0.
  const start = timeAt(loop, 0, 0);
  const end = timeAt(loop, loop.frames, 0);

  it("closes every periodic driver", () => {
    expect(end.phase - start.phase).toBeCloseTo(1, 12);
    for (const n of [1, 2, 4, 8]) expect(cycle(loop, end.beat, n)).toBeCloseTo(cycle(loop, start.beat, n), 9);
    for (const turns of [1, 2, 5, 10]) expect(wave(end, turns)).toBeCloseTo(wave(start, turns), 9);
    for (let seed = 0; seed < 50; seed++) expect(stepNoise(loop, end.beat, 4, seed)).toBe(stepNoise(loop, start.beat, 4, seed));
  });

  it("puts every module back where it started", () => {
    for (const slot of layoutTrack(loop)) {
      expect(relAhead(slot.z, end.camZ, loop.length, 30)).toBeCloseTo(relAhead(slot.z, start.camZ, loop.length, 30), 6);
    }
  });

  it("closes at any frame offset, not only at frame 0", () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: loop.frames - 1 }), fc.integer({ min: 0, max: 7 }), (f, sub) => {
        const a = timeAt(loop, f, sub);
        const b = timeAt(loop, f + loop.frames, sub);
        return (
          Math.abs(cycle(loop, a.beat, 8) - cycle(loop, b.beat, 8)) < 1e-6 &&
          Math.abs(wave(a, 10) - wave(b, 10)) < 1e-6
        );
      }),
    );
  });

  it("rejects a wave that would not close", () => {
    expect(() => wave(start, 1.5)).toThrow();
  });
});

describe("layout", () => {
  const slots = layoutTrack(loop);
  it("has one module per beat, in equal zones, with a downbeat every bar", () => {
    expect(slots).toHaveLength(80);
    for (const z of ZONES) expect(slots.filter((s) => s.zone === z)).toHaveLength(20);
    expect(slots.filter((s) => s.downbeat)).toHaveLength(20);
    expect(slots[0]!.downbeat).toBe(true);
  });
  it("refuses a loop that does not split into equal zones", () => {
    expect(() => layoutTrack(deriveLoop(LoopSpec.parse({ bars: 5, bpm: 150 })))).not.toThrow();
    expect(() => layoutTrack(deriveLoop(LoopSpec.parse({ bars: 5, beatsPerBar: 3, bpm: 150 })))).toThrow(/equal zones/);
  });
});

describe("randomness", () => {
  it("is seeded and repeatable", () => {
    const a = rng(42);
    const b = rng(42);
    for (let i = 0; i < 100; i++) expect(a()).toBe(b());
  });
  it("hash01 stays in [0, 1)", () => {
    fc.assert(fc.property(fc.integer(), (n) => hash01(n) >= 0 && hash01(n) < 1));
  });
});

describe("cellDividing", () => {
  it("returns a cell that tiles the lap a whole number of times and is no larger than asked", async () => {
    const { cellDividing } = await import("../src/scene/kit");
    fc.assert(
      fc.property(fc.double({ min: 10, max: 5000, noNaN: true }), fc.double({ min: 0.05, max: 5, noNaN: true }), (length, want) => {
        const cell = cellDividing(length, want);
        const n = length / cell;
        return cell <= want + 1e-12 && Math.abs(n - Math.round(n)) < 1e-6;
      }),
    );
  });
});
