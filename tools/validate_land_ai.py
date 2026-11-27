"""Read-only land-AI reference, selection and change-boundary checks.

The scenario evaluator deliberately supports only the predicates used by this
patch. It fails on unknown syntax; it is not an HOI4 simulation or CWTools.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
from itertools import product
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "legacy_of_kattail_painter"))
from model import child, parse, scalar, value, walk  # noqa: E402

TEMPLATES = "common/ai_templates/generic.txt"
PREDICATES = "common/scripted_triggers/lok_ai_land_triggers.txt"
STRATEGIES = "common/ai_strategy/lok_land_ai.txt"
DEFAULT = "common/ai_strategy/default.txt"
DOCTRINES = "common/ai_strategy/doctrines.txt"
NATIVE_CHANGED = {
    TEMPLATES, PREDICATES, STRATEGIES, DEFAULT, DOCTRINES,
    "common/terrain/00_terrain.txt", "common/units/infantry.txt",
    "common/ai_equipment/generic_tank.txt",
    "interface/countryconstructionsview.gui",
}
WIDTHS = {
    "forest": (90, 45), "hills": (105, 52.5), "mountain": (75, 37.5),
    "plains": (105, 52.5), "urban": (120, 60), "jungle": (90, 45),
    "marsh": (75, 37.5), "desert": (105, 52.5),
}


@dataclass
class Source:
    text: str
    nodes: list = field(init=False)
    constants: dict = field(init=False)

    def __post_init__(self):
        self.nodes = parse(self.text)
        self.constants = {
            n.key: float(value(self.text, n)) for n in self.nodes
            if n.key.startswith("@") and n.children is None
        }

    def raw(self, node):
        return value(self.text, node).strip('"')

    def number(self, node):
        raw = self.raw(node)
        return self.constants[raw] if raw.startswith("@") else float(raw)


def read(relative):
    return Source((ROOT / relative).read_text(encoding="utf-8-sig"))


def structure(nodes, source):
    return [(n.key, n.op, structure(n.children, source) if n.children is not None
             else source.raw(n)) for n in nodes]


def registry(folder, container):
    result = {}
    for path in (ROOT / folder).glob("*.txt"):
        source = Source(path.read_text(encoding="utf-8-sig"))
        for root in source.nodes:
            if root.key == container:
                for node in root.children or []:
                    if node.children is not None:
                        result[node.key] = source, node
    return result


def check_country_filters(source, country_tags=None):
    """Reject balanced syntax that the engine's AI-template tag reader misreads.

    In the 2026-11-26 live log an empty blocked_for consumed tokens through the
    following upgrade_prio block, leaving all nine entries with role = none.
    A generic Clausewitz brace/parser check cannot catch that engine behavior.
    """
    groups = 0
    for group in source.nodes:
        if group.children is None:
            continue
        filters = [n for n in group.children if n.key in {"blocked_for", "available_for"}]
        assert len(filters) == 1, (group.key, "use exactly one country filter")
        entry = filters[0]
        assert entry.children, (group.key, "empty " + entry.key + " is unsafe in the engine")
        for tag in entry.children:
            assert tag.children is None and not tag.op, (group.key, "country filter must contain tag atoms")
            if country_tags is not None:
                assert tag.key.strip('"') in country_tags, (group.key, "unknown country tag", tag.key)
        assert scalar(source.text, group.children, "role"), (group.key, "missing role after country filter")
        groups += 1
    return groups


def check_country_filter_regressions():
    valid = Source("armor_generic = { blocked_for = { PLR HAR KAR } role = armor upgrade_prio = { base = 3 } }")
    assert check_country_filters(valid, {"PLR", "HAR", "KAR"}) == 1
    bad_filters = ["blocked_for = {}", "blocked_for = {\n\t\t}",
                   "available_for = {}", "blocked_for = { PLR } available_for = { HAR }"]
    for bad in bad_filters:
        fixture = Source("armor_generic = { " + bad + " role = armor upgrade_prio = { base = 3 } }")
        # These all parse as balanced Clausewitz, but must fail the engine guard.
        rejected = False
        try:
            check_country_filters(fixture, {"PLR", "HAR", "KAR"})
        except AssertionError:
            rejected = True
        assert rejected, ("unsafe country-filter fixture accepted", bad)
    return len(bad_filters)


def check_engine_log(path):
    """Check the two observed engine regressions in a caller-supplied fresh log.

    Descriptor warnings from other Workshop mods are outside this check. The
    caller must establish that this log came from a restart with current files.
    """
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    errors = Counter()
    for line in lines:
        if "AI role 'none' is missing a specified role" in line:
            errors["role_none"] += 1
        if "AI template database entry" in line and "missing a specified role" in line:
            errors["template_missing_role"] += 1
        if 'Could not find "pin_icon" in window production_building_line_entry' in line:
            errors["construction_pin"] += 1
    assert not errors, ("engine regressions remain", dict(errors))
    return len(lines)


@dataclass
class Country:
    factories: int = 30
    armor: float = 0
    year: int = 104
    nsb: bool = True
    mobile_doctrine: bool = False
    paluush: bool = False
    non_playable: bool = False
    war: bool = False
    reserves: bool = True
    manpower: int = 100000
    technologies: set = field(default_factory=set)


class Conditions:
    def __init__(self, source):
        self.source = source
        self.predicates = {n.key: n for n in source.nodes if n.children is not None}

    @staticmethod
    def compare(actual, op, expected):
        if op == "=":
            return actual == expected
        if op == ">":
            return actual > expected
        if op == "<":
            return actual < expected
        raise AssertionError(("unsupported comparison", op))

    def all(self, nodes, source, country, chain=()):
        return all(self.test(n, source, country, chain) for n in nodes)

    def test(self, node, source, country, chain=()):
        key, raw = node.key, source.raw(node)
        if key in {"AND", "OR", "NOT"}:
            values = [self.test(n, source, country, chain) for n in node.children]
            if key == "OR":
                return any(values)
            if key == "NOT":
                assert len(values) == 1, "this evaluator only supports single-condition NOT"
                return not values[0]
            return all(values)
        if key in self.predicates:
            assert key not in chain, ("recursive predicate", chain, key)
            result = self.all(self.predicates[key].children, self.source, country, chain + (key,))
            return result == (raw == "yes")
        booleans = {
            "always": True, "is_paluush_state": country.paluush,
            "is_non_playable_country": country.non_playable, "has_war": country.war,
        }
        if key in booleans:
            return booleans[key] == (raw == "yes")
        if key == "has_tech":
            return raw in country.technologies
        if key == "has_dlc":
            assert raw == "No Step Back", raw
            return country.nsb
        if key == "has_doctrine":
            assert raw == "new_mobile_warfare", raw
            return country.mobile_doctrine
        if key == "has_army_size":
            assert scalar(source.text, node.children, "type") == "armor"
            size = next(n for n in node.children if n.key == "size")
            return self.compare(country.armor, size.op, source.number(size))
        if key == "has_equipment":
            return all(self.compare(10000 if country.reserves else 0, n.op, source.number(n))
                       for n in node.children)
        numbers = {
            "num_of_military_factories": country.factories,
            "has_manpower": country.manpower, "ai_wants_divisions": 40,
        }
        if key in numbers:
            return self.compare(numbers[key], node.op, source.number(node))
        if key == "date":
            date = tuple(int(n) for n in raw.split("."))
            return self.compare((country.year, 1, 2), node.op, date)
        raise AssertionError(("unsupported condition", key, raw))


def check_references(templates, predicates, strategies, technologies, equipment, units):
    trigger_counts = Counter()
    for path in (ROOT / "common/scripted_triggers").glob("*.txt"):
        source = Source(path.read_text(encoding="utf-8-sig"))
        trigger_counts.update(n.key for n in source.nodes if n.children is not None)
    custom = {n.key for n in predicates.nodes if n.children is not None}
    assert all(trigger_counts[name] == 1 for name in custom)
    policy_counts = Counter()
    for path in (ROOT / "common/ai_strategy").glob("*.txt"):
        source = Source(path.read_text(encoding="utf-8-sig"))
        policy_counts.update(n.key for n in source.nodes if n.children is not None)
    assert all(policy_counts[n.key] == 1 for n in strategies.nodes if n.children is not None)
    roles = []
    targets = []
    for group in templates.nodes:
        roles.append(scalar(templates.text, group.children, "role"))
        group_targets = {n.key: n for n in group.children
                         if n.children and child(n.children, "target_template")}
        targets.extend(group_targets)
        for name, target in group_targets.items():
            successor = scalar(templates.text, target.children, "replace_with")
            seen = {name}
            while successor:
                assert successor in group_targets, (name, "missing successor", successor)
                assert successor not in seen, ("cyclic replacement chain", seen)
                seen.add(successor)
                successor = scalar(templates.text, group_targets[successor].children, "replace_with")
            meat = child(target.children, "target_template")
            for section in ["regiments", "support", "regimental_support"]:
                body = child(meat.children, section)
                for unit in body.children if body else []:
                    assert unit.key in units, (name, unit.key)
                    assert templates.number(unit) > 0
                    us, un = units[unit.key]
                    support = scalar(us.text, un.children, "group") == "support"
                    assert support == (section != "regiments"), (name, section, unit.key)
                    if scalar(templates.text, group.children, "role") == "infantry":
                        assert unit.key not in {"motorized", "mechanized", "mot_artillery_brigade"}
    assert len(set(roles)) == len(roles), "duplicate role owner"
    assert len(set(targets)) == len(targets), "duplicate target identifier"
    assert not {"modern_armor", "modern_sp_artillery_brigade"} & {
        n.key for _, n in walk(templates.nodes)
    }
    known = custom | {"is_paluush_state", "is_non_playable_country"}
    for source in [templates, predicates, strategies, read("common/ai_equipment/generic_tank.txt")]:
        for path, node in walk(source.nodes):
            if node.key == "has_tech":
                assert source.raw(node) in technologies, (path, source.raw(node))
            if node.key.startswith("lok_ai_land_") and node.children is None:
                assert node.key in known, (path, "undefined predicate")
            if node.key == "has_equipment":
                assert all(n.key in equipment for n in node.children), path
            if node.key == "ai_strategy" and node.children:
                kind = scalar(source.text, node.children, "type")
                identity = scalar(source.text, node.children, "id")
                if kind == "research_weight_factor":
                    assert identity in technologies, identity
                elif kind == "role_ratio":
                    assert identity in roles, identity
                elif kind in {"equipment_production_min_factories_archetype",
                              "equipment_production_surplus_management"}:
                    assert identity in equipment, identity
    return len(targets)


def check_scenarios(templates, predicates, strategies, default, technologies):
    conditions = Conditions(predicates)
    policies = [n for n in strategies.nodes if n.children]
    defaults = {"default_unit_production", "default_mobile_production",
                "default_armored_production", "highered_armored_production",
                "default_produce_some_trucks_for_buffer"}
    policies += [n for n in default.nodes if n.key in defaults]
    source_for = {id(n): strategies for n in strategies.nodes if n.children}
    source_for.update({id(n): default for n in default.nodes if n.key in defaults})
    count = 0
    for factories, armor, year, nsb, reserves, mobile in product(
            [0, 9, 10, 19, 20, 29, 30, 49, 50, 69, 70, 99, 100],
            [0, 1, 2, 3, 4], [100, 104, 108, 112], [False, True], [False, True], [False, True]):
        tech = set(technologies)
        # Preserve the real DLC split in the fixtures, rather than giving both
        # legacy and chassis techs to every simulated country.
        tech -= {"basic_light_tank", "basic_medium_tank", "improved_medium_tank"} if nsb else {
            "basic_light_tank_chassis", "basic_medium_tank_chassis", "improved_medium_tank_chassis"}
        c = Country(factories, armor, year, nsb, mobile, reserves=reserves, technologies=tech)
        ratios = defaultdict(float)
        floors = 0
        for policy in policies:
            source = source_for[id(policy)]
            enable = child(policy.children, "enable")
            if enable and not conditions.all(enable.children, source, c):
                continue
            for st in policy.children:
                if st.key != "ai_strategy" or st.children is None:
                    continue
                kind = scalar(source.text, st.children, "type")
                identity = scalar(source.text, st.children, "id")
                amount = next((n for n in st.children if n.key == "value"), None)
                if kind == "role_ratio":
                    ratios[identity] += source.number(amount)
                if kind == "equipment_production_min_factories_archetype":
                    floors += source.number(amount)
        assert floors <= factories, (c, "floors exceed available industry", floors)
        if factories < 10:
            assert all(ratios[r] == 0 for r in ["armor", "mobile", "infantry_assault"]), (c, ratios)
        elif factories < 30:
            goal = 4 if factories >= 20 else 2
            assert (ratios["armor"] > 0) == (armor < goal and (mobile or armor > 0 or factories >= 20)), (c, ratios)
        else:
            assert ratios["armor"] == (18 if factories >= 70 else 12), (c, ratios)
            assert ratios["mobile"] == 8, (c, ratios)
        for group in templates.nodes:
            candidates = []
            for target in group.children:
                if not target.children or not child(target.children, "target_template"):
                    continue
                enable = child(target.children, "enable")
                if conditions.all(enable.children, templates, c):
                    priority = child(target.children, "upgrade_prio")
                    candidates.append((float(scalar(templates.text, priority.children, "base")), target))
                guard = child(target.children, "can_upgrade_in_field")
                if guard and not reserves:
                    assert not conditions.all(guard.children, templates, c), (target.key, "unfunded upgrade")
            if group.key == "infantry_generic":
                winner = max(candidates, key=lambda item: item[0])[1]
                expected = "infantry_basic" if factories < 10 else (
                    "infantry_mid" if factories >= 30 and year >= 104 else "infantry_early")
                assert winner.key == expected, (c, winner.key, expected)
            if group.key == "armor_generic" and candidates:
                winner = max(candidates, key=lambda item: item[0])[1]
                expected = "medium_armor_assault" if factories >= 100 and year >= 108 else (
                    "medium_armor_mechanized" if factories >= 70 and year >= 104 else (
                    "medium_armor_mid" if factories >= 50 and year >= 104 else "medium_armor_early"))
                assert winner.key == expected, (c, winner.key, expected)
        count += 1
    for restricted in ["paluush", "non_playable"]:
        c = Country(factories=100, technologies=set(technologies))
        setattr(c, restricted, True)
        assert not conditions.all(conditions.predicates["lok_ai_land_conventional_country"].children, predicates, c)
    c = Country(100, technologies=set())
    assert not conditions.all(conditions.predicates["lok_ai_land_armor_country"].children, predicates, c)
    c = Country(20, technologies=set())
    assert conditions.all(conditions.predicates["lok_ai_land_wants_armor_research"].children, predicates, c)
    for inherited in [0, 1]:
        c = Country(5, armor=inherited, technologies=set(technologies))
        assert conditions.all(conditions.predicates["lok_ai_land_can_design_armor"].children, predicates, c) == bool(inherited)
    armor_group = next(n for n in templates.nodes if n.key == "armor_generic")
    for family in ["light", "medium"]:
        c = Country(20, mobile_doctrine=True, technologies={
            "motorised_infantry", f"basic_{family}_tank_chassis"})
        enabled = [n for n in armor_group.children if n.children
                   and child(n.children, "target_template")
                   and conditions.all(child(n.children, "enable").children, templates, c)]
        assert enabled, (family, "no starter without the other chassis family")
        winner = max(enabled, key=lambda n: float(scalar(
            templates.text, child(n.children, "upgrade_prio").children, "base")))
        assert winner.key == ("light_armor_expanded" if family == "light" else "medium_armor_early")
    return count


def check_shapes_and_modules(templates, units):
    armor_group = next(n for n in templates.nodes if n.key == "armor_generic")
    for target in armor_group.children:
        if not target.children or not child(target.children, "target_template"):
            continue
        meat = child(target.children, "target_template")
        width = organization = battalions = 0
        for section in ["regiments", "support"]:
            body = child(meat.children, section)
            for n in body.children if body else []:
                source, unit = units[n.key]
                amount = templates.number(n)
                width += float(scalar(source.text, unit.children, "combat_width", "0")) * amount
                organization += float(scalar(source.text, unit.children, "max_organisation", "0")) * amount
                battalions += amount
        # Conservative unmodified division average, including all support slots.
        assert organization / battalions >= 30, (target.key, "low base organization")
        expected = {"light_armor_early": 12, "light_armor_expanded": 20,
                    "medium_armor_early": 20, "medium_armor_mid": 30,
                    "medium_armor_mechanized": 30, "medium_armor_assault": 35}
        assert width == expected[target.key], (target.key, width)
    modules = registry("common/units/equipment/modules", "equipment_modules")
    categories = {scalar(s.text, n.children, "category") for s, n in modules.values()}
    tank = read("common/ai_equipment/generic_tank.txt")
    for path, node in walk(tank.nodes):
        if ("/modules[" in path or "/allowed_modules[" in path) and node.children is None:
            assert tank.raw(node) in set(modules) | categories | {"empty", "current"}, (path, tank.raw(node))
    for group in tank.nodes:
        if group.key in {"generic_modern_tanks", "generic_modern_tank_destroyer"}:
            for variant in group.children:
                if variant.children and child(variant.children, "target_variant"):
                    enable = child(variant.children, "enable")
                    assert enable and scalar(tank.text, enable.children, "always") == "no"
    # Turrets can extend a chassis's main-armament categories. Check the new
    # medium guns against that extension, not just the chassis's small-gun slot.
    _, turret = modules["tank_medium_three_man_tank_turret"]
    extension = child(turret.children, "allowed_module_categories")
    allowed = {n.key for n in child(extension.children, "main_armament_slot").children}
    for gun in ["tank_medium_cannon", "tank_medium_cannon_2"]:
        source, module = modules[gun]
        assert scalar(source.text, module.children, "category") in allowed


def check_reserve_reachability(predicates, strategies):
    # Production floors must be able to reach the stockpile thresholds used to
    # permit field conversion, even when no deployed unit needs the new item yet.
    pairs = {
        "@rifle_upgrade_buffer": "@upgrade_rifle_reserve",
        "@support_upgrade_buffer": "@upgrade_support_reserve",
        "@artillery_upgrade_buffer": "@upgrade_artillery_reserve",
        "@aa_upgrade_buffer": "@upgrade_aa_reserve",
        "@regional_tank_reserve": "@upgrade_tank_reserve",
        "@regional_truck_reserve": "@upgrade_truck_reserve",
        "@industrial_tank_reserve": "@upgrade_mechanized_reserve",
        "@assault_spg_reserve": "@upgrade_spg_reserve",
        "@power_infantry_reserve": "@upgrade_exoskeleton_reserve",
    }
    for production, conversion in pairs.items():
        assert strategies.constants[production] > predicates.constants[conversion], (production, conversion)


def check_terrain_and_units(units, game):
    source = read("common/terrain/00_terrain.txt")
    categories = child(source.nodes, "categories")
    for name, numbers in WIDTHS.items():
        terrain = child(categories.children, name)
        for key, expected in zip(["combat_width", "combat_support_width"], numbers):
            assert float(scalar(source.text, terrain.children, key)) == expected
    if game:
        vanilla = Source((game / "common/terrain/00_terrain.txt").read_text(encoding="utf-8-sig"))
        vc = child(vanilla.nodes, "categories")
        for name, numbers in WIDTHS.items():
            for key, expected in zip(["combat_width", "combat_support_width"], numbers):
                assert float(scalar(vanilla.text, child(vc.children, name).children, key)) * 1.5 == expected
    us, un = units["mechanized"]
    needs = child(un.children, "need")
    assert {n.key: us.number(n) for n in needs.children} == {
        "mechanized_equipment": 40, "infantry_equipment": 100,
    }
    us, un = units["power_motorized"]
    assert scalar(us.text, child(un.children, "need").children, "anti_tank_equipment") == "50"


def check_boundary(baseline):
    import json
    manifest = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))
    changed = {name for name, old in manifest.items()
               if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != old}
    assert changed <= NATIVE_CHANGED, ("unrelated native changes", changed - NATIVE_CHANGED)
    current = {p.relative_to(ROOT).as_posix() for folder in [
        "common", "events", "history", "map", "localisation", "interface"
    ] for p in (ROOT / folder).rglob("*") if p.is_file()}
    added = current - set(manifest)
    assert added <= {PREDICATES, STRATEGIES}, ("unexpected added native files", added)
    assert (ROOT / "common/terrain/LOK_terrain.txt").read_bytes() == (baseline / "common/terrain/LOK_terrain.txt").read_bytes()
    before = Source((baseline / "common/units/infantry.txt").read_text(encoding="utf-8-sig"))
    after = read("common/units/infantry.txt")
    needs = child(child(child(before.nodes, "sub_units").children, "mechanized").children, "need")
    needs.children[:] = [n for n in needs.children if n.key != "anti_tank_equipment"]
    assert structure(before.nodes, before) == structure(after.nodes, after), "unrelated battalion change"
    before = Source((baseline / "common/terrain/00_terrain.txt").read_text(encoding="utf-8-sig"))
    after = read("common/terrain/00_terrain.txt")
    def without_widths(source):
        for terrain in child(source.nodes, "categories").children:
            if terrain.key in WIDTHS:
                terrain.children[:] = [n for n in terrain.children
                                       if n.key not in {"combat_width", "combat_support_width"}]
        return structure(source.nodes, source)
    assert without_widths(before) == without_widths(after), "unrelated terrain change"
    gui_name = "interface/countryconstructionsview.gui"
    if gui_name in changed:
        before = Source((baseline / gui_name).read_text(encoding="utf-8-sig"))
        after = read(gui_name)
        parent = next(n for _, n in walk(after.nodes) if n.children
                      and scalar(after.text, n.children, "name") == "production_building_line_entry")
        pins = [n for n in parent.children if n.children
                and scalar(after.text, n.children, "name") == "pin_icon"]
        assert len(pins) == 1, "missing/duplicate construction pin"
        parent.children.remove(pins[0])
        assert structure(before.nodes, before) == structure(after.nodes, after), "unrelated GUI change"
    # All old root blocks not owned by this land patch must be exactly equivalent.
    allowed = {"keep_logistics_buffer", "herzland_warlord_prep_for_krieg",
               "default_garrison_production", "default_mountaineers_production",
               "default_mobile_production", "default_armored_production", "highered_armored_production",
               "DEFAULT_early_template_design", "DEFAULT_midlate_template_design",
               "default_produce_some_trucks_for_buffer"}
    for filename in [DEFAULT, DOCTRINES]:
        before = Source((baseline / filename).read_text(encoding="utf-8-sig"))
        after = read(filename)
        before_groups = [n for n in before.nodes if n.children]
        after_groups = [n for n in after.nodes if n.children]
        assert [n.key for n in before_groups] == [n.key for n in after_groups]
        for old, new in zip(before_groups, after_groups):
            if filename == DEFAULT and old.key in allowed:
                continue
            def keep(node, source):
                if node.key != "ai_strategy" or node.children is None:
                    return True
                role = scalar(source.text, node.children, "id")
                kind = scalar(source.text, node.children, "type")
                land_roles = {"armor", "motorized", "mobile", "artillery", "anti_tank", "infantry_assault"}
                if filename == DEFAULT:
                    land_roles = {"armor", "mountaineers"}
                return not (kind == "role_ratio" and role in land_roles)
            assert structure([n for n in old.children if keep(n, before)], before) == structure(
                [n for n in new.children if keep(n, after)], after), (filename, old.key, "non-land change")
    for filename in changed:
        before = (baseline / filename).read_bytes()
        after = (ROOT / filename).read_bytes()
        assert before.startswith(b"\xef\xbb\xbf") == after.startswith(b"\xef\xbb\xbf"), filename
        if before.count(b"\n") == before.count(b"\r\n"):
            assert after.count(b"\n") == after.count(b"\r\n"), (filename, "newline conversion")
    return len(changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, help="Installed game root for exact terrain scaling checks")
    parser.add_argument("--baseline", type=Path, help="Optional pre-edit snapshot with manifest.json")
    parser.add_argument("--error-log", type=Path, help="Fresh post-restart engine log to check for the observed role/pin failures")
    args = parser.parse_args()
    try:
        templates, predicates, strategies, default = map(read, [TEMPLATES, PREDICATES, STRATEGIES, DEFAULT])
        tags = set()
        for path in (ROOT / "common/country_tags").glob("*.txt"):
            tags.update(n.key for n in Source(path.read_text(encoding="utf-8-sig")).nodes if n.op == "=")
        groups = check_country_filters(templates, tags)
        regressions = check_country_filter_regressions()
        technologies = registry("common/technologies", "technologies")
        equipment = registry("common/units/equipment", "equipments")
        equipment.update(registry("common/units/equipment", "duplicate_archetypes"))
        units = registry("common/units", "sub_units")
        targets = check_references(templates, predicates, strategies, technologies, equipment, units)
        scenarios = check_scenarios(templates, predicates, strategies, default, technologies)
        check_shapes_and_modules(templates, units)
        check_reserve_reachability(predicates, strategies)
        check_terrain_and_units(units, args.game)
        if args.baseline:
            changed = check_boundary(args.baseline)
            print(f"Change-boundary check passed: {changed} modified native files; air/naval policies preserved.")
        if args.error_log:
            lines = check_engine_log(args.error_log)
            print(f"Engine-log check passed: {lines} lines, no role-none/missing-role/construction-pin errors.")
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        print("Land AI validation failed:", exc)
        return 1
    print(f"Land AI validation passed: {targets} targets, {scenarios} selection/budget scenarios, references, widths and mechanized needs.")
    print(f"Engine-filter regression checks passed: {groups} nonempty tag lists, {regressions} unsafe fixtures rejected.")
    print("Static/scenario checks only: engine role matching, training queues and gameplay require a fresh campaign.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
