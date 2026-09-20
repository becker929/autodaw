// Render the whole loop small and measure flashing and black level. See src/core/flash.ts.
//   tsx scripts/flashcheck.ts            measure and enforce the limits
//   tsx scripts/flashcheck.ts --report   measure only
import { PNG } from "pngjs";
import { analyseFlashes, lumaFromRgba } from "../src/core/flash";
import { parseFlags, splitFlags } from "./flags";
import { openSession } from "./session";

async function main(): Promise<void> {
  const { spec, rest } = splitFlags({ width: 320, height: 180, subframes: 2, ...parseFlags(process.argv.slice(2)) });
  const session = await openSession(spec);
  const frames: Float32Array[] = [];
  try {
    const n = session.loop.frames;
    for (let f = 0; f < n; f++) {
      frames.push(lumaFromRgba(PNG.sync.read(await session.capture(f)).data));
      if ((f + 1) % 300 === 0) console.log(`measured ${f + 1}/${n}`);
    }
  } finally {
    await session.close();
  }
  const r = analyseFlashes(frames, spec.fps);
  console.log(JSON.stringify(r, null, 2));
  if (rest.report) return;
  const failures: string[] = [];
  if (r.worstFlashesPerSecond > 3) failures.push(`${r.worstFlashesPerSecond} flashes in the second starting at frame ${r.worstWindowStart}; the limit is 3`);
  if (r.blackShare < 0.15) failures.push(`only ${(r.blackShare * 100).toFixed(1)}% of pixels are black; an LED wall needs real black, at least 15%`);
  for (const f of failures) console.error(`FAIL: ${f}`);
  if (failures.length) process.exit(1);
  console.log("PASS");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
