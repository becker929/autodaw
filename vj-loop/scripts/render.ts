// Render the loop to a video file, or render single frames to PNG.
//
//   tsx scripts/render.ts                       full UHD render to out/factory-loop.mp4
//   tsx scripts/render.ts --still 0,450,900     PNG stills of those frames
//   tsx scripts/render.ts --width 1280 --height 720 --subframes 4 --out out/preview.mp4
//   tsx scripts/render.ts --from 0 --to 120     part of the loop
import { spawn, spawnSync } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs";
import path from "node:path";
import { SceneLoopError, validateSceneLoop } from "../src/core/layout";
import { parseFlags, planRender, splitFlags, UsageError, type Codec } from "./flags";
import { deriveLoop } from "../src/core/timeline";
import { openSession, ROOT } from "./session";

/** Tags written onto the frames. In ffmpeg 7 frame tags win over encoder flags, and PNG input leaves them unknown. */
const TO_BT709 = (fmt: string) =>
  `scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=${fmt},setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv`;
const BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"];

function encoderArgs(codec: Codec, crf: number, gop: number): string[] {
  const keyframes = ["-g", String(gop), "-bf", gop === 1 ? "0" : "2"];
  switch (codec) {
    case "h264":
      return ["-vf", TO_BT709("yuv420p"), "-c:v", "libx264", "-preset", "slow", "-crf", String(crf), ...keyframes, ...BT709, "-movflags", "+faststart"];
    case "hevc":
      return ["-vf", TO_BT709("yuv420p10le"), "-c:v", "libx265", "-preset", "slow", "-crf", String(crf), ...keyframes, ...BT709, "-tag:v", "hvc1"];
    case "prores":
      return ["-vf", TO_BT709("yuv422p10le"), "-c:v", "prores_ks", "-profile:v", "3", ...BT709];
  }
}

async function main(): Promise<void> {
  const { spec, rest } = splitFlags(parseFlags(process.argv.slice(2)));
  const outDir = path.join(ROOT, "out");
  // The plan needs the frame count, which needs only arithmetic. Work it out before any browser starts.
  const early = deriveLoop(spec);
  validateSceneLoop(early);
  const plan = planRender(rest, early.frames, spec.fps, outDir);

  fs.mkdirSync(outDir, { recursive: true });
  if (plan.kind === "video") {
    const dir = path.dirname(plan.out);
    if (!fs.existsSync(dir)) throw new UsageError(`The folder for --out does not exist: ${dir}`);
    if (spawnSync("ffmpeg", ["-version"]).status !== 0) throw new UsageError("ffmpeg was not found on the PATH");
  }

  const session = await openSession(spec);
  const { loop } = session;
  console.log(`loop: ${loop.beats} beats, ${loop.seconds}s, ${loop.frames} frames at ${spec.width}x${spec.height}`);
  console.log(`gpu: ${session.gpu}`);
  if (/swiftshader|llvmpipe/i.test(session.gpu)) console.warn("WARNING: software rendering. This will be slow.");

  let partial: string | null = null;
  try {
    if (plan.kind === "stills") {
      for (const f of plan.frames) {
        const file = plan.out ?? path.join(outDir, `still-${String(f).padStart(5, "0")}.png`);
        const t0 = Date.now();
        fs.writeFileSync(file, await session.capture(f));
        console.log(`${file} (${Date.now() - t0} ms)`);
      }
      return;
    }

    // Encode to a partial file and rename at the end, so a failed render never leaves a file that looks
    // finished. The process id keeps two renders at once from sharing a partial file.
    partial = path.join(path.dirname(plan.out), `.partial-${process.pid}-${path.basename(plan.out)}`);
    const container = path.extname(plan.out) === ".mov" ? "mov" : "mp4";
    const ff = spawn(
      "ffmpeg",
      ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "png", "-i", "-",
        ...encoderArgs(plan.codec, plan.crf, plan.gop), "-r", String(spec.fps), "-f", container, partial],
      { stdio: ["pipe", "inherit", "inherit"] },
    );
    // If ffmpeg dies, a pending write never drains and never errors. So every wait races against its exit.
    let done = false;
    let ffError: Error | null = null;
    ff.stdin.on("error", (e) => (ffError ??= e));
    const ffGone = new Promise<never>((_, reject) => {
      ff.once("error", (e) => reject(new Error(`ffmpeg could not start: ${e.message}`)));
      ff.once("exit", (code, signal) => {
        if (!done) reject(new Error(`ffmpeg stopped early (${signal ?? `exit code ${code}`}). ${ffError?.message ?? ""}`));
      });
    });
    ffGone.catch(() => {});

    const t0 = Date.now();
    for (let f = plan.from; f < plan.to; f++) {
      const png = await Promise.race([session.capture(f), ffGone]);
      if (!ff.stdin.write(png)) await Promise.race([once(ff.stdin, "drain"), ffGone]);
      const n = f - plan.from + 1;
      if (n % 30 === 0 || f === plan.to - 1) {
        const per = (Date.now() - t0) / n;
        console.log(`frame ${f + 1}/${plan.to}  ${per.toFixed(0)} ms/frame  eta ${(((plan.to - f - 1) * per) / 60000).toFixed(1)} min`);
      }
    }
    done = true;
    const exit = once(ff, "exit");
    ff.stdin.end();
    const [code] = await exit;
    if (code !== 0) throw new Error(`ffmpeg exited with code ${code}`);
    fs.renameSync(partial, plan.out);
    partial = null;
    console.log(`wrote ${plan.out}`);
  } finally {
    if (partial && fs.existsSync(partial)) fs.rmSync(partial);
    await session.close();
  }
}

main().catch((e) => {
  // Usage mistakes get one clean message. Anything else keeps its stack trace.
  const usage = e instanceof UsageError || e instanceof SceneLoopError;
  console.error(usage ? e.message : e);
  process.exit(usage ? 2 : 1);
});
