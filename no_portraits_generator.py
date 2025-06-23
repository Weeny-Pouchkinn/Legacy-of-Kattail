#!/usr/bin/env python3
"""
generate_missing_portraits.py
--------------------------------
Scan your HoI4 mod for country tags that are *missing* any portrait definitions and
write out generic placeholders to **portraits/no_portraits.txt**.

Usage (run from the mod root):
    python generate_missing_portraits.py

The script is non‑destructive: if you already have a portraits/no_portraits.txt it
will be overwritten, but nothing else in your mod is changed.
"""
from pathlib import Path
import re
import sys

# --- Helpers --------------------------------------------------------------
TAG_LINE_RE = re.compile(r"^\s*([A-Z]{3})\s*=")  # e.g. "USA = \"United States\""
PORTRAIT_TAG_RE = re.compile(r"^\s*([A-Z]{3})\s*=")  # e.g. "USA = {"

GENERIC_SNIPPET = """{tag} = {{
	political = {{
		communism  = {{ male = {{ \"GFX_no_portrait_communism\"  }} female = {{ \"GFX_no_portrait_communism\"  }} }}
		democratic = {{ male = {{ \"GFX_no_portrait_democratic\" }} female = {{ \"GFX_no_portrait_democratic\" }} }}
		fascism    = {{ male = {{ \"GFX_no_portrait_fascism\"    }} female = {{ \"GFX_no_portrait_fascism\"    }} }}
		neutrality = {{ male = {{ \"GFX_no_portrait_neutrality\" }} female = {{ \"GFX_no_portrait_neutrality\" }} }}
		gestalt    = {{ male = {{ \"GFX_no_portrait_gestalt\"    }} female = {{ \"GFX_no_portrait_gestalt\"    }} }}
	}}
	army      = {{ male = {{ \"GFX_no_portrait_military\" }} female = {{ \"GFX_no_portrait_military\" }} }}
	navy      = {{ male = {{ \"GFX_no_portrait_navy\"     }} female = {{ \"GFX_no_portrait_navy\"     }} }}
	operative = {{ male = {{ \"GFX_no_portrait_spy\"      }} female = {{ \"GFX_no_portrait_spy\"      }} }}
	scientist = {{ male = {{ \"GFX_no_portrait_scientist\" }} female = {{ \"GFX_no_portrait_scientist\" }} }}
}}
"""


def collect_tags(country_tags_dir: Path) -> set[str]:
    """Return the set of three‑letter country tags defined under *common/country_tags*."""
    if not country_tags_dir.exists():
        sys.exit("[ERROR] common/country_tags not found – are you running from the mod root?")

    files = ([country_tags_dir] if country_tags_dir.is_file()
             else sorted(country_tags_dir.glob("*.txt")))

    tags: set[str] = set()
    for file in files:
        with file.open(encoding="utf‑8", errors="ignore") as fh:
            for line in fh:
                m = TAG_LINE_RE.match(line)
                if m:
                    tags.add(m.group(1))
    return tags


def collect_portrait_tags(portraits_dir: Path) -> set[str]:
    """Return the set of tags that *already* have a portrait definition."""
    if not portraits_dir.exists():
        sys.exit("[ERROR] portraits/ folder not found – are you running from the mod root?")

    tags: set[str] = set()
    for file in portraits_dir.rglob("*.txt"):
        with file.open(encoding="utf‑8", errors="ignore") as fh:
            for line in fh:
                m = PORTRAIT_TAG_RE.match(line)
                if m:
                    tags.add(m.group(1))
    return tags


def main() -> None:
    root = Path(__file__).resolve().parent

    all_tags = collect_tags(root / "common" / "country_tags")
    defined_tags = collect_portrait_tags(root / "portraits")

    missing = sorted(all_tags - defined_tags)
    if not missing:
        print("✅ All countries already have portrait definitions – nothing to do!")
        return

    output_path = root / "portraits" / "no_portraits.txt"
    with output_path.open("w", encoding="utf‑8") as out:
        for tag in missing:
            out.write(GENERIC_SNIPPET.format(tag=tag))
            out.write("\n")

    print(f"✨ Wrote {len(missing)} entries to {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
