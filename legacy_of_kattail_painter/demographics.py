"""Conservative evaluator for this mod's initial state demographics, not a game VM."""
from __future__ import annotations

import re
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from PIL import Image, ImageOps
from model import child, parse, scalar, value, walk

STARTUP = 'common/on_actions/LOK_on_actions.txt'


def startup_effect(world):
    text = world.docs.text(STARTUP)
    root = child(parse(text), 'on_actions')
    startup = child(root.children, 'on_startup')
    return text, child(startup.children, 'effect').children


def targets_demographics(text, node):
    for _, n in walk([node]):
        if n.key == 'clear_array' and value(text, n) == 'state_cultures':
            return True
        if n.key == 'set_variable' and n.children:
            if any(v.key in {'species', 'minority'} for v in n.children):
                return True
        if n.key == 'add_to_array' and n.children:
            if scalar(text, n.children, 'array') == 'state_cultures':
                return True
    return False


class Setup:
    def __init__(self, world):
        self.world = world
        self.data = {sid: {'culture': [], 'species': 0, 'minority': 1000} for sid in world.states}
        self.triggers = {}
        for f in sorted((world.root / 'common/scripted_triggers').glob('*.txt')):
            t = world.docs.text(f.relative_to(world.root).as_posix())
            for n in parse(t):
                if n.children is not None:
                    self.triggers[n.key] = (t, n.children)
        self.missing_states = set()
        self.selected = []
        self.redundant_minorities = set()
        self.text = ''
        self.cores = {}
        for sid in world.states:
            t, ns = world.state_nodes(sid)
            h = child(ns, 'history')
            self.cores[sid] = {value(t, c) for c in (h.children if h else []) if c.key == 'add_core_of'}

    def limit(self, text, nodes, sid=None, tag=None, depth=0):
        if depth > 20:
            raise ValueError('Recursive scripted trigger')
        tests = []
        for n in nodes:
            key = n.key.lower()
            v = value(text, n).strip('"')
            if key in {'not', 'or', 'and'}:
                ts = [self.limit(text, [c], sid, tag, depth + 1) for c in n.children]
                result = not any(ts) if key == 'not' else any(ts) if key == 'or' else all(ts)
            elif key == 'tag':
                result = tag == v
            elif key == 'is_owned_by':
                result = sid is not None and self.world.states[sid].owner == v
            elif key == 'is_core_of':
                result = sid is not None and v in self.cores[sid]
            elif key == 'is_in_array':
                if sid is None or scalar(text, n.children, 'array') != 'state_cultures':
                    raise ValueError('Unsupported demographic array check')
                result = int(scalar(text, n.children, 'value')) in self.data[sid]['culture']
            elif key == 'check_variable':
                ts = []
                for c in n.children:
                    if sid is None or c.key not in {'species', 'minority'} or c.op != '=':
                        raise ValueError('Unsupported demographic variable check')
                    ts.append(self.data[sid][c.key] == int(value(text, c)))
                result = all(ts)
            elif n.key in self.triggers:
                t, cs = self.triggers[n.key]
                result = self.limit(t, cs, sid, tag, depth + 1)
                if v == 'no':
                    result = not result
                elif v != 'yes':
                    raise ValueError('Unsupported scripted trigger parameter')
            else:
                raise ValueError('Unsupported initial demographic trigger: ' + n.key)
            tests.append(result)
        return all(tests)

    def run(self, text, nodes, sid=None, tag=None):
        for n in nodes:
            if n.key == 'limit':
                continue
            if n.key.isdigit() and n.children is not None:
                state = int(n.key)
                if state not in self.data:
                    self.missing_states.add(state)
                    continue
                self.run(text, n.children, state, tag)
            elif re.fullmatch('[A-Z0-9]{3}', n.key) and n.children is not None:
                self.run(text, n.children, None, n.key)
            elif n.key in {'every_state', 'every_owned_state'}:
                lim = child(n.children, 'limit')
                for state, rec in self.world.states.items():
                    if n.key == 'every_owned_state' and rec.owner != tag:
                        continue
                    if lim is None or self.limit(text, lim.children, state, tag):
                        self.run(text, n.children, state, tag)
            elif n.key == 'every_country':
                lim = child(n.children, 'limit')
                for country in sorted({s.owner for s in self.world.states.values()} - {''}):
                    if lim is None or self.limit(text, lim.children, None, country):
                        self.run(text, n.children, None, country)
            elif n.key == 'if':
                lim = child(n.children, 'limit')
                if lim is None or self.limit(text, lim.children, sid, tag):
                    self.run(text, n.children, sid, tag)
            elif n.key == 'set_variable':
                if sid is None:
                    raise ValueError('State demographic effect in country scope')
                for c in n.children:
                    if c.key not in {'species', 'minority'}:
                        raise ValueError('Unrelated variable mixed into demographics: ' + c.key)
                    self.data[sid][c.key] = int(value(text, c))
            elif n.key == 'add_to_array':
                if sid is None or scalar(text, n.children, 'array') != 'state_cultures':
                    raise ValueError('Unrelated array mixed into demographics')
                self.data[sid]['culture'].append(int(scalar(text, n.children, 'value')))
            elif n.key == 'clear_array':
                if sid is None or value(text, n) != 'state_cultures':
                    raise ValueError('Unrelated array clear mixed into demographics')
                self.data[sid]['culture'] = []
            else:
                raise ValueError('Unsupported initial demographic effect: ' + n.key)

    def load(self):
        text, nodes = startup_effect(self.world)
        self.text = text
        # Select whole top-level effect statements, retaining all nested conditions and order.
        # Limit to the initial on_startup block; later conversion/weekly effects are untouched.
        self.selected = [n for n in nodes if targets_demographics(text, n)]
        for n in self.selected:
            self.run(text, [n])
        # A migrated state is authoritative. Keep the old evaluator usable before installation.
        for sid in self.world.states:
            t, ns = self.world.state_nodes(sid)
            h = child(ns, 'history')
            if h:
                local = [n for n in h.children if targets_demographics(t, n)]
                if local:
                    self.data[sid] = {'culture': [], 'species': 0, 'minority': 1000}
                    self.run(t, local, sid)
        for sid, data in self.data.items():
            if data['species'] == 1000:
                raise ValueError(f'State {sid}: No minority (1000) cannot be the majority species')
            if data['minority'] == data['species']:
                self.redundant_minorities.add(sid)
                data['minority'] = 1000
        return self.data


def set_local_draft(world, sid, cultures, species, minority):
    if any(c < 0 for c in cultures) or species < 0 or minority < 0:
        raise ValueError('Demographic IDs must be nonnegative')
    if species == 1000:
        raise ValueError('No minority (1000) cannot be the majority species')
    if minority == species:
        minority = 1000
    rel = world.states[sid].path
    t, ns = world.state_nodes(sid)
    hist = child(ns, 'history')
    if hist is None:
        raise ValueError('State has no history block')
    start_marker = '# LOK PAINTER DEMOGRAPHICS BEGIN'
    end_marker = '# LOK PAINTER DEMOGRAPHICS END'
    snippet = '\t\t' + start_marker + '\n'
    snippet += '\t\tclear_array = state_cultures\n'
    for c in cultures:
        snippet += f'\t\tadd_to_array = {{ array = state_cultures value = {c} }}\n'
    snippet += f'\t\tset_variable = {{ species = {species} }}\n'
    snippet += f'\t\tset_variable = {{ minority = {minority} }}\n'
    snippet += '\t\t' + end_marker + '\n'
    newline = '\r\n' if '\r\n' in t else '\n'
    snippet = snippet.replace('\n', newline)
    if start_marker in t:
        a = t.rfind('\n', 0, t.index(start_marker)) + 1
        b = t.index(end_marker, a) + len(end_marker)
        end_line = t.find('\n', b)
        b = len(t) if end_line < 0 else end_line + 1
        new = t[:a] + snippet + t[b:]
    else:
        # Insert before the history closing line, preserving its existing indentation.
        at = t.rfind('\n', 0, hist.end - 1) + 1
        if t[at:hist.end - 1].strip():
            at = hist.end - 1
            snippet = newline + snippet
        new = t[:at] + snippet + t[at:]
    world.docs.replace(rel, new)
    world.demographics[sid] = {'culture': list(cultures), 'species': species, 'minority': minority}


def repair_redundant_minorities(world):
    """Normalise loaded/raw-edited demographics and stage persistent repairs."""
    setup = Setup(world)
    world.demographics = setup.load()
    with world.docs.grouped():
        for sid in sorted(setup.redundant_minorities):
            data = world.demographics[sid]
            set_local_draft(world, sid, data['culture'], data['species'], 1000)
    return setup.redundant_minorities


# Source-backed definition editors. These are native files, never painter sidecars.
CATALOG_PATHS = {
    'culture_loc': 'localisation/english/lok_culture_l_english.yml',
    'species_loc': 'localisation/english/species_l_english.yml',
    'wonder_loc': 'localisation/english/wonders_l_english.yml',
    'culture_map': 'common/map_modes/LOK_culture_map_mode.txt',
    'species_map': 'common/map_modes/LOK_species_map_mode.txt',
    'culture_triggers': 'common/scripted_triggers/LOK_culture_triggers.txt',
    'culture_effects': 'common/scripted_effects/LOK_culture_effects.txt',
    'species_triggers': 'common/scripted_triggers/lok_species_trait_scripted_triggers.txt',
    'advisor_triggers': 'common/scripted_triggers/LOK_advisor_setup_tag_triggers.txt',
    'species_modifiers': 'common/dynamic_modifiers/LOK_species_trait_dynamic_modifiers.txt',
    'species_ideas': 'common/ideas/lok_species_ideas.txt',
    'effects': 'common/scripted_effects/LOK_scripted_effects.txt',
    'dynamic': 'common/dynamic_modifiers/LOK_dynamic_modifiers.txt',
    'culture_text': 'common/scripted_localisation/LOK_culture_scripted_loc.txt',
    'species_text': 'common/scripted_localisation/LOK_species_scripted_localisation.txt',
    'wonder_text': 'common/scripted_localisation/LOK_wonder_scripted_loc.txt',
    'species_gfx': 'interface/species_icon.gfx',
    'wonder_gfx': 'interface/wonder_icon.gfx',
    'trait_gfx': 'interface/lok_misc_icons.gfx',
    'startup': STARTUP,
}


@dataclass
class MapDefinition:
    key: object
    name: str
    description: str = ''
    name_color: str = ''
    color: object = None
    minority_color: object = None
    group: object = None
    traits: tuple = ()
    sprite: str = ''
    effects: dict = field(default_factory=dict)
    extras: tuple = ()


def _catalog_decimal(raw):
    try: number = Decimal(str(raw))
    except InvalidOperation: raise ValueError('Enter a numeric game-unit value') from None
    if not number.is_finite(): raise ValueError('Values must be finite')
    return format(number, 'f')


class MapCatalogStore:
    def __init__(self, world, characters):
        self.world, self.characters, self.docs = world, characters, world.docs
        self._cache = {}; self._palette_signature = None
        self._existing_native_paths = set()
        world.catalog_store = self

    def text(self, name):
        path = CATALOG_PATHS.get(name, name)
        if path not in self._existing_native_paths:
            if not (self.world.root / path).is_file():
                raise ValueError('Required existing native file is missing: ' + path)
            self._existing_native_paths.add(path)
        return self.docs.text(path)

    def parsed(self, name):
        path = CATALOG_PATHS.get(name, name); self.text(path)
        return self.docs.parsed(path)

    def signature(self, names):
        return tuple(self.text(name) for name in names)

    def cached(self, key, names, build):
        signature = self.signature(names)
        old = self._cache.get(key)
        if old is None or old[0] != signature:
            old = self._cache[key] = (signature, build())
        return old[1]

    @staticmethod
    def name_parts(raw):
        color = raw[1] if len(raw) > 1 and raw[0] in {'\u00a7', '\x15'} else ''
        return re.sub('[\u00a7\x15].', '', raw), color if color != '!' else ''

    def localisations(self, name):
        from character_model import LOC, unescape
        return {m[1]: unescape(m[3]) for line in self.text(name).splitlines() if (m := LOC.match(line))}

    def set_loc(self, file, key, content):
        from character_model import LOC, quote, unescape
        text = self.text(file); lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if (m := LOC.match(line)) and m[1] == key:
                if unescape(m[3]) == content: return
                lines[i] = line[:m.start(3)] + quote(content)[1:-1] + line[m.end(3):]
                break
        else:
            newline = '\r\n' if '\r\n' in text else '\n'
            if lines and not lines[-1].endswith(('\n', '\r')): lines[-1] += newline
            lines.append(' ' + key + ':0 ' + quote(content) + newline)
        self.docs.replace(CATALOG_PATHS.get(file, file), ''.join(lines))

    def set_name(self, file, key, name, color):
        if not name.strip(): raise ValueError('Enter a display name')
        if len(color) > 1 or color == '!': raise ValueError('Choose one native text color code, or None')
        old = self.localisations(file).get(key, '')
        if self.name_parts(old) == (name, color): return
        self.set_loc(file, key, ('\u00a7' + color + name + '\u00a7!') if color else name)

    def replace_node(self, file, node, raw):
        text = self.text(file)
        self.docs.replace(CATALOG_PATHS.get(file, file), text[:node.start] + raw + text[node.end:])

    def insert(self, file, parent, raw, at=None):
        text = self.text(file)
        at = parent.end - 1 if at is None else at
        self.docs.replace(CATALOG_PATHS.get(file, file), text[:at] + '\n' + raw.rstrip() + '\n' + text[at:])

    def put_root(self, file, key, body):
        text, roots = self.parsed(file); node = next((n for n in roots if n.key == key), None)
        raw = key + ' = {\n' + body.rstrip() + '\n}'
        if node: self.replace_node(file, node, raw)
        else: self.docs.replace(CATALOG_PATHS.get(file, file), text.rstrip() + '\n\n' + raw + '\n')

    def startup(self):
        from character_model import block
        text, roots = self.parsed('startup')
        actions = block(roots, 'on_actions'); startup = block(actions.children, 'on_startup')
        return text, block(startup.children, 'effect')

    @staticmethod
    def checked_ids(text, node, variable):
        return {int(value(text, n)) for _, n in walk([node]) if n.key == variable and n.children is None
                and value(text, n).isdigit() and n.op == '='}

    def groups(self):
        def build():
            loc = self.localisations('culture_loc'); out = {}
            for key, raw in loc.items():
                if (m := re.fullmatch(r'culture_group_(\d+)_name', key)):
                    ident = int(m[1]); name, color = self.name_parts(raw)
                    out[ident] = MapDefinition(ident, name, loc.get(f'culture_group_{ident}_desc', ''), color)
            return out
        return self.cached('groups', ('culture_loc',), build)

    def cultures(self):
        def build():
            loc = self.localisations('culture_loc'); text, effect = self.startup(); membership = {}
            for node in effect.children:
                if node.key == 'add_to_array' and node.children:
                    array = scalar(text, node.children, 'array'); raw = scalar(text, node.children, 'value')
                    if (m := re.fullmatch(r'global.culture_group_(\d+)_array', array)) and raw.isdigit(): membership[int(raw)] = int(m[1])
            colors = self.culture_colors(); out = {}
            for key, raw in loc.items():
                if (m := re.fullmatch(r'culture_(\d+)_name', key)):
                    ident = int(m[1]); name, color = self.name_parts(raw)
                    full = loc.get(f'culture_{ident}_full', ''); group = re.search(r'\$culture_group_(\d+)_name\$', full)
                    out[ident] = MapDefinition(ident, name, loc.get(f'culture_{ident}_desc', ''), color,
                                              colors.get(ident), group=membership.get(ident, int(group[1]) if group else None))
            return out
        return self.cached('cultures', ('culture_loc', 'culture_map', 'startup'), build)

    def culture_colors(self):
        text, roots = self.parsed('culture_map'); channels = {}
        for _, n in walk(roots):
            if n.key == 'add_to_temp_variable' and n.children:
                for c in n.children:
                    if (m := re.fullmatch(r'culture_(\d+)_(red|green|blue)', c.key)):
                        channels.setdefault(int(m[1]), {})[m[2]] = float(value(text, c))
        return {key: self.world._fraction_rgb(v) for key, v in channels.items()}

    def species_traits(self):
        from character_model import atom
        def build():
            text, roots = self.parsed('species_modifiers'); loc = self.localisations('species_loc'); out = {}
            for n in roots:
                if re.fullmatch(r'lok_species_[A-Za-z0-9_]+_trait_modifier', n.key) and n.children is not None:
                    name, color = self.name_parts(loc.get(n.key, n.key))
                    effects = {c.key: value(text, c) for c in n.children if c.children is None and c.key not in {'icon', 'remove_trigger'} }
                    out[n.key] = MapDefinition(n.key, name, loc.get(n.key + '_desc', ''), color,
                                              sprite=atom(text, n.children, 'icon'), effects=effects)
            return out
        return self.cached('species_traits', ('species_modifiers', 'species_loc'), build)

    @staticmethod
    def trait_trigger(key):
        return 'has_' + key.removeprefix('lok_species_').removesuffix('_trait_modifier') + '_trait'

    def species(self):
        def build():
            loc = self.localisations('species_loc'); text, roots = self.parsed('species_triggers'); traits = {}
            for n in roots:
                for ident in self.checked_ids(text, n, 'species'):
                    key = 'lok_species_' + n.key.removeprefix('has_').removesuffix('_trait') + '_trait_modifier'
                    traits.setdefault(ident, []).append(key)
            major, minor = self.species_colors(); out = {}
            for key, raw in loc.items():
                if (m := re.fullmatch(r'var_species_(\d+)', key)) and int(m[1]) != 1000:
                    ident = int(m[1]); name, color = self.name_parts(raw)
                    out[ident] = MapDefinition(ident, name, loc.get(f'var_species_{ident}_desc', ''), color,
                                              major.get(ident), minor.get(ident), traits=tuple(traits.get(ident, [])),
                                              sprite=f'GFX_idea_var_species_{ident}')
            return out
        return self.cached('species', ('species_loc', 'species_map', 'species_triggers'), build)

    def species_colors(self):
        from character_model import block
        text, roots = self.parsed('species_map'); mode = block(block(roots, 'scripted_map_modes').children, 'LOK_species_map_mode')
        out = []
        for part, field in [('bottom', 'species'), ('top', 'minority')]:
            colors = {}; color = block(block(mode.children, part).children, 'color')
            for n in color.children:
                if n.key != 'if': continue
                ids = self.checked_ids(text, n, field)
                rgb = {c.key: float(value(text, c)) for s in n.children if s.key == 'set_temp_variable' for c in s.children if c.key in {'red', 'green', 'blue'}}
                if ids and rgb: colors[next(iter(ids))] = self.world._fraction_rgb(rgb)
            out.append(colors)
        return out

    def sync_world(self):
        signature = self.signature(('culture_loc', 'species_loc', 'culture_map', 'species_map'))
        if signature != self._palette_signature:
            self.world.localisation = self.characters.localisations()
            self.world._demographic_catalogs(); self._palette_signature = signature

    @staticmethod
    def validate_id(ident, current, create, reserved=()):
        if not isinstance(ident, int) or ident < 0 or ident in reserved: raise ValueError('Choose a valid numeric ID')
        if create and ident in current: raise ValueError('That ID already exists')
        if not create and ident not in current: raise ValueError('That definition no longer exists')

    @staticmethod
    def rgb(raw):
        if isinstance(raw, str):
            if not re.fullmatch(r'#[0-9A-Fa-f]{6}', raw): raise ValueError('Use a color such as #336699')
            return tuple(int(raw[i:i+2], 16) for i in (1, 3, 5))
        if len(raw) != 3 or any(not 0 <= v <= 255 for v in raw): raise ValueError('RGB components must be 0–255')
        return tuple(raw)

    def set_map_color(self, kind, ident, rgb, part=None):
        from character_model import block
        rgb = self.rgb(rgb); file = 'culture_map' if kind == 'culture' else 'species_map'
        text, roots = self.parsed(file)
        mode = block(block(roots, 'scripted_map_modes').children, 'LOK_' + kind + '_map_mode')
        section = block(block(mode.children, part or 'bottom').children, 'color')
        field = 'v' if kind == 'culture' else 'minority' if part == 'top' else 'species'
        branches = [n for n in section.children if n.key == 'if' and n.children]
        target = next((n for n in branches if ident in self.checked_ids(text, n, field)), None)
        if target:
            raw = text[target.start:target.end]
        else:
            if not branches: raise ValueError('No native map-color template is available')
            template = next((n for n in branches if 1 in self.checked_ids(text, n, field)), branches[0])
            old = next(iter(self.checked_ids(text, template, field)))
            raw = text[template.start:template.end]
            if kind == 'culture': raw = raw.replace(f'culture_{old}_', f'culture_{ident}_')
            edits = [(n.value_start, n.end, str(ident)) for _, n in walk(parse(raw)) if n.key == field and n.children is None and value(raw, n) == str(old)]
            for start, end, new in sorted(edits, reverse=True): raw = raw[:start] + new + raw[end:]
        edits = []
        for _, n in walk(parse(raw)):
            for key, component in zip(('red', 'green', 'blue'), rgb):
                wanted = f'culture_{ident}_{key}' if kind == 'culture' else key
                if n.key == wanted and n.children is None:
                    edits.append((n.value_start, n.end, format(Decimal(component) / Decimal(255), '.6f')))
        for start, end, new in sorted(edits, reverse=True): raw = raw[:start] + new + raw[end:]
        if target: self.replace_node(file, target, raw)
        else: self.insert(file, section, '\t\t\t\t' + raw)

    def ensure_text_case(self, file, function, ident, variable, loc_key):
        from character_model import atom, block, patch_field
        text, roots = self.parsed(file); node = next((n for n in roots if n.children and atom(text, n.children, 'name') == function), None)
        if node is None: raise ValueError('Missing native scripted localisation function: ' + function)
        entry = next((n for n in node.children if n.key == 'text' and ident in self.checked_ids(text, n, variable)), None)
        if entry:
            if atom(text, entry.children, 'localization_key') == loc_key: return
            self.docs.replace(CATALOG_PATHS[file], patch_field(text, entry, 'localization_key', loc_key)); return
        raw = f'\ttext = {{\n\t\ttrigger = {{ check_variable = {{ {variable} = {ident} }} }}\n\t\tlocalization_key = {loc_key}\n\t}}'
        fallback = next((n for n in node.children if n.key == 'text' and block(n.children, 'trigger') is None), None)
        self.insert(file, node, raw, fallback.start if fallback else None)

    def edit_group(self, ident, name, description, name_color='', create=False):
        from character_model import block
        self.validate_id(ident, self.groups(), create, (0,))
        with self.docs.grouped():
            self.set_name('culture_loc', f'culture_group_{ident}_name', name, name_color)
            self.set_loc('culture_loc', f'culture_group_{ident}_desc', description)
            if create:
                self.put_root('culture_triggers', f'culture_is_culture_group_{ident}', '\tOR = { always = no }')
                self.put_root('culture_effects', f'remove_culture_group_{ident}', f'\tcustom_effect_tooltip = remove_culture_group_{ident}_tt\n\thidden_effect = {{\n\t\tfor_each_loop = {{\n\t\t\tarray = global.culture_group_{ident}_array\n\t\t\tvalue = v\n\t\t\tset_temp_variable = {{ culture_temp = v }}\n\t\t\tremove_state_culture = yes\n\t\t}}\n\t}}')
                self.set_loc('culture_loc', f'remove_culture_group_{ident}_tt', f'$culture_group_{ident}_name$')
                text, startup = self.startup()
                first = next((n for n in startup.children if n.key == 'add_to_array' and 'global.culture_group_' in value(text, n)), None)
                self.insert('startup', startup, f'\t\t\tclear_array = global.culture_group_{ident}_array', first.start if first else startup.value_start + 1)

    def edit_culture(self, ident, name, description, color, name_color, group, create=False):
        from character_model import block, patch_field
        current = self.cultures(); self.validate_id(ident, current, create, (0,))
        if group not in self.groups(): raise ValueError('Choose an existing culture group')
        rgb = self.rgb(color)
        with self.docs.grouped():
            self.set_name('culture_loc', f'culture_{ident}_name', name, name_color)
            self.set_loc('culture_loc', f'culture_{ident}_desc', description)
            self.set_loc('culture_loc', f'culture_{ident}_full', f'$culture_{ident}_name$ is part of the $culture_group_{group}_name$ $culture_group$.$culture_{ident}_desc$')
            if create or current[ident].color != rgb: self.set_map_color('culture', ident, rgb)
            text, startup = self.startup()
            members = [n for n in startup.children if n.key == 'add_to_array' and re.fullmatch(r'global.culture_group_\d+_array', scalar(text, n.children, 'array')) and scalar(text, n.children, 'value') == str(ident)]
            if members:
                edits = []
                for n in members:
                    raw = text[n.start:n.end]; root = parse(raw)[0]
                    raw = patch_field(raw, root, 'array', f'global.culture_group_{group}_array')
                    edits.append((n.start, n.end, raw))
                for start, end, raw in reversed(edits): text = text[:start] + raw + text[end:]
                self.docs.replace(STARTUP, text)
            else:
                cohort = [n for n in startup.children if n.key in {'add_to_array', 'clear_array'} and 'global.culture_group_' in value(text, n)]
                self.insert('startup', startup, f'\t\t\tadd_to_array = {{ array = global.culture_group_{group}_array value = {ident} }}', cohort[-1].end if cohort else startup.value_start + 1)
            text, roots = self.parsed('culture_triggers'); edits = []
            for trigger in roots:
                if not re.fullmatch(r'culture_is_culture_group_\d+', trigger.key): continue
                raw = text[trigger.start:trigger.end]; r = parse(raw)[0]; old = self.checked_ids(raw, r, 'v')
                target_group = int(trigger.key.rsplit('_', 1)[1])
                if (ident in old) == (target_group == group): continue
                container = block(r.children, 'OR')
                if container is None: raise ValueError('Culture group trigger needs a native OR block: ' + trigger.key)
                if ident in old:
                    remove = [n for n in container.children if ident in self.checked_ids(raw, n, 'v')]
                    for n in reversed(remove): raw = raw[:n.start] + raw[n.end:]
                else:
                    at = container.end - 1
                    raw = raw[:at] + f'\n\t\tany_of = {{ array = FROM.state_cultures value = v check_variable = {{ v = {ident} }} }}\n\t' + raw[at:]
                edits.append((trigger.start, trigger.end, raw))
            for start, end, raw in reversed(edits): text = text[:start] + raw + text[end:]
            self.docs.replace(CATALOG_PATHS['culture_triggers'], text)
            for index in range(3):
                self.ensure_text_case('culture_text', f'GetCulture{index+1}', ident, f'state_cultures^{index}', f'culture_{ident}_name')
                self.ensure_text_case('culture_text', f'GetCulture{index+1}Desc', ident, f'state_cultures^{index}', f'culture_{ident}_full')
            self.ensure_text_case('culture_text', 'GetCultureTemp', ident, 'culture_temp', f'culture_{ident}_name')
        self.sync_world()

    def wonder_registry(self):
        text, roots = self.parsed('dynamic')
        node = child(roots, 'lok_wonder_modifier')
        return {n.key: int(m[1]) for n in node.children if n.children is None
                and (m := re.fullmatch(r'wonder_modifiers_values\^(\d+)', value(text, n)))}

    @staticmethod
    def wonder_id(text, node):
        for n in node.children or []:
            if n.key == 'set_variable' and n.children:
                raw = scalar(text, n.children, 'wonder')
                if raw.isdigit(): return int(raw)
            if re.fullmatch(r'setup_wonder_\d+', n.key): return int(n.key.rsplit('_', 1)[1])
        return None

    def wonder_values(self, text, node):
        registry = {i: k for k, i in self.wonder_registry().items()}
        return {registry[int(m[1])]: value(text, c)
                for n in node.children or [] if n.key == 'set_variable' and n.children
                for c in n.children if (m := re.fullmatch(r'wonder_modifiers_values\^(\d+)', c.key)) and int(m[1]) in registry}

    def wonder_sites(self):
        def build():
            text, effect = self.startup(); sites = {}
            for n in effect.children:
                if n.key.isdigit() and n.children and (ident := self.wonder_id(text, n)) is not None:
                    sites[int(n.key)] = ident
            return sites
        return self.cached('wonder_sites', ('startup',), build)

    def wonder_records(self):
        def build():
            loc = self.localisations('wonder_loc'); out = {}; templates = {}
            for file in ('startup', 'effects'):
                text, roots = self.parsed(file)
                for _, n in walk(roots):
                    if n.children and (ident := self.wonder_id(text, n)) is not None:
                        effects = self.wonder_values(text, n)
                        extras = tuple(text[c.start:c.end] for c in n.children if c.key in {'save_global_event_target_as', 'set_state_flag'})
                        if effects or ident not in templates: templates[ident] = (effects, extras)
            for key, raw in loc.items():
                if (m := re.fullmatch(r'var_wonder\.(\d+)', key)) and int(m[1]) > 0:
                    ident = int(m[1]); name, color = self.name_parts(raw)
                    effects, extras = templates.get(ident, ({}, ()))
                    desc = loc.get(f'var_wonder_desc.{ident}', '')
                    desc = re.sub(r'^\$wonder_effects_tooltips\$(?:\\n|\n)?', '', desc)
                    out[ident] = MapDefinition(ident, name, desc, color, sprite=f'GFX_wonder_{ident}', effects=effects, extras=extras)
            return out
        return self.cached('wonders', ('wonder_loc', 'startup', 'effects', 'dynamic'), build)

    def wonder_script_blocks(self, ident):
        # Only parse candidate files, on demand when editing a wonder. No scan on map redraw.
        candidates = set(self.characters.files('common', '.txt')) | set(self.characters.files('events', '.txt'))
        pattern = re.compile(r'\bwonder\s*=\s*' + str(ident) + r'\b')
        found = []
        for path in sorted(candidates):
            text = self.docs.text(path)
            if not pattern.search(text): continue
            roots = parse(text)
            for _, n in walk(roots):
                if n.children and self.wonder_id(text, n) == ident and self.wonder_values(text, n):
                    found.append((path, text, n))
        return found

    def wonder_detail(self, ident):
        record = self.wonder_records()[ident]
        if record.effects: return record
        for _, text, node in self.wonder_script_blocks(ident):
            record.effects = self.wonder_values(text, node)
            record.extras = tuple(text[c.start:c.end] for c in node.children if c.key in {'save_global_event_target_as', 'set_state_flag'})
            break
        return record

    def add_wonder_modifier(self, key, percent=False):
        from character_model import patch_field
        registry = self.wonder_registry()
        if key in registry: return registry[key]
        catalog = self.characters.trait_store.modifier_catalog()
        if key not in catalog: raise ValueError('Choose a defined modifier')
        index = max(registry.values(), default=-1) + 1
        text, roots = self.parsed('dynamic'); node = child(roots, 'lok_wonder_modifier')
        self.docs.replace(CATALOG_PATHS['dynamic'], patch_field(text, node, key, f'wonder_modifiers_values^{index}'))
        text, roots = self.parsed('effects'); count = child(roots, '@wonder_modifier_count')
        if count is None: raise ValueError('Missing native wonder modifier count')
        self.docs.edit(CATALOG_PATHS['effects'], count, str(index + 1))
        text = self.text('wonder_text')
        self.docs.replace(CATALOG_PATHS['wonder_text'], text.rstrip() + f'\n\ndefined_text = {{\n\tname = wonder_modifier_{index}_scripted\n\ttext = {{\n\t\ttrigger = {{ check_variable = {{ var = THIS.wonder_modifiers_values^{index} value = 0 compare = not_equals }} }}\n\t\tlocalization_key = wonder_modifiers_{index}\n\t}}\n\ttext = {{ localization_key = wonder_effects_NA }}\n}}\n')
        entry = catalog[key]; label = '$' + entry['localisation_key'] + '$' if entry.get('localized') else entry['choice'].name
        self.set_loc('wonder_loc', f'wonder_modifiers_{index}', label + f': [?THIS.wonder_modifiers_values_real^{index}|' + ('%' if percent else '') + '+1=]\\n')
        tooltip = self.localisations('wonder_loc').get('wonder_effects_tooltips', '')
        self.set_loc('wonder_loc', 'wonder_effects_tooltips', tooltip + f'[wonder_modifier_{index}_scripted]')
        return index

    def wonder_body(self, ident, effects, extras=()):
        registry = self.wonder_registry()
        lines = [f'\tset_variable = {{ wonder = {ident} }}', '\tsetup_wonder_array = yes']
        lines += [f'\tset_variable = {{ wonder_modifiers_values^{registry[k]} = {_catalog_decimal(v)} }}' for k, v in effects.items()]
        lines += ['\t' + raw for raw in extras]
        return '\n'.join(lines)

    @staticmethod
    def strip_wonder(text, node, markers=False):
        edits = []
        for n in node.children:
            if n.key == 'set_variable' and n.children:
                owned = [c for c in n.children if c.key == 'wonder' or re.fullmatch(r'wonder_modifiers_values(?:_real)?\^\d+', c.key)]
                if len(owned) == len(n.children): edits.append((n.start, n.end, ''))
                else: edits.extend((c.start, c.end, '') for c in owned)
            elif n.key == 'setup_wonder_array' or re.fullmatch(r'setup_wonder_\d+', n.key) or markers and n.key in {'save_global_event_target_as', 'set_state_flag'}:
                edits.append((n.start, n.end, ''))
        raw = text[node.start:node.end]
        for start, end, replacement in sorted(edits, reverse=True): raw = raw[:start-node.start] + replacement + raw[end-node.start:]
        return raw

    def edit_wonder(self, ident, name, description, effects, icon=None, create=False, percent=(), update_scripts=False):
        current = self.wonder_records(); self.validate_id(ident, current, create, (0,))
        if not name.strip(): raise ValueError('Enter a display name')
        values = {k: _catalog_decimal(v) for k, v in effects.items()}
        known = self.characters.trait_store.modifier_catalog()
        registry = self.wonder_registry()
        if any(k not in known and k not in registry for k in values): raise ValueError('Choose defined wonder modifiers')
        extras = () if create else self.wonder_detail(ident).extras
        with self.docs.grouped():
            for key in values:
                if key not in registry: self.add_wonder_modifier(key, key in percent)
            self.set_loc('wonder_loc', f'var_wonder.{ident}', name)
            self.set_loc('wonder_loc', f'var_wonder_desc.{ident}', '$wonder_effects_tooltips$\\n' + description)
            if icon: self.import_icon('wonder', ident, icon)
            elif create: raise ValueError('Import an icon for the new wonder')
            # A native scripted effect retains definitions of unplaced wonders.
            self.put_root('effects', f'setup_wonder_{ident}', self.wonder_body(ident, values, extras))
            paths = {CATALOG_PATHS['startup']}
            if update_scripts: paths.update(path for path, _, _ in self.wonder_script_blocks(ident))
            for path in paths:
                text, roots = self.characters.parsed(path); edits = []
                for _, n in walk(roots):
                    if not n.children or self.wonder_id(text, n) != ident: continue
                    if n.key == f'setup_wonder_{ident}': continue
                    raw = self.strip_wonder(text, n)
                    root = parse(raw)[0]; at = root.end - 1
                    # Existing flags/targets are left in their authored scopes.
                    raw = raw[:at] + '\n' + self.wonder_body(ident, values) + '\n' + raw[at:]
                    edits.append((n.start, n.end, raw))
                for start, end, raw in sorted(edits, reverse=True): text = text[:start] + raw + text[end:]
                self.docs.replace(path, text)
            self.ensure_text_case('species_text', 'GetWonder', ident, 'wonder', f'var_wonder.{ident}')
            self.ensure_text_case('species_text', 'GetWonderDesc', ident, 'wonder', f'var_wonder_desc.{ident}')

    def paint_wonder(self, states, ident, operation='Move'):
        from character_model import patch_field
        states = tuple(states)
        if not states: return ()
        if any(s not in self.world.states for s in states): raise ValueError('Unknown state')
        if ident and ident not in self.wonder_records(): raise ValueError('Choose a defined wonder')
        record = self.wonder_detail(ident) if ident else None
        if ident and operation == 'Move' and len(states) != 1: raise ValueError('Move a wonder to one state, or choose Place copies for region painting')
        if record and record.extras and (operation != 'Move' or len(states) != 1):
            raise ValueError('This wonder has a unique scripted location. Use Move with State scope.')
        sites = self.wonder_sites(); remove = set(states)
        if ident and operation == 'Move': remove.update(s for s, w in sites.items() if w == ident)
        text, startup = self.startup(); edits = []
        for n in startup.children:
            if not n.key.isdigit() or int(n.key) not in remove or self.wonder_id(text, n) is None: continue
            old_id = self.wonder_id(text, n)
            # Transfer only markers owned by the wonder being moved.
            markers = bool(ident and old_id == ident and operation == 'Move' and record.extras)
            raw = self.strip_wonder(text, n, markers)
            if not parse(raw)[0].children: raw = ''
            edits.append((n.start, n.end, raw))
        for start, end, raw in sorted(edits, reverse=True): text = text[:start] + raw + text[end:]
        at = startup.end - 1 + sum(len(raw) - (end - start) for start, end, raw in edits)
        with self.docs.grouped():
            if ident:
                # Register the reusable native definition only when first used/edited.
                self.put_root('effects', f'setup_wonder_{ident}', self.wonder_body(ident, record.effects, record.extras))
                addition = ''.join(f'\n\t\t\t{s} = {{ setup_wonder_{ident} = yes controller = {{ apply_wonder_effects = yes }} }}\n' for s in states)
                text = text[:at] + addition + text[at:]
            self.docs.replace(STARTUP, text)
        return tuple(sorted(remove))

    def put_sprite(self, file, sprite, texture):
        from character_model import atom, block, patch_field, quote
        entries = self.characters.sprites().get(sprite, [])
        if entries:
            for entry in entries:
                text = self.docs.text(entry['path'])
                node = next(n for _, n in walk(parse(text)) if n.children and atom(text, n.children, 'name') == sprite)
                self.docs.replace(entry['path'], patch_field(text, node, 'texturefile', quote(texture)))
        else:
            text, roots = self.parsed(file); root = block(roots, 'spriteTypes')
            if root is None: raise ValueError('Existing GFX file needs a spriteTypes block')
            self.insert(file, root, f'\tspriteType = {{ name = {quote(sprite)} texturefile = {quote(texture)} }}')

    def import_icon(self, kind, ident, source):
        names = {'species': (f'GFX_idea_var_species_{ident}', 'species_gfx', 'species', (60, 60)),
                 'wonder': (f'GFX_wonder_{ident}', 'wonder_gfx', 'wonders', (100, 61)),
                 'trait': ('GFX_' + str(ident), 'trait_gfx', 'state_modifiers', (36, 36))}
        sprite, file, folder, size = names[kind]
        existing = self.characters.sprites().get(sprite, [])
        if existing:
            image = self.characters.image(sprite)
            if image is not None: size = image.size
        stem = f'{kind}_{ident}' if kind != 'trait' else str(ident)
        destination = f'gfx/interface/{folder}/{stem}.dds'
        allowed = {sprite, f'GFX_species_{ident}'} if kind == 'species' else {sprite}
        original_path = existing[0]['texture'] if existing else ''
        all_sprites = self.characters.sprites()
        suffix = 2
        while self.docs.binary(destination) is not None and (destination != original_path or any(
                e['texture'] == destination for key, entries in all_sprites.items() if key not in allowed for e in entries)):
            destination = f'gfx/interface/{folder}/{stem}_{suffix}.dds'; suffix += 1
        with Image.open(source) as opened:
            image = ImageOps.contain(opened.convert('RGBA'), size, Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', size); canvas.alpha_composite(image, ((size[0]-image.width)//2, (size[1]-image.height)//2))
            output = io.BytesIO(); canvas.save(output, format='DDS')
        self.docs.stage_bytes(destination, output.getvalue()); self.put_sprite(file, sprite, destination)
        if kind == 'species' and f'GFX_species_{ident}' in all_sprites:
            self.put_sprite(file, f'GFX_species_{ident}', destination)
        return sprite

    def edit_species_trait(self, key, name, description, effects, icon=None, create=False):
        from character_model import atom, patch_field
        if not re.fullmatch(r'lok_species_[a-z][a-z0-9_]*_trait_modifier', key):
            raise ValueError('Use lok_species_<unique_name>_trait_modifier')
        current = self.species_traits()
        if create and (key in current or key in self.characters.localisations()): raise ValueError('That species trait already exists')
        if not create and key not in current: raise ValueError('Select an existing species trait')
        values = {k: _catalog_decimal(v) for k, v in effects.items()}
        known = self.characters.trait_store.modifier_catalog()
        if any(k not in known for k in values): raise ValueError('Choose defined state modifier IDs')
        with self.docs.grouped():
            if create:
                self.put_root('species_modifiers', key, f'\tenable = {{ always = yes }}\n\ticon = GFX_{key}')
                self.put_root('species_triggers', self.trait_trigger(key), '\tOR = { always = no }')
                text, roots = self.parsed('effects')
                clear = next(n for n in roots if n.key == 'clear_all_state_species_modifier')
                self.insert('effects', clear, f'\tif = {{\n\t\tlimit = {{ has_dynamic_modifier = {{ modifier = {key} }} }}\n\t\tremove_dynamic_modifier = {{ modifier = {key} }}\n\t}}')
                text, roots = self.parsed('effects'); apply = next(n for n in roots if n.key == 'apply_state_species_modifier')
                self.insert('effects', apply, f'\tif = {{\n\t\tlimit = {{ {self.trait_trigger(key)} = yes }}\n\t\tadd_dynamic_modifier = {{ modifier = {key} }}\n\t}}')
            text, roots = self.parsed('species_modifiers'); node = next(n for n in roots if n.key == key)
            old = current[key].effects if not create else {}
            raw = text[node.start:node.end]
            for remove in set(old) - values.keys():
                root = parse(raw)[0]
                for n in reversed([n for n in root.children if n.key == remove]): raw = raw[:n.start] + raw[n.end:]
            for modifier, amount in values.items(): raw = patch_field(raw, parse(raw)[0], modifier, amount)
            self.replace_node('species_modifiers', node, raw)
            self.set_loc('species_loc', key, name); self.set_loc('species_loc', key + '_desc', description)
            if icon: self.import_icon('trait', key, icon)
            elif create:
                # Reuse an existing registered native icon; no fabricated binary placeholder.
                template = next((r.sprite for r in current.values() if self.characters.image(r.sprite) is not None), '')
                if not template: raise ValueError('Import an icon for the new species trait')
                path = self.characters.sprite_entries(template)[0]['texture']; self.put_sprite('trait_gfx', 'GFX_' + key, path)

    def edit_species(self, ident, name, description, color, minority_color, name_color, traits, icon=None, create=False):
        from character_model import block, patch_field
        current = self.species(); self.validate_id(ident, current, create, (1000,))
        if any(key not in self.species_traits() for key in traits): raise ValueError('Choose existing species state traits')
        rgb, minor = self.rgb(color), self.rgb(minority_color)
        with self.docs.grouped():
            self.set_name('species_loc', f'var_species_{ident}', name, name_color)
            self.set_loc('species_loc', f'var_species_{ident}_desc', description)
            self.set_loc('species_loc', f'var_minority_desc.{ident}', f'$var_species_{ident}_desc$')
            if create or current[ident].color != rgb: self.set_map_color('species', ident, rgb, 'bottom')
            if create or current[ident].minority_color != minor: self.set_map_color('species', ident, minor, 'top')
            if icon: self.import_icon('species', ident, icon)
            elif create: raise ValueError('Import an icon for the new species')
            if create:
                text, roots = self.parsed('species_ideas'); ideas = block(block(roots, 'ideas').children, 'species')
                self.insert('species_ideas', ideas, f'\t\tvar_species_{ident} = {{\n\t\t\tallowed = {{ always = no }}\n\t\t\tremoval_cost = -1\n\t\t\tallowed_to_remove = {{ always = no }}\n\t\t\tcancel_if_invalid = no\n\t\t}}')
                text, roots = self.parsed('advisor_triggers'); trigger = next((n for n in roots if n.key == f'tag_is_species_{ident}'), None)
                # Vacant generated slots contain only always=no; never erase authored tag lists.
                if trigger is None or not any(n.key == 'original_tag' for _, n in walk([trigger])):
                    self.put_root('advisor_triggers', f'tag_is_species_{ident}', f'\thas_idea = var_species_{ident}')
                text, roots = self.parsed('effects'); clear = next(n for n in roots if n.key == 'clear_all_species_ideas')
                if ident >= 100:
                    loops = [(n, c) for _, n in walk([clear]) if n.key == 'for_loop_effect' for c in n.children if c.key == 'end' and value(text, c).isdigit() and int(value(text, c)) >= 100]
                    for _, c in reversed(loops):
                        if int(value(text, c)) <= ident: self.docs.edit(CATALOG_PATHS['effects'], c, str(ident + 1))
            text, roots = self.parsed('species_triggers'); edits = []
            for key in self.species_traits():
                trigger_key = self.trait_trigger(key); node = next((n for n in roots if n.key == trigger_key), None)
                if node is None: raise ValueError('Missing species trait trigger: ' + trigger_key)
                old = self.checked_ids(text, node, 'species')
                if (ident in old) == (key in traits): continue
                raw = text[node.start:node.end]; root = parse(raw)[0]; container = block(root.children, 'OR')
                if container is None: raise ValueError('Species trait needs its native OR membership block: ' + trigger_key)
                if ident in old:
                    for n in reversed([n for n in container.children if ident in self.checked_ids(raw, n, 'species')]): raw = raw[:n.start] + raw[n.end:]
                else:
                    at = container.end - 1; raw = raw[:at] + f'\n\t\tcheck_variable = {{ species = {ident} }}\n\t' + raw[at:]
                edits.append((node.start, node.end, raw))
            for start, end, raw in sorted(edits, reverse=True): text = text[:start] + raw + text[end:]
            self.docs.replace(CATALOG_PATHS['species_triggers'], text)
            for function, variable, key in [('GetSpecies', 'species', f'var_species_{ident}'), ('GetSpeciesDesc', 'species', f'var_species_{ident}_desc'),
                                             ('GetMinority', 'minority', f'var_species_{ident}'), ('GetMinorityDesc', 'minority', f'var_minority_desc.{ident}'),
                                             ('GetSpeciesTemp', 'species_temp', f'var_species_{ident}')]:
                self.ensure_text_case('species_text', function, ident, variable, key)
        self.sync_world()
