"""Chord progression parser.

Parses the chordonomicon dataset: extracts sections, normalizes chord names,
splits genre tags, and groups by (genre_tag, decade, section) for bigram counting.
"""

import re
from collections import defaultdict
from typing import Iterable

import pandas as pd

from ..models.chord import NAME_TO_PITCH_CLASS, PITCH_CLASS_TO_NAME

# Section label pattern in chord strings: <intro_1>, <verse_2>, etc.
SECTION_PATTERN = re.compile(r"<(\w+?)_?\d*>")

# Flat-to-sharp root mapping
FLAT_TO_SHARP: dict[str, str] = {
    "Db": "Cs", "db": "Cs",
    "Eb": "Ds", "eb": "Ds",
    "Gb": "Fs", "gb": "Fs",
    "Ab": "Gs", "ab": "Gs",
    "Bb": "As", "bb": "As",
    # Single flat names (dataset sometimes uses these)
    # But flats are always 2 chars in standard notation
}

# Canonical section types (strip the number suffix)
SECTION_CANONICAL = {
    "intro", "verse", "chorus", "bridge",
    "solo", "interlude", "instrumental", "outro",
}


def parse_genre_tags(genres_str: str) -> list[str]:
    """Parse the genres field into individual genre tags.

    Input format: 'tag1' 'tag2' 'tag3'
    Returns: ['tag1', 'tag2', 'tag3']
    """
    if pd.isna(genres_str) or not genres_str.strip():
        return []
    s = genres_str.strip()
    tags = [t.strip() for t in s.split("' '")]
    # Clean first and last quotes
    if tags:
        tags[0] = tags[0].lstrip("'")
        tags[-1] = tags[-1].rstrip("'")
    return [t for t in tags if t]


def normalize_chord_name(raw_name: str) -> str | None:
    """Normalize a chord name from the dataset to chords_mapping convention.

    - Converts flat roots to sharp equivalents (Db->Cs, Eb->Ds, etc.)
    - Strips bass note from slash chords (D/Fs -> D)
    - Strips inversion markers
    - Returns None if the chord cannot be normalized
    """
    raw_name = raw_name.strip()
    if not raw_name:
        return None

    # Skip section markers and special tokens
    if raw_name.startswith("<") or raw_name == ">" or raw_name == "N":
        return None

    # Handle slash chords: keep only the chord before slash
    if "/" in raw_name:
        raw_name = raw_name.split("/")[0].strip()

    # Try flat-to-sharp conversion for root
    # Check 2-char roots first
    root_str = None
    quality = None

    if len(raw_name) >= 2 and raw_name[:2] in FLAT_TO_SHARP:
        root_str = FLAT_TO_SHARP[raw_name[:2]]
        quality = raw_name[2:]
    elif len(raw_name) >= 2:
        # Check if first 2 chars form a valid root (sharp notation)
        test_root = raw_name[:2]
        if test_root in NAME_TO_PITCH_CLASS:
            root_str = test_root
            quality = raw_name[2:]
    if root_str is None and len(raw_name) >= 1:
        test_root = raw_name[:1]
        if test_root in NAME_TO_PITCH_CLASS:
            root_str = test_root
            quality = raw_name[1:]

    if root_str is None or quality is None:
        return None

    return root_str + quality


def extract_sections(chords_str: str) -> list[tuple[str, list[str]]]:
    """Split a chord progression string into sections.

    Returns list of (section_type, [normalized_chord_names]) tuples.
    Unknown or unparseable chords are silently skipped.
    """
    if pd.isna(chords_str) or not chords_str.strip():
        return []

    # Tokenize
    tokens = chords_str.strip().split()
    sections: list[tuple[str, list[str]]] = []
    current_section = "unknown"
    current_chords: list[str] = []

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        m = SECTION_PATTERN.match(token)
        if m and token.startswith("<") and token.endswith(">"):
            section_raw = m.group(1)
            # Map to canonical section type
            for canonical in SECTION_CANONICAL:
                if section_raw.startswith(canonical):
                    section_type = canonical
                    break
            else:
                section_type = section_raw

            # Save previous section
            if current_chords:
                sections.append((current_section, current_chords))
            current_section = section_type
            current_chords = []
        elif token == ">":
            continue
        elif token == "N":
            # "N" = no chord marker, skip
            continue
        else:
            normalized = normalize_chord_name(token)
            if normalized:
                current_chords.append(normalized)

    # Don't forget the last section
    if current_chords:
        sections.append((current_section, current_chords))

    return sections


def _extract_decade(row: pd.Series) -> int | None:
    """Extract decade from a dataset row.

    Uses the decade column if available, otherwise derives from release_date.
    Returns None if decade cannot be determined.
    """
    decade = row.get("decade")
    if not pd.isna(decade):
        return int(float(decade))

    release_date = row.get("release_date")
    if not pd.isna(release_date):
        try:
            year = int(str(release_date)[:4])
            return (year // 10) * 10
        except (ValueError, TypeError):
            pass
    return None


# Records generated by parse_dataset
ParsedRecord = tuple[str, int, str, list[str]]  # (genre_tag, decade, section, chord_list)


def parse_dataset(df: pd.DataFrame, chord_vocab: set[str]) -> list[ParsedRecord]:
    """Parse the full dataset into flat records for bigram counting.

    Each record is (genre_tag, decade, section_type, chord_sequence).
    One row from the dataset can produce multiple records:
      - One per genre tag (for each sub-tag in genres)
      - One per main_genre (for fallback)
      - One per section within the chord progression

    Args:
        df: Full dataset DataFrame
        chord_vocab: Set of valid chord names from chords_mapping

    Returns:
        List of (genre_tag, decade, section, chord_list) records
    """
    records: list[ParsedRecord] = []
    unknown_chords: dict[str, int] = defaultdict(int)
    skipped_no_decade = 0
    skipped_no_genre = 0

    for _, row in df.iterrows():
        decade = _extract_decade(row)
        if decade is None:
            skipped_no_decade += 1
            continue

        # Get genre tags
        genre_tags = parse_genre_tags(row.get("genres", ""))
        main_genre = row.get("main_genre")
        if not pd.isna(main_genre):
            main_genre = main_genre.strip().lower()
        else:
            main_genre = ""

        if not genre_tags and not main_genre:
            skipped_no_genre += 1
            continue

        # Parse sections from chord string
        sections = extract_sections(row.get("chords", ""))
        if not sections:
            continue

        for section_type, chord_list in sections:
            if len(chord_list) < 2:
                continue  # Need at least 2 chords for bigrams

            # Filter to known chords, tracking unknown ones
            filtered = []
            for c in chord_list:
                if c in chord_vocab:
                    filtered.append(c)
                else:
                    unknown_chords[c] += 1
            if len(filtered) < 2:
                continue

            # Emit records for each genre sub-tag
            for tag in genre_tags:
                if tag:
                    records.append((tag, decade, section_type, filtered))

            # Emit main_genre fallback record
            if main_genre:
                records.append((f"__main__{main_genre}", decade, section_type, filtered))

    if unknown_chords:
        top_unknown = sorted(unknown_chords.items(), key=lambda x: -x[1])[:20]
        print(f"Skipped {sum(unknown_chords.values())} unrecognized chord tokens")
        print(f"Top unknown chords: {top_unknown}")

    print(f"Produced {len(records)} records")
    print(f"Skipped rows: {skipped_no_decade} (no decade), {skipped_no_genre} (no genre)")
    return records


def count_bigrams(
    records: list[ParsedRecord],
    chord_to_idx: dict[str, int],
) -> dict[tuple[str, int, str], dict]:
    """Count chord bigrams from parsed records.

    Groups records by (genre_tag, decade, section_type) and builds
    sparse bigram count matrices for each group.

    Returns:
        dict mapping group_key -> { "counts": {(from_idx, to_idx): count},
                                   "total_bigrams": int,
                                   "starting_counts": {chord_idx: count} }
    """
    groups: dict[tuple[str, int, str], dict] = {}

    for genre_tag, decade, section, chord_list in records:
        key = (genre_tag, decade, section)
        if key not in groups:
            groups[key] = {
                "counts": defaultdict(int),
                "total_bigrams": 0,
                "starting_counts": defaultdict(int),
            }

        group = groups[key]
        # First chord as starting chord
        start_idx = chord_to_idx.get(chord_list[0])
        if start_idx is not None:
            group["starting_counts"][start_idx] += 1

        # Bigrams
        for i in range(len(chord_list) - 1):
            from_idx = chord_to_idx.get(chord_list[i])
            to_idx = chord_to_idx.get(chord_list[i + 1])
            if from_idx is not None and to_idx is not None:
                group["counts"][(from_idx, to_idx)] += 1
                group["total_bigrams"] += 1

    print(f"Built {len(groups)} genre/decade/section groups")
    return groups
