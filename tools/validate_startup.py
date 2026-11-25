"""Read-only regression checks for the errors in the 2026-11-25 engine log.

This complements validate_map.py; it does not emulate the engine or assert that
neutral foreign deployments are illegal. External Workshop descriptors are not
part of this repository's validation scope.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'legacy_of_kattail_painter'))
from model import World, child, parse, read_text, scalar, walk


GUI_BINDINGS = {
    'countrytradeview.gui': {
        'guiTypes': ('auto_import_priority_window', 'auto_import_priority_entry'),
        'countrytradeview': ('factories_consumer', 'factories_trade', 'auto_import_checkbox',
                             'auto_import_budget_txt', 'auto_import_slider', 'auto_import_priority_open_button',
                             'consumer_goods_icon', 'traded_factories_icon', 'auto_import_label', 'auto_import_budget_bg'),
    },
    'countryconstructionsview.gui': {
        'guiTypes': ('repair_order_window', 'repair_order_entry'),
        'count_container': ('repair_order_open_button',),
        'start_construction_entry': ('repair_order_number_window',),
        'production_building_line_entry': ('repair_order_number_window',),
        'production_railway_gun_repair_entry': ('repair_order_number_window',),
    },
    'countrydiplomacyview.gui': {
        'diplomacy_action_entry': ('response_icon',),
        'diplomatic_actions': ('edit_auto_response', 'actions_title'),
        'diplomacy_action_info_window': ('recall_volunteers',),
    },
    'unitview.gui': {'army_division_view': ('recall_volunteers_indicator',)},
    'topbar.gui': {
        'topbar': ('national_focus_shortcut',),
        'after_intel_agency_button': ('technology_button_shortcut', 'technology_button_ctrl_shortcut',
                                     'technology_button_alt_shortcut'),
    },
}


def check_gui(game: Path | None) -> None:
    required_sprites = set()
    for filename, parents in GUI_BINDINGS.items():
        source = read_text(ROOT/'interface'/filename)
        roots = parse(source)
        for parent_name, names in parents.items():
            candidates = [n for _, n in walk(roots) if n.children is not None
                          and (n.key == parent_name == 'guiTypes'
                               or scalar(source, n.children, 'name') == parent_name)]
            assert len(candidates) == 1, (filename, parent_name, 'ambiguous/missing parent')
            children = Counter(scalar(source, n.children, 'name') for n in candidates[0].children if n.children)
            for name in names:
                assert children[name] == 1, (filename, parent_name, name)
                target = next(n for n in candidates[0].children if n.children and scalar(source, n.children, 'name') == name)
                for _, node in walk([target]):
                    if node.key.lower() in {'spritetype', 'quadtexturesprite'} and node.children is None:
                        sprite = source[node.value_start:node.end].strip('"')
                        if sprite.startswith('GFX_'):
                            required_sprites.add(sprite)
                if name == 'repair_order_number_window':
                    window = next(n for n in candidates[0].children if n.children and scalar(source, n.children, 'name') == name)
                    assert any(n.children and scalar(source, n.children, 'name') == 'repair_order_number' for n in window.children)
    override = ROOT/'common/scripted_guis/ROM_diplomacy_scripted_gui.txt'
    assert child(parse(read_text(override)), 'scripted_gui').children == []
    if game:
        files = {p.relative_to(game/'interface').as_posix(): p for p in (game/'interface').rglob('*.gfx')}
        files.update({p.relative_to(ROOT/'interface').as_posix(): p for p in (ROOT/'interface').rglob('*.gfx')})
        sprites = set()
        for path in files.values():
            sprites.update(re.findall(r'\bname\s*=\s*"?(GFX_[\w.-]+)', read_text(path)))
        for sprite in sorted(required_sprites):
            assert sprite in sprites, ('missing inherited GUI sprite', sprite)


def check_localisation() -> int:
    keys = {}
    for path in (ROOT/'localisation/english').rglob('*.yml'):
        layer = 'replace' if 'replace' in path.relative_to(ROOT).parts else 'base'
        for key in re.findall(r'^\s*([^\s:#]+):\d*\s*"', read_text(path), re.M):
            identity = (layer, key)
            assert identity not in keys, (key, keys.get(identity), path)
            keys[identity] = path
    return len(keys)


def check_fallbacks() -> None:
    source = read_text(ROOT/'common/names/misc_names.txt')
    fallback = child(parse(source), 'default')
    assert fallback is not None
    for gender in ['male', 'female']:
        scope = child(fallback.children, gender)
        names = child(scope.children, 'names') if scope else child(fallback.children, 'names')
        assert names and names.children, ('missing fallback names', gender)
    assert child(fallback.children, 'surnames').children
    source = read_text(ROOT/'portraits/00_portraits.txt')
    fallback = child(child(parse(source), 'default').children, 'scientist')
    assert fallback is not None
    sprite_source = read_text(ROOT/'interface/lok_generic_species_portraits.gfx')
    for gender in ['male', 'female']:
        scope = child(fallback.children, gender)
        assert scope and scope.children
        for node in scope.children:
            name = node.key.strip('"')
            for sprite in [name, name+'_small']:
                match = re.search(r'\bname\s*=\s*"'+re.escape(sprite)+r'"[^}]*?texture[Ff]ile\s*=\s*"([^"]+)"', sprite_source)
                assert match and (ROOT/match[1]).is_file(), ('unresolved fallback portrait', sprite)


def check_history(world: World, baseline: dict) -> None:
    owned = defaultdict(set)
    histories = {}
    for sid in world.states:
        source, nodes = world.state_nodes(sid)
        history = child(nodes, 'history')
        assert history is not None, sid
        owned[scalar(source, history.children, 'owner')].add(sid)
        histories[sid] = (source, nodes, history)
    for tag, path in world.countries.items():
        source = world.docs.text(path)
        capital = scalar(source, parse(source), 'capital')
        if owned[tag] and capital:
            assert capital.isdigit() and int(capital) in owned[tag], ('foreign capital', tag, capital)
    for path in (ROOT/'history/units').glob('*.txt'):
        parse(read_text(path))
    old_locations = set()
    for message in baseline['families']['unit_deployment_ownership']['messages']:
        match = re.match(r'(.*?) has been placed in (\d+) at start', message['message'])
        old_locations.add((match[1], int(match[2])))
    for tag in ['TEM', 'KKN', 'FOD']:
        source = read_text(ROOT/f'history/units/{tag}_1936.txt')
        for unit in child(parse(source), 'units').children:
            if unit.key == 'division' and unit.children is not None:
                identity = (scalar(source, unit.children, 'name'), int(scalar(source, unit.children, 'location')))
                assert identity not in old_locations, ('unrepaired enemy deployment', tag, identity)
    source = read_text(ROOT/'history/units/RST_1936_air.txt')
    for wings in child(parse(source), 'air_wings').children:
        sid = int(wings.key)
        state_source, _, history = histories[sid]
        buildings = child(history.children, 'buildings')
        assert sid in owned['RST'] and buildings and int(scalar(state_source, buildings.children, 'air_base', '0')) > 0, sid
    source = read_text(ROOT/'history/countries/PGN - Piertuguese.txt')
    assert not child(parse(source), 'declare_war_on'), 'unguarded PGN declaration'
    categories = {}
    for path in (ROOT/'common/state_category').glob('*.txt'):
        source = read_text(path)
        for category in child(parse(source), 'state_categories').children:
            categories[category.key] = int(scalar(source, category.children, 'local_building_slots', '0'))
    for message in baseline['families']['shared_building_slot_overflow']['messages']:
        sid = int(message['message'].split(' - ')[0])
        source, nodes, history = histories[sid]
        buildings = child(history.children, 'buildings')
        total = sum(int(scalar(source, buildings.children, kind, '0')) for kind in ['industrial_complex', 'arms_factory', 'dockyard'])
        extra = sum(int(source[n.value_start:n.end]) for n in history.children if n.key == 'add_extra_state_shared_building_slots')
        assert total <= categories[scalar(source, nodes, 'state_category')]+extra, ('overfilled state', sid)


def check_flags_and_music(baseline: dict) -> None:
    for relative, record in baseline['flag_files'].items():
        path = ROOT/relative
        assert path.read_bytes()[16] == 32, relative
        with Image.open(path) as image:
            assert image.size == (record['width'], record['height']), relative
            assert image.getchannel('A').getextrema() == (255, 255), relative
    songs = {message['message'].split('Could not find music named ')[1] for message in baseline['families']['unregistered_music']['messages']}
    for path in (ROOT/'music').glob('*.txt'):
        references = set(re.findall(r'\bsong\s*=\s*"([^"]+)"', read_text(path)))
        assert not songs.intersection(references), ('orphaned optional songs', path)


def check_generated_equipment(world: World) -> tuple[int, int]:
    """Check both native template branches against each country's tech context."""
    source = read_text(ROOT/'common/on_actions/LOK_on_actions.txt')
    def find_branch(nodes):
        for index, node in enumerate(nodes):
            template = child(node.children, 'division_template') if node.key == 'if' and node.children else None
            if template and scalar(source, template.children, 'name') == 'Standard Infantry':
                assert nodes[index+1].key == 'else'
                return node, template, child(nodes[index+1].children, 'division_template')
            if node.children:
                result = find_branch(node.children)
                if result:
                    return result
        return None
    branch, modern, basic = find_branch(parse(source))
    required = {source[n.value_start:n.end] for n in child(branch.children, 'limit').children if n.key == 'has_tech'}
    assert required == {'motorised_infantry', 'gw_artillery', 'tech_support', 'tech_engineers'}
    equipment, active = {}, set()
    for path in (ROOT/'common/units/equipment').glob('*.txt'):
        data = read_text(path)
        container = child(parse(data), 'equipments')
        for model in container.children if container else []:
            if not model.children:
                continue
            archetype = scalar(data, model.children, 'archetype')
            if archetype:
                equipment[model.key] = archetype
                if scalar(data, model.children, 'active') == 'yes':
                    active.add(archetype)
    assert 'infantry_equipment' in active
    unlocks = {}
    for path in (ROOT/'common/technologies').glob('*.txt'):
        data = read_text(path)
        container = child(parse(data), 'technologies')
        for technology in container.children if container else []:
            enabled = child(technology.children, 'enable_equipments') if technology.children else None
            if enabled:
                unlocks[technology.key] = {equipment[n.key] for n in enabled.children if n.key in equipment}
    needs = {}
    for path in (ROOT/'common/units').glob('*.txt'):
        data = read_text(path)
        container = child(parse(data), 'sub_units')
        for unit in container.children if container else []:
            needed = child(unit.children, 'need') if unit.children else None
            if needed:
                needs[unit.key] = {n.key for n in needed.children}
    counts = Counter()
    for tag, path in world.countries.items():
        data = world.docs.text(path)
        learned = {n.key for root in parse(data) if root.key == 'set_technology' and root.children
                   for n in root.children if n.key != 'popup' and n.children is None and float(data[n.value_start:n.end]) > 0}
        available = active | set().union(*(unlocks.get(technology, set()) for technology in learned))
        template = modern if required <= learned else basic
        for role in ['regiments', 'support']:
            container = child(template.children, role)
            for unit in container.children if container else []:
                assert unit.key in needs and needs[unit.key] <= available, ('startup equipment unavailable', tag, unit.key, needs.get(unit.key, set())-available)
        counts['modern' if template is modern else 'basic'] += 1
    return counts['modern'], counts['basic']


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, help='Installed game root, for inherited GUI sprite checks')
    args = parser.parse_args()
    baseline = json.loads((ROOT/'modding_documentation/agent_memory/error_log_audit_20261125/inventory.json').read_text(encoding='utf-8'))
    try:
        check_gui(args.game)
        count = check_localisation()
        check_fallbacks()
        world = World(ROOT)
        assert not world.warnings, world.warnings
        check_history(world, baseline)
        check_flags_and_music(baseline)
        modern, basic = check_generated_equipment(world)
    except (AssertionError, ValueError, OSError) as exc:
        print('Startup validation failed:', exc)
        return 1
    print(f'Startup validation passed: GUI bindings, {count} unique localisation keys/layers, '
          'name/portrait fallbacks, capitals/OOBs, logged deployments, air bases, slots, flags and music.')
    print(f'Generated equipment coverage: {modern} modern and {basic} basic country technology contexts.')
    print('Engine validation and external Workshop descriptors require a separate fresh-game check.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
