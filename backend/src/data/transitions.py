"""Transition matrix builder and persistence.

Builds transition probability matrices from parsed bigram counts,
applies augmentation, and saves results as parquet files.
"""

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz

from ..config import TRANSITIONS_DIR, DATA_DIR, N_CHORD_TYPES, N_ROOTS, CHORD_VOCAB_SIZE
from .augment import augment_count_matrix, augment_root_matrix
from .parser import ParsedRecord, count_bigrams


def build_transition_matrices(
    records: list[ParsedRecord],
    chord_vocab: list[str],
    resume: bool = False,
) -> dict:
    """Build and persist all transition matrices from parsed records.

    Args:
        records: List of (genre_tag, decade, section, chord_list) tuples
        chord_vocab: Sorted list of chord names (used for indexing)
        resume: If True, skip groups that already have parquet files

    Returns:
        style_index dict with metadata about each group
    """
    vocab_size = len(chord_vocab)
    chord_to_idx = {name: i for i, name in enumerate(chord_vocab)}

    # Pre-compute root info for each chord
    chord_root: dict[int, int] = {}  # chord_idx -> root_pc
    for name, idx in chord_to_idx.items():
        root_name = name[:2] if name[:2] in {"Cs", "Ds", "Fs", "Gs", "As"} else name[:1]
        root_map = {"C": 0, "Cs": 1, "D": 2, "Ds": 3, "E": 4, "F": 5, "Fs": 6,
                    "G": 7, "Gs": 8, "A": 9, "As": 10, "B": 11}
        chord_root[idx] = root_map[root_name]

    # Group records
    groups = count_bigrams(records, chord_to_idx)

    style_index: dict[str, dict] = {}
    group_count = 0
    skipped_count = 0

    for (genre_tag, decade, section), group_data in groups.items():
        group_count += 1
        total_bigrams = group_data["total_bigrams"]

        # Skip groups with too few samples
        if total_bigrams < 50:
            skipped_count += 1
            continue

        # Build file path
        safe_tag = genre_tag.replace("/", "_").replace(" ", "_").lower()
        safe_section = section.replace("/", "_").replace(" ", "_").lower()
        filename = f"{safe_tag}_{decade}_{safe_section}.parquet"
        filepath = TRANSITIONS_DIR / filename

        root_filename = f"root_{safe_tag}_{decade}_{safe_section}.npz"
        root_filepath = TRANSITIONS_DIR / root_filename

        if resume and filepath.exists():
            continue

        # Build sparse probability matrix
        counts = group_data["counts"]
        augmented = augment_count_matrix(counts, vocab_size, chord_vocab)

        # Build root transition matrix
        raw_root_counts: dict[tuple[int, int], int] = defaultdict(int)
        for (from_idx, to_idx), count in counts.items():
            from_root = chord_root.get(from_idx)
            to_root = chord_root.get(to_idx)
            if from_root is not None and to_root is not None:
                raw_root_counts[(from_root, to_root)] += count
        root_matrix = augment_root_matrix(raw_root_counts)

        # Convert augmented matrix to sparse CSR and save as parquet
        sparse_csr = csr_matrix(augmented)
        _save_sparse_as_parquet(sparse_csr, filepath)

        # Save root matrix as compressed numpy
        save_npz(root_filepath, csr_matrix(root_matrix))

        # Build unigram (starting chords) distribution
        starting = group_data["starting_counts"]
        total_starts = sum(starting.values())
        starting_probs = {
            chord_idx: count / total_starts
            for chord_idx, count in starting.items()
        }

        # Update style index
        key = f"{genre_tag}|{decade}|{section}"
        style_index[key] = {
            "genre_tag": genre_tag,
            "decade": decade,
            "section": section,
            "total_bigrams": total_bigrams,
            "sample_count": total_starts,
            "file": filename,
            "root_file": root_filename,
            "starting_probs": starting_probs,
        }

        if group_count % 500 == 0:
            print(f"  Processed {group_count} groups, {skipped_count} skipped...")

    # Persist style index
    index_path = DATA_DIR / "style_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(style_index, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(style_index)} groups to {index_path}")
    print(f"Skipped {skipped_count} groups (too few samples)")
    return style_index


def _save_sparse_as_parquet(sparse_csr: csr_matrix, filepath: Path) -> None:
    """Save a sparse CSR matrix as a parquet file (COO format)."""
    coo = sparse_csr.tocoo()
    df = pd.DataFrame({
        "from_idx": coo.row,
        "to_idx": coo.col,
        "probability": coo.data,
    })
    # Use column compression
    df.to_parquet(filepath, compression="zstd", index=False)


def load_transition_matrix(filepath: Path) -> csr_matrix:
    """Load a transition matrix from parquet back into sparse CSR format."""
    df = pd.read_parquet(filepath)
    max_idx = max(df["from_idx"].max(), df["to_idx"].max()) + 1
    shape = max(max_idx, CHORD_VOCAB_SIZE)
    return csr_matrix(
        (df["probability"].values, (df["from_idx"].values, df["to_idx"].values)),
        shape=(shape, shape),
    )


def load_root_matrix(filepath: Path) -> np.ndarray:
    """Load a root transition matrix from npz into dense numpy array."""
    from scipy.sparse import load_npz
    return load_npz(filepath).toarray()


def load_style_index() -> dict:
    """Load the style index from disk."""
    index_path = DATA_DIR / "style_index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Style index not found at {index_path}. Run build_matrices.py first.")
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)
