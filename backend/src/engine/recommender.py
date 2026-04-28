"""Chord recommendation engine.

Weighted n-gram model with dual-factor scoring (chord transitions + root motion),
exponential temporal decay, cold-start handling, and duplicate exclusion.
"""

import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix

from ..config import CONTEXT_WINDOW, DECAY_LAMBDA, TOP_K, ALPHA, TRANSITIONS_DIR
from ..data.transitions import load_transition_matrix, load_root_matrix
from ..models.chord import ChordInfo


def _root_pc_from_name(name: str) -> int:
    """Extract root pitch class from a chord name."""
    root_map = {"C": 0, "Cs": 1, "D": 2, "Ds": 3, "E": 4, "F": 5,
                "Fs": 6, "G": 7, "Gs": 8, "A": 9, "As": 10, "B": 11}
    root = name[:2] if name[:2] in root_map else name[:1]
    return root_map[root]


class Recommender:
    """Weighted n-gram chord recommender with dual-factor scoring."""

    def __init__(
        self,
        chord_vocab: list[str],
        chord_map: dict[str, ChordInfo],
        transitions_dir: Path = TRANSITIONS_DIR,
    ) -> None:
        self.chord_vocab = chord_vocab
        self.chord_map = chord_map
        self.transitions_dir = transitions_dir
        self.vocab_size = len(chord_vocab)
        self.chord_to_idx = {name: i for i, name in enumerate(chord_vocab)}

        # Pre-compute root pitch class per chord index
        self.idx_to_root: dict[int, int] = {}
        for name, idx in self.chord_to_idx.items():
            self.idx_to_root[idx] = _root_pc_from_name(name)

    def recommend(
        self,
        style_group: dict[str, Any],
        selected_indices: list[int],
        top_k: int = TOP_K,
        musicality: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Recommend the next chord given a style group and selected sequence.

        Args:
            style_group: Style index entry with file/root_file/starting_probs keys.
            selected_indices: Ordered list of previously selected chord indices.
            top_k: Number of candidates to return.
            musicality: 0.0=normal, 1.0=prefer non-triad chords.

        Returns:
            List of {chord_idx, chord_name, score, chord_info} dicts.
        """
        chord_matrix = load_transition_matrix(
            self.transitions_dir / style_group["file"]
        )
        root_matrix = load_root_matrix(
            self.transitions_dir / style_group["root_file"]
        )

        # Cold start: use starting (unigram) distribution
        if not selected_indices:
            return self._cold_start(style_group, top_k, musicality)

        # Weighted n-gram scoring
        context = selected_indices[-CONTEXT_WINDOW:]
        scores = np.zeros(self.vocab_size, dtype=np.float64)

        for distance, prev_idx in enumerate(reversed(context)):
            weight = DECAY_LAMBDA ** distance

            # --- Chord transition factor ---
            chord_row = chord_matrix.getrow(prev_idx)
            if chord_row.nnz > 0:
                # Get dense row and scale
                dense_row = chord_row.toarray().ravel()
                scores += ALPHA * weight * dense_row

            # --- Root motion factor ---
            prev_root = self.idx_to_root.get(prev_idx)
            if prev_root is not None:
                root_row = root_matrix[prev_root]
                for cand_idx in range(self.vocab_size):
                    cand_root = self.idx_to_root.get(cand_idx)
                    if cand_root is not None:
                        scores[cand_idx] += (1 - ALPHA) * weight * root_row[cand_root]

        # Exclude already-selected chords
        for idx in selected_indices:
            scores[idx] = -1.0

        return self._top_k(scores, top_k, musicality)

    def _cold_start(
        self, style_group: dict[str, Any], top_k: int, musicality: float = 0.0
    ) -> list[dict[str, Any]]:
        """Recommend from the unigram starting-probability distribution."""
        starting = style_group.get("starting_probs", {})
        if not starting:
            # Absolute fallback: return most common chords (tonic + dominant)
            return self._default_start(top_k)

        scores = np.zeros(self.vocab_size, dtype=np.float64)
        for idx_str, prob in starting.items():
            idx = int(idx_str)
            if idx < self.vocab_size:
                scores[idx] = float(prob)

        return self._top_k(scores, top_k, musicality)

    def _apply_musicality(self, scores: np.ndarray, musicality: float) -> None:
        """Adjust scores to penalize basic major/minor triads and boost other chords.
        Modifies scores in-place."""
        if musicality <= 0:
            return
        triad_qualities = {"maj", "min"}
        for idx in range(len(scores)):
            if scores[idx] <= 0:
                continue
            name = self.chord_vocab[idx]
            info = self.chord_map.get(name)
            if info is None:
                continue
            if info.quality in triad_qualities:
                scores[idx] *= (1.0 - musicality * 0.9)
            else:
                scores[idx] *= (1.0 + musicality * 0.5)

    def _default_start(self, top_k: int) -> list[dict[str, Any]]:
        """Fallback cold-start: common chords across all 12 roots."""
        # Major and minor triads for all 12 roots, roughly ordered by commonness
        tonic_names = [
            "C", "G", "F", "A", "D", "E",
            "Amin", "Emin", "Dmin", "Bmin", "Fmin", "Cmin",
            "B", "Fs", "Cs", "Gs", "Ds", "As",
            "Gmin", "Fsmin", "Csmin", "Gsmin", "Dsmin", "Asmin",
            "C7", "G7", "F7", "D7", "A7", "E7",
            "Cmaj7", "Fmaj7", "Gmaj7",
            "Amin7", "Dmin7", "Emin7",
        ]
        results: list[dict[str, Any]] = []
        for name in tonic_names:
            idx = self.chord_to_idx.get(name)
            if idx is not None and len(results) < top_k:
                results.append({
                    "chord_idx": idx,
                    "chord_name": name,
                    "score": 1.0,
                    "chord_info": self.chord_map[name],
                })
        return results

    def _top_k(self, scores: np.ndarray, top_k: int, musicality: float = 0.0) -> list[dict[str, Any]]:
        """Extract top-k scored chords, optionally applying musicality bias."""
        self._apply_musicality(scores, musicality)
        order = np.argsort(-scores)
        results: list[dict[str, Any]] = []
        for idx in order:
            idx = int(idx)
            if scores[idx] <= 0:
                continue
            name = self.chord_vocab[idx]
            results.append({
                "chord_idx": idx,
                "chord_name": name,
                "score": round(float(scores[idx]), 6),
                "chord_info": self.chord_map.get(name),
            })
            if len(results) >= top_k:
                break
        return results
