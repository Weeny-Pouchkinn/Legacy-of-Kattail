"""Consolidate country leader portrait definitions into one sorted GFX file."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from interface_reorganization import active_definitions


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "interface"
TARGET = INTERFACE / "lok_leader_portraits.gfx"
COUNTRY_FILE = re.compile(r"lok_country_([A-Z]{3})_portraits\.gfx$")
PORTRAIT_TAG = re.compile(r"GFX_portrait_([A-Z]{3})_")
TEXTURE_TAG = re.compile(r"(?:leaders|interface/ministers)/([A-Z]{3})/")


def group_for_shared(definition: dict[str, str]) -> str:
    if definition["name"] in {"GFX_portrait_", "GFX_portrait__Small"}:
        return "SHARED TEMPLATES"
    match = PORTRAIT_TAG.match(definition["name"])
    if match:
        return match.group(1)
    match = TEXTURE_TAG.search(definition["texture"])
    if match:
        return match.group(1)
    if definition["name"].startswith("GFX_portrait_generic_"):
        return "GENERIC"
    if definition["name"].startswith("GFX_portrait_"):
        return "MISCELLANEOUS"
    return "SHARED TEMPLATES"


def main() -> None:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    sources: list[Path] = []

    if TARGET.exists():
        for definition in active_definitions(TARGET):
            groups[group_for_shared(definition)].append(definition)

    if not groups:
        for path in sorted(INTERFACE.glob("lok_country_*_portraits.gfx")):
            match = COUNTRY_FILE.fullmatch(path.name)
            if not match:
                continue
            groups[match.group(1)].extend(active_definitions(path))
            sources.append(path)

    shared = INTERFACE / "lok_shared_leader_portraits.gfx"
    if shared.exists() and not groups:
        for definition in active_definitions(shared):
            groups[group_for_shared(definition)].append(definition)
        sources.append(shared)

    if not groups:
        raise RuntimeError("no leader portrait definitions found")

    lines = ["spriteTypes = {", ""]
    country_groups = sorted(group for group in groups if len(group) == 3)
    shared_groups = sorted(group for group in groups if len(group) != 3)
    for group in country_groups + shared_groups:
        if group in {"GENERIC", "MISCELLANEOUS", "SHARED TEMPLATES"}:
            comment = group
        else:
            comment = group
        lines.extend([f"\t# {comment}", ""])
        for definition in groups[group]:
            block = definition["block"].replace("\r\n", "\n").replace("\r", "\n")
            lines.extend(block.splitlines())
            lines.append("")
        lines.append("")
    lines.extend(["}", ""])
    TARGET.write_bytes("\r\n".join(lines).encode("utf-8"))

    for source in sources:
        source.unlink()

    print(f"Consolidated {sum(len(items) for items in groups.values())} leader portrait definitions into {TARGET}.")
    print(f"Country sections: {sum(1 for key in groups if len(key) == 3)}; shared sections: {sum(1 for key in groups if len(key) != 3)}")


if __name__ == "__main__":
    main()
