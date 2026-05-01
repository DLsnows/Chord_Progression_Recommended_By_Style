import * as Tone from 'tone';

class AudioEngine {
  synth: Tone.PolySynth | null = null;
  private _ready = false;
  onEnd: (() => void) | null = null;

  async init(): Promise<void> {
    if (this._ready) return;
    await Tone.start();
    this.synth = new Tone.PolySynth(Tone.Synth).set({
      oscillator: { type: 'triangle' as const },
      envelope: { attack: 0.02, decay: 0.15, sustain: 0.3, release: 0.6 },
    }).toDestination();
    this.synth.volume.value = -10;
    this._ready = true;
  }

  get isReady(): boolean {
    return this._ready;
  }

  playChord(midiNotes: number[], duration: string = '2n'): void {
    if (!this.synth || midiNotes.length === 0) return;
    const now = Tone.now();
    const freqs = midiNotes.map((n) => Tone.Frequency(n, 'midi').toFrequency());
    this.synth.triggerAttackRelease(freqs, duration, now);
  }

  playChordAtTime(midiNotes: number[], time: number, duration: string = '2n'): void {
    if (!this.synth || midiNotes.length === 0) return;
    const freqs = midiNotes.map((n) => Tone.Frequency(n, 'midi').toFrequency());
    this.synth.triggerAttackRelease(freqs, duration, time);
  }

  playProgression(chords: number[][], tempoBpm: number = 100): void {
    if (!this.synth) return;
    this.stop();

    Tone.Transport.bpm.value = tempoBpm;

    chords.forEach((midiNotes, i) => {
      Tone.Transport.schedule((time) => {
        const freqs = midiNotes.map((n) => Tone.Frequency(n, 'midi').toFrequency());
        this.synth!.triggerAttackRelease(freqs, '2n', time);
      }, i * 2);
    });

    Tone.Transport.schedule(() => {
      this.onEnd?.();
    }, chords.length * 2);

    Tone.Transport.start();
  }

  stop(): void {
    this.synth?.releaseAll();
    Tone.Transport.stop();
    Tone.Transport.cancel();
  }

  setVolume(db: number): void {
    if (this.synth) this.synth.volume.value = db;
  }
}

export const audioEngine = new AudioEngine();
