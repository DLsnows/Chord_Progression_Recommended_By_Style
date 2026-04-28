"""Quick exploration of the chordonomicon dataset schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.loader import load_dataset

df = load_dataset()

print("=== decade column ===")
print(f"Non-null: {df['decade'].notna().sum()} / {len(df)}")
decades = sorted(d for d in df["decade"].dropna().unique())
print(f"Unique decades: {decades}")

print("\n=== release_date column ===")
print(f"Non-null: {df['release_date'].notna().sum()} / {len(df)}")
sample_dates = df["release_date"].dropna().head(5).tolist()
print(f"Samples: {sample_dates}")

print("\n=== main_genre column ===")
print(f"Non-null: {df['main_genre'].notna().sum()} / {len(df)}")
print(f"Top main genres: {df['main_genre'].value_counts().head(15).to_dict()}")

print("\n=== genres column ===")
print(f"Non-null: {df['genres'].notna().sum()} / {len(df)}")

# Parse all unique genre tags
all_tags = set()
for g_str in df["genres"].dropna():
    # Format: 'tag1' 'tag2' 'tag3'
    g_str = g_str.strip()
    # Split by quote-space-quote pattern
    parts = g_str.split("' '")
    for i, p in enumerate(parts):
        p = p.strip("'")
        if p:
            all_tags.add(p)

print(f"Unique genre tags: {len(all_tags)}")
print(f"Sample tags: {sorted(all_tags)[:40]}")

# Check section labels in chords
print("\n=== Section labels in chord strings ===")
import re
section_pattern = re.compile(r"<(\w+)>")
all_sections = set()
for chords_str in df["chords"].dropna().head(5000):
    sections = section_pattern.findall(chords_str)
    all_sections.update(sections)
print(f"Unique section types (first 5000 rows): {sorted(all_sections)}")
