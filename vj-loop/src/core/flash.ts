// Pure flash and black-level analysis of a sequence of frames.
// This follows the shape of broadcast photosensitivity guidance (ITU-R BT.1702, the "Harding test"):
// a flash is a pair of opposing luminance changes of at least 0.1 (relative luminance) over at least a
// quarter of the screen, and more than three flashes in any one second is a failure.
// It is an estimate for catching regressions. It is not a certified test.

export interface FrameLuma {
  /** Relative luminance per pixel, 0..1. */
  luma: Float32Array;
}

export interface FlashReport {
  transitions: number;
  /** The largest number of flashes (transition pairs) inside any one-second window. */
  worstFlashesPerSecond: number;
  worstWindowStart: number;
  /** Share of one-second windows with more than three flashes. */
  windowsOverLimit: number;
  meanLuma: number;
  /** Share of all pixels that are effectively black (relative luminance below 0.002, about 8-bit level 4). */
  blackShare: number;
  /** The largest mean luminance of any frame. */
  peakFrameLuma: number;
}

const SRGB_TO_LINEAR = new Float32Array(256);
for (let i = 0; i < 256; i++) {
  const c = i / 255;
  SRGB_TO_LINEAR[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

/** Relative luminance (Rec. 709 weights) from 8-bit sRGB RGBA bytes. */
export function lumaFromRgba(rgba: Uint8Array): Float32Array {
  const out = new Float32Array(rgba.length / 4);
  for (let i = 0, p = 0; i < rgba.length; i += 4, p++) {
    out[p] = 0.2126 * SRGB_TO_LINEAR[rgba[i]!]! + 0.7152 * SRGB_TO_LINEAR[rgba[i + 1]!]! + 0.0722 * SRGB_TO_LINEAR[rgba[i + 2]!]!;
  }
  return out;
}

/**
 * +1 if at least `area` of the pixels rose by more than `delta`, -1 if that many fell, else 0.
 */
export function transitionSign(prev: Float32Array, next: Float32Array, delta = 0.1, area = 0.25): -1 | 0 | 1 {
  let up = 0;
  let down = 0;
  for (let i = 0; i < prev.length; i++) {
    const d = next[i]! - prev[i]!;
    if (d > delta) up++;
    else if (d < -delta) down++;
  }
  if (up >= area * prev.length) return 1;
  if (down >= area * prev.length) return -1;
  return 0;
}

/** Analyse a looping sequence. The step from the last frame back to the first counts, and windows wrap. */
export function analyseFlashes(frames: Float32Array[], fps: number): FlashReport {
  const n = frames.length;
  const signs: number[] = [];
  let lumaSum = 0;
  let black = 0;
  let pixels = 0;
  let peak = 0;
  for (let f = 0; f < n; f++) {
    const cur = frames[f]!;
    signs.push(transitionSign(cur, frames[(f + 1) % n]!));
    let s = 0;
    for (let i = 0; i < cur.length; i++) {
      s += cur[i]!;
      if (cur[i]! < 0.002) black++;
    }
    pixels += cur.length;
    lumaSum += s;
    peak = Math.max(peak, s / cur.length);
  }
  // Count opposing pairs inside each one-second window.
  let worst = 0;
  let worstStart = 0;
  let over = 0;
  for (let start = 0; start < n; start++) {
    let last = 0;
    let changes = 0;
    for (let k = 0; k < fps; k++) {
      const s = signs[(start + k) % n]!;
      if (s !== 0 && s !== last) {
        changes++;
        last = s;
      }
    }
    const flashes = changes / 2;
    if (flashes > worst) {
      worst = flashes;
      worstStart = start;
    }
    if (flashes > 3) over++;
  }
  return {
    transitions: signs.filter((s) => s !== 0).length,
    worstFlashesPerSecond: worst,
    worstWindowStart: worstStart,
    windowsOverLimit: over / n,
    meanLuma: lumaSum / pixels,
    blackShare: black / pixels,
    peakFrameLuma: peak,
  };
}
