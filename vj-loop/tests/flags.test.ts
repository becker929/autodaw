import { describe, expect, it } from "vitest";
import { parseFlags, planRender, splitFlags, UsageError } from "../scripts/flags";

const plan = (argv: string[]) => {
  const { spec, rest } = splitFlags(parseFlags(argv));
  return planRender(rest, 1800, spec.fps, "/out");
};

describe("parseFlags", () => {
  it("reads numbers, strings, booleans and negative numbers", () => {
    expect(parseFlags(["--a", "1", "--b", "x.mp4", "--c", "--d", "-5", "--e", "0.5"])).toEqual({ a: 1, b: "x.mp4", c: true, d: -5, e: 0.5 });
  });
  it("rejects bare words", () => {
    expect(() => parseFlags(["render"])).toThrow(UsageError);
  });
});

describe("splitFlags", () => {
  it("rejects bad loop values with a one-line reason", () => {
    expect(() => splitFlags({ bpm: -1 })).toThrow(/--bpm/);
    expect(() => splitFlags({ width: 641 })).toThrow(/even/);
  });
});

describe("planRender", () => {
  it("plans the default video", () => {
    expect(plan([])).toEqual({ kind: "video", from: 0, to: 1800, codec: "h264", crf: 16, gop: 30, out: "/out/factory-loop.mp4" });
  });
  it("accepts frame 0 as a still", () => {
    expect(plan(["--still", "0"])).toEqual({ kind: "stills", frames: [0], out: undefined });
  });
  it.each([
    [["--still", "abc"]],
    [["--still", "-5"]],
    [["--still", "0.5"]],
    [["--still", "1800"]],
    [["--still"]],
    [["--still", "0,1", "--out", "x.png"]],
    [["--from", "10", "--to", "5"]],
    [["--from", "1795", "--to", "1805"]],
    [["--codec", "prores", "--out", "x.mp4"]],
    [["--codec", "h264", "--out", "x.mov"]],
    [["--bogus"]],
    [["--help"]],
    [["--gop", "0"]],
  ])("refuses %j with a UsageError", (argv) => {
    expect(() => plan(argv)).toThrow(UsageError);
  });
  it("ties the container to the codec", () => {
    expect(plan(["--codec", "prores"])).toMatchObject({ out: "/out/factory-loop.mov" });
  });
});
