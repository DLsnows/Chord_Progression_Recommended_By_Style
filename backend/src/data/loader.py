"""Chord mapping data loader.

Parses chordonomicon's chords_mapping.csv into a lookup of ChordInfo objects.
Also handles loading the HuggingFace dataset.
"""

import ast
from pathlib import Path

import pandas as pd

from ..config import CHORD_MAPPING_URL, HF_DATASET_NAME, RAW_DATA_DIR, N_CHORD_TYPES
from ..models.chord import ChordInfo, PITCH_CLASS_TO_NAME, NAME_TO_PITCH_CLASS

# Root name patterns in chords_mapping.csv: C, Cs, Db, D, Ds, Eb, E, F, Fs, Gb, G, Gs, Ab, A, As, Bb, B
# The file uses s=sharp, b=flat notation
ROOT_ALIASES: dict[str, int] = {
    "C": 0, "Cs": 1, "Db": 1, "D": 2, "Ds": 3, "Eb": 3,
    "E": 4, "F": 5, "Fs": 6, "Gb": 6, "G": 7, "Gs": 8,
    "Ab": 8, "A": 9, "As": 10, "Bb": 10, "B": 11,
}

# Solfege to pitch-class mapping
SOLFEGE_MAP: dict[str, int] = {
    "do": 0, "dos": 1, "re": 2, "res": 3, "mi": 4,
    "fa": 5, "fas": 6, "sol": 7, "sols": 8, "la": 9,
    "las": 10, "si": 11, "s": 11,
}


def _parse_root_and_quality(chord_name: str) -> tuple[int, str]:
    """Parse chord name into root pitch-class and quality string."""
    chord_name = chord_name.strip()
    # Try two-character roots first (Cs, Db, Ds, Eb, Fs, Gb, Gs, Ab, As, Bb)
    if len(chord_name) >= 2 and chord_name[:2] in ROOT_ALIASES:
        root_pc = ROOT_ALIASES[chord_name[:2]]
        quality = chord_name[2:]
    elif chord_name[:1] in ROOT_ALIASES:
        root_pc = ROOT_ALIASES[chord_name[:1]]
        quality = chord_name[1:]
    else:
        raise ValueError(f"Cannot parse chord: {chord_name}")
    return root_pc, quality


def _solfege_to_pitch_class(note: str, root_pc: int) -> int:
    """Convert a solfege note name (with 's' suffix for sharp) to absolute pitch class."""
    # Remove trailing 's' handling
    note = note.strip().lower()
    if note in SOLFEGE_MAP:
        pc = SOLFEGE_MAP[note]
    elif note + "s" in SOLFEGE_MAP:
        # Handle alternate spellings
        pc = SOLFEGE_MAP[note + "s"]
    else:
        raise ValueError(f"Unknown solfege note: {note}")
    # The solfege notes are relative to the root (do=root)
    return (root_pc + pc) % 12


def _compute_semitone_intervals(binary_vector: list[int]) -> list[int]:
    """Convert a 12-element binary vector to a list of semitone intervals from root."""
    intervals = []
    for i, present in enumerate(binary_vector):
        if present:
            intervals.append(i)
    return intervals


def load_chord_mapping(csv_path: str | Path | None = None) -> dict[str, ChordInfo]:
    """Parse chords_mapping.csv into a dict of chord_name -> ChordInfo.

    The CSV contains chords for all 12 roots, organized in blocks of N_CHORD_TYPES=148
    chord qualities per root. The first 148 rows are C-rooted, then C#, D, etc.
    """
    if csv_path is None:
        csv_path = RAW_DATA_DIR / "chords_mapping.csv"

    df = pd.read_csv(csv_path)
    # Columns: (unnamed index), Chords, Notes, Degrees

    # Extract the C-rooted chord quality names from first N_CHORD_TYPES rows
    c_rooted = df.iloc[:N_CHORD_TYPES]
    base_qualities: list[str] = []
    for _, row in c_rooted.iterrows():
        _, quality = _parse_root_and_quality(row["Chords"])
        base_qualities.append(quality)

    # Parse notes and degrees from C-rooted chords (used as reference)
    c_notes_list: list[list[str]] = []
    c_degrees_list: list[list[int]] = []
    for _, row in c_rooted.iterrows():
        notes = ast.literal_eval(row["Notes"])
        degrees = ast.literal_eval(row["Degrees"])
        c_notes_list.append(notes)
        c_degrees_list.append(degrees)

    # Build chord lookup for all 12 roots
    chords: dict[str, ChordInfo] = {}
    for root_pc in range(12):
        root_name = PITCH_CLASS_TO_NAME[root_pc]
        for qual_idx, quality in enumerate(base_qualities):
            chord_name = f"{root_name}{quality}"

            # Translate solfege notes to absolute pitch classes
            c_notes = c_notes_list[qual_idx]
            translated_notes: list[str] = []
            for solf in c_notes:
                try:
                    abs_pc = _solfege_to_pitch_class(solf, root_pc)
                    translated_notes.append(PITCH_CLASS_TO_NAME[abs_pc])
                except ValueError:
                    translated_notes.append(solf)  # keep as-is if unknown

            # Rotate binary vector by root_pc
            c_degrees = c_degrees_list[qual_idx]
            rotated_vector = [0] * 12
            for i, val in enumerate(c_degrees):
                if val:
                    rotated_vector[(i + root_pc) % 12] = 1

            intervals = _compute_semitone_intervals(rotated_vector)

            chords[chord_name] = ChordInfo(
                name=chord_name,
                root_pc=root_pc,
                quality=quality,
                notes_solfege=translated_notes,
                binary_vector=rotated_vector,
                semitone_intervals=intervals,
            )

    # Add basic triads (major, minor, diminished, augmented)
    # These are not in chords_mapping.csv which only contains 7th+ chords
    _add_basic_triads(chords)

    return chords


# Basic triad definitions: (quality_name, semitone_intervals_from_root)
BASIC_TRIADS: list[tuple[str, list[int]]] = [
    ("", [0, 4, 7]),       # major triad: e.g. "C"
    ("min", [0, 3, 7]),    # minor triad: e.g. "Cmin"
    ("dim", [0, 3, 6]),    # diminished triad: e.g. "Cdim"
    ("aug", [0, 4, 8]),    # augmented triad: e.g. "Caug"
    ("sus2", [0, 2, 7]),   # suspended 2nd triad: e.g. "Csus2"
    ("sus4", [0, 5, 7]),   # suspended 4th triad: e.g. "Csus4"
    ("no3d", [0, 7]),      # power chord (no 3rd): e.g. "Cno3d"
]


def _add_basic_triads(chords: dict[str, "ChordInfo"]) -> None:
    """Add basic triad definitions to the chord vocabulary.

    chords_mapping.csv only contains extended chords (7th and beyond),
    but the dataset uses basic triads extensively (e.g. "C", "Amin").
    """
    for root_pc in range(12):
        root_name = PITCH_CLASS_TO_NAME[root_pc]
        for quality, intervals in BASIC_TRIADS:
            name = f"{root_name}{quality}"
            if name in chords:
                continue  # already exists (unlikely but safe)
            binary = [0] * 12
            notes = []
            for interval in intervals:
                pc = (root_pc + interval) % 12
                binary[pc] = 1
                notes.append(PITCH_CLASS_TO_NAME[pc])
            chords[name] = ChordInfo(
                name=name,
                root_pc=root_pc,
                quality=quality if quality else "maj",
                notes_solfege=notes,
                binary_vector=binary,
                semitone_intervals=list(intervals),
            )


def download_chord_mapping() -> Path:
    """Download chords_mapping.csv from GitHub if not already present."""
    import urllib.request

    dest = RAW_DATA_DIR / "chords_mapping.csv"
    if dest.exists():
        return dest

    print(f"Downloading {CHORD_MAPPING_URL} ...")
    urllib.request.urlretrieve(CHORD_MAPPING_URL, dest)
    print(f"Saved to {dest}")
    return dest


def load_dataset() -> pd.DataFrame:
    """Load the HuggingFace chordonomicon dataset as a pandas DataFrame.

    Returns the full dataset with columns including:
    main_genre, genres, decade, chords (the progression string), etc.
    """
    from datasets import load_dataset as hf_load

    print(f"Loading dataset {HF_DATASET_NAME} ...")
    ds = hf_load(HF_DATASET_NAME, split="train")
    df = ds.to_pandas()
    print(f"Loaded {len(df)} rows")
    return df


def load_chord_vocabulary(csv_path: str | Path | None = None) -> tuple[dict[str, ChordInfo], list[str]]:
    """Load chord mapping and return (name->ChordInfo dict, sorted name list for indexing)."""
    chord_map = load_chord_mapping(csv_path)
    chord_names = sorted(chord_map.keys())
    return chord_map, chord_names
