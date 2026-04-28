from dataclasses import dataclass, field

# Pitch-class to note name mapping (sharp notation, matching chords_mapping.csv)
PITCH_CLASS_TO_NAME = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]
NAME_TO_PITCH_CLASS = {name: i for i, name in enumerate(PITCH_CLASS_TO_NAME)}

# Standard MIDI note: C0 = 12, C3 = 48, C4 = 60
MIDI_C0 = 12


@dataclass
class ChordInfo:
    """Immutable chord definition."""

    name: str
    root_pc: int  # root pitch class 0..11 (C=0)
    quality: str  # chord quality string (e.g. "maj7", "min9")
    notes_solfege: list[str] = field(default_factory=list)
    binary_vector: list[int] = field(default_factory=list)  # 12-element pitch-class vector
    semitone_intervals: list[int] = field(default_factory=list)  # offsets from root in semitones

    @property
    def root_name(self) -> str:
        return PITCH_CLASS_TO_NAME[self.root_pc]

    def to_midi_notes(self, base_octave: int = 4) -> list[int]:
        """Convert chord to MIDI note numbers at the given octave."""
        base_midi = MIDI_C0 + base_octave * 12 + self.root_pc
        return [base_midi + interval for interval in self.semitone_intervals]

    def to_midi_notes_multi_octave(
        self, start_octave: int = 3, num_octaves: int = 3
    ) -> dict[str, list[int]]:
        """Return MIDI notes grouped by octave range for piano roll display."""
        result = {}
        for octave in range(start_octave, start_octave + num_octaves):
            key = f"C{octave}-B{octave}"
            result[key] = self.to_midi_notes(octave)
        return result
