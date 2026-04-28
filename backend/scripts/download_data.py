"""One-shot script: download chordonomicon data.

Usage:
    python -m backend.scripts.download_data
"""

import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.loader import download_chord_mapping, load_chord_mapping, load_dataset


def main():
    print("=== Downloading chord mapping CSV ===")
    csv_path = download_chord_mapping()

    print("\n=== Parsing chord mapping ===")
    chords = load_chord_mapping(csv_path)
    print(f"Loaded {len(chords)} chords ({len(chords)//12} types x 12 roots)")

    print("\n=== Downloading HuggingFace dataset ===")
    df = load_dataset()
    print(f"Dataset columns: {list(df.columns)}")
    print(f"Sample row:\n{df.iloc[0].to_dict()}")


if __name__ == "__main__":
    main()
