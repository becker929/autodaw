// Black-box check of the rendered loop. It looks only at pixels.
//   1. Determinism: the same frame renders to the same pixels, whatever was rendered in between.
//   2. Closure: frame f + N (one full lap later) equals frame f. This is checked inside every zone,
//      because a part that fails to close is only visible while its zone is on screen.
//   3. The last frame differs from the first, so the loop point does not stutter on a repeated frame.
import { PNG } from "pngjs";
import { layoutTrack, ZONES } from "../src/core/layout";
import { parseFlags, splitFlags } from "./flags";
import { openSession } from "./session";

function diff(a: Buffer, b: Buffer): { mean: number; max: number } {
  const pa = PNG.sync.read(a);
  const pb = PNG.sync.read(b);
  if (pa.width !== pb.width || pa.height !== pb.height) throw new Error("size mismatch");
  let sum = 0;
  let max = 0;
  let n = 0;
  for (let i = 0; i < pa.data.length; i += 4) {
    for (let c = 0; c < 3; c++) {
      const d = Math.abs(pa.data[i + c]! - pb.data[i + c]!);
      sum += d;
      if (d > max) max = d;
      n++;
    }
  }
  return { mean: sum / n, max };
}

async function main(): Promise<void> {
  const { spec } = splitFlags({ width: 640, height: 360, subframes: 2, ...parseFlags(process.argv.slice(2)) });
  const session = await openSession(spec);
  const N = session.loop.frames;
  const failures: string[] = [];
  try {
    console.log(`gpu: ${session.gpu}; ${N} frames`);
    const f0 = await session.capture(0);

    // Two probe frames inside each zone: one at 30% and one at 70% of the zone, off the beat grid.
    const slots = layoutTrack(session.loop);
    const framesPerBeat = N / session.loop.beats;
    const probes: { zone: string; frame: number }[] = [{ zone: "start", frame: 0 }];
    for (const zone of ZONES) {
      const own = slots.filter((s) => s.zone === zone);
      for (const at of [0.3, 0.7]) {
        const beat = own[0]!.index + own.length * at + 0.37;
        probes.push({ zone, frame: Math.round(beat * framesPerBeat) });
      }
    }
    for (const p of probes) {
      const a = await session.capture(p.frame);
      const b = await session.capture(p.frame + N);
      const d = diff(a, b);
      console.log(`closure  ${p.zone.padEnd(6)} frame ${String(p.frame).padStart(4)} vs ${p.frame + N}: mean ${d.mean.toFixed(4)} max ${d.max}`);
      // The scene uses a floating origin, so one lap later the geometry is the same to the bit.
      // Allow one level of rounding. A loose threshold here once hid a panel pattern that changed every lap.
      if (d.max > 1) failures.push(`${p.zone}: frame ${p.frame + N} differs from frame ${p.frame} (mean ${d.mean.toFixed(4)}, max ${d.max})`);
    }

    const again = diff(f0, await session.capture(0));
    console.log(`determinism  frame 0 again after ${probes.length * 2} other frames: max ${again.max}`);
    if (again.max !== 0) failures.push("frame 0 is not deterministic");

    const seam = diff(await session.capture(N - 1), f0);
    console.log(`seam step    ${N - 1} -> 0: mean ${seam.mean.toFixed(3)}`);
    if (seam.max === 0) failures.push("the last frame equals the first, so the loop point would stutter");
  } finally {
    await session.close();
  }
  for (const f of failures) console.error(`FAIL: ${f}`);
  if (failures.length) process.exit(1);
  console.log("PASS");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
