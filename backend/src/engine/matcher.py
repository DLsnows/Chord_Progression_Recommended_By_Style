"""Style matcher: NL query → ranked (genre_tag, decade, section) groups.

Layered weighted matching:
  - Genre sub-tags: 0.60  (dominant signal)
  - Decade:          0.20
  - Main genre:      0.20
"""

import math
import re
from typing import Any

from ..config import GENRE_TAG_WEIGHT, DECADE_WEIGHT, MAIN_GENRE_WEIGHT

# Decade extraction: "1960s", "60s", "1970", "80年代", "nineties"
DECADE_PATTERNS = [
    re.compile(r"(?:19|20)(\d{2})0s?"),
    re.compile(r"\b(\d{2})s\b"),
    re.compile(r"(?:19|20)(\d{2})0\b"),
]
DECADE_BY_ERA: dict[str, int] = {
    "fifties": 1950, "50s": 1950, "1950s": 1950,
    "sixties": 1960, "60s": 1960, "1960s": 1960,
    "seventies": 1970, "70s": 1970, "1970s": 1970,
    "eighties": 1980, "80s": 1980, "1980s": 1980,
    "nineties": 1990, "90s": 1990, "1990s": 1990,
    "two thousands": 2000, "2000s": 2000, "noughties": 2000,
    "tens": 2010, "2010s": 2010,
    "twenties": 2020, "2020s": 2020,
}

SECTION_KEYWORDS = {
    "intro", "verse", "chorus", "bridge", "solo",
    "outro", "interlude", "instrumental", "unknown",
}

MAIN_GENRE_PREFIX = "__main__"


class StyleMatcher:
    """Match natural language queries to available style groups."""

    def __init__(self, style_index: dict[str, dict[str, Any]]) -> None:
        self.style_index = style_index

        self.all_sub_tags: set[str] = set()
        self.all_main_genres: set[str] = set()
        self.all_decades: set[int] = set()
        self.all_sections: set[str] = set()

        for info in style_index.values():
            tag = info["genre_tag"]
            if tag.startswith(MAIN_GENRE_PREFIX):
                self.all_main_genres.add(tag[len(MAIN_GENRE_PREFIX):])
            else:
                self.all_sub_tags.add(tag)
            self.all_decades.add(info["decade"])
            self.all_sections.add(info["section"])

        self.max_samples = max(
            (g["sample_count"] for g in style_index.values()), default=1
        )

    def search(self, query: str, top_n: int = 20) -> list[dict[str, Any]]:
        """Search for style groups matching a natural language query.

        Returns ranked list of matches with keys: key, genre_tag, main_genre,
        decade, section, score, sample_count, total_bigrams, file, root_file,
        starting_probs.
        """
        tokens = self._tokenize(query)
        genre_hits = tokens & self.all_sub_tags
        main_genre_hits = tokens & self.all_main_genres
        decade_hit = self._extract_decade(tokens)
        section_hit = self._extract_section(tokens)

        results: list[dict[str, Any]] = []
        for key, info in self.style_index.items():
            tag = info["genre_tag"]

            genre_score = 0.0
            main_genre_score = 0.0

            if tag.startswith(MAIN_GENRE_PREFIX):
                main = tag[len(MAIN_GENRE_PREFIX):]
                if main in main_genre_hits:
                    main_genre_score = MAIN_GENRE_WEIGHT
            else:
                if tag in genre_hits:
                    genre_score = GENRE_TAG_WEIGHT

            decade_score = DECADE_WEIGHT if (decade_hit is not None and info["decade"] == decade_hit) else 0.0

            raw_score = genre_score + main_genre_score + decade_score
            if raw_score == 0:
                continue

            # Drop section mismatch early — section is a hard filter when specified
            if section_hit is not None and info["section"] != section_hit:
                continue

            # Normalize by sample count (log-scale, so large samples get modest boost)
            norm = math.log(1 + info["sample_count"]) / math.log(1 + self.max_samples)
            score = raw_score * norm

            results.append({
                "key": key,
                "genre_tag": info["genre_tag"],
                "decade": info["decade"],
                "section": info["section"],
                "score": round(score, 6),
                "sample_count": info["sample_count"],
                "total_bigrams": info["total_bigrams"],
                "file": info["file"],
                "root_file": info["root_file"],
                "starting_probs": info["starting_probs"],
            })

        results.sort(key=lambda r: -r["score"])

        # Fallback: if no results, try without section filter
        if not results and section_hit is not None:
            return self._fallback_search(genre_hits, main_genre_hits, decade_hit, None, top_n)

        # Fallback: if still no results, try without decade filter
        if not results:
            return self._fallback_search(genre_hits, main_genre_hits, None, None, top_n)

        return results[:top_n]

    def _fallback_search(
        self,
        genre_hits: set[str],
        main_genre_hits: set[str],
        decade_hit: int | None,
        section_hit: str | None,
        top_n: int,
    ) -> list[dict[str, Any]]:
        """Search with progressively relaxed constraints."""
        results: list[dict[str, Any]] = []
        for key, info in self.style_index.items():
            tag = info["genre_tag"]
            genre_score = 0.0
            main_genre_score = 0.0

            if tag.startswith(MAIN_GENRE_PREFIX):
                main = tag[len(MAIN_GENRE_PREFIX):]
                if main in main_genre_hits:
                    main_genre_score = MAIN_GENRE_WEIGHT
            else:
                if tag in genre_hits:
                    genre_score = GENRE_TAG_WEIGHT

            decade_score = 0.0
            if decade_hit is not None and info["decade"] == decade_hit:
                decade_score = DECADE_WEIGHT

            if section_hit is not None and info["section"] != section_hit:
                continue

            raw_score = genre_score + main_genre_score + decade_score
            if raw_score == 0:
                # In final fallback (global), match on section alone
                if section_hit is not None and info["section"] == section_hit:
                    raw_score = 0.05

            if raw_score == 0:
                continue

            norm = math.log(1 + info["sample_count"]) / math.log(1 + self.max_samples)
            score = raw_score * norm

            results.append({
                "key": key,
                "genre_tag": info["genre_tag"],
                "decade": info["decade"],
                "section": info["section"],
                "score": round(score, 6),
                "sample_count": info["sample_count"],
                "total_bigrams": info["total_bigrams"],
                "file": info["file"],
                "root_file": info["root_file"],
                "starting_probs": info["starting_probs"],
            })

        results.sort(key=lambda r: -r["score"])
        return results[:top_n]

    def _tokenize(self, query: str) -> set[str]:
        """Lowercase + split query into tokens, also emit multi-word substrings."""
        lower = query.strip().lower()
        tokens = set(lower.split())
        # Remove common stopwords
        stopwords = {"a", "an", "the", "and", "or", "in", "of", "to", "from",
                     "with", "like", "style", "music", "song", "section", "genre",
                     "年代", "风格", "音乐", "歌曲", "部分", "的"}
        tokens -= stopwords
        return tokens

    def _extract_decade(self, tokens: set[str]) -> int | None:
        """Extract a decade bucket from query tokens."""
        query = " ".join(tokens)

        # Try era keywords first
        for keyword, decade in DECADE_BY_ERA.items():
            if keyword in query:
                return decade

        # Try numeric patterns
        for pattern in DECADE_PATTERNS:
            m = pattern.search(query.replace("-", "").replace("_", ""))
            if m:
                prefix = m.group(1)
                year = int(prefix) if len(prefix) == 2 else None
                if year is not None:
                    year = 1900 + year if year >= 50 else 2000 + year
                else:
                    year = int(prefix)
                return (year // 10) * 10

        # Direct decade number (e.g. "1960" in query)
        for token in tokens:
            try:
                n = int(token)
                if 1900 <= n <= 2030:
                    return (n // 10) * 10
            except ValueError:
                continue

        return None

    def _extract_section(self, tokens: set[str]) -> str | None:
        """Extract a section type from query tokens."""
        for token in tokens:
            if token.lower() in SECTION_KEYWORDS:
                return token.lower()
        return None
