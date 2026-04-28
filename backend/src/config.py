from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TRANSITIONS_DIR = DATA_DIR / "transitions"
RAW_DATA_DIR = DATA_DIR / "raw"

# Chord vocabulary
N_CHORD_TYPES = 148
N_ROOTS = 12
# 148 CSV chord types + 7 basic triads (maj/min/dim/aug/sus2/sus4/no3d) × 12 roots
CHORD_VOCAB_SIZE = (N_CHORD_TYPES + 7) * N_ROOTS  # 1860

# Recommendation engine
CONTEXT_WINDOW = 16
DECAY_LAMBDA = 0.85
TOP_K = 5
ALPHA = 0.85  # main factor weight (chord transition) vs root motion

# Augmentation
AUG_SIGMA = 3.85  # transposition weight: 1.0 at shift=0, ~0.30 at shift=6
AUG_EPSILON = 0.001  # floor weight to prevent zero probabilities

# Style matching weights
GENRE_TAG_WEIGHT = 0.60
DECADE_WEIGHT = 0.20
MAIN_GENRE_WEIGHT = 0.20

# MIDI
DEFAULT_BASE_OCTAVE = 3  # C3 = MIDI 48
PIANO_OCTAVES = 3

# SQLite
SESSION_DB_PATH = DATA_DIR / "sessions.db"

# Chordonomicon sources
CHORD_MAPPING_URL = (
    "https://raw.githubusercontent.com/"
    "spyroskantarelis/chordonomicon/main/chords_mapping.csv"
)
HF_DATASET_NAME = "ailsntua/Chordonomicon"

# Ensure directories exist
for d in [DATA_DIR, TRANSITIONS_DIR, RAW_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)
