"""Inventory and migrate the mod's English localisation ownership.

This tool intentionally treats localisation as line-oriented Clausewitz data. It
preserves the text inside quoted values verbatim, including escaped tokens and
formatting. It does not rewrite localisation keys or values.

Usage:
    localization_migration.py inventory --root PATH --output PATH
    localization_migration.py migrate --root PATH --output PATH

The migration output is a staging directory. The caller must compare its
manifest with the source before replacing files in the working tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+):\s*(\d*)\s*\"")
HEADER_RE = re.compile(r"^\s*(?:\ufeff)?l_english:\s*$")
TAG_PREFIX_RE = re.compile(r"^([A-Z]{3})(?:_|\.)")
TAG_EXACT_RE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class Entry:
    source: str
    line: int
    key: str
    raw: str
    value: str
    order: int


@dataclass(frozen=True)
class Malformed:
    source: str
    line: int
    raw: str
    key: str | None


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def parse_entry(line: str) -> tuple[str, str] | None:
    match = KEY_RE.match(line)
    if not match:
        return None
    key = match.group(1)
    opening = match.end() - 1
    escaped = False
    closing = None
    for index in range(opening + 1, len(line)):
        char = line[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            closing = index
    if closing is None:
        return None
    trailing = line[closing + 1 :].strip()
    if trailing and not trailing.startswith("#"):
        return None
    return key, line[opening + 1 : closing]


def looks_like_localisation(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped and not stripped.startswith("#") and ":" in stripped and not HEADER_RE.match(stripped))


def scan(root: Path) -> tuple[list[Entry], list[Malformed], list[str]]:
    entries: list[Entry] = []
    malformed: list[Malformed] = []
    files: list[str] = []
    order = 0
    loc_root = root / "localisation" / "english"
    for path in sorted(loc_root.rglob("*.yml"), key=lambda p: rel(p, root)):
        source = rel(path, root)
        files.append(source)
        text = path.read_text(encoding="utf-8-sig")
        for line_number, line in enumerate(text.splitlines(), 1):
            parsed = parse_entry(line)
            if parsed:
                key, value = parsed
                entries.append(Entry(source, line_number, key, line, value, order))
                order += 1
            elif looks_like_localisation(line):
                prefix = re.match(r"^\s*([A-Za-z0-9_.-]+):", line)
                malformed.append(Malformed(source, line_number, line, prefix.group(1) if prefix else None))
    return entries, malformed, files


def duplicate_report(entries: Iterable[Entry]) -> dict:
    by_key: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        by_key[entry.key].append(entry)
    duplicates = {key: values for key, values in by_key.items() if len(values) > 1}
    exact = sum(1 for values in duplicates.values() if len({v.value for v in values}) == 1)
    conflicting = len(duplicates) - exact
    same_file = sum(1 for values in duplicates.values() if len({v.source for v in values}) == 1)
    ordinary_replace = sum(
        1
        for values in duplicates.values()
        if any("/replace/" in v.source for v in values) and any("/replace/" not in v.source for v in values)
    )
    return {
        "duplicate_key_count": len(duplicates),
        "duplicate_definition_count": sum(len(values) - 1 for values in duplicates.values()),
        "exact_value_duplicate_key_count": exact,
        "conflicting_duplicate_key_count": conflicting,
        "same_file_duplicate_key_count": same_file,
        "ordinary_vs_replace_duplicate_key_count": ordinary_replace,
        "keys": {
            key: [asdict(value) for value in values]
            for key, values in sorted(duplicates.items())
        },
    }


def tags_from_repository(root: Path, entries: Iterable[Entry]) -> set[str]:
    tags: set[str] = set()
    for path in (root / "common" / "countries").glob("*.txt"):
        if TAG_EXACT_RE.match(path.stem):
            tags.add(path.stem)
    for path in (root / "history" / "countries").glob("*.txt"):
        match = re.match(r"([A-Z]{3})\s", path.name)
        if match:
            tags.add(match.group(1))
    country_sources = {"countries", "parties", "characters", "ideas", "lok_traits"}
    for entry in entries:
        if source_stem(entry.source).lower() not in country_sources:
            continue
        match = TAG_PREFIX_RE.match(entry.key)
        if match and match.group(1) != "LOK":
            tags.add(match.group(1))
    return tags


def source_stem(source: str) -> str:
    return Path(source).stem.removesuffix("_l_english")


def country_from_key(key: str, tags: set[str]) -> str | None:
    if TAG_EXACT_RE.match(key) and key in tags:
        return key
    match = TAG_PREFIX_RE.match(key)
    if match and match.group(1) in tags:
        return match.group(1)
    return None


def country_file(tag: str) -> str:
    return f"localisation/english/lok_country_{tag}_l_english.yml"


def system_file(name: str) -> str:
    return f"localisation/english/lok_system_{name}_l_english.yml"


def shared_file(name: str) -> str:
    return f"localisation/english/lok_shared_{name}_l_english.yml"


def world_file(name: str) -> str:
    return f"localisation/english/lok_world_{name}_l_english.yml"


def replace_file(source: str) -> str:
    path = Path(source)
    stem = source_stem(source).lower()
    if not stem.startswith("lok_"):
        stem = "lok_" + stem
    return (path.parent / f"{stem}_l_english.yml").as_posix()


def explicit_source_destination(source: str) -> str | None:
    stem = source_stem(source).lower()
    if "/replace/" in source:
        return replace_file(source)
    if source.startswith("localisation/english/localized_state_names/"):
        suffix = Path(source).stem.removesuffix("_l_english").lower()
        return f"localisation/english/localized_state_names/lok_world_{suffix}_l_english.yml"
    if source.startswith("localisation/english/name_lists/"):
        return shared_file("name_lists")
    fixed = {
        "anarchy_countries": world_file("countries"),
        "factions": shared_file("factions"),
        "equip_air": shared_file("equipment"),
        "equip_naval": shared_file("equipment"),
        "equipment": shared_file("equipment"),
        "loading_tips": shared_file("loading_tips"),
        "lok_ideologies": system_file("ideologies"),
        "lok_ideas": shared_file("ideas"),
        "lok_traits": shared_file("traits"),
        "lok_culture": system_file("culture"),
        "lok_fiscal_capacity": system_file("fiscal_capacity"),
        "lok_great_game": system_file("great_game"),
        "lok_parliament": system_file("parliament"),
        "lok_map_mode": system_file("map_modes"),
        "species": world_file("species"),
        "state_names": world_file("states"),
        "strategic_region_names": world_file("strategic_regions"),
        "strategic_resources": world_file("resources"),
        "victory_points": world_file("victory_points"),
        "wonders": system_file("wonders"),
        "lok_cityfall_news": system_file("news"),
        "lok_news": system_file("news"),
        "lok_generic": shared_file("tooltips"),
        "hyp_events": country_file("HYP"),
        "kus_nek_war": system_file("kus_nek_war"),
        "roq_reclamation": country_file("ROQ"),
        "plr_expedition": country_file("PLR"),
        "lok_gal_events": country_file("GAL"),
        "lok_gal_ideas": country_file("GAL"),
    }
    return fixed.get(stem)


def classify_misc(key: str, source: str, tags: set[str]) -> str:
    country = country_from_key(key, tags)
    if country:
        return country_file(country)
    stem = source_stem(source)
    if stem == "LOK_Extremadoughria":
        return system_file("extremadoughria")
    if stem == "LOK_decisions":
        lowered = key.lower()
        if key.startswith("ROQ_"):
            return country_file("ROQ")
        if lowered.startswith(("lok_food", "country_food", "food_")) or "food" in lowered:
            return system_file("food")
        if lowered.startswith(("lok_katzen_high_command", "lok_high_command", "leader_is_")) or key.startswith("LOK_high_command"):
            return system_file("katzen_high_command")
        if lowered.startswith(("herzlands", "reunite_herzlands", "reduce_herzland", "has_herzland", "move_capital_to_katown", "fix_collapse", "drive_nmi_away")):
            return system_file("herzlands_unification")
        if lowered.startswith(("lok_peace", "decide_fate", "return_occupied", "nation_content", "show_potential", "lok_noncore", "state_core_threshold")):
            return system_file("peace_occupation")
        if lowered.startswith(("lok_space", "space_", "orbital_", "flusion_exp", "muno_exp", "xenon_exp", "lok_survey", "lok_colonize", "lok_build_up_xenon", "lok_prepare_xenon", "lok_xenon", "xenon_landing")):
            return system_file("space_program")
        if lowered.startswith("lok_power_grid") or lowered.startswith("lok_show_") or lowered.startswith("lok_hide_") or lowered.startswith("lok_decommission_"):
            return system_file("power_grid")
        if lowered.startswith(("equip_", "lok_restore_blimp", "lok_build_armored_blimp")):
            return system_file("equipment_programmes")
        if lowered.startswith(("decision_cost_", "LOK_".lower())) and "food" not in lowered:
            return shared_file("decisions")
        return shared_file("decisions")
    if stem == "lok_misc":
        lowered = key.lower()
        if key.startswith("LOK_tutorial"):
            return system_file("tutorial")
        if key.startswith("LOK_country_intro") or key.startswith("BK_"):
            return system_file("country_intro")
        if key.startswith("LOK_herzlands") or lowered.startswith("herzlands_"):
            return system_file("herzlands_unification")
        if lowered.startswith(("lok_space", "space_", "xenon_", "muno_", "lok_seize_the_mondkanone")):
            return system_file("space_program")
        if lowered.startswith(("lok_food", "country_food", "modifier_production_speed_food", "food_")) or "food" in lowered:
            return system_file("food")
        if lowered.startswith(("lok_nuke", "lok_fission", "lok_fusion", "lok_cobalt", "lok_mondkanone", "lok_sturmer", "nuclear_")) or "nuke" in lowered:
            return system_file("nuclear_program")
        if lowered.startswith(("lok_state_actions", "lok_state_productivity", "lok_state_death", "lok_country_death", "lok_global_death", "lok_radiation", "lok_coring")):
            return system_file("state_management")
        if lowered.startswith(("lok_ipf", "lok_ksk", "ipf_", "ksk_", "katlinin", "meowrius", "raid_ksk", "concessions_to_", "censor_the_", "shoot_the_", "look_for_", "try_to_kill_")):
            return system_file("ipf_ksk")
        if lowered.startswith(("lok_economy", "lok_centrally", "lok_decentralized", "lok_cybernetic", "lok_market", "lok_social_market", "lok_mixed", "lok_corporatist", "lok_laissez", "lok_free_market", "lok_household", "lok_tribal", "lok_war_chief", "lok_mastery", "economy_laws", "lok_ps_")):
            return system_file("economy")
        if lowered.startswith(("lok_puppet", "dynamic_puppet", "unique_puppet")):
            return system_file("puppet_management")
        if lowered.startswith(("ant arctic".replace(" ", ""), "grand_canal", "pink_sea", "blasterian", "ezikatzen", "fishy_pass", "bog_river", "mog_river", "herzlands_solkatzia", "solkatzia", "solakea_strait", "norwegen", "auralia", "purrlin", "arlenisk", "kotijgrad", "barnsems", "new_kastra", "bridge_", "canal_")):
            return system_file("map_infrastructure")
        if lowered.startswith(("lok_notification", "lok_music")):
            return system_file("notifications")
        if lowered.startswith("ktz_"):
            return country_file("KTZ")
        if lowered.startswith("decision_cost_"):
            return shared_file("decisions")
        return shared_file("tooltips")
    if stem == "LOK_journal_entries":
        return system_file("journal_entries")
    return shared_file("tooltips")


def destination(entry: Entry, tags: set[str]) -> str:
    source = entry.source
    stem = source_stem(source)
    stem_lower = stem.lower()
    explicit = explicit_source_destination(source)
    if explicit:
        if stem_lower in {"countries", "parties", "characters", "ideas", "lok_traits"}:
            pass
        else:
            return explicit
    if stem_lower == "countries":
        country = country_from_key(entry.key, tags)
        if country:
            return country_file(country)
        return world_file("countries")
    if stem_lower in {"parties", "characters", "ideas", "lok_traits"}:
        country = country_from_key(entry.key, tags)
        if country:
            return country_file(country)
        if stem_lower == "parties":
            return shared_file("parties")
        if stem_lower == "characters":
            return shared_file("characters")
        if stem_lower == "ideas":
            return shared_file("ideas")
        return shared_file("traits")
    if explicit_source_destination(source):
        return explicit_source_destination(source)  # pragma: no cover
    if TAG_EXACT_RE.match(stem) and stem in tags:
        return country_file(stem)
    return classify_misc(entry.key, source, tags)


def section(entry: Entry, dest: str) -> str:
    key = entry.key
    source = entry.source.lower()
    if "/lok_country_" in dest:
        if "." in key and re.search(r"\.\d+\.", key):
            return "EVENTS"
        if "focus" in source or key.endswith(("_focus", "_focus_desc", "_focus_tt")):
            return "FOCUSES"
        if "idea" in source or key.endswith(("_idea", "_idea_desc", "_spirit", "_spirit_desc")):
            return "IDEAS / NATIONAL SPIRITS"
        if "decision" in source or key.endswith(("_cat", "_cat_desc", "_decision", "_decision_desc")):
            return "DECISIONS"
        if key.endswith("_BOOKMARK_DESC") or key.endswith(("_party", "_party_long")) or "character" in source or "trait" in source:
            return "CORE"
        if key in {Path(dest).stem.removeprefix("lok_country_").removesuffix("_l_english"), "BPT", "ZZZ"} or key.endswith(("_DEF", "_ADJ")):
            return "CORE"
        return "TOOLTIPS AND MISC COUNTRY CONTENT"
    if "." in key and re.search(r"\.\d+\.", key):
        return "EVENTS"
    if "decision" in source or key.endswith(("_cat", "_cat_desc")):
        return "DECISIONS"
    if "idea" in source or key.endswith(("_idea", "_idea_desc", "_modifier", "_modifier_desc")):
        return "IDEAS / MODIFIERS"
    if "map" in source or "gui" in key.lower():
        return "SCRIPTED GUI / DISPLAY TEXT"
    return "CORE"


def object_ids(root: Path, directory: str, include_id_field: bool = False) -> set[str]:
    """Collect likely database object IDs without interpreting their values."""
    found: set[str] = set()
    folder = root / "common" / directory
    if not folder.exists():
        return found
    block_pattern = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=\s*\{")
    id_pattern = re.compile(r"\bid\s*=\s*([A-Za-z0-9_.-]+)")
    for path in folder.rglob("*.txt"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = block_pattern.match(line)
            if match:
                found.add(match.group(1))
            if include_id_field:
                match = id_pattern.search(line)
                if match:
                    found.add(match.group(1))
    return found


def refined_section(entry: Entry, dest: str, focus_ids: set[str], idea_ids: set[str], decision_ids: set[str]) -> str:
    key = entry.key
    bases = {key}
    for suffix in ("_desc", "_tt", "_effect", "_name"):
        if key.endswith(suffix):
            bases.add(key[: -len(suffix)])
    if bases & focus_ids:
        return "FOCUSES"
    if bases & idea_ids:
        return "IDEAS / NATIONAL SPIRITS" if "/lok_country_" in dest else "IDEAS / MODIFIERS"
    if bases & decision_ids:
        return "DECISIONS"
    return section(entry, dest)


def header(title: str) -> list[str]:
    return [
        "l_english:",
        "",
        " # ============================================================",
        f" # {title}",
        " # ============================================================",
        "",
    ]


def write_staged(root: Path, output: Path, entries: list[Entry], malformed: list[Malformed]) -> dict:
    tags = tags_from_repository(root, entries)
    focus_ids = object_ids(root, "national_focus", include_id_field=True)
    idea_ids = object_ids(root, "ideas")
    decision_ids = object_ids(root, "decisions")
    grouped: dict[str, dict[str, list[Entry]]] = defaultdict(lambda: defaultdict(list))
    malformed_grouped: dict[str, list[Malformed]] = defaultdict(list)
    for entry in entries:
        dest = destination(entry, tags)
        grouped[dest][refined_section(entry, dest, focus_ids, idea_ids, decision_ids)].append(entry)
    for item in malformed:
        if "/replace/" in item.source:
            dest = replace_file(item.source)
        else:
            country = country_from_key(item.key or "", tags)
            dest = country_file(country) if country else shared_file("unclassified")
        malformed_grouped[dest].append(item)

    output.mkdir(parents=True, exist_ok=True)
    section_order = ["CORE", "FOCUSES", "IDEAS / NATIONAL SPIRITS", "IDEAS / MODIFIERS", "DECISIONS", "EVENTS", "SCRIPTED GUI / DISPLAY TEXT", "TOOLTIPS AND MISC COUNTRY CONTENT"]
    generated: dict[str, int] = {}
    for dest in sorted(set(grouped) | set(malformed_grouped)):
        target = output / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        title = Path(dest).stem.removesuffix("_l_english").replace("_", " ")
        lines = header(title)
        for section_name in section_order:
            values = grouped[dest].get(section_name, [])
            values = sorted(values, key=lambda e: e.order)
            if not values and section_name not in {"CORE"}:
                continue
            lines.extend([f" # ============================================================", f" # {section_name}", f" # ============================================================", ""])
            lines.extend(entry.raw for entry in values)
            if values:
                lines.append("")
        for item in sorted(malformed_grouped.get(dest, []), key=lambda m: (m.source, m.line)):
            lines.append(f" # PRESERVED MALFORMED SOURCE: {item.source}:{item.line}")
            lines.append(item.raw)
        text = "\n".join(lines).rstrip("\n") + "\n"
        target.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        generated[dest] = sum(len(values) for values in grouped[dest].values()) + len(malformed_grouped.get(dest, []))
    return {"generated_files": generated, "tags": sorted(tags), "malformed_destinations": {k: [asdict(v) for v in vals] for k, vals in malformed_grouped.items()}}


def manifest(entries: Iterable[Entry], malformed: Iterable[Malformed]) -> dict:
    entries = list(entries)
    by_key: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_key[entry.key].append({"value": entry.value, "source": entry.source, "line": entry.line})
    return {
        "entry_count": len(entries),
        "unique_key_count": len(by_key),
        "malformed_count": len(list(malformed)),
        "keys": {key: values for key, values in sorted(by_key.items())},
    }


def cmd_inventory(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    entries, malformed, files = scan(root)
    output = Path(args.output).resolve()
    data = {
        "root": str(root),
        "files": files,
        "manifest": manifest(entries, malformed),
        "duplicates": duplicate_report(entries),
        "malformed": [asdict(item) for item in malformed],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "files": len(files),
        "entry_count": data["manifest"]["entry_count"],
        "unique_key_count": data["manifest"]["unique_key_count"],
        "malformed_count": data["manifest"]["malformed_count"],
        **{k: v for k, v in data["duplicates"].items() if k.endswith("count")},
    }
    print(json.dumps(summary, indent=2))


def cmd_migrate(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    entries, malformed, files = scan(root)
    output = Path(args.output).resolve()
    if output.exists():
        for path in sorted(output.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    result = write_staged(root, output, entries, malformed)
    (output / "_migration_metadata.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"source_files": len(files), "staged_files": len(result["generated_files"]), "entries": len(entries), "malformed": len(malformed)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    for name, function in (("inventory", cmd_inventory), ("migrate", cmd_migrate)):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--root", required=True)
        subparser.add_argument("--output", required=True)
        subparser.set_defaults(function=function)
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
