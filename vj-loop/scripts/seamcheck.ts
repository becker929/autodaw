// Black-box check of the rendered loop. It looks only at pixels.
//   1. Determinism: the same frame renders to the same pixels, whatever was rendered in between.
//   2. Closure: frame N (one full lap) equals frame 0.
//   3. Continuity: the step across the seam (last frame -> frame 0) is no bigger than ordinary steps.
import { PNG } from "pngjs";
import { openSession, parseFlags, splitFlags } from "./session";

function meanAbsDiff(a: Buffer, b: Buffer): { mean: number; max: number } {
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
    const f1 = await session.capture(1);
    const fMid = await session.capture(Math.floor(N / 2));
    const fMid1 = await session.capture(Math.floor(N / 2) + 1);
    const fLast2 = await session.capture(N - 2);
    const fLast = await session.capture(N - 1);
    const fN = await session.capture(N);
    const f0again = await session.capture(0);

    const det = meanAbsDiff(f0, f0again);
    console.log(`determinism   frame 0 vs frame 0 again: mean ${det.mean.toFixed(4)} max ${det.max}`);
    if (det.max !== 0) failures.push("frame 0 is not deterministic");

    const close = meanAbsDiff(f0, fN);
    console.log(`closure       frame 0 vs frame ${N}:      mean ${close.mean.toFixed(4)} max ${close.max}`);
    // Phase 1.0 and phase 0.0 go through different floating point paths, so allow a few levels on a few pixels.
    if (close.mean > 0.05) failures.push(`frame ${N} differs from frame 0 (mean ${close.mean})`);

    // Frame 0 is a bar downbeat: lights flash and the lens kicks. So the fair comparison for the seam step
    // is the same musical event elsewhere in the loop, not an ordinary frame step.
    const framesPerBar = (N / session.loop.beats) * spec.beatsPerBar;
    if (!Number.isInteger(framesPerBar)) throw new Error("bar length is not a whole number of frames");
    const downbeatSteps: number[] = [];
    for (const bar of [1, Math.floor(spec.bars / 2), spec.bars - 1]) {
      const f = bar * framesPerBar;
      const step = meanAbsDiff(await session.capture(f - 1), await session.capture(f)).mean;
      console.log(`downbeat step ${f - 1} -> ${f}: mean ${step.toFixed(3)}`);
      downbeatSteps.push(step);
    }
    console.log(`plain step    0 -> 1: mean ${meanAbsDiff(f0, f1).mean.toFixed(3)}`);
    console.log(`plain step    mid -> mid+1: mean ${meanAbsDiff(fMid, fMid1).mean.toFixed(3)}`);
    console.log(`plain step    N-2 -> N-1: mean ${meanAbsDiff(fLast2, fLast).mean.toFixed(3)}`);
    const seam = meanAbsDiff(fLast, f0).mean;
    console.log(`seam          N-1 -> 0: mean ${seam.toFixed(3)}`);
    const worst = Math.max(...downbeatSteps);
    if (seam > worst * 1.5) failures.push(`seam step ${seam.toFixed(3)} is more than 1.5x the largest downbeat step ${worst.toFixed(3)}`);
    if (seam === 0) failures.push("seam step is zero: the last frame duplicates the first, which would stutter");
  } finally {
    await session.close();
  }
  if (failures.length) {
    for (const f of failures) console.error(`FAIL: ${f}`);
    process.exit(1);
  }
  console.log("PASS");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
