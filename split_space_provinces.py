"""Split the oversized space provinces at the top of provinces.bmp.

This is intentionally a one-shot migration.  It keeps the original province IDs,
adds the minimum twenty new IDs, and updates the map metadata that refers to the
split provinces.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
MAP = ROOT / "map"
PROVINCES = MAP / "provinces.bmp"
DEFINITION = MAP / "definition.csv"
UNITSTACKS = MAP / "unitstacks.txt"
BUILDINGS = MAP / "buildings.txt"
STATE_966 = ROOT / "history" / "states" / "966-Meogartha.txt"

REGIONS = {
    11874: MAP / "strategicregions" / "151-Outer Jublio System.txt",
    20847: MAP / "strategicregions" / "152-Flusion Orbit.txt",
    20850: MAP / "strategicregions" / "150-Inner Jublio System.txt",
    20851: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20852: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20853: MAP / "strategicregions" / "151-Outer Jublio System.txt",
    20854: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20855: MAP / "strategicregions" / "150-Inner Jublio System.txt",
    20856: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20857: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20858: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20859: MAP / "strategicregions" / "151-Outer Jublio System.txt",
    20860: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
    20861: MAP / "strategicregions" / "152-Flusion Orbit.txt",
    20862: MAP / "strategicregions" / "150-Inner Jublio System.txt",
    20863: MAP / "strategicregions" / "150-Inner Jublio System.txt",
    20864: MAP / "strategicregions" / "151-Outer Jublio System.txt",
    20865: MAP / "strategicregions" / "281-Giant Metallic Hearts of Iron Divider.txt",
}

SEA_CUTS = {
    20850: 317,
    20855: 318,
    20862: 317,
    20863: 318,
    20847: 317,
    20861: 318,
    20859: 317,
    20853: 318,
    11874: 317,
}
LAND_IDS = (20851, 20852, 20854, 20856, 20857, 20858, 20860, 20865)
TARGET_IDS = tuple(REGIONS)
EXPECTED_LAST_ID = 20951
FIRST_NEW_ID = EXPECTED_LAST_ID + 1
CHILDREN = {
    11874: [20952],
    20847: [20953],
    20850: [20954],
    20851: [20955],
    20852: [20956],
    20853: [20957],
    20854: [20958],
    20855: [20959],
    20856: [20960],
    20857: [20961],
    20858: [20962],
    20859: [20963],
    20860: [20964],
    20861: [20965],
    20862: [20966],
    20863: [20967],
    20864: [20968, 20969, 20970],
    20865: [20971],
}


@dataclass
class Piece:
    province_id: int
    mask: np.ndarray
    colour: tuple[int, int, int] | None = None

    @property
    def points(self) -> np.ndarray:
        return np.argwhere(self.mask)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        points = self.points
        return (
            int(points[:, 1].min()),
            int(points[:, 0].min()),
            int(points[:, 1].max()),
            int(points[:, 0].max()),
        )


def read_definitions(expected_last_id: int = EXPECTED_LAST_ID) -> tuple[list[list[str]], dict[int, list[str]]]:
    raw = DEFINITION.read_bytes()
    if b"\r\n" not in raw:
        raise RuntimeError("definition.csv must retain CRLF line endings")
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8")), delimiter=";"))
    by_id = {int(row[0]): row for row in rows if row}
    ids = sorted(by_id)
    if ids != list(range(expected_last_id + 1)):
        raise RuntimeError(f"definition.csv is not the expected contiguous 0..{expected_last_id} table")
    return rows, by_id


def encode_colours(array: np.ndarray) -> np.ndarray:
    widened = array.astype(np.uint32)
    return (widened[..., 0] << 16) | (widened[..., 1] << 8) | widened[..., 2]


def crossing_coordinates(array: np.ndarray, max_y: int = 514) -> set[tuple[int, int]]:
    """Return four-colour 2x2 corners, including the horizontal map seam."""
    encoded = encode_colours(array[:max_y])
    right = np.roll(encoded, -1, axis=1)
    a = encoded[:-1]
    b = right[:-1]
    c = encoded[1:]
    d = right[1:]
    crossing = (
        (a != b)
        & (a != c)
        & (a != d)
        & (b != c)
        & (b != d)
        & (c != d)
    )
    ys, xs = np.where(crossing)
    return set(zip(xs.astype(int), ys.astype(int)))


def choose_colour(used: set[tuple[int, int, int]], province_id: int) -> tuple[int, int, int]:
    value = (province_id * 0x9E3779B1) & 0xFFFFFF
    while True:
        colour = ((value >> 16) & 255, (value >> 8) & 255, value & 255)
        if colour not in used:
            used.add(colour)
            return colour
        value = (value + 0x010101) & 0xFFFFFF


def make_pieces(array: np.ndarray, definitions: dict[int, list[str]]) -> dict[int, list[Piece]]:
    pieces: dict[int, list[Piece]] = {}
    next_id = FIRST_NEW_ID

    for parent in TARGET_IDS:
        row = definitions[parent]
        colour = tuple(map(int, row[1:4]))
        source = np.all(array == colour, axis=2)
        ys, xs = np.where(source)
        if not len(xs):
            raise RuntimeError(f"Province {parent} has no pixels")

        if parent in SEA_CUTS:
            cut = SEA_CUTS[parent]
            top = source & (np.indices(source.shape)[0] < cut)
            bottom = source & (np.indices(source.shape)[0] >= cut)
            parent_pieces = [Piece(parent, bottom), Piece(next_id, top)]
            next_id += 1
        elif parent in LAND_IDS:
            split_x = (int(xs.min()) + int(xs.max()) + 1) // 2
            x_grid = np.indices(source.shape)[1]
            left = source & (x_grid < split_x)
            right = source & (x_grid >= split_x)
            parent_pieces = [Piece(parent, left), Piece(next_id, right)]
            next_id += 1
        elif parent == 20864:
            y_grid, x_grid = np.indices(source.shape)
            # Offset the upper and lower vertical cuts by one pixel.  This
            # prevents four provinces from meeting at a single corner.
            top_left = source & (y_grid < 318) & (x_grid < 3728)
            top_right = source & (y_grid < 318) & (x_grid >= 3728)
            bottom_left = source & (y_grid >= 318) & (x_grid < 3729)
            bottom_right = source & (y_grid >= 318) & (x_grid >= 3729)
            parent_pieces = [
                Piece(parent, bottom_right),
                Piece(next_id, top_left),
                Piece(next_id + 1, top_right),
                Piece(next_id + 2, bottom_left),
            ]
            next_id += 3
        else:
            raise AssertionError(parent)

        if any(not piece.mask.any() for piece in parent_pieces):
            raise RuntimeError(f"Province {parent} produced an empty piece")
        union = np.logical_or.reduce([piece.mask for piece in parent_pieces])
        if not np.array_equal(union, source):
            raise RuntimeError(f"Province {parent} split does not preserve all pixels")
        pieces[parent] = parent_pieces

    if next_id != FIRST_NEW_ID + 20:
        raise RuntimeError(f"Expected 20 new provinces, got {next_id - FIRST_NEW_ID}")
    return pieces


def load_existing_pieces(array: np.ndarray, definitions: dict[int, list[str]]) -> dict[int, list[Piece]]:
    pieces: dict[int, list[Piece]] = {}
    for parent, children in CHILDREN.items():
        group = []
        for province_id in [parent, *children]:
            row = definitions[province_id]
            colour = tuple(map(int, row[1:4]))
            mask = np.all(array == colour, axis=2)
            if not mask.any():
                raise RuntimeError(f"Province {province_id} has no pixels")
            group.append(Piece(province_id, mask, colour))
        pieces[parent] = group
    return pieces


def tighten_existing_splits(array: np.ndarray, definitions: dict[int, list[str]]) -> int:
    """Apply the stricter vertical limit demonstrated by the 1.19 engine log."""
    changed = 0
    for parent, cut in SEA_CUTS.items():
        child = CHILDREN[parent][0]
        parent_colour = tuple(map(int, definitions[parent][1:4]))
        child_colour = tuple(map(int, definitions[child][1:4]))
        child_mask = np.all(array == child_colour, axis=2)
        y_grid = np.indices(child_mask.shape)[0]
        move = child_mask & (y_grid >= cut)
        changed += int(move.sum())
        array[move] = parent_colour

    # Province 20864 has two upper pieces and staggered upper/lower x cuts.
    y_grid, x_grid = np.indices(array.shape[:2])
    for child in (20968, 20969):
        child_colour = tuple(map(int, definitions[child][1:4]))
        move = np.all(array == child_colour, axis=2) & (y_grid >= 318)
        left = move & (x_grid < 3729)
        right = move & (x_grid >= 3729)
        array[left] = tuple(map(int, definitions[20970][1:4]))
        array[right] = tuple(map(int, definitions[20864][1:4]))
        changed += int(move.sum())
    return changed


def nearest_pixel(piece: Piece, desired_x: float, desired_y: float) -> tuple[float, float]:
    points = piece.points
    distances = (points[:, 1] - desired_x) ** 2 + (points[:, 0] - desired_y) ** 2
    y, x = points[int(np.argmin(distances))]
    return float(x), float(y)


def remap_position(
    piece: Piece,
    source_bbox: tuple[int, int, int, int],
    source_x: float,
    source_y: float,
) -> tuple[float, float]:
    sx0, sy0, sx1, sy1 = source_bbox
    px0, py0, px1, py1 = piece.bbox
    nx = 0.5 if sx1 == sx0 else (source_x - sx0) / (sx1 - sx0)
    ny = 0.5 if sy1 == sy0 else (source_y - sy0) / (sy1 - sy0)
    desired_x = px0 + min(1.0, max(0.0, nx)) * (px1 - px0)
    desired_y = py0 + min(1.0, max(0.0, ny)) * (py1 - py0)
    return nearest_pixel(piece, desired_x, desired_y)


def update_unitstacks(pieces: dict[int, list[Piece]], height: int) -> int:
    raw = UNITSTACKS.read_bytes()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    trailing = raw.endswith((b"\n", b"\r"))
    lines = raw.decode("utf-8").splitlines()
    source_bbox = {parent: group[0].mask | np.logical_or.reduce([p.mask for p in group[1:]]) for parent, group in pieces.items()}
    bbox = {}
    for parent, mask in source_bbox.items():
        ys, xs = np.where(mask)
        bbox[parent] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

    output: list[str] = []
    added = 0
    for line in lines:
        fields = line.split(";")
        if len(fields) != 7 or not fields[0].isdigit() or int(fields[0]) not in pieces:
            output.append(line)
            continue
        parent = int(fields[0])
        source_x = float(fields[2])
        source_y = height - float(fields[4])
        for index, piece in enumerate(pieces[parent]):
            x, y = remap_position(piece, bbox[parent], source_x, source_y)
            new_fields = fields.copy()
            new_fields[0] = str(piece.province_id)
            new_fields[2] = f"{x:.2f}"
            new_fields[4] = f"{height - y:.2f}"
            output.append(";".join(new_fields))
            if index:
                added += 1
    data = eol.join(line.encode("utf-8") for line in output)
    if trailing:
        data += eol
    UNITSTACKS.write_bytes(data)
    return added


def update_buildings(pieces: dict[int, list[Piece]], height: int) -> int:
    raw = BUILDINGS.read_bytes()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    trailing = raw.endswith((b"\n", b"\r"))
    lines = raw.decode("utf-8").splitlines()
    changed = 0
    output: list[str] = []
    for line in lines:
        fields = line.split(";")
        if len(fields) != 7 or not fields[6].isdigit() or int(fields[6]) not in pieces:
            output.append(line)
            continue
        parent = int(fields[6])
        x = float(fields[2])
        y = height - float(fields[4])
        best_piece = min(
            pieces[parent],
            key=lambda piece: float(np.min((piece.points[:, 1] - x) ** 2 + (piece.points[:, 0] - y) ** 2)),
        )
        if best_piece.province_id != parent:
            fields[6] = str(best_piece.province_id)
            changed += 1
        output.append(";".join(fields))
    data = eol.join(line.encode("utf-8") for line in output)
    if trailing:
        data += eol
    BUILDINGS.write_bytes(data)
    return changed


def add_missing_space_ports(array: np.ndarray, definitions: dict[int, list[str]]) -> list[int]:
    """Give every coastal half of state 966 its own nudger naval-base position."""
    colour_to_id = {
        tuple(map(int, row[1:4])): province_id
        for province_id, row in definitions.items()
    }
    land_ids = set(LAND_IDS) | {child for parent in LAND_IDS for child in CHILDREN[parent]}
    raw = BUILDINGS.read_bytes()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    trailing = raw.endswith((b"\n", b"\r"))
    lines = raw.decode("utf-8").splitlines()

    covered: set[int] = set()
    insert_after = -1
    for index, line in enumerate(lines):
        fields = line.split(";")
        if len(fields) != 7 or fields[0] != "966" or fields[1] != "naval_base":
            continue
        insert_after = index
        x = min(array.shape[1] - 1, max(0, int(round(float(fields[2])))))
        y = min(array.shape[0] - 1, max(0, int(round(array.shape[0] - float(fields[4])))))
        province_id = colour_to_id.get(tuple(map(int, array[y, x])))
        if province_id in land_ids:
            covered.add(province_id)

    missing = sorted(land_ids - covered)
    if not missing:
        return []
    if insert_after < 0:
        raise RuntimeError("Could not find state 966 naval-base block in buildings.txt")

    added_lines = []
    for province_id in missing:
        colour = tuple(map(int, definitions[province_id][1:4]))
        mask = np.all(array == colour, axis=2)
        # Existing space ports sit at bitmap y=377 (map Z=2183), immediately
        # below the sea/land boundary. Pick the most central x where this
        # province occupies y=377 and a sea province occupies y=375.
        candidates = []
        for x in np.flatnonzero(mask[377]):
            adjacent_id = colour_to_id.get(tuple(map(int, array[375, x])))
            if adjacent_id is not None and definitions[adjacent_id][4] == "sea":
                candidates.append((int(x), adjacent_id))
        if not candidates:
            raise RuntimeError(f"No valid port/sea pair found for coastal province {province_id}")
        center_x = float(np.where(mask)[1].mean())
        x, adjacent_id = min(candidates, key=lambda item: abs(item[0] - center_x))
        added_lines.append(f"966;naval_base;{x:.2f};10.50;2183.00;-3.14;{adjacent_id}")

    lines[insert_after + 1:insert_after + 1] = added_lines
    data = eol.join(line.encode("utf-8") for line in lines)
    if trailing:
        data += eol
    BUILDINGS.write_bytes(data)
    return missing


def center_flagged_unitstacks(pieces: dict[int, list[Piece]]) -> int:
    flagged = {20963: {"9", "10", "38"}, 20965: {"10", "38"}}
    centers = {}
    for province_id in flagged:
        piece = next(piece for group in pieces.values() for piece in group if piece.province_id == province_id)
        points = piece.points
        mean_y, mean_x = points.mean(axis=0)
        centers[province_id] = nearest_pixel(piece, float(mean_x), float(mean_y))

    raw = UNITSTACKS.read_bytes()
    eol = b"\r\n" if b"\r\n" in raw else b"\n"
    trailing = raw.endswith((b"\n", b"\r"))
    lines = raw.decode("utf-8").splitlines()
    changed = 0
    output = []
    for line in lines:
        fields = line.split(";")
        if len(fields) == 7 and fields[0].isdigit():
            province_id = int(fields[0])
            if province_id in flagged and fields[1] in flagged[province_id]:
                x, y = centers[province_id]
                fields[2] = f"{x:.2f}"
                fields[4] = f"{2560 - y:.2f}"
                line = ";".join(fields)
                changed += 1
        output.append(line)
    data = eol.join(line.encode("utf-8") for line in output)
    if trailing:
        data += eol
    UNITSTACKS.write_bytes(data)
    return changed


def validate_map(array: np.ndarray, definitions: dict[int, list[str]]) -> dict[str, object]:
    height, width = array.shape[:2]
    ids = sorted(definitions)
    if ids != list(range(ids[-1] + 1)):
        raise RuntimeError("Province IDs are not contiguous")

    colours = [tuple(map(int, definitions[province_id][1:4])) for province_id in ids]
    if len(colours) != len(set(colours)):
        raise RuntimeError("definition.csv contains duplicate RGB colours")

    colour_codes = np.array(
        [(red << 16) | (green << 8) | blue for red, green, blue in colours],
        dtype=np.uint32,
    )
    colour_lut = np.full(1 << 24, -1, dtype=np.int32)
    colour_lut[colour_codes] = np.arange(len(ids), dtype=np.int32)
    encoded = encode_colours(array)
    pixel_ids = colour_lut[encoded]
    undefined_pixels = int(np.count_nonzero(pixel_ids < 0))
    if undefined_pixels:
        raise RuntimeError(f"provinces.bmp has {undefined_pixels} pixels with undefined colours")

    count = np.bincount(pixel_ids.ravel(), minlength=len(ids))
    # Province 0 is the engine's reserved sentinel definition and has no map pixels.
    missing = [province_id for province_id in np.flatnonzero(count == 0).astype(int).tolist() if province_id != 0]
    if missing:
        raise RuntimeError(f"Defined provinces with no pixels: {missing[:50]}")

    min_x = np.full(len(ids), width, dtype=np.int32)
    max_x = np.full(len(ids), -1, dtype=np.int32)
    min_y = np.full(len(ids), height, dtype=np.int32)
    max_y = np.full(len(ids), -1, dtype=np.int32)
    x_values = np.arange(width, dtype=np.int32)
    for y in range(height):
        row_ids = pixel_ids[y]
        np.minimum.at(min_x, row_ids, x_values)
        np.maximum.at(max_x, row_ids, x_values)
        np.minimum.at(min_y, row_ids, y)
        np.maximum.at(max_y, row_ids, y)
    spans_x = max_x - min_x + 1
    spans_y = max_y - min_y + 1
    # Empirical 1.19 limits from error.log: a 512-pixel-wide box and a
    # 319-pixel-tall box are rejected on this 4096x2560 map.
    oversized = np.flatnonzero((spans_x >= 512) | (spans_y >= 319)).astype(int).tolist()
    if oversized:
        details = {province_id: (int(spans_x[province_id]), int(spans_y[province_id])) for province_id in oversized}
        raise RuntimeError(f"Oversized province bounding boxes remain: {details}")

    new_ids = [child for children in CHILDREN.values() for child in children]
    too_small = [province_id for province_id in new_ids if count[province_id] <= 8]
    if too_small:
        raise RuntimeError(f"New provinces with too few pixels: {too_small}")

    # The BMP file header stores bits-per-pixel at byte offset 28.
    bmp = PROVINCES.read_bytes()
    bit_depth = int.from_bytes(bmp[28:30], "little")
    if bit_depth != 24:
        raise RuntimeError(f"provinces.bmp is {bit_depth}-bit instead of 24-bit RGB")

    return {
        "province_count": len(ids),
        "bitmap_size": [width, height],
        "bitmap_bit_depth": bit_depth,
        "undefined_bitmap_colours": 0,
        "definitions_without_pixels": 0,
        "oversized_provinces": [],
        "new_province_min_pixels": int(min(count[province_id] for province_id in new_ids)),
        "new_province_max_bbox": [
            int(max(spans_x[province_id] for province_id in new_ids)),
            int(max(spans_y[province_id] for province_id in new_ids)),
        ],
        "four_colour_corners_in_edited_band": len(crossing_coordinates(array)),
    }


def validate_metadata(definitions: dict[int, list[str]]) -> dict[str, object]:
    state_texts = [path.read_text(encoding="utf-8") for path in (ROOT / "history" / "states").glob("*.txt")]
    region_texts = [path.read_text(encoding="utf-8") for path in (MAP / "strategicregions").glob("*.txt")]
    land_children = {child for parent in LAND_IDS for child in CHILDREN[parent]}
    all_children = [child for children in CHILDREN.values() for child in children]

    bad_state_membership = {}
    bad_region_membership = {}
    for child in all_children:
        token = re.compile(rf"(?<!\d){child}(?!\d)")
        state_count = sum(len(token.findall(text)) for text in state_texts)
        region_count = sum(len(token.findall(text)) for text in region_texts)
        expected_state_count = 1 if child in land_children else 0
        if state_count != expected_state_count:
            bad_state_membership[child] = state_count
        if region_count != 1:
            bad_region_membership[child] = region_count
    if bad_state_membership:
        raise RuntimeError(f"Incorrect new-province state membership: {bad_state_membership}")
    if bad_region_membership:
        raise RuntimeError(f"Incorrect new-province strategic-region membership: {bad_region_membership}")

    unitstack_types: dict[int, list[str]] = {}
    for line in UNITSTACKS.read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        if len(fields) == 7 and fields[0].isdigit():
            unitstack_types.setdefault(int(fields[0]), []).append(fields[1])
    bad_unitstacks = {}
    for parent, children in CHILDREN.items():
        for child in children:
            if unitstack_types.get(child) != unitstack_types.get(parent):
                bad_unitstacks[child] = {
                    "parent": parent,
                    "parent_types": unitstack_types.get(parent),
                    "child_types": unitstack_types.get(child),
                }
    if bad_unitstacks:
        raise RuntimeError(f"New province unitstack rows do not match parents: {bad_unitstacks}")

    undefined_building_refs = []
    space_land_with_ports: set[int] = set()
    colour_to_id = {
        tuple(map(int, row[1:4])): province_id
        for province_id, row in definitions.items()
    }
    province_array = np.array(Image.open(PROVINCES))
    for line_number, line in enumerate(BUILDINGS.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.split(";")
        if len(fields) == 7 and fields[6].isdigit():
            reference = int(fields[6])
            if reference and reference not in definitions:
                undefined_building_refs.append((line_number, reference))
        if len(fields) == 7 and fields[0] == "966" and fields[1] == "naval_base":
            x = min(province_array.shape[1] - 1, max(0, int(round(float(fields[2])))))
            y = min(province_array.shape[0] - 1, max(0, int(round(province_array.shape[0] - float(fields[4])))))
            province_id = colour_to_id.get(tuple(map(int, province_array[y, x])))
            if province_id is not None:
                space_land_with_ports.add(province_id)
    if undefined_building_refs:
        raise RuntimeError(f"Undefined building province references: {undefined_building_refs[:50]}")
    expected_space_land = set(LAND_IDS) | {child for parent in LAND_IDS for child in CHILDREN[parent]}
    missing_space_ports = sorted(expected_space_land - space_land_with_ports)
    if missing_space_ports:
        raise RuntimeError(f"Coastal state 966 provinces without naval-base positions: {missing_space_ports}")

    return {
        "new_land_provinces_in_exactly_one_state": len(land_children),
        "new_sea_provinces_in_no_state": len(all_children) - len(land_children),
        "new_provinces_in_exactly_one_strategic_region": len(all_children),
        "new_provinces_with_parent_matching_unitstack_types": len(all_children),
        "undefined_building_province_references": 0,
        "coastal_space_land_provinces_with_port_positions": len(expected_space_land),
    }


def add_children_after_parent(path: Path, additions: dict[int, list[int]]) -> None:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    for parent, children in additions.items():
        pattern = re.compile(rf"(?<!\d){parent}(?!\d)")
        replacement = " ".join([str(parent), *(str(child) for child in children)])
        text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            raise RuntimeError(f"Expected one province-list reference to {parent} in {path}")
    path.write_bytes(text.encode("utf-8"))


def main() -> None:
    with DEFINITION.open("r", encoding="utf-8", newline="") as stream:
        current_last_id = int(list(csv.reader(stream, delimiter=";"))[-1][0])
    if current_last_id == 20971:
        rows, definitions = read_definitions(20971)
        image = Image.open(PROVINCES)
        array = np.array(image)
        before_crossings = crossing_coordinates(array)
        tightened_pixels = tighten_existing_splits(array, definitions)
        after_crossings = crossing_coordinates(array)
        introduced = sorted(after_crossings - before_crossings)
        if introduced:
            raise RuntimeError(f"Threshold correction introduces invalid corners: {introduced[:20]}")
        if tightened_pixels:
            Image.fromarray(array, "RGB").save(PROVINCES, format="BMP")
        pieces = load_existing_pieces(array, definitions)
        unitstack_text = UNITSTACKS.read_text(encoding="utf-8")
        already_updated = all(
            re.search(rf"(?m)^{child};", unitstack_text)
            for children in CHILDREN.values()
            for child in children
        )
        unitstack_rows_added = 0 if already_updated else update_unitstacks(pieces, image.height)
        building_refs_changed = update_buildings(pieces, image.height)
        ports_added = add_missing_space_ports(array, definitions)
        centered_unitstacks = center_flagged_unitstacks(pieces)
        validation = validate_map(array, definitions)
        metadata_validation = validate_metadata(definitions)
        print(json.dumps({
            "resumed_metadata": True,
            "unitstacks_already_updated": already_updated,
            "unitstack_rows_added": unitstack_rows_added,
            "building_references_changed": building_refs_changed,
            "pixels_shifted_for_engine_threshold": tightened_pixels,
            "port_positions_added_for_provinces": ports_added,
            "unitstack_positions_centered": centered_unitstacks,
            "validation": validation,
            "metadata_validation": metadata_validation,
        }, indent=2))
        return
    if current_last_id != EXPECTED_LAST_ID:
        raise RuntimeError(f"Unexpected last province ID {current_last_id}")

    rows, definitions = read_definitions()
    image = Image.open(PROVINCES)
    if image.mode != "RGB" or image.size != (4096, 2560):
        raise RuntimeError(f"Unexpected provinces.bmp format: {image.mode} {image.size}")
    array = np.array(image)
    before_crossings = crossing_coordinates(array)
    pieces = make_pieces(array, definitions)

    used = {tuple(map(int, row[1:4])) for row in rows if row}
    used.update(map(tuple, np.unique(array.reshape(-1, 3), axis=0).tolist()))
    new_rows: list[list[str]] = []
    additions: dict[int, list[int]] = {}
    for parent, group in pieces.items():
        additions[parent] = []
        for piece in group[1:]:
            piece.colour = choose_colour(used, piece.province_id)
            additions[parent].append(piece.province_id)
            source = definitions[parent]
            new_rows.append(
                [str(piece.province_id), *(str(value) for value in piece.colour), *source[4:]]
            )
            array[piece.mask] = piece.colour

    after_crossings = crossing_coordinates(array)
    introduced = sorted(after_crossings - before_crossings)
    if introduced:
        raise RuntimeError(f"Split introduces invalid four-province corners: {introduced[:20]}")

    # The original ID remains on group[0]; only child masks are recoloured.
    Image.fromarray(array, "RGB").save(PROVINCES, format="BMP")

    definition_lines = [";".join(row) for row in [*rows, *new_rows]]
    DEFINITION.write_bytes(("\r\n".join(definition_lines) + "\r\n").encode("utf-8"))

    land_additions = {parent: additions[parent] for parent in LAND_IDS}
    add_children_after_parent(STATE_966, land_additions)
    for region_path in sorted(set(REGIONS.values()), key=str):
        region_additions = {
            parent: additions[parent]
            for parent, path in REGIONS.items()
            if path == region_path
        }
        add_children_after_parent(region_path, region_additions)

    unitstack_rows_added = update_unitstacks(pieces, image.height)
    building_refs_changed = update_buildings(pieces, image.height)
    ports_added = add_missing_space_ports(array, {**definitions, **{int(row[0]): row for row in new_rows}})
    centered_unitstacks = center_flagged_unitstacks(pieces)

    summary = {
        "new_ids": [row[0] for row in new_rows],
        "new_provinces": len(new_rows),
        "unitstack_rows_added": unitstack_rows_added,
        "building_references_changed": building_refs_changed,
        "port_positions_added_for_provinces": ports_added,
        "unitstack_positions_centered": centered_unitstacks,
        "preexisting_crossings_in_edited_band": len(before_crossings),
        "crossings_after_split_in_edited_band": len(after_crossings),
        "pieces": {
            str(parent): [
                {"id": piece.province_id, "bbox": piece.bbox, "pixels": int(piece.mask.sum())}
                for piece in group
            ]
            for parent, group in pieces.items()
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
