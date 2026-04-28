/** SVG piano key geometry calculations.

 * Layout: 3 octaves (C3–B5), 7 white keys + 5 black keys per octave.
 * White keys: 24px wide × 120px tall (full-size) or scaled for thumbnails.
 * Black keys: 14px wide × 72px tall, overlapping white key gaps.
 */

// Per-octave key layout (offsets within one octave in px)
// White key positions: C=0, D=1, E=2, F=3, G=4, A=5, B=6
const WHITE_KEY_PITCHES = [0, 2, 4, 5, 7, 9, 11]; // pitch classes
const BLACK_KEY_PITCHES = [1, 3, 6, 8, 10];        // pitch classes

export interface KeyGeometry {
  midiNote: number;
  x: number;
  y: number;
  width: number;
  height: number;
  isBlack: boolean;
  pitchClass: number;
  octave: number;
}

export interface PianoLayout {
  keys: KeyGeometry[];
  totalWidth: number;
  totalHeight: number;
}

const DEFAULT_WHITE_W = 24;
const DEFAULT_WHITE_H = 120;
const DEFAULT_BLACK_W = 14;
const DEFAULT_BLACK_H = 72;

/** Black key x-offsets relative to the start of their octave (in white-key units). */
function blackKeyOffsets(whiteW: number): Record<number, number> {
  return {
    1: whiteW - DEFAULT_BLACK_W / 2,        // Cs — between C and D
    3: whiteW * 2 - DEFAULT_BLACK_W / 2,    // Ds — between D and E
    6: whiteW * 4 - DEFAULT_BLACK_W / 2,    // Fs — between F and G
    8: whiteW * 5 - DEFAULT_BLACK_W / 2,    // Gs — between G and A
    10: whiteW * 6 - DEFAULT_BLACK_W / 2,   // As — between A and B
  };
}

/**
 * Compute key geometry for a range of octaves.
 *
 * @param startOctave First octave (e.g., 3 for C3)
 * @param numOctaves  Number of octaves
 * @param scale       Uniform scale factor (1.0 = full size)
 */
export function computePianoLayout(
  startOctave: number = 3,
  numOctaves: number = 3,
  scale: number = 1.0
): PianoLayout {
  const whiteW = DEFAULT_WHITE_W * scale;
  const whiteH = DEFAULT_WHITE_H * scale;
  const blackW = DEFAULT_BLACK_W * scale;
  const blackH = DEFAULT_BLACK_H * scale;

  const keys: KeyGeometry[] = [];
  const whitesPerOctave = 7;
  const offsets = blackKeyOffsets(whiteW);

  for (let octIdx = 0; octIdx < numOctaves; octIdx++) {
    const octave = startOctave + octIdx;
    const octaveStartX = octIdx * whitesPerOctave * whiteW;

    // White keys
    for (let wi = 0; wi < WHITE_KEY_PITCHES.length; wi++) {
      const pc = WHITE_KEY_PITCHES[wi];
      keys.push({
        midiNote: 12 + octave * 12 + pc,
        x: octaveStartX + wi * whiteW,
        y: 0,
        width: whiteW,
        height: whiteH,
        isBlack: false,
        pitchClass: pc,
        octave,
      });
    }

    // Black keys (drawn after white to sit on top)
    for (const pc of BLACK_KEY_PITCHES) {
      const offset = offsets[pc];
      keys.push({
        midiNote: 12 + octave * 12 + pc,
        x: octaveStartX + offset,
        y: 0,
        width: blackW,
        height: blackH,
        isBlack: true,
        pitchClass: pc,
        octave,
      });
    }
  }

  return {
    keys,
    totalWidth: numOctaves * whitesPerOctave * whiteW,
    totalHeight: whiteH,
  };
}

/** Active note highlight colors. */
export const NOTE_COLORS = {
  root: '#4ade80',
  active: '#22c55e',
  blackKeyDefault: '#0a0a0a',
  blackKeyActive: '#4ade80',
  whiteKeyDefault: '#f0f0f0',
  whiteKeyActive: '#22c55e',
  whiteKeyRoot: '#4ade80',
  border: '#333',
} as const;
