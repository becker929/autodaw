// Render the loop to a video file, or render single frames to PNG.
//
//   tsx scripts/render.ts                       full UHD render to out/factory-loop.mp4
//   tsx scripts/render.ts --still 0,450,900     PNG stills of those frames
//   tsx scripts/render.ts --width 1280 --height 720 --subframes 2 --out out/preview.mp4
//   tsx scripts/render.ts --from 0 --to 120     part of the loop
import { spawn } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs";
import path from "node:path";
import { z } from "zod";
import { openSession, parseFlags, ROOT, splitFlags } from "./session";

const RenderFlags = z
  .object({
    still: z.union([z.number(), z.string()]).optional(),
    out: z.string().optional(),
    from: z.number().int().min(0).default(0),
    to: z.number().int().positive().optional(),
    codec: z.enum(["h264", "hevc", "prores"]).default("h264"),
    crf: z.number().min(0).max(40).default(14),
  })
  .strict();

function encoderArgs(codec: "h264" | "hevc" | "prores", crf: number): string[] {
  switch (codec) {
    case "h264":
      return ["-c:v", "libx264", "-preset", "slow", "-crf", String(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"];
    case "hevc":
      return ["-c:v", "libx265", "-preset", "slow", "-crf", String(crf), "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1"];
    case "prores":
      return ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"];
  }
}

async function main(): Promise<void> {
  const { spec, rest } = splitFlags(parseFlags(process.argv.slice(2)));
  const flags = RenderFlags.parse(rest);
  const outDir = path.join(ROOT, "out");
  fs.mkdirSync(outDir, { recursive: true });

  const session = await openSession(spec);
  const { loop } = session;
  console.log(`loop: ${loop.beats} beats, ${loop.seconds}s, ${loop.frames} frames at ${spec.width}x${spec.height}`);
  console.log(`gpu: ${session.gpu}`);
  if (/swiftshader|llvmpipe/i.test(session.gpu)) console.warn("WARNING: software rendering. This will be slow.");

  try {
    if (flags.still !== undefined) {
      for (const f of String(flags.still).split(",").map(Number)) {
        const file = flags.out && !String(flags.still).includes(",") ? flags.out : path.join(outDir, `still-${String(f).padStart(5, "0")}.png`);
        const t0 = Date.now();
        fs.writeFileSync(file, await session.capture(f));
        console.log(`${file} (${Date.now() - t0} ms)`);
      }
      return;
    }

    const to = flags.to ?? loop.frames;
    const ext = flags.codec === "prores" ? "mov" : "mp4";
    const file = flags.out ?? path.join(outDir, `factory-loop.${ext}`);
    // Encode to a partial file and rename at the end, so a failed render never leaves a file that looks finished.
    const partial = path.join(path.dirname(file), `.partial-${path.basename(file)}`);
    const ff = spawn(
      "ffmpeg",
      ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "png", "-i", "-",
        ...encoderArgs(flags.codec, flags.crf), "-r", String(spec.fps), "-f", ext === "mov" ? "mov" : "mp4", partial],
      { stdio: ["pipe", "inherit", "inherit"] },
    );
    const ffExit = once(ff, "exit");
    const t0 = Date.now();
    for (let f = flags.from; f < to; f++) {
      const png = await session.capture(f);
      if (!ff.stdin.write(png)) await once(ff.stdin, "drain");
      const done = f - flags.from + 1;
      if (done % 30 === 0 || f === to - 1) {
        const per = (Date.now() - t0) / done;
        console.log(`frame ${f + 1}/${to}  ${per.toFixed(0)} ms/frame  eta ${(((to - f - 1) * per) / 60000).toFixed(1)} min`);
      }
    }
    ff.stdin.end();
    const [code] = await ffExit;
    if (code !== 0) throw new Error(`ffmpeg exited with code ${code}`);
    fs.renameSync(partial, file);
    console.log(`wrote ${file}`);
  } finally {
    await session.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
