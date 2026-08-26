"""Reorganize Legacy of Kattail interface assets by ownership.

The script is deliberately opt-in: without ``--apply`` it only audits the
current interface tree.  Applying the migration preserves active definition
blocks and their identifiers while replacing catch-all filenames with
ownership-oriented files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "interface"
REPORT_DEFAULT = ROOT / "modding_documentation" / "interface_migration_report.json"

DEF_START = re.compile(
    r"(?m)^[ \t]*(?!#)(?:spriteType|SpriteType|frameAnimatedSpriteType)\s*=\s*\{"
)
NAME = re.compile(r'\bname\s*=\s*"([^"]+)"')
TEXTURE = re.compile(r'(?mi)\btexturefile\s*=\s*"([^"]+)"')


def block_hash(block: str) -> str:
    # Formatting-only changes must not make the active-definition audit fail.
    # Full-line comments are also ignored because section labels are layout.
    content = "\n".join(
        line for line in block.replace("\r\n", "\n").replace("\r", "\n").splitlines()
        if not line.lstrip().startswith("#")
    )
    normalized = re.sub(r"\s+", " ", content).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    bom = "\ufeff" if raw.startswith(b"\xef\xbb\xbf") else ""
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return text, newline


def write_text(path: Path, text: str, newline: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
    path.write_bytes(text.encode("utf-8"))


def balanced_block(text: str, start: int) -> tuple[str, int]:
    opening = text.find("{", start)
    depth = 0
    quote = False
    escaped = False
    index = opening
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = False
        elif char == '"':
            quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1], index + 1
        index += 1
    raise ValueError(f"unbalanced definition beginning at offset {start}")


def definitions_from_text(text: str, source: str) -> list[dict[str, str]]:
    result = []
    cursor = 0
    for match in DEF_START.finditer(text):
        if match.start() < cursor:
            continue
        block, cursor = balanced_block(text, match.start())
        active_block = "\n".join(
            line for line in block.splitlines() if not line.lstrip().startswith("#")
        )
        name = NAME.search(active_block)
        if not name:
            continue
        result.append(
            {
                "name": name.group(1),
                "block": block.strip(),
                "texture": (TEXTURE.search(block).group(1) if TEXTURE.search(block) else ""),
                "source": source,
            }
        )
    return result


def definitions(path: Path) -> list[dict[str, str]]:
    text, _ = read_text(path)
    return definitions_from_text(text, str(path.relative_to(ROOT)))


def active_definitions(path: Path) -> list[dict[str, str]]:
    return definitions(path) if path.exists() else []


def target_file(name: str, blocks: list[dict[str, str]], header: str = "") -> tuple[Path, str]:
    if not blocks:
        raise ValueError(f"no active definitions assigned to {name}")
    newline = "\r\n"
    if all("\r\n" not in block["block"] for block in blocks):
        newline = "\n"
    body = ["spriteTypes = {", ""]
    if header:
        body.extend(header.splitlines())
        body.append("")
    body.extend(block["block"] for block in blocks)
    body.extend(["", "}", ""])
    return INTERFACE / name, newline.join(body)


def file_inventory() -> dict:
    files = []
    names = []
    for path in sorted(INTERFACE.rglob("*.gfx")):
        text, _ = read_text(path)
        defs = active_definitions(path)
        files.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "active_definition_count": len(defs),
                "balanced": text.count("{") == text.count("}"),
            }
        )
        for definition in defs:
            names.append(
                {
                    "name": definition["name"],
                    "source": definition["source"],
                    "texture": definition["texture"],
                }
            )
    duplicate_names = {
        name: entries
        for name, entries in _group_by_name(names).items()
        if len(entries) > 1
    }
    return {
        "gfx_file_count": len(files),
        "active_definition_count": len(names),
        "unique_definition_count": len({entry["name"] for entry in names}),
        "duplicate_definition_names": duplicate_names,
        "definition_fingerprints": [
            {
                "name": entry["name"],
                "texture": entry["texture"],
                "sha256": block_hash(entry["block"]),
            }
            for path in sorted(INTERFACE.rglob("*.gfx"))
            for entry in active_definitions(path)
        ],
        "files": files,
    }


def head_definition_fingerprints() -> list[dict[str, str]]:
    git = shutil.which("git") or r"C:\Users\elowi\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
    paths = subprocess.check_output(
        [git, "ls-tree", "-r", "--name-only", "HEAD", "interface"], cwd=ROOT, text=True
    ).splitlines()
    result = []
    for relative in paths:
        if not relative.endswith(".gfx"):
            continue
        raw = subprocess.check_output([git, "show", f"HEAD:{relative}"], cwd=ROOT)
        text = raw.decode("utf-8-sig")
        for entry in definitions_from_text(text, relative):
            result.append(
                {
                    "name": entry["name"],
                    "texture": entry["texture"],
                    "sha256": block_hash(entry["block"]),
                }
            )
    return result


def effective_winners_current() -> dict[str, str]:
    winners = {}
    for path in sorted(INTERFACE.rglob("*.gfx"), key=lambda item: str(item.relative_to(ROOT)).lower()):
        for entry in active_definitions(path):
            winners[entry["name"]] = block_hash(entry["block"])
    return winners


def effective_winners_head() -> dict[str, str]:
    git = shutil.which("git") or r"C:\Users\elowi\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
    paths = subprocess.check_output(
        [git, "ls-tree", "-r", "--name-only", "HEAD", "interface"], cwd=ROOT, text=True
    ).splitlines()
    winners = {}
    for relative in sorted((path for path in paths if path.endswith(".gfx")), key=str.lower):
        raw = subprocess.check_output([git, "show", f"HEAD:{relative}"], cwd=ROOT)
        for entry in definitions_from_text(raw.decode("utf-8-sig"), relative):
            winners[entry["name"]] = block_hash(entry["block"])
    return winners


def _group_by_name(entries: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["name"]].append(entry)
    return dict(grouped)


def write_grouped(path_name: str, blocks: list[dict], header: str) -> None:
    path, text = target_file(path_name, blocks, header)
    if path.exists():
        raise FileExistsError(f"migration target already exists: {path}")
    newline = "\r\n" if "\r\n" in blocks[0]["block"] else "\n"
    write_text(path, text, newline)


def source_order(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: str(path.relative_to(ROOT)).lower())


def country_tags() -> set[str]:
    result = set()
    for path in (ROOT / "common" / "countries").glob("*"):
        if path.is_file() and re.fullmatch(r"[A-Z]{3}", path.stem):
            result.add(path.stem)
    return result


def apply_migration() -> None:
    tags = country_tags()
    all_sources = []
    for path in sorted(INTERFACE.rglob("*.gfx")):
        all_sources.extend(active_definitions(path))

    # Split the mixed idea library and every existing country idea library by
    # the country tag embedded in the sprite identifier.
    idea_sources = [INTERFACE / "lok_ideas.gfx"] + source_order(
        [path for path in INTERFACE.glob("*_lok_ideas.gfx") if path.name != "lok_ideas.gfx"]
    )
    idea_groups: dict[str, list[dict]] = defaultdict(list)
    for path in idea_sources:
        for definition in active_definitions(path):
            match = re.match(r"GFX_idea_([A-Za-z]{3})_", definition["name"])
            tag = match.group(1).upper() if match else ""
            if tag in tags:
                idea_groups[f"lok_country_{tag}_ideas.gfx"].append(definition)
            else:
                idea_groups["lok_shared_ideas.gfx"].append(definition)
    for name, blocks in sorted(idea_groups.items()):
        write_grouped(name, blocks, "# Reorganized by content ownership.")
    for path in idea_sources:
        path.unlink()

    # Split focus icons by the tag prefix used by the focus identifier.
    focus_source = INTERFACE / "lok_national_focus_icons.gfx"
    focus_groups: dict[str, list[dict]] = defaultdict(list)
    for definition in active_definitions(focus_source):
        match = re.match(r"([A-Z]{3})_", definition["name"])
        if match and match.group(1) in tags:
            target = f"lok_country_{match.group(1)}_focus_icons.gfx"
        else:
            target = "lok_shared_focus_icons.gfx"
        focus_groups[target].append(definition)
    for name, blocks in sorted(focus_groups.items()):
        write_grouped(name, blocks, "# Reorganized by content ownership.")
    focus_source.unlink()

    # Split leader portraits by the tag in the portrait name or texture path;
    # the two template entries and any otherwise unassigned portrait remain
    # in a shared library.
    portrait_source = INTERFACE / "lok_leader_portraits.gfx"
    portrait_groups: dict[str, list[dict]] = defaultdict(list)
    for definition in active_definitions(portrait_source):
        match = re.match(r"GFX_portrait_([A-Z]{3})_", definition["name"])
        path_match = re.search(r"(?:leaders|interface/ministers)/([A-Z]{3})/", definition["texture"])
        tag = match.group(1) if match else (path_match.group(1) if path_match else "")
        target = f"lok_country_{tag}_portraits.gfx" if tag in tags else "lok_shared_leader_portraits.gfx"
        portrait_groups[target].append(definition)
    for name, blocks in sorted(portrait_groups.items()):
        write_grouped(name, blocks, "# Reorganized by content ownership.")
    portrait_source.unlink()

    # Categorize every active block in the former miscellaneous sprite file.
    misc_source = INTERFACE / "lok_misc_icons.gfx"
    misc_groups: dict[str, list[dict]] = defaultdict(list)
    for definition in active_definitions(misc_source):
        name = definition["name"]
        if name.startswith(("GFX_lok_actor_opinion", "GFX_lok_parliament", "GFX_lok_political_orientation")):
            target = "lok_system_parliament.gfx"
        elif name.startswith("GFX_decision_"):
            target = "lok_system_decisions.gfx"
        elif name == "GFX_LOK_armored_blimp_carrier_modifier":
            target = "lok_system_state_modifiers.gfx"
        elif name == "GFX_TAK_petite_charles_state_modifier":
            target = "lok_country_TAK_modifiers.gfx"
        elif name == "GFX_icon_private_sector_button":
            target = "lok_system_private_sector.gfx"
        elif name.startswith(("GFX_LOK_species_", "GFX_lok_species_")) or name == "GFX_idea_slot_species":
            target = "lok_system_species.gfx"
        elif name.startswith("GFX_navalcombat_") or name.startswith("GFX_unit_"):
            target = "lok_shared_unit_icons.gfx"
        elif name == "GFX_ktz_focus_tree_map_bg":
            target = "lok_system_ktz_focus_tree_map.gfx"
        elif name.startswith("GFX_autonomy_"):
            target = "lok_shared_autonomy.gfx"
        elif name in {"GFX_tall_build_slot_bg", "GFX_energy_icon"}:
            target = "lok_system_state_view.gfx"
        elif name in {"GFX_anarchy_picture", "GFX_unowned_picture", "GFX_water_picture"}:
            target = "lok_system_anarchy_view.gfx"
        elif name.startswith("GFX_planet_"):
            target = "lok_system_planet_data_view.gfx"
        elif name.startswith("GFX_lok_state_actions_"):
            target = "lok_system_state_actions.gfx"
        elif name.startswith("GFX_terrain_"):
            target = "lok_shared_terrain.gfx"
        elif name.startswith("GFX_death_counter_"):
            target = "lok_system_death_counter.gfx"
        elif name.startswith("GFX_food_"):
            target = "lok_system_food_tracker.gfx"
        elif name.startswith("GFX_nuke_counter") or name in {"GFX_salvo_capacity_icon", "GFX_thermonuclear_salvo_button"}:
            target = "lok_system_nuke_tracker.gfx"
        elif name == "GFX_soot_counter_icon":
            target = "lok_system_soot_tracker.gfx"
        elif name == "GFX_radiation_counter_icon":
            target = "lok_system_radiation_counter.gfx"
        elif name.startswith("GFX_ideology_"):
            target = "lok_system_ideologies.gfx"
        elif name == "GFX_space_techtree_bg":
            target = "lok_system_space.gfx"
        elif name.startswith("GFX_bookmark_"):
            target = "lok_shared_bookmarks.gfx"
        elif name.startswith("GFX_excapature_industries"):
            target = "lok_system_economy.gfx"
        elif name.endswith("_medium"):
            if any(token in name.lower() for token in ("nuke", "nuclear", "solar_power", "fusion", "antimatter", "mondkanone")):
                target = "lok_system_nuclear.gfx"
            else:
                target = "lok_shared_technology_icons.gfx"
        elif name in {"GFX_Meogartha_Sprite", "GFX_Stateview_Overlay"}:
            target = "lok_system_novelty_views.gfx"
        else:
            raise ValueError(f"unclassified active miscellaneous sprite: {name}")
        misc_groups[target].append(definition)

    # Append the existing specialist unit library to the new shared unit file.
    specialist_source = INTERFACE / "paluush_specialist_unit_icons.gfx"
    misc_groups["lok_shared_unit_icons.gfx"].extend(active_definitions(specialist_source))

    # These two existing libraries now share the ownership files created from
    # the former miscellaneous library.  Keep the old source order: the
    # Parliament file preceded lok_misc_icons, while species_icon followed it
    # in the case-insensitive interface filename order.
    parliament_source = INTERFACE / "LOK_parliament_gui.gfx"
    misc_groups["lok_system_parliament.gfx"] = active_definitions(parliament_source) + misc_groups["lok_system_parliament.gfx"]
    species_source = INTERFACE / "species_icon.gfx"
    misc_groups["lok_system_species.gfx"].extend(active_definitions(species_source))
    for name, blocks in sorted(misc_groups.items()):
        write_grouped(name, blocks, "# Reorganized from the former miscellaneous interface library.")
    misc_source.unlink()
    specialist_source.unlink()
    parliament_source.unlink()
    species_source.unlink()

    # Merge the walker designer and walker text-icon libraries.  The role
    # sprite remains a separate explicit late-loading override below.
    walker_sources = [INTERFACE / "LOK_tank_designer_icons.gfx", INTERFACE / "LOK_walker_texticons.gfx"]
    walker_text = "\n\n".join(read_text(path)[0].rstrip() for path in walker_sources) + "\n"
    write_text(INTERFACE / "lok_system_walker.gfx", walker_text, "\n")
    for path in walker_sources:
        path.unlink()

    # Existing file names whose content has a single clear owner.  GUI
    # internals are intentionally untouched; only automatic load filenames
    # change.
    renames = {
        "LOK_alert_scripted_gui.gfx": "lok_system_alerts.gfx",
        "LOK_alert_scripted_gui.gui": "lok_system_alerts.gui",
        "LOK_parliament_gui.gui": "lok_system_parliament.gui",
        "TAI_estates.gfx": "lok_country_TAI_estates.gfx",
        "TAI_estates.gui": "lok_country_TAI_estates.gui",
        "lok_aka_year.gui": "lok_system_aka_year.gui",
        "lok_anarchy_view.gui": "lok_system_anarchy_view.gui",
        "lok_coring_threshold.gui": "lok_system_coring_threshold.gui",
        "lok_death_counter.gui": "lok_system_death_counter.gui",
        "lok_decision_guis.gui": "lok_system_ipf_ksk.gui",
        "lok_economy_laws.gfx": "lok_system_economy_laws.gfx",
        "lok_eventpictures.gfx": "lok_shared_event_pictures.gfx",
        "lok_food_tracker.gui": "lok_system_food_tracker.gui",
        "lok_generic_species_portraits.gfx": "lok_shared_species_portraits.gfx",
        "lok_ideology_info.gui": "lok_system_ideology_info.gui",
        "lok_ktz_focus_tree_map.gui": "lok_system_ktz_focus_tree_map.gui",
        "lok_music_station.gui": "lok_system_music_station.gui",
        "lok_nuke_tracker.gui": "lok_system_nuke_tracker.gui",
        "lok_planet_data_view.gui": "lok_system_planet_data_view.gui",
        "lok_private_sector.gui": "lok_system_private_sector.gui",
        "lok_radiation_counter.gui": "lok_system_radiation_counter.gui",
        "lok_shitpost_guis.gui": "lok_system_novelty_views.gui",
        "lok_soot_tracker.gui": "lok_system_soot_tracker.gui",
        "lok_state_actions.gui": "lok_system_state_actions.gui",
        "lok_state_culture.gui": "lok_system_state_culture.gui",
        "lok_state_productivity.gui": "lok_system_state_productivity.gui",
        "lok_thermonuclear_salvo.gui": "lok_system_thermonuclear_salvo.gui",
        "species_icon.gui": "lok_system_species.gui",
        "stratres_icon.gfx": "lok_system_strategic_resources.gfx",
        "stratres_icon.gui": "lok_system_strategic_resources.gui",
        "wonder_icon.gfx": "lok_system_wonders.gfx",
        "wonder_icon.gui": "lok_system_wonders.gui",
        "LOK_special_project_icons.gfx": "lok_system_special_projects.gfx",
        "lok_countrypoliticsview.gfx": "lok_system_ideology_info.gfx",
    }
    for old_name, new_name in renames.items():
        old = INTERFACE / old_name
        new = INTERFACE / new_name
        if not old.exists():
            raise FileNotFoundError(old)
        if new.exists():
            raise FileExistsError(new)
        old.rename(new)

    # Make the already-late role replacement explicit without changing the
    # sprite name GFX_rocket used by the tank designer.
    role_old = INTERFACE / "zz_LOK_walker_role.gfx"
    role_new = INTERFACE / "zzz_lok_override_walker_role.gfx"
    role_old.rename(role_new)

    # Replace-folder content is a deliberate override, not a magical source
    # of definitions.  Keep each override in a clearly named final-load file.
    replace_source = INTERFACE / "replace" / "lok_general_stuff.gfx"
    replace_groups = defaultdict(list)
    for definition in active_definitions(replace_source):
        target = (
            "zzz_lok_override_idea_categories.gfx"
            if definition["name"] == "GFX_idea_categories"
            else "zzz_lok_override_resources.gfx"
        )
        replace_groups[target].append(definition)
    for name, blocks in sorted(replace_groups.items()):
        write_grouped(name, blocks, "# Explicit late-loading override; preserve the vanilla sprite identifier.")
    replace_source.unlink()
    try:
        (INTERFACE / "replace").rmdir()
    except OSError:
        pass

    # These files contain comments only and no active interface definitions.
    # They are removed only after the active-definition parser has proven that
    # they cannot affect runtime loading.
    for legacy in (INTERFACE / "lok_FRA.gfx", INTERFACE / "lok_FRA.gui"):
        if legacy.exists():
            text, _ = read_text(legacy)
            if not active_definitions(legacy) and not re.search(r"(?m)^[ \t]*(?:containerWindowType|windowType|instantTextboxType)\s*=", text):
                legacy.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply the ownership migration")
    parser.add_argument("--compare-head", action="store_true", help="compare active GFX definition blocks with HEAD")
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT, help="JSON inventory output path")
    args = parser.parse_args()

    before = file_inventory()
    if args.apply:
        apply_migration()
    after = file_inventory()
    if args.compare_head:
        current = Counter(
            (entry["name"], entry["texture"], entry["sha256"])
            for entry in after["definition_fingerprints"]
        )
        head = Counter(
            (entry["name"], entry["texture"], entry["sha256"])
            for entry in head_definition_fingerprints()
        )
        if current != head:
            print("definition fingerprint mismatch")
            print("missing from current:", list((head - current).elements())[:20])
            print("extra in current:", list((current - head).elements())[:20])
            raise SystemExit(1)
        print("active GFX definition fingerprint comparison with HEAD: PASS")
        current_winners = effective_winners_current()
        head_winners = effective_winners_head()
        if current_winners != head_winners:
            changed = sorted(
                name for name in set(current_winners) | set(head_winners)
                if current_winners.get(name) != head_winners.get(name)
            )
            print("lexical final-definition winners changed:", changed[:20])
            raise SystemExit(1)
        print("lexical final-definition winner comparison with HEAD: PASS")
    report = {"before": before, "after": after}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "applied": args.apply,
        "before_gfx_files": before["gfx_file_count"],
        "after_gfx_files": after["gfx_file_count"],
        "before_active_definitions": before["active_definition_count"],
        "after_active_definitions": after["active_definition_count"],
        "before_duplicates": len(before["duplicate_definition_names"]),
        "after_duplicates": len(after["duplicate_definition_names"]),
        "report": str(args.report),
    }, indent=2))


if __name__ == "__main__":
    main()
