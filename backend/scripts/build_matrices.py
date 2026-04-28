"""One-shot script: build all transition matrices from the chordonomicon dataset.

Usage:
    python scripts/build_matrices.py
    python scripts/build_matrices.py --resume   # skip already-built groups
    python scripts/build_matrices.py --limit 10000  # test with subset
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CHORD_VOCAB_SIZE
from src.data.loader import load_chord_vocabulary, download_chord_mapping, load_dataset
from src.data.parser import parse_dataset
from src.data.transitions import build_transition_matrices


def main():
    parser_arg = argparse.ArgumentParser(description="Build chord transition matrices")
    parser_arg.add_argument("--resume", action="store_true",
                            help="Skip groups that already have parquet files")
    parser_arg.add_argument("--limit", type=int, default=None,
                            help="Limit dataset to N rows (for testing)")
    parser_arg.add_argument("--skip-augment", action="store_true",
                            help="Skip augmentation (faster, for testing)")
    args = parser_arg.parse_args()

    t0 = time.time()

    # Step 1: Load chord vocabulary
    print("=" * 60)
    print("Step 1: Loading chord vocabulary...")
    print("=" * 60)
    csv_path = download_chord_mapping()
    chord_map, chord_names = load_chord_vocabulary(csv_path)
    chord_vocab_set = set(chord_names)
    print(f"Chord vocabulary: {len(chord_names)} chords")

    # Step 2: Load dataset
    print("\n" + "=" * 60)
    print("Step 2: Loading dataset...")
    print("=" * 60)
    df = load_dataset()
    if args.limit:
        df = df.head(args.limit)
        print(f"  Limited to {len(df)} rows for testing")

    # Step 3: Parse into records
    print("\n" + "=" * 60)
    print("Step 3: Parsing dataset into records...")
    print("=" * 60)
    t_parse = time.time()
    records = parse_dataset(df, chord_vocab_set)
    print(f"Parsing took {time.time() - t_parse:.1f}s, produced {len(records)} records")

    # Step 4: Build and persist transition matrices
    print("\n" + "=" * 60)
    print("Step 4: Building transition matrices...")
    print("=" * 60)
    t_build = time.time()
    style_index = build_transition_matrices(
        records, chord_names, resume=args.resume
    )
    build_time = time.time() - t_build
    print(f"Build took {build_time:.1f}s ({build_time/60:.1f} min)")

    # Summary
    total_time = time.time() - t0
    print("\n" + "=" * 60)
    print(f"DONE in {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Chord vocabulary: {len(chord_names)} chords")
    print(f"  Records parsed: {len(records)}")
    print(f"  Transition groups built: {len(style_index)}")
    total_bigrams = sum(g["total_bigrams"] for g in style_index.values())
    print(f"  Total bigrams: {total_bigrams:,}")


if __name__ == "__main__":
    main()
