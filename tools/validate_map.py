"""Static consistency checks for the Legacy of Kattail HOI4 map."""

from __future__ import annotations

import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def error(message: str) -> None:
    ERRORS.append(message)


def definition_rows() -> dict[int, list[str]]:
    rows: dict[int, list[str]] = {}
    for line in (ROOT / "map" / "definition.csv").read_text(
        encoding="utf-8-sig"
    ).splitlines():
        fields = line.split(";")
        if fields[0].isdigit():
            rows[int(fields[0])] = fields
    return rows


def province_block(path: Path) -> list[int]:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"\bprovinces\s*=\s*\{(.*?)\}", text, re.DOTALL)
    if not match:
        error(f"{path.relative_to(ROOT)} has no provinces block")
        return []
    return [int(value) for value in re.findall(r"\b\d+\b", match.group(1))]


def main() -> int:
    rows = definition_rows()
    ids = sorted(rows)
    if ids != list(range(ids[-1] + 1)):
        error("definition.csv province IDs are not continuous from 0")

    colors = {
        province_id: (int(row[1]) << 16) | (int(row[2]) << 8) | int(row[3])
        for province_id, row in rows.items()
    }
    reverse_colors = {color: province_id for province_id, color in colors.items()}
    if len(reverse_colors) != len(colors):
        error("definition.csv contains duplicate RGB colors")

    image_path = ROOT / "map" / "provinces.bmp"
    header = image_path.read_bytes()[:34]
    bits_per_pixel = struct.unpack_from("<H", header, 28)[0]
    compression = struct.unpack_from("<I", header, 30)[0]
    if bits_per_pixel != 24 or compression != 0:
        error(
            f"provinces.bmp is {bits_per_pixel}-bit with compression {compression}; "
            "HOI4 requires uncompressed 24-bit RGB"
        )

    with Image.open(image_path) as image:
        rgb = np.array(image.convert("RGB"), dtype=np.uint32)
    height, width = rgb.shape[:2]
    if width % 128 or height % 128:
        error(f"provinces.bmp dimensions {width}x{height} are not multiples of 128")

    packed = (rgb[:, :, 0] << 16) | (rgb[:, :, 1] << 8) | rgb[:, :, 2]
    bitmap_colors = set(map(int, np.unique(packed)))
    defined_colors = set(colors.values())
    if bitmap_colors - defined_colors:
        error(f"{len(bitmap_colors - defined_colors)} bitmap colors are undefined")
    missing_pixels = defined_colors - bitmap_colors - {colors[0]}
    if missing_pixels:
        error(f"{len(missing_pixels)} province definitions have no bitmap pixels")

    quads = np.stack(
        (
            packed[:-1, :-1],
            packed[:-1, 1:],
            packed[1:, :-1],
            packed[1:, 1:],
        ),
        axis=2,
    )
    ordered = np.sort(quads, axis=2)
    x_crossings = (
        (ordered[:, :, 0] != ordered[:, :, 1])
        & (ordered[:, :, 1] != ordered[:, :, 2])
        & (ordered[:, :, 2] != ordered[:, :, 3])
    )
    if np.any(x_crossings):
        error(f"{int(np.sum(x_crossings))} invalid X crossings remain")

    adjacency: set[tuple[int, int]] = set()
    for left, right in (
        (packed[:, :-1], packed[:, 1:]),
        (packed[:-1, :], packed[1:, :]),
        (packed[:, -1:], packed[:, :1]),
    ):
        mask = left != right
        for color_a, color_b in np.unique(
            np.stack((left[mask], right[mask]), axis=1), axis=0
        ):
            id_a = reverse_colors[int(color_a)]
            id_b = reverse_colors[int(color_b)]
            adjacency.add((id_a, id_b))
            adjacency.add((id_b, id_a))

    province_types = {province_id: row[4] for province_id, row in rows.items()}
    actual_coastal: set[int] = set()
    for province_a, province_b in adjacency:
        if {province_types[province_a], province_types[province_b]} == {
            "land",
            "sea",
        }:
            actual_coastal.add(province_a)
            actual_coastal.add(province_b)
    declared_coastal = {
        province_id for province_id, row in rows.items() if row[5] == "true"
    }
    if actual_coastal != declared_coastal:
        error(
            f"{len(actual_coastal ^ declared_coastal)} coastal flags disagree "
            "with bitmap adjacency"
        )

    state_membership: defaultdict[int, list[str]] = defaultdict(list)
    expected_ports: set[int] = set()
    for path in (ROOT / "history" / "states").glob("*.txt"):
        relative = str(path.relative_to(ROOT))
        provinces = province_block(path)
        if len(provinces) != len(set(provinces)):
            error(f"{relative} contains duplicate province IDs")
        for province_id in provinces:
            if province_id not in rows:
                error(f"{relative} references undefined province {province_id}")
            else:
                state_membership[province_id].append(relative)

        text = path.read_text(encoding="utf-8-sig")
        for match in re.finditer(
            r"(?m)^\s*(\d+)\s*=\s*\{([^{}]*)\}",
            text,
        ):
            province_id = int(match.group(1))
            body = re.sub(r"#.*", "", match.group(2))
            coastal_building = re.search(
                r"\b(?:naval_base|coastal_bunker)\s*=\s*([1-9]\d*(?:\.\d+)?)",
                body,
            )
            if coastal_building and province_id not in actual_coastal:
                error(
                    f"{relative} puts a coastal building in inland province "
                    f"{province_id}"
                )
            if re.search(
                r"\bnaval_base\s*=\s*[1-9]\d*(?:\.\d+)?",
                body,
            ):
                expected_ports.add(province_id)

    for province_id, province_type in province_types.items():
        if province_id == 0 or province_type != "land":
            continue
        memberships = state_membership.get(province_id, [])
        if len(memberships) != 1:
            error(
                f"land province {province_id} belongs to {len(memberships)} states"
            )

    region_membership: Counter[int] = Counter()
    for path in (ROOT / "map" / "strategicregions").glob("*.txt"):
        provinces = province_block(path)
        if len(provinces) != len(set(provinces)):
            error(f"{path.relative_to(ROOT)} contains duplicate province IDs")
        region_membership.update(provinces)
    for province_id in range(1, ids[-1] + 1):
        if region_membership[province_id] != 1:
            error(
                f"province {province_id} belongs to "
                f"{region_membership[province_id]} strategic regions"
            )

    railway_path = ROOT / "map" / "railways.txt"
    placed_ports: set[int] = set()
    for line_number, line in enumerate(
        railway_path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        fields = [int(value) for value in line.split()]
        if len(fields) < 4 or fields[1] != len(fields) - 2:
            error(f"railways.txt:{line_number} has an incorrect province count")
            continue
        for province_a, province_b in zip(fields[2:], fields[3:]):
            if (province_a, province_b) not in adjacency:
                error(
                    f"railways.txt:{line_number} jumps between non-neighbors "
                    f"{province_a} and {province_b}"
                )

    for line_number, line in enumerate(
        (ROOT / "map" / "supply_nodes.txt")
        .read_text(encoding="utf-8-sig")
        .splitlines(),
        start=1,
    ):
        fields = line.split()
        if len(fields) >= 2:
            province_id = int(fields[1])
            if province_id not in state_membership:
                error(
                    f"supply_nodes.txt:{line_number} uses stateless province "
                    f"{province_id}"
                )

    for line_number, line in enumerate(
        (ROOT / "map" / "buildings.txt")
        .read_text(encoding="utf-8-sig")
        .splitlines(),
        start=1,
    ):
        fields = line.split(";")
        if len(fields) != 7:
            continue
        if fields[1] == "naval_base":
            sea_id = int(fields[6])
            if sea_id and province_types.get(sea_id) != "sea":
                error(
                    f"buildings.txt:{line_number} points {fields[1]} at "
                    f"non-sea province {sea_id}"
                )
            x = max(0, min(width - 1, round(float(fields[2]))))
            y = max(0, min(height - 1, height - 1 - round(float(fields[4]))))
            placed_ports.add(reverse_colors[int(packed[y, x])])

    for province_id in sorted(expected_ports - placed_ports):
        error(f"province {province_id} has a naval base but no map placement")

    if ERRORS:
        print(f"Map validation failed with {len(ERRORS)} issue(s):")
        for message in ERRORS[:200]:
            print(f"- {message}")
        if len(ERRORS) > 200:
            print(f"- ... and {len(ERRORS) - 200} more")
        return 1

    print(
        f"Map validation passed: {ids[-1]} provinces, "
        f"{len(state_membership)} state-assigned provinces, "
        f"{len(list((ROOT / 'map' / 'strategicregions').glob('*.txt')))} "
        "strategic regions, no X crossings."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
