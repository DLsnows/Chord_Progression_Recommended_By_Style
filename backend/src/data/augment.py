"""Chord transposition and augmentation utilities.

Provides chord transposition (root shift mod 12) and the weighted augmentation
pipeline using a single-peak Gaussian distance-based weight function.
"""

import numpy as np

from ..config import AUG_SIGMA, AUG_EPSILON, N_ROOTS
from ..models.chord import PITCH_CLASS_TO_NAME


def circular_distance(s1: int, s2: int, modulus: int = 12) -> int:
    """Shortest distance on a circle of `modulus` semitones."""
    d = abs(s1 - s2) % modulus
    return min(d, modulus - d)


def augmentation_weight(shift: int, sigma: float = AUG_SIGMA) -> float:
    """Compute the weight for transposition by `shift` semitones.

    Single-peak Gaussian centered at shift=0:
        w(s) = exp(-d(s)^2 / (2*sigma^2))
    where d(s) = min(s, 12-s) is the circular distance from 0.

    With sigma=3.85:
        shift=0:  1.00  (max - original key most authentic)
        shift=±1: 0.97  (nearby - dominant/subdominant keys)
        shift=±3: 0.74
        shift=±6: 0.30  (min - tritone, farthest relation)
    """
    d = circular_distance(shift, 0)
    return max(float(np.exp(-(d**2) / (2 * sigma**2))), AUG_EPSILON)


def transpose_root(base_root: int, shift: int) -> int:
    """Shift a root pitch class by `shift` semitones (mod 12)."""
    return (base_root + shift) % 12


def transpose_chord_name(chord_name: str, shift: int) -> str:
    """Transpose a chord name by `shift` semitones.

    Parses root+quality, shifts root mod 12, reconstructs name.
    Uses sharp notation matching chords_mapping conventions.

    Args:
        chord_name: Chord name in sharp notation (e.g. "Fsmaj7")
        shift: Number of semitones to transpose (0-11)

    Returns:
        Transposed chord name
    """
    if shift == 0:
        return chord_name

    # Parse root: try 2-char roots first (Cs, Ds, Fs, Gs, As)
    name = chord_name.strip()
    root_pc = None
    quality = None
    for r_len in [2, 1]:
        root_candidate = name[:r_len]
        if root_candidate in {"C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"}:
            root_map = {"C": 0, "Cs": 1, "D": 2, "Ds": 3, "E": 4, "F": 5, "Fs": 6,
                        "G": 7, "Gs": 8, "A": 9, "As": 10, "B": 11}
            root_pc = root_map[root_candidate]
            quality = name[r_len:]
            break

    if root_pc is None:
        raise ValueError(f"Cannot parse chord name: {chord_name}")

    new_root_pc = transpose_root(root_pc, shift)
    new_root = PITCH_CLASS_TO_NAME[new_root_pc]
    return f"{new_root}{quality}"


def transposed_binary_vector(binary_vector: list[int], shift: int) -> list[int]:
    """Circularly rotate a 12-element binary vector by `shift` positions."""
    shift = shift % 12
    return binary_vector[-shift:] + binary_vector[:-shift]


def augment_count_matrix(
    raw_counts: dict[tuple[int, int], int],
    vocab_size: int,
    chord_vocab: list[str],
    sigma: float = AUG_SIGMA,
) -> np.ndarray:
    """Apply transposition augmentation to a bigram count dictionary.

    For each shift s in 0..11:
      - Transpose both chords in each bigram by s
      - Weight the count by w(s)
      - Accumulate into a dense matrix

    Returns:
        Dense (vocab_size x vocab_size) numpy array of augmented counts,
        then row-normalized to conditional probabilities.
    """
    # Build index lookup for all shifted chord names
    # Pre-compute shifted indices for each chord
    chord_to_idx = {name: i for i, name in enumerate(chord_vocab)}

    # Initialize augmented matrix
    augmented = np.zeros((vocab_size, vocab_size), dtype=np.float64)

    for shift in range(12):
        w = augmentation_weight(shift, sigma)
        if w < AUG_EPSILON:
            continue

        for (from_idx, to_idx), count in raw_counts.items():
            from_name = chord_vocab[from_idx]
            to_name = chord_vocab[to_idx]

            try:
                shifted_from = transpose_chord_name(from_name, shift)
                shifted_to = transpose_chord_name(to_name, shift)
            except (ValueError, IndexError):
                continue

            new_from_idx = chord_to_idx.get(shifted_from)
            new_to_idx = chord_to_idx.get(shifted_to)

            if new_from_idx is not None and new_to_idx is not None:
                augmented[new_from_idx][new_to_idx] += w * count

    # Row-normalize to conditional probabilities
    row_sums = augmented.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0  # avoid division by zero for unseen chords
    augmented /= row_sums

    return augmented


def augment_root_matrix(
    raw_root_counts: dict[tuple[int, int], int],
    sigma: float = AUG_SIGMA,
) -> np.ndarray:
    """Augment a root-transition count matrix with transposition weights.

    Args:
        raw_root_counts: dict mapping (from_root_pc, to_root_pc) -> count

    Returns:
        (12 x 12) numpy array of augmented root transition probabilities.
    """
    augmented = np.zeros((N_ROOTS, N_ROOTS), dtype=np.float64)

    for shift in range(12):
        w = augmentation_weight(shift, sigma)
        if w < AUG_EPSILON:
            continue

        for (from_root, to_root), count in raw_root_counts.items():
            shifted_from = (from_root + shift) % 12
            shifted_to = (to_root + shift) % 12
            augmented[shifted_from][shifted_to] += w * count

    row_sums = augmented.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    augmented /= row_sums
    return augmented
