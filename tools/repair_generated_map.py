"""Repair consistency damage left by the July 2026 province regeneration.

The generator painted over 46 old provinces without removing their definitions
or references. HOI4 cannot safely leave gaps in definition.csv, so this script:

* redirects references to erased provinces to the province occupying most of
  their former area;
* moves the 46 highest live province IDs into the vacated ID slots;
* repairs state/strategic-region lists, railways, supply nodes, adjacencies, and
  unit-stack records;
* removes the 14 four-way ("invalid X") pixel crossings; and
* recalculates the coastal flags from bitmap adjacency.

It is intentionally specific to this committed map revision. Run it once.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]

MISSING_TO_SURVIVOR = {
    446: 21124,
    488: 18035,
    1483: 2405,
    1583: 3374,
    1864: 16921,
    3708: 18035,
    4836: 17700,
    5391: 22,
    5784: 20982,
    5940: 8771,
    5961: 6176,
    6094: 16826,
    6194: 1919,
    6336: 20975,
    7285: 11534,
    7641: 10348,
    7657: 17832,
    7773: 17869,
    7881: 5595,
    8521: 17910,
    9540: 17869,
    9826: 17906,
    10669: 20984,
    13326: 5289,
    15809: 15739,
    16690: 3637,
    16888: 16960,
    16910: 1859,
    16956: 21075,
    16966: 16921,
    17018: 5503,
    17062: 17054,
    17131: 21077,
    17147: 17063,
    17318: 8771,
    17321: 10617,
    17467: 11574,
    17523: 10737,
    17822: 17910,
    17855: 11597,
    17871: 4998,
    18073: 21000,
    18089: 8180,
    18285: 1284,
    20296: 21076,
    21046: 20984,
}

DONOR_TO_GAP = dict(
    zip(
        range(21135, 21089, -1),
        MISSING_TO_SURVIVOR,
    )
)


def read_text(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), bom


def write_text(path: Path, text: str, bom: bool) -> None:
    payload = text.encode("utf-8")
    if bom:
        payload = b"\xef\xbb\xbf" + payload
    path.write_bytes(payload)


def final_id(province_id: int) -> int:
    redirected = MISSING_TO_SURVIVOR.get(province_id, province_id)
    return DONOR_TO_GAP.get(redirected, redirected)


def replace_number_tokens(text: str) -> str:
    return re.sub(r"\b\d+\b", lambda m: str(final_id(int(m.group()))), text)


def repair_province_block(match: re.Match[str]) -> str:
    prefix, body, suffix = match.groups()
    seen: set[int] = set()

    def replace(match_number: re.Match[str]) -> str:
        value = final_id(int(match_number.group()))
        if value in seen:
            return ""
        seen.add(value)
        return str(value)

    return prefix + re.sub(r"\b\d+\b", replace, body) + suffix


def repair_state_files() -> None:
    block_pattern = re.compile(
        r"(\bprovinces\s*=\s*\{)(.*?)(\})",
        flags=re.DOTALL,
    )
    scoped_pattern = re.compile(
        r"(\bvictory_points\s*=\s*\{\s*)(\d+)"
        r"|^(\s*)(\d+)(\s*=\s*\{)",
        flags=re.MULTILINE,
    )

    for path in (ROOT / "history" / "states").glob("*.txt"):
        text, bom = read_text(path)
        original = text
        text = block_pattern.sub(repair_province_block, text, count=1)

        def replace_scoped(match: re.Match[str]) -> str:
            if match.group(2):
                return match.group(1) + str(final_id(int(match.group(2))))
            return (
                match.group(3)
                + str(final_id(int(match.group(4))))
                + match.group(5)
            )

        text = scoped_pattern.sub(replace_scoped, text)
        if text != original:
            write_text(path, text, bom)


def repair_strategic_regions() -> None:
    block_pattern = re.compile(
        r"(\bprovinces\s*=\s*\{)(.*?)(\})",
        flags=re.DOTALL,
    )
    for path in (ROOT / "map" / "strategicregions").glob("*.txt"):
        text, bom = read_text(path)
        changed = block_pattern.sub(repair_province_block, text, count=1)
        if changed != text:
            write_text(path, changed, bom)


def repair_railways() -> None:
    path = ROOT / "map" / "railways.txt"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    output = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3 or not all(field.isdigit() for field in fields):
            output.append(line)
            continue
        provinces = [final_id(int(value)) for value in fields[2:]]
        provinces = [
            value
            for index, value in enumerate(provinces)
            if index == 0 or value != provinces[index - 1]
        ]
        if len(provinces) < 2:
            continue
        output.append(f"{fields[0]} {len(provinces)} " + " ".join(map(str, provinces)) + " ")
    write_text(path, newline.join(output) + newline, bom)


def repair_supply_nodes() -> None:
    path = ROOT / "map" / "supply_nodes.txt"
    text, bom = read_text(path)
    changed = re.sub(
        r"(?m)^(\s*\d+\s+)(\d+)(\s*)$",
        lambda m: m.group(1) + str(final_id(int(m.group(2)))) + m.group(3),
        text,
    )
    write_text(path, changed, bom)


def repair_adjacencies() -> None:
    path = ROOT / "map" / "adjacencies.csv"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    output = []
    for line in text.splitlines():
        fields = line.split(";")
        if fields and fields[0].isdigit():
            for index in range(min(3, len(fields))):
                if fields[index].isdigit():
                    fields[index] = str(final_id(int(fields[index])))
        output.append(";".join(fields))
    write_text(path, newline.join(output) + newline, bom)


def repair_unitstacks() -> None:
    path = ROOT / "map" / "unitstacks.txt"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    output = []
    for line in text.splitlines():
        fields = line.split(";", 1)
        if fields[0].isdigit():
            old_id = int(fields[0])
            if old_id in MISSING_TO_SURVIVOR:
                continue
            fields[0] = str(final_id(old_id))
        output.append(";".join(fields))
    write_text(path, newline.join(output) + newline, bom)


def repair_building_sea_references() -> None:
    path = ROOT / "map" / "buildings.txt"
    text, bom = read_text(path)
    changed = re.sub(
        r"(?m)^(.*;)(\d+)(\s*)$",
        lambda m: m.group(1) + str(final_id(int(m.group(2)))) + m.group(3),
        text,
    )
    write_text(path, changed, bom)


def repair_definition_and_coasts(province_map: np.ndarray) -> None:
    path = ROOT / "map" / "definition.csv"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = {}
    for line in text.splitlines():
        fields = line.split(";")
        if fields[0].isdigit():
            rows[int(fields[0])] = fields

    for donor, gap in DONOR_TO_GAP.items():
        fields = rows.pop(donor)
        fields[0] = str(gap)
        rows[gap] = fields

    packed = (
        province_map[:, :, 0].astype(np.uint32) << 16
        | province_map[:, :, 1].astype(np.uint32) << 8
        | province_map[:, :, 2].astype(np.uint32)
    )
    color_to_id = {
        (int(fields[1]) << 16) | (int(fields[2]) << 8) | int(fields[3]): province_id
        for province_id, fields in rows.items()
    }
    province_type = {province_id: fields[4] for province_id, fields in rows.items()}
    coastal: set[int] = set()

    for left, right in (
        (packed[:, :-1], packed[:, 1:]),
        (packed[:-1, :], packed[1:, :]),
    ):
        mask = left != right
        pairs = np.unique(np.stack((left[mask], right[mask]), axis=1), axis=0)
        for color_a, color_b in pairs:
            id_a = color_to_id.get(int(color_a))
            id_b = color_to_id.get(int(color_b))
            if id_a is None or id_b is None:
                continue
            type_a, type_b = province_type[id_a], province_type[id_b]
            if {type_a, type_b} == {"land", "sea"}:
                coastal.add(id_a)
                coastal.add(id_b)

    for province_id, fields in rows.items():
        fields[5] = "true" if province_id in coastal else "false"

    output = [";".join(rows[province_id]) for province_id in sorted(rows)]
    write_text(path, newline.join(output) + newline, bom)


def split_disjointed_railways(province_map: np.ndarray) -> None:
    definition_text, _ = read_text(ROOT / "map" / "definition.csv")
    color_to_id = {}
    for line in definition_text.splitlines():
        fields = line.split(";")
        if fields[0].isdigit():
            color = (int(fields[1]) << 16) | (int(fields[2]) << 8) | int(fields[3])
            color_to_id[color] = int(fields[0])

    packed = (
        province_map[:, :, 0].astype(np.uint32) << 16
        | province_map[:, :, 1].astype(np.uint32) << 8
        | province_map[:, :, 2].astype(np.uint32)
    )
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
            id_a = color_to_id[int(color_a)]
            id_b = color_to_id[int(color_b)]
            adjacency.add((id_a, id_b))
            adjacency.add((id_b, id_a))

    path = ROOT / "map" / "railways.txt"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    output = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 4:
            continue
        level = fields[0]
        provinces = [int(value) for value in fields[2:]]
        segment = [provinces[0]]
        segments = []
        for province_id in provinces[1:]:
            if (segment[-1], province_id) in adjacency:
                segment.append(province_id)
            else:
                if len(segment) >= 2:
                    segments.append(segment)
                segment = [province_id]
        if len(segment) >= 2:
            segments.append(segment)
        if len(segments) == 1 and segments[0] == provinces:
            output.append(line)
            continue
        for valid_segment in segments:
            output.append(
                f"{level} {len(valid_segment)} "
                + " ".join(map(str, valid_segment))
            )
    write_text(path, newline.join(output) + newline, bom)


def ensure_port_buildings(province_map: np.ndarray) -> None:
    definition_text, _ = read_text(ROOT / "map" / "definition.csv")
    color_to_id = {}
    province_type = {}
    id_to_color = {}
    for line in definition_text.splitlines():
        fields = line.split(";")
        if fields[0].isdigit():
            province_id = int(fields[0])
            color = (int(fields[1]) << 16) | (int(fields[2]) << 8) | int(fields[3])
            color_to_id[color] = province_id
            id_to_color[province_id] = color
            province_type[province_id] = fields[4]

    packed = (
        province_map[:, :, 0].astype(np.uint32) << 16
        | province_map[:, :, 1].astype(np.uint32) << 8
        | province_map[:, :, 2].astype(np.uint32)
    )
    height, width = packed.shape

    province_to_state = {}
    expected_ports = set()
    for path in (ROOT / "history" / "states").glob("*.txt"):
        text, _ = read_text(path)
        state_match = re.search(r"\bid\s*=\s*(\d+)", text)
        province_match = re.search(
            r"\bprovinces\s*=\s*\{(.*?)\}",
            text,
            re.DOTALL,
        )
        if not state_match or not province_match:
            continue
        state_id = int(state_match.group(1))
        for value in re.findall(r"\b\d+\b", province_match.group(1)):
            province_to_state[int(value)] = state_id
        for match in re.finditer(
            r"(?m)^\s*(\d+)\s*=\s*\{([^{}]*)\}",
            text,
        ):
            body = re.sub(r"#.*", "", match.group(2))
            if re.search(r"\bnaval_base\s*=\s*[1-9]\d*(?:\.\d+)?", body):
                expected_ports.add(int(match.group(1)))

    path = ROOT / "map" / "buildings.txt"
    text, bom = read_text(path)
    newline = "\r\n" if "\r\n" in text else "\n"
    placed_ports = set()
    for line in text.splitlines():
        fields = line.split(";")
        if len(fields) != 7 or fields[1] != "naval_base":
            continue
        x = max(0, min(width - 1, round(float(fields[2]))))
        y = max(0, min(height - 1, height - 1 - round(float(fields[4]))))
        placed_ports.add(color_to_id[int(packed[y, x])])

    additions = []
    for province_id in sorted(expected_ports - placed_ports):
        color = id_to_color[province_id]
        ys, xs = np.where(packed == color)
        candidate = None
        for y, x in zip(ys, xs):
            for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                ny, nx = int(y + dy), int((x + dx) % width)
                if ny < 0 or ny >= height:
                    continue
                sea_id = color_to_id[int(packed[ny, nx])]
                if province_type[sea_id] == "sea":
                    candidate = (int(x), int(y), sea_id)
                    break
            if candidate:
                break
        if not candidate:
            raise RuntimeError(
                f"Province {province_id} needs a naval base but has no sea border"
            )
        x, y, sea_id = candidate
        z = height - 1 - y
        additions.append(
            f"{province_to_state[province_id]};naval_base;"
            f"{x:.2f};9.50;{z:.2f};0.00;{sea_id}"
        )

    if additions:
        if text and not text.endswith(("\n", "\r")):
            text += newline
        text += newline.join(additions) + newline
        write_text(path, text, bom)


def repair_x_crossings(province_map: np.ndarray) -> np.ndarray:
    packed = (
        province_map[:, :, 0].astype(np.uint32) << 16
        | province_map[:, :, 1].astype(np.uint32) << 8
        | province_map[:, :, 2].astype(np.uint32)
    )
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
    crossings = (
        (ordered[:, :, 0] != ordered[:, :, 1])
        & (ordered[:, :, 1] != ordered[:, :, 2])
        & (ordered[:, :, 2] != ordered[:, :, 3])
    )
    ys, xs = np.where(crossings)

    # Extend the upper-left province one pixel diagonally. This turns the
    # ambiguous four-corner junction into an unambiguous T junction.
    for y, x in zip(ys, xs):
        province_map[y + 1, x + 1] = province_map[y, x]
    return province_map


def main() -> None:
    current_ids = [
        int(line.split(";", 1)[0])
        for line in (ROOT / "map" / "definition.csv")
        .read_text(encoding="utf-8-sig")
        .splitlines()
        if line.split(";", 1)[0].isdigit()
    ]
    if max(current_ids) <= 21089:
        print("This map revision has already been repaired; no changes made.")
        return

    image_path = ROOT / "map" / "provinces.bmp"
    with Image.open(image_path) as image:
        province_map = np.array(image.convert("RGB"))
    province_map = repair_x_crossings(province_map)

    repair_state_files()
    repair_strategic_regions()
    repair_railways()
    repair_supply_nodes()
    repair_adjacencies()
    repair_unitstacks()
    repair_building_sea_references()
    repair_definition_and_coasts(province_map)
    split_disjointed_railways(province_map)
    ensure_port_buildings(province_map)

    Image.fromarray(province_map, mode="RGB").save(
        image_path,
        format="BMP",
        bitmap_format="bmp",
    )


if __name__ == "__main__":
    main()
