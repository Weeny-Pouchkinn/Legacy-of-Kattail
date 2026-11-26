"""Native trait databases, modifier catalog and draft-only commander randomizers."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from decimal import Decimal, InvalidOperation
import random
import re

from model import parse, value, walk, read_text
from character_model import atom, block, patch_field, quote, unescape, LOC, sort_name, inherited_localisations
from select_ui import Choice

TRAIT_LOC = 'localisation/english/painter/traits_l_english.yml'
TRAIT_PATHS = {'unit': 'common/unit_leader/lok_traits.txt', 'country': 'common/country_leader/lok_traits.txt'}
FOLDERS = {'unit': 'common/unit_leader', 'country': 'common/country_leader'}
MILITARY = ('corps_commander', 'field_marshal', 'navy_leader')
STAT_FIELDS = {'land': ('attack_skill', 'defense_skill', 'planning_skill', 'logistics_skill'),
               'navy': ('attack_skill', 'defense_skill', 'maneuvering_skill', 'coordination_skill')}
TRAIT_TYPES = ('personality_trait', 'basic_trait', 'basic_terrain_trait', 'assignable_trait',
               'assignable_terrain_trait', 'status_trait', 'exile')
MODIFIER_BLOCKS = ('modifier', 'non_shared_modifier', 'corps_commander_modifier', 'field_marshal_modifier')


@dataclass(frozen=True)
class Trait:
    key: str
    family: str
    path: str
    text: str
    node: object
    origin: str
    active: bool = True

    @property
    def unit_type(self):
        return atom(self.text, self.node.children, 'type') if self.family == 'unit' else 'country'

    @property
    def trait_type(self):
        return atom(self.text, self.node.children, 'trait_type')

    @property
    def groups(self):
        if self.family == 'country': return ('Political advisors',)
        groups = []
        if self.unit_type in {'all', 'land', 'corps_commander', 'field_marshal'}: groups.append('Generals')
        if self.unit_type in {'all', 'navy'}: groups.append('Admirals')
        return tuple(groups) or ('Other unit traits',)


@lru_cache(maxsize=2)
def vanilla_traits(game_root):
    records = []
    for family, folder in FOLDERS.items():
        for path in sorted((Path(game_root) / folder).rglob('*.txt')):
            text = read_text(path)
            for root in parse(text):
                if root.key == 'leader_traits' and root.children:
                    records.extend(Trait(n.key, family, path.relative_to(game_root).as_posix(), text, n, 'Vanilla')
                                   for n in root.children if n.children is not None)
    return tuple(records)


def _number(raw):
    if str(raw).strip() in {'yes', 'no'}: return str(raw).strip()
    try:
        number = Decimal(str(raw))
    except InvalidOperation:
        raise ValueError('Enter a finite number, for example 0.1 or -0.05') from None
    if not number.is_finite(): raise ValueError('Modifier value must be finite')
    return format(number, 'f')


def documented_modifiers(text):
    """Expand the engine's static entries and supplied parameterized type lists.

    Categories control tooltip filtering, not which script scopes may add a
    modifier (see common/modifier_definitions/modifier_definitions.txt).
    """
    result = {}
    sections = list(re.finditer(r'^##[ \t]+([^\r\n]+)', text, re.M))
    for index, section in enumerate(sections):
        heading = re.sub(r'<span\b[^>]*>\s*</span>', '', section[1]).strip()
        body = text[section.end():sections[index+1].start() if index+1 < len(sections) else len(text)]
        category = re.search(r'\*\*Categories\*\*:[ \t]*([^\r\n]+)', body)
        categories = {c.strip() for c in category[1].split(',')} if category else set()
        description = re.search(r'\*\*Description\*\*:[ \t]*([^\r\n]+)', body)
        boolean = bool(re.search(r'^\*[ \t]+Boolean[ \t]*\r?$',body,re.M))
        precision = re.search(r'^\*[ \t]+Number with (\d+) decimal places',body,re.M)
        parameter = re.search(r'<[A-Za-z][A-Za-z0-9_]*>', heading)
        if parameter and re.fullmatch(r'[A-Za-z0-9_]*<[A-Za-z][A-Za-z0-9_]*>[A-Za-z0-9_]*', heading):
            types = re.search(r'\*\*Modified types\*\*:[ \t]*([^\r\n]+)', body)
            keys = [heading.replace(parameter[0],t.strip()) for t in types[1].split(',')] if types else []
        elif re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', heading):
            keys = [heading]
        else:
            continue
        for key in keys:
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', key): continue
            entry = result.setdefault(key, {'categories': set(), 'source': 'Game modifier documentation'})
            entry['categories'].update(categories)
            entry['value_type'] = 'yes_no' if boolean else 'number'
            if precision: entry['precision'] = int(precision[1])
            if parameter: entry['template'] = heading
            if description: entry['description'] = description[1].strip()
    return result


class TraitStore:
    def __init__(self, characters):
        self.characters, self.docs = characters, characters.docs
        self._signature = None
        self._records = None
        self._modifiers = None
        self._rules = None
        self._names = None
        self._seen_revision = -1
        self._seen_game = None
        self._name_cache = {}
        self._choices_by_role = {}
        self.warnings = []

    def signature(self):
        prefixes = ('common/unit_leader/', 'common/country_leader/', 'common/modifier_definitions/', 'common/defines/', 'localisation/')
        return (str(self.characters.game_root),
                tuple(sorted((p, id(v)) for p, v in self.docs.drafts.items() if p.startswith(prefixes) or p == 'descriptor.mod')),
                tuple((p, self.docs.snapshots[p]) for p in self.docs.originals if p.startswith(prefixes) or p == 'descriptor.mod'))

    def sync(self):
        game = str(self.characters.game_root)
        if self._seen_revision == self.docs.revision and self._seen_game == game: return
        self._seen_revision, self._seen_game = self.docs.revision, game
        signature = self.signature()
        if signature != self._signature:
            self._signature = signature
            self._records = self._modifiers = self._rules = self._names = None
            self._name_cache.clear(); self._choices_by_role.clear()

    def names(self):
        self.sync()
        if self._names is None:
            self._names = dict(inherited_localisations(str(self.characters.game_root)))
            self._names.update(self.characters.localisations())
            self._signature = self.signature()
        return self._names

    def name(self, key):
        self.sync()
        if key in self._name_cache: return self._name_cache[key]
        loc = self.names()
        text = loc.get(key, key)
        for _ in range(8):
            updated = re.sub(r'\$([^$|]+)\$', lambda m: loc.get(m[1], m[0]), text)
            if updated == text: break
            text = updated
        self._name_cache[key] = text
        return text

    def records(self):
        self.sync()
        if self._records is not None: return self._records
        descriptor = self.docs.text('descriptor.mod')
        replaced = [value(descriptor, n).strip('"').rstrip('/') for n in parse(descriptor) if n.key == 'replace_path']
        paths = {family: self.characters.files(folder, '.txt') for family, folder in FOLDERS.items()}
        mod_paths = {p for files in paths.values() for p in files if self.docs.binary(p) is not None}
        records = []
        for record in vanilla_traits(str(self.characters.game_root)):
            active = record.path not in mod_paths and not any(record.path == p or record.path.startswith(p + '/') for p in replaced)
            records.append(Trait(record.key, record.family, record.path, record.text, record.node, record.origin, active))
        for family, files in paths.items():
            for path in files:
                text, roots = self.characters.parsed(path)
                for root in roots:
                    if root.key == 'leader_traits' and root.children:
                        records.extend(Trait(n.key, family, path, text, n, 'Mod') for n in root.children if n.children is not None)
        mod_keys = {(t.family, t.key) for t in records if t.origin == 'Mod'}
        self._records = tuple(Trait(t.key, t.family, t.path, t.text, t.node, t.origin,
                                   t.active and (t.origin == 'Mod' or (t.family, t.key) not in mod_keys)) for t in records)
        self._signature = self.signature()
        return self._records

    def effective(self):
        out = {}
        for trait in self.records():
            if trait.active: out[(trait.family, trait.key)] = trait
        return out

    def choices_for_role(self, role):
        self.sync()
        if role in self._choices_by_role: return self._choices_by_role[role]
        group = 'Admirals' if role == 'navy_leader' else 'Generals' if role in MILITARY else 'Political advisors'
        records = {t.key: t for t in self.records() if t.active and group in t.groups}
        result = tuple(sorted((Choice(key, self.name(key)) for key in records), key=lambda c: (sort_name(c.name), c.code)))
        self._choices_by_role[role] = result
        return result

    def modifier_catalog(self):
        self.sync()
        if self._modifiers is not None: return self._modifiers
        info = {}
        path = self.characters.game_root / 'documentation/modifiers_documentation.md'
        if path.is_file():
            info.update(documented_modifiers(read_text(path)))
        for directory, origin in [(self.characters.game_root / 'common/modifier_definitions', 'Vanilla modifier definition'),
                                  (self.characters.world.root / 'common/modifier_definitions', 'Mod modifier definition')]:
            files = (self.characters.files('common/modifier_definitions', '.txt') if origin.startswith('Mod ') else
                     [p.as_posix() for p in sorted(directory.rglob('*.txt'))])
            for filename in files:
                text, roots = self.characters.parsed(filename) if origin.startswith('Mod ') else (read_text(Path(filename)), None)
                for node in roots if roots is not None else parse(text):
                    if node.children is None: continue
                    categories = {value(text, n).strip('"') for n in node.children if n.key == 'category'}
                    info[node.key] = {'categories': categories, 'source': origin,
                                      'value_type': atom(text,node.children,'value_type','number')}
        # Native unit-trait stat bonuses belong directly on a trait, not in its modifier block.
        for field in set(sum((list(v) for v in STAT_FIELDS.values()), [])):
            info.setdefault(field, {'categories': {'unit_leader'}, 'source': 'Unit trait stat bonus', 'trait_stat': True})
            info.setdefault(field + '_factor', {'categories': {'unit_leader'}, 'source': 'Unit trait stat weight', 'trait_stat': True})
        loc = self.names()
        for key, entry in info.items():
            aliases = {'max_commander_army_size': 'MODIFIER_ARMY_LEADER_MAX_ARMY_SIZE',
                       'max_army_group_size': 'MODIFIER_ARMY_LEADER_MAX_ARMY_GROUP_SIZE'}
            candidates = (key, 'MODIFIER_' + key.upper(), 'MODIFIERS_' + key.upper(), 'modifier_' + key, aliases.get(key, ''))
            tooltip = loc.get(key + '_tt', '')
            candidates += tuple(re.findall(r'\$(MODIFIERS?_[A-Z0-9_]+)\$', tooltip))
            loc_key = next((k for k in candidates if k in loc), key)
            entry['localized'] = loc_key in loc
            entry['localisation_key'] = loc_key
            entry['choice'] = Choice(key, self.name(loc_key) if loc_key in loc else key.replace('_', ' ').title())
        self._modifiers = info
        self._signature = self.signature()
        return info

    def modifier_choices(self):
        return tuple(sorted((v['choice'] for v in self.modifier_catalog().values()), key=lambda c: (sort_name(c.name), c.code)))

    def spirit_modifier_choices(self):
        return tuple(sorted((v['choice'] for v in self.modifier_catalog().values() if not v.get('trait_stat')), key=lambda c: (sort_name(c.name), c.code)))

    def modifier_value(self, key, raw):
        text = str(raw).strip()
        if text in {'yes','no'} and self.modifier_catalog().get(key,{}).get('value_type') != 'yes_no':
            raise ValueError('Use a finite number for this modifier')
        return _number(text)

    def modifier_rows(self, trait):
        catalog = self.modifier_catalog(); rows = []
        for node in trait.node.children:
            if node.children is not None and node.key in MODIFIER_BLOCKS:
                rows.extend((node.key, n.key, value(trait.text, n)) for n in node.children if n.children is None)
            elif node.children is None and node.key in catalog:
                rows.append(('root', node.key, value(trait.text, node)))
        return rows

    @staticmethod
    def body(trait, clone=False):
        body = value(trait.text, trait.node)[1:-1]
        if not clone: return body
        constants = {n.key: value(trait.text, n) for n in parse(trait.text) if n.key.startswith('@')}
        wrapped = 'trait = {' + body + '}'
        edits = []
        for _, node in walk(parse(wrapped)):
            if node.children is not None: continue
            raw = value(wrapped, node)
            seen = set()
            while re.fullmatch(r'@[A-Za-z0-9_]+', raw):
                if raw in seen or raw not in constants: raise ValueError('Cannot clone unresolved file constant: ' + raw)
                seen.add(raw); raw = constants[raw]
            if raw != value(wrapped, node): edits.append((node.value_start, node.end, raw))
        for start, end, raw in sorted(edits, reverse=True): wrapped = wrapped[:start] + raw + wrapped[end:]
        return value(wrapped, parse(wrapped)[0])[1:-1]

    def edit(self, key, family, name, description, body, create=False, source=None):
        if family not in FOLDERS: raise ValueError('Choose a military or political trait database')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', key): raise ValueError('Trait ID must use letters, digits and underscores')
        if not name.strip(): raise ValueError('Enter the trait display name')
        definitions = [t for t in self.records() if t.key == key]
        if create and (definitions or key in self.names() or key + '_desc' in self.names()):
            raise ValueError('Trait ID or its localisation already exists; choose a unique ID')
        roots = parse('trait = {\n' + body + '\n}')
        node = roots[0]
        unit_type = atom('trait = {\n' + body + '\n}', node.children, 'type')
        if family == 'unit' and unit_type not in {'', 'land', 'corps_commander', 'field_marshal', 'navy', 'all', 'operative'}:
            raise ValueError('Military traits need a defined unit type')
        path = TRAIT_PATHS[family]
        if not create:
            matching = [t for t in definitions if t.family == family and t.origin == 'Mod' and (source is None or t.path == source)]
            if len(matching) != 1: raise ValueError('Select one mod definition to edit; clone vanilla traits under a new ID')
            path = matching[0].path
        with self.docs.grouped():
            text = self.docs.text(path) or 'leader_traits = {\n}\n'
            root = block(parse(text), 'leader_traits')
            if root is None: raise ValueError('Trait file has no leader_traits block')
            entry = next((n for n in root.children if n.key == key), None)
            raw = key + ' = {\n' + body.rstrip() + '\n\t}'
            if entry: updated = text[:entry.start] + raw + text[entry.end:]
            else: updated = text[:root.end - 1] + '\t' + raw + '\n' + text[root.end - 1:]
            self.docs.replace(path, updated)
            if path == TRAIT_PATHS[family]: self.organise(path)
            self.set_localisation(key, name, description)

    def set_localisation(self, key, name, description):
        values = {key: name, key + '_desc': description}
        # Explicit trait edits move only their own two strings; all other authored text stays.
        for relative in self.characters.files('localisation/english', '.yml'):
            if relative == TRAIT_LOC: continue
            text = self.docs.text(relative)
            updated = ''.join(line for line in text.splitlines(keepends=True) if not ((m := LOC.match(line)) and m[1] in values))
            if updated != text: self.docs.replace(relative, updated)
        text = self.docs.text(TRAIT_LOC) or 'l_english:\n'
        lines, notes = {}, []
        for line in text.splitlines()[1:]:
            if (m := LOC.match(line)):
                if m[1] in lines: raise ValueError('Duplicate key in managed trait localisation: ' + m[1])
                lines[m[1]] = line.rstrip()
            elif line.strip(): notes.append(line)
        for loc_key, content in values.items(): lines[loc_key] = ' ' + loc_key + ':0 ' + quote(content)
        output = ['l_english:'] + notes + [''] + [lines[k] for k in sorted(lines, key=lambda k: (k.casefold(), k))]
        self.docs.replace(TRAIT_LOC, '\n'.join(output) + '\n')

    def organise(self, path):
        text = self.docs.text(path); root = block(parse(text), 'leader_traits')
        if root is None: return
        entries, last = [], root.value_start + 1
        for node in root.children:
            prefix = text[last:node.start].strip()
            entries.append((node.key.casefold(), node.key, ('\t' + prefix + '\n' if prefix else '') + '\t' + text[node.start:node.end]))
            last = node.end
        suffix = text[last:root.end - 1].strip()
        body = '\n\n'.join(raw for _, _, raw in sorted(entries))
        self.docs.replace(path, text[:root.value_start] + '{\n' + body + ('\n\t' + suffix if suffix else '') + '\n}' + text[root.end:])

    def skill_rules(self, role):
        if role not in MILITARY: raise ValueError('Skill randomization is available for generals and admirals')
        self.sync()
        if self._rules is None or not self._rules.get('_ready'):
            self._rules = {}
            files = {p.name: (read_text(p), 'Vanilla') for p in (self.characters.game_root / FOLDERS['unit']).glob('*skills*.txt')}
            for relative in self.characters.files(FOLDERS['unit'], '.txt'):
                if 'skills' in Path(relative).stem: files[Path(relative).name] = (self.docs.text(relative), 'Mod')
            for text, _ in files.values():
                for root in parse(text):
                    if not root.children: continue
                    for n in root.children:
                        if n.children and n.key.isdigit():
                            kind = atom(text, n.children, 'type')
                            self._rules.setdefault((root.key, kind), set()).add(int(n.key))
            mod_files = self.characters.files('common/defines', '.lua')
            overrides = {Path(p).name for p in mod_files if self.docs.binary(p) is not None}
            defines = [read_text(p) for p in sorted((self.characters.game_root / 'common/defines').glob('*.lua')) if p.name not in overrides]
            defines.extend(self.docs.text(p) for p in mod_files)
            rules_text = '\n'.join(re.sub(r'--[^\n]*', '', t) for t in defines)
            for key in ['COMMANDER_LEVEL_UP_STAT_COUNT', 'COMMANDER_LEVEL_UP_STAT_WEIGHTS', 'NAVY_LEADER_LEVEL_UP_STAT_WEIGHTS']:
                matches = re.findall(r'\b' + key + r'\s*=\s*(\{[^}]+\}|[^\n,]+)', rules_text)
                if not matches: raise ValueError('Installed commander rules are unavailable: ' + key)
                if not re.fullmatch(r'\s*(\{\s*[0-9\s,]+\}|[0-9]+)\s*', matches[-1]):
                    raise ValueError('Commander rule uses an unsupported Lua expression: ' + key)
                self._rules[key] = [int(n) for n in re.findall(r'\d+', matches[-1])]
            self._rules['_ready'] = True
            self._signature = self.signature()
        kind = 'navy' if role == 'navy_leader' else role
        levels = self._rules.get(('leader_skills', kind), set())
        fields = STAT_FIELDS['navy' if kind == 'navy' else 'land']
        ranges = [self._rules.get(('leader_' + field.replace('_skill', '') + '_skills', kind), set()) for field in fields]
        if not levels or any(not r for r in ranges): raise ValueError('Complete installed skill tables are required')
        return levels, fields, ranges, self._rules['COMMANDER_LEVEL_UP_STAT_COUNT'][0], self._rules[
            'NAVY_LEADER_LEVEL_UP_STAT_WEIGHTS' if kind == 'navy' else 'COMMANDER_LEVEL_UP_STAT_WEIGHTS']

    def random_skills(self, role, level, rng=None):
        levels, fields, ranges, per_level, weights = self.skill_rules(role)
        if not str(level).isdigit() or int(level) not in levels: raise ValueError('Level must be one of ' + ', '.join(map(str, sorted(levels))))
        if len(weights) != len(fields): raise ValueError('Commander stat weights do not match the skill fields')
        rng = rng or random.SystemRandom(); result = {field: min(r) for field, r in zip(fields, ranges)}
        for _ in range(per_level * (int(level) - min(levels))):
            available = [i for i, field in enumerate(fields) if result[field] + 1 in ranges[i] and weights[i] > 0]
            if not available: raise ValueError('Level budget exceeds the supported skill values')
            index = rng.choices(available, weights=[weights[i] for i in available], k=1)[0]
            result[fields[index]] += 1
        return result

    @staticmethod
    def incompatible(trait):
        forbidden = {value(trait.text, n).strip('"') for n in trait.node.children if n.key == 'mutually_exclusive' and n.children is None}
        weight = block(trait.node.children, 'new_commander_weight')
        if weight:
            for node in weight.children:
                if node.key == 'modifier' and node.children and atom(trait.text, node.children, 'factor') == '0':
                    forbidden.update(value(trait.text, n).strip('"') for n in node.children if n.key == 'has_trait' and n.children is None)
        return forbidden

    def random_traits(self, role, current, count=3, replace=True, rng=None):
        if role not in MILITARY: raise ValueError('Random military traits require a general or admiral')
        if not isinstance(count, int) or not 0 <= count <= 10: raise ValueError('Choose between 0 and 10 traits')
        group = 'Admirals' if role == 'navy_leader' else 'Generals'
        effective = self.effective(); pool = {}
        for original in self.records():
            if original.origin != 'Vanilla' or group not in original.groups: continue
            trait = effective.get(('unit', original.key))
            if trait is None or group not in trait.groups: continue
            if trait.unit_type == 'field_marshal' and role != 'field_marshal': continue
            # Field marshals also carry general traits (the mod has existing examples).
            if any(n.key in {'allowed', 'prerequisites', 'parent', 'any_parent', 'all_parents'} for n in trait.node.children): continue
            if trait.trait_type == 'personality_trait':
                weight = block(trait.node.children, 'new_commander_weight')
                try: eligible = weight is not None and float(atom(trait.text, weight.children, 'factor', '0')) > 0
                except ValueError: eligible = False
                if not eligible: continue
            elif trait.trait_type not in {'basic_trait', 'basic_terrain_trait', ''}: continue
            elif not trait.trait_type and not atom(trait.text, trait.node.children, 'cost'): continue
            pool[trait.key] = trait
        selected = [key for key in dict.fromkeys(current) if not replace or key not in pool]
        rng = rng or random.SystemRandom(); candidates = list(pool.values()); rng.shuffle(candidates)
        added = []
        for trait in candidates:
            if len(added) >= count: break
            if trait.key in selected: continue
            if self.incompatible(trait).intersection(selected): continue
            if any(trait.key in self.incompatible(effective[('unit', key)]) for key in selected if ('unit', key) in effective): continue
            selected.append(trait.key); added.append(trait.key)
        if len(added) < count: raise ValueError(f'Only {len(added)} compatible generic vanilla traits available; request fewer')
        return selected
