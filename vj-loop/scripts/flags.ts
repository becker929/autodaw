// Pure command-line parsing for the render tools. No I/O here, so it is unit tested.
import path from "node:path";
import { z } from "zod";
import { LoopSpec } from "../src/core/timeline";

export type RawFlags = Record<string, string | number | boolean>;

export class UsageError extends Error {}

/** Turn `--key value` pairs into an object. Whole and decimal numbers become numbers. */
export function parseFlags(argv: string[]): RawFlags {
  const out: RawFlags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (!a.startsWith("--") || a.length < 3) throw new UsageError(`Unexpected argument: ${a}`);
    const next = argv[i + 1];
    // A value may start with "-" when it is a negative number. Only "--" starts the next flag.
    if (next === undefined || next.startsWith("--")) {
      out[a.slice(2)] = true;
    } else {
      out[a.slice(2)] = /^-?\d+(\.\d+)?$/.test(next) ? Number(next) : next;
      i++;
    }
  }
  return out;
}

const SPEC_KEYS = Object.keys(LoopSpec.shape);

function explain(what: string, err: z.ZodError): UsageError {
  const lines = err.issues.map((i) =>
    i.code === "unrecognized_keys"
      ? `  unknown flag: ${i.keys.map((k) => `--${k}`).join(", ")}`
      : `  --${i.path.join(".")}: ${i.message}`,
  );
  return new UsageError(`Bad ${what}:\n${lines.join("\n")}`);
}

/** Split flags into the loop spec and everything else. The spec part is validated by Zod. */
export function splitFlags(flags: RawFlags): { spec: LoopSpec; rest: RawFlags } {
  const specRaw: RawFlags = {};
  const rest: RawFlags = {};
  for (const [k, v] of Object.entries(flags)) (SPEC_KEYS.includes(k) ? specRaw : rest)[k] = v;
  const parsed = LoopSpec.safeParse(specRaw);
  if (!parsed.success) throw explain("loop flags", parsed.error);
  if (parsed.data.width % 2 || parsed.data.height % 2) {
    throw new UsageError("Bad loop flags:\n  --width and --height must be even. The video encoders need that.");
  }
  return { spec: parsed.data, rest };
}

export const CODECS = { h264: "mp4", hevc: "mp4", prores: "mov" } as const;
export type Codec = keyof typeof CODECS;

const RenderFlags = z
  .object({
    still: z.union([z.number(), z.string()]).optional(),
    out: z.string().min(1).optional(),
    from: z.number().int().min(0).default(0),
    to: z.number().int().positive().optional(),
    codec: z.enum(["h264", "hevc", "prores"]).default("h264"),
    crf: z.number().min(0).max(40).default(16),
    // Frames between keyframes. 1 makes every frame a keyframe: large files, instant seeking.
    gop: z.number().int().min(1).optional(),
  })
  .strict();

export type RenderPlan =
  | { kind: "stills"; frames: number[]; out?: string }
  | { kind: "video"; from: number; to: number; codec: Codec; crf: number; gop: number; out: string };

/** Validate the render flags against the loop and resolve them into a plan. Throws UsageError. */
export function planRender(rest: RawFlags, loopFrames: number, fps: number, outDir: string): RenderPlan {
  const parsed = RenderFlags.safeParse(rest);
  if (!parsed.success) throw explain("render flags", parsed.error);
  const f = parsed.data;

  if (f.still !== undefined) {
    if (f.still === "" ) throw new UsageError("--still needs frame numbers, for example --still 0,450,900");
    const frames = String(f.still).split(",").map((s) => Number(s.trim()));
    for (const n of frames) {
      if (!Number.isInteger(n) || n < 0 || n >= loopFrames) {
        throw new UsageError(`--still ${f.still}: each frame must be a whole number from 0 to ${loopFrames - 1}`);
      }
    }
    if (f.out && frames.length > 1) throw new UsageError("--out works with one --still frame, not a list");
    return { kind: "stills", frames, out: f.out };
  }

  const to = f.to ?? loopFrames;
  if (f.from >= to) throw new UsageError(`--from ${f.from} must be below --to ${to}`);
  if (to > loopFrames) throw new UsageError(`--to ${to} is past the end of the loop (${loopFrames} frames)`);
  const ext = CODECS[f.codec];
  const out = f.out ?? path.join(outDir, `factory-loop.${ext}`);
  if (path.extname(out).toLowerCase() !== `.${ext}`) {
    throw new UsageError(`--codec ${f.codec} writes a .${ext} file, but --out is ${out}`);
  }
  return { kind: "video", from: f.from, to, codec: f.codec, crf: f.crf, gop: f.gop ?? Math.max(1, Math.round(fps / 2)), out };
}
