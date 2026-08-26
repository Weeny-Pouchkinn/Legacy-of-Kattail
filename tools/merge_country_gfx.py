"""Merge each country's remaining GFX libraries into one file."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from interface_reorganization import active_definitions


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "interface"
SOURCE = re.compile(r"lok_country_([A-Z]{3})_(ideas|focus_icons|modifiers|estates)\.gfx$")
SECTION_ORDER = {"ideas": 0, "focus_icons": 1, "modifiers": 2, "estates": 3}
SECTION_LABEL = {
    "ideas": "IDEAS",
    "focus_icons": "FOCUS ICONS",
    "modifiers": "MODIFIERS",
    "estates": "ESTATES",
}


def main() -> None:
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    sources: list[Path] = []
    for path in sorted(INTERFACE.glob("lok_country_*.gfx")):
        match = SOURCE.fullmatch(path.name)
        if not match:
            continue
        tag, section = match.groups()
        target = INTERFACE / f"lok_country_{tag}.gfx"
        if target.exists():
            raise FileExistsError(f"target already exists: {target}")
        grouped[tag][section].extend(active_definitions(path))
        sources.append(path)

    if not grouped:
        raise RuntimeError("no split country GFX files found")

    for tag in sorted(grouped):
        lines = ["spriteTypes = {", ""]
        for section in sorted(grouped[tag], key=lambda item: SECTION_ORDER.get(item, 99)):
            lines.extend([f"\t# {SECTION_LABEL.get(section, section.upper())}", ""])
            for definition in grouped[tag][section]:
                block = definition["block"].replace("\r\n", "\n").replace("\r", "\n")
                lines.extend(block.splitlines())
                lines.append("")
            lines.append("")
        lines.extend(["}", ""])
        (INTERFACE / f"lok_country_{tag}.gfx").write_bytes("\r\n".join(lines).encode("utf-8"))

    for source in sources:
        source.unlink()

    print(f"Merged {len(grouped)} countries and {len(sources)} source GFX files.")


if __name__ == "__main__":
    main()
