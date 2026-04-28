/** MIDI note utilities. */

// Pitch class (C=0) to note name
const PITCH_CLASS_TO_NAME = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B'];

// Note name to MIDI number: C0=12, C3=48, C4=60
export function noteToMidi(noteName: string, octave: number = 4): number {
  // Parse: root (1-2 chars) + optional quality (ignored for root)
  const root = noteName.length >= 2 && PITCH_CLASS_TO_NAME.includes(noteName.slice(0, 2))
    ? noteName.slice(0, 2)
    : noteName.slice(0, 1);

  const pc = PITCH_CLASS_TO_NAME.indexOf(root);
  if (pc === -1) {
    throw new Error(`Unknown note: ${noteName}`);
  }
  return 12 + octave * 12 + pc;
}

/** Convert chord semitone intervals to MIDI notes at a given octave. */
export function intervalsToMidi(rootPc: number, intervals: number[], octave: number = 4): number[] {
  const base = 12 + octave * 12 + rootPc;
  return intervals.map((i) => base + i);
}

/** Get MIDI note numbers for white keys only across multiple octaves. */
export function whiteKeysInRange(startOctave: number, endOctave: number): number[] {
  const result: number[] = [];
  for (let oct = startOctave; oct <= endOctave; oct++) {
    // White key pitch classes: C(0), D(2), E(4), F(5), G(7), A(9), B(11)
    for (const pc of [0, 2, 4, 5, 7, 9, 11]) {
      result.push(12 + oct * 12 + pc);
    }
  }
  return result;
}

/** Determine if a MIDI note corresponds to a black key. */
export function isBlackKey(midiNote: number): boolean {
  const pc = midiNote % 12;
  return [1, 3, 6, 8, 10].includes(pc);
}

/** Get the pitch class name for a MIDI note. */
export function midiToNoteName(midiNote: number): string {
  const pc = midiNote % 12;
  const octave = Math.floor(midiNote / 12) - 1;
  return `${PITCH_CLASS_TO_NAME[pc]}${octave}`;
}

export { PITCH_CLASS_TO_NAME };
