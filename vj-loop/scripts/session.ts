// Effectful shell: serves the page with Vite, opens it in headless Chromium, and returns frame captures.
import { fileURLToPath } from "node:url";
import path from "node:path";
import { chromium, type Browser, type Page } from "playwright";
import { createServer, type ViteDevServer } from "vite";
import { deriveLoop, LoopSpec, type Loop } from "../src/core/timeline";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export interface Session {
  loop: Loop;
  gpu: string;
  /** Render one output frame and return it as PNG bytes. */
  capture(frame: number): Promise<Buffer>;
  close(): Promise<void>;
}

/** Turn `--key value` pairs into an object. Numbers become numbers. */
export function parseFlags(argv: string[]): Record<string, string | number | boolean> {
  const out: Record<string, string | number | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (!a.startsWith("--")) throw new Error(`Unexpected argument: ${a}`);
    const next = argv[i + 1];
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

/** Split flags into the loop spec and everything else. The spec part is validated by Zod. */
export function splitFlags(flags: Record<string, string | number | boolean>): {
  spec: LoopSpec;
  rest: Record<string, string | number | boolean>;
} {
  const specRaw: Record<string, unknown> = {};
  const rest: Record<string, string | number | boolean> = {};
  for (const [k, v] of Object.entries(flags)) (SPEC_KEYS.includes(k) ? specRaw : rest)[k] = v;
  return { spec: LoopSpec.parse(specRaw), rest };
}

export async function openSession(spec: LoopSpec): Promise<Session> {
  const loop = deriveLoop(spec);
  let server: ViteDevServer | null = null;
  let browser: Browser | null = null;
  try {
    // No file watching and no hot reload. A long render must not restart because someone saved a file.
    server = await createServer({
      root: ROOT,
      logLevel: "warn",
      server: { port: 0, host: "127.0.0.1", hmr: false, watch: null },
    });
    await server.listen();
    const addr = server.httpServer?.address();
    if (!addr || typeof addr === "string") throw new Error("Vite did not report a port");

    browser = await chromium.launch({
      // Full Chromium in new headless mode. It can reach the real GPU; the headless shell cannot.
      channel: "chromium",
      headless: true,
      // Metal on macOS. Elsewhere Chromium picks its own backend, or falls back to software rendering.
      args: [
        ...(process.platform === "darwin" ? ["--use-angle=metal"] : []),
        "--enable-gpu",
        "--ignore-gpu-blocklist",
        "--enable-unsafe-swiftshader",
      ],
    });
    const page: Page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    page.on("console", (m) => {
      if (m.type() === "error" || m.type() === "warning") console.error(`[page ${m.type()}] ${m.text()}`);
    });
    page.on("pageerror", (e) => console.error(`[page error] ${e.message}`));
    await page.goto(`http://127.0.0.1:${addr.port}/`);
    page.on("framenavigated", () => {
      throw new Error("The render page navigated or reloaded. The scene state is gone, so the render is invalid.");
    });
    await page.waitForFunction(() => typeof window.__vj !== "undefined");
    const info = await page.evaluate((s) => window.__vj.init(s), spec);
    if (info.frames !== loop.frames) throw new Error(`Page reports ${info.frames} frames, script expects ${loop.frames}`);

    const srv = server;
    const br = browser;
    return {
      loop,
      gpu: info.gpu,
      async capture(frame) {
        const url = await page.evaluate((f) => window.__vj.capture(f), frame);
        return Buffer.from(url.slice(url.indexOf(",") + 1), "base64");
      },
      async close() {
        await br.close();
        await srv.close();
      },
    };
  } catch (e) {
    await browser?.close();
    await server?.close();
    throw e;
  }
}
