// Effectful shell: serves the page with Vite, opens it in headless Chromium, and returns frame captures.
import { fileURLToPath } from "node:url";
import path from "node:path";
import { chromium, type Browser, type Page } from "playwright";
import { createServer, type ViteDevServer } from "vite";
import { validateSceneLoop } from "../src/core/layout";
import { deriveLoop, type Loop, type LoopSpec } from "../src/core/timeline";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/** How many times one frame may be retried in a fresh browser before the render gives up. */
const MAX_RESTARTS_PER_FRAME = 2;

export interface Session {
  loop: Loop;
  gpu: string;
  /** Browser restarts so far. A healthy render has zero. */
  restarts(): number;
  /** Render one output frame and return it as PNG bytes. */
  capture(frame: number): Promise<Buffer>;
  close(): Promise<void>;
}

interface Tab {
  browser: Browser;
  page: Page;
  gpu: string;
  /** Set when the page reloads or navigates. The scene state is gone then, so the tab must be replaced. */
  navigated: boolean;
}

async function openTab(url: string, spec: LoopSpec, loop: Loop): Promise<Tab> {
  const browser = await chromium.launch({
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
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    page.on("console", (m) => {
      if (m.type() === "error" || m.type() === "warning") console.error(`[page ${m.type()}] ${m.text()}`);
    });
    page.on("pageerror", (e) => console.error(`[page error] ${e.message}`));
    await page.goto(url);
    const tab: Tab = { browser, page, gpu: "unknown", navigated: false };
    page.on("framenavigated", () => {
      tab.navigated = true;
    });
    await page.waitForFunction(() => typeof window.__vj !== "undefined");
    const info = await page.evaluate((s) => window.__vj.init(s), spec);
    if (info.frames !== loop.frames) throw new Error(`Page reports ${info.frames} frames, script expects ${loop.frames}`);
    tab.gpu = info.gpu;
    return tab;
  } catch (e) {
    await browser.close().catch(() => {});
    throw e;
  }
}

export async function openSession(spec: LoopSpec): Promise<Session> {
  const loop = deriveLoop(spec);
  // Fail on a loop the scene cannot animate before spending time on a browser.
  validateSceneLoop(loop);
  // No file watching and no hot reload. A long render must not restart because someone saved a file.
  const server: ViteDevServer = await createServer({
    root: ROOT,
    logLevel: "warn",
    server: { port: 0, host: "127.0.0.1", hmr: false, watch: null },
  });
  let tab: Tab;
  let url: string;
  try {
    await server.listen();
    const addr = server.httpServer?.address();
    if (!addr || typeof addr === "string") throw new Error("Vite did not report a port");
    url = `http://127.0.0.1:${addr.port}/`;
    tab = await openTab(url, spec, loop);
  } catch (e) {
    await server.close();
    throw e;
  }

  let restarts = 0;
  return {
    loop,
    gpu: tab.gpu,
    restarts: () => restarts,
    async capture(frame) {
      // A frame is a pure function of its index, and renders do not depend on order. So when the page
      // crashes, reloads, or loses its GPU context, a fresh browser gives the same pixels for the same frame.
      for (let attempt = 0; ; attempt++) {
        try {
          if (tab.navigated) throw new Error("The render page navigated or reloaded.");
          // capture() throws inside the page if the GPU context was lost. Without that check, a lost
          // context gives black frames and a render that looks successful.
          const data = await tab.page.evaluate((f) => window.__vj.capture(f), frame);
          return Buffer.from(data.slice(data.indexOf(",") + 1), "base64");
        } catch (e) {
          if (attempt >= MAX_RESTARTS_PER_FRAME) throw e;
          restarts++;
          console.warn(`WARNING: frame ${frame} failed (${String(e).split("\n")[0]}). Restarting the browser, attempt ${attempt + 1} of ${MAX_RESTARTS_PER_FRAME}.`);
          await tab.browser.close().catch(() => {});
          tab = await openTab(url, spec, loop);
        }
      }
    },
    async close() {
      await tab.browser.close().catch(() => {});
      await server.close();
    },
  };
}
