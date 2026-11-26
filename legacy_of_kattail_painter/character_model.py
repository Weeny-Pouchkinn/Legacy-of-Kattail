"""Native character editing and independent portrait pairs over guarded drafts."""
from __future__ import annotations

from dataclasses import dataclass
import io
import json
from pathlib import Path
import re
import unicodedata
from functools import lru_cache
from collections import OrderedDict

from PIL import Image, ImageOps

from model import child, parse, scalar, value, walk, read_text, default_paths
from small_portrait import generate_small_portrait

CHAR_LOC = 'localisation/english/characters_l_english.yml'
PORTRAIT_GFX = 'interface/lok_leader_portraits.gfx'
METADATA = 'legacy_of_kattail_painter/characters_painter_data.json'
ROLES = ('country_leader', 'advisor', 'corps_commander', 'field_marshal', 'navy_leader', 'scientist')
PORTRAIT_SLOTS = ('civilian', 'army', 'navy')
LARGE_SIZE, SMALL_SIZE = (156, 210), (65, 67)
LOC = re.compile(r'^\s*([^\s:#]+):(\d*)\s*"((?:\\.|[^"\\])*)"(.*)$')
TAG = re.compile(r'^[A-Z]{3}$')
MISSING = object()


def block(nodes, key):
    return next((n for n in nodes if n.key.casefold() == key.casefold() and n.children is not None), None)


def atom(text, nodes, key, default=''):
    nodes = [n for n in nodes if n.key.casefold() == key.casefold() and n.children is None]
    return value(text, nodes[-1]).strip('"') if nodes else default


def sort_name(text):
    text = re.sub('§.', '', text)
    return ''.join(c for c in unicodedata.normalize('NFKD', text).casefold() if not unicodedata.combining(c))


def matching_base(key, bases):
    """Longest exact or underscore-prefix match, without scanning every character."""
    while key:
        if key in bases:
            return key
        key = key.rpartition('_')[0]
    return ''


def quote(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\r\n', '\n').replace('\n', '\\n') + '"'


def unescape(text):
    return text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def patch_field(text, parent, key, raw):
    found = [n for n in parent.children if n.key.casefold() == key.casefold()]
    if found:
        n = found[-1]
        return text[:n.value_start] + raw + text[n.end:]
    newline = '\r\n' if '\r\n' in text else '\n'
    from script_format import indentation
    indent = '\t' * indentation(text,parent.start)
    at = text.rfind('\n', 0, parent.end - 1) + 1
    addition = indent + '\t' + key + ' = ' + raw + newline
    if text[at:parent.end - 1].strip():
        at = parent.end - 1
        addition = newline + addition + indent
        return text[:at].rstrip(' \t') + addition + text[at:]
    return text[:at] + addition + text[at:]


@lru_cache(maxsize=2)
def inherited_sprites(game_root):
    out = {}
    for path in sorted((Path(game_root) / 'interface').glob('*.gfx')):
        text = read_text(path)
        try:
            nodes = list(walk(parse(text)))
        except ValueError:
            continue
        for _, node in nodes:
            if node.key.casefold() in {'spritetype', 'frameanimatedspritetype'}:
                name = atom(text, node.children, 'name')
                if name:
                    out.setdefault(name, []).append({'path': path.name, 'node': node, 'text': text,
                                                     'texture': atom(text, node.children, 'texturefile'), 'inherited': True})
    return out


@lru_cache(maxsize=2)
def inherited_localisations(game_root):
    out = {}
    for path in sorted((Path(game_root) / 'localisation/english').rglob('*.yml')):
        for line in read_text(path).splitlines():
            if (match := LOC.match(line)):
                out[match[1]] = unescape(match[3])
    return out


@dataclass
class Character:
    key: str
    path: str
    node: object
    text: str
    name_key: str
    name: str
    countries: tuple[str, ...]
    description_key: str
    description: str
    art_source: str

    @property
    def roles(self):
        return [n for n in self.node.children if n.key.casefold() in ROLES and n.children is not None]


@dataclass
class Portrait:
    key: str
    tag: str
    large: str = ''
    small: str = ''
    large_path: str = ''
    small_path: str = ''
    art_source: str = ''
    description: str = ''


class CharacterStore:
    def __init__(self, world):
        self.world, self.docs = world, world.docs
        self.warnings = []
        self._cache = {}
        self._revision = -1
        self._last_drafts = {}
        self._inventories = {}
        self._parsed = {}
        self._loc_files = {}
        self._images = OrderedDict()
        self.game_root = default_paths()['game']

    @property
    def generic_portraits(self):
        if not hasattr(self, '_generic_portraits'):
            from generic_portrait_model import GenericPortraitStore
            self._generic_portraits = GenericPortraitStore(self)
        return self._generic_portraits

    @property
    def trait_store(self):
        if not hasattr(self, '_trait_store'):
            from trait_model import TraitStore
            self._trait_store = TraitStore(self)
        return self._trait_store

    def sprite_entries(self, name):
        entries = self.sprites().get(name, [])
        if entries:
            return entries
        fallback = self.cached('fallback')
        if fallback is None:
            fallback = self._cache['fallback'] = {}
        if name in fallback:
            return fallback[name]
        descriptor = self.docs.text('descriptor.mod')
        replaced = [value(descriptor, n).strip('"').rstrip('/') for n in parse(descriptor) if n.key == 'replace_path'] if descriptor else []
        if any(p == 'interface' or 'interface'.startswith(p + '/') for p in replaced):
            fallback[name] = []
            return []
        overrides = {Path(p).name.casefold() for p in self.files('interface', '.gfx')}
        fallback[name] = [entry for entry in inherited_sprites(str(self.game_root)).get(name, []) if entry['path'].casefold() not in overrides]
        return fallback[name]

    def cached(self, key):
        if self._revision != self.docs.revision:
            current = self.docs.drafts
            changed = {p for p in self._last_drafts.keys() | current.keys()
                       if self._last_drafts.get(p, MISSING) is not current.get(p, MISSING)}
            loc = any(p.startswith('localisation/') for p in changed)
            people = any(p.startswith(('common/characters/', 'history/countries/')) for p in changed)
            gfx = any(p.startswith('interface/') or p == 'descriptor.mod' for p in changed)
            meta = METADATA in changed
            invalid = set()
            if loc: invalid.update(('loc', 'loc_values'))
            if loc or people or meta: invalid.add('characters')
            if any(p.startswith('history/countries/') for p in changed): invalid.add('recruitments')
            if gfx: invalid.update(('sprites', 'fallback'))
            if gfx or meta: invalid.add('portraits')
            if any(p.startswith(('common/country_leader/', 'common/unit_leader/')) for p in changed): invalid.add('traits')
            if any(p.startswith('common/ideologies/') for p in changed): invalid.add('ideologies')
            if loc: invalid.update(('choices:countries', 'choices:traits', 'choices:ideologies', 'choices:portraits'))
            if people or gfx or meta: invalid.add('choices:portraits')
            if 'traits' in invalid: invalid.add('choices:traits')
            if 'ideologies' in invalid: invalid.add('choices:ideologies')
            for name in invalid: self._cache.pop(name, None)
            self._last_drafts = dict(current)
            self._revision = self.docs.revision
        return self._cache.get(key)

    def files(self, prefix, suffix):
        index = (prefix, suffix)
        if index not in self._inventories:
            self._inventories[index] = {p.relative_to(self.world.root).as_posix()
                                        for p in (self.world.root / prefix).rglob('*' + suffix)}
        return sorted(self._inventories[index] | {p for p in self.docs.originals
                      if p.startswith(prefix + '/') and p.endswith(suffix)})

    def parsed(self, relative):
        text = self.docs.text(relative)
        cached = self._parsed.get(relative)
        if cached is None or cached[0] is not text:
            cached = self._parsed[relative] = (text, parse(text))
        return cached

    def metadata(self):
        text = self.docs.text(METADATA)
        data = json.loads(text) if text.strip() else {'version': 1, 'characters': {}, 'portraits': {}}
        if data.get('version') != 1:
            raise ValueError('Unsupported character metadata version')
        return data

    def save_metadata(self, data):
        self.docs.replace(METADATA, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def loc_records(self):
        if (cached := self.cached('loc')) is not None:
            return cached
        out = {}
        for relative in self.files('localisation/english', '.yml'):
            text = self.docs.text(relative)
            cached = self._loc_files.get(relative)
            if cached is None or cached[0] is not text:
                entries = [(match[1], (relative, line, match[3])) for line in text.splitlines()
                           if (match := LOC.match(line))]
                cached = self._loc_files[relative] = (text, entries)
            for name, record in cached[1]:
                out.setdefault(name, []).append(record)
        self._cache['loc'] = out
        return out

    def localisations(self):
        if (cached := self.cached('loc_values')) is not None:
            return cached
        values = {key: unescape(records[-1][2]) for key, records in self.loc_records().items()}
        self._cache['loc_values'] = values
        return values

    def neutral_name(self, tag, loc=None):
        loc = loc or self.localisations()
        return re.sub('§.', '', loc.get(tag, '') or loc.get(tag + '_DEF', '') or tag).replace('\n', ' ')

    def recruitments(self):
        if (cached := self.cached('recruitments')) is not None:
            return cached
        out = {}
        for relative in self.files('history/countries', '.txt'):
            tag = Path(relative).name[:3]
            if tag not in self.world.country_paths:
                continue
            # Undated, unconditional native starting recruitment only. Dated/conditional
            # effects remain in place and are exposed separately in the source editor.
            text, nodes = self.parsed(relative)
            for node in nodes:
                if node.key == 'recruit_character' and node.children is None:
                    out.setdefault(value(text, node).strip('"'), []).append(tag)
        result = {key: tuple(sorted(set(tags))) for key, tags in out.items()}
        self._cache['recruitments'] = result
        return result

    def characters(self):
        if (cached := self.cached('characters')) is not None:
            return cached
        loc, recruited, meta = self.localisations(), self.recruitments(), self.metadata()['characters']
        out = {}
        for relative in self.files('common/characters', '.txt'):
            text, nodes = self.parsed(relative)
            for root in nodes:
                if root.key.casefold() != 'characters':
                    continue
                for node in root.children:
                    if node.children is None:
                        continue
                    if node.key in out:
                        raise ValueError('Duplicate character ID: ' + node.key)
                    name_key = atom(text, node.children, 'name', node.key)
                    desc = next((atom(text, n.children, 'desc') for n in node.children
                                 if n.children and atom(text, n.children, 'desc')), node.key + '_desc')
                    desc = meta.get(node.key, {}).get('description_key', desc)
                    out[node.key] = Character(node.key, relative, node, text, name_key,
                                              loc.get(name_key, name_key), recruited.get(node.key, ()),
                                              desc, loc.get(desc, ''), meta.get(node.key, {}).get('art_source', ''))
        self._cache['characters'] = out
        return out

    def ordered(self, by_nation=False, nation='', query=''):
        characters = list(self.characters().values())
        if nation:
            characters = [c for c in characters if (not c.countries if nation == 'UNASSIGNED' else nation in c.countries)]
        query = sort_name(query)
        direct = [c for c in characters if query in sort_name(c.name + ' ' + c.key + ' ' + ' '.join(c.countries))]
        if query and not direct:
            from select_ui import Choice, ChoiceIndex
            matches = {choice.code for choice in ChoiceIndex(Choice(c.key, c.name) for c in characters).matching(query)}
            direct = [c for c in characters if c.key in matches]
        def order(c):
            group = ((sort_name(self.neutral_name(c.countries[0])), c.countries[0]) if c.countries else ('\uffff', '')) if by_nation else ('', '')
            return group, sort_name(c.name), c.key
        return sorted(direct, key=order)

    def set_recruitment(self, key, country):
        if country and country not in self.world.countries:
            raise ValueError('Choose a country with a country-history file')
        current = self.recruitments().get(key, ())
        if current == ((country,) if country else ()):
            return
        for relative in self.files('history/countries', '.txt'):
            text = self.docs.text(relative)
            nodes = [n for n in parse(text) if n.key == 'recruit_character' and value(text, n).strip('"') == key]
            for n in reversed(nodes):
                start = text.rfind('\n', 0, n.start) + 1
                end = text.find('\n', n.end)
                end = len(text) if end < 0 else end + 1
                suffix = text[n.end:end].strip()
                if text[start:n.start].strip() or (suffix and not suffix.startswith('#')):
                    text = text[:n.start] + text[n.end:]
                else:
                    text = text[:start] + text[end:]
            if nodes:
                self.docs.replace(relative, text)
        if country:
            path = self.world.countries[country]
            text = self.docs.text(path)
            newline = '\r\n' if '\r\n' in text else '\n'
            self.docs.replace(path, text.rstrip('\r\n') + newline + 'recruit_character = ' + key + newline)

    def collect_character_localisation(self):
        from trait_model import TRAIT_LOC
        characters = self.characters()
        records = self.loc_records()
        bases = {base for c in characters.values() for base in (c.key, c.name_key, c.description_key)}
        chosen = {key for key in records if matching_base(key, bases)}
        main = self.docs.text(CHAR_LOC) or 'l_english:\n'
        main_keys = {m[1] for line in main.splitlines() if (m := LOC.match(line))}
        additions, removals = [], {}
        for key in sorted(chosen):
            entries = records[key]
            # Trait strings have their own database even if an ID starts with a character ID.
            if any(relative == TRAIT_LOC for relative, _, _ in entries):
                continue
            if len({e[2] for e in entries}) > 1:
                raise ValueError('Conflicting authored character localisation: ' + key)
            if key not in main_keys:
                additions.append(entries[0][1])
            for relative, line, _ in entries:
                if relative != CHAR_LOC:
                    removals.setdefault(relative, set()).add(key)
        if additions:
            self.docs.replace(CHAR_LOC, main.rstrip('\r\n') + '\n' + '\n'.join(additions) + '\n')
        for relative, keys in removals.items():
            text = self.docs.text(relative)
            lines = [line for line in text.splitlines(keepends=True) if not ((m := LOC.match(line)) and m[1] in keys)]
            self.docs.replace(relative, ''.join(lines))

    def set_loc(self, key, text):
        source = self.docs.text(CHAR_LOC) or 'l_english:\n'
        lines = source.splitlines()
        replacement = f' {key}:0 {quote(text)}'
        found = False
        for i, line in enumerate(lines):
            match = LOC.match(line)
            if match and match[1] == key:
                if unescape(match[3]) == text:
                    return
                lines[i] = replacement
                found = True
        if not found:
            lines.append(replacement)
        self.docs.replace(CHAR_LOC, '\n'.join(lines) + '\n')

    def organise_localisation(self):
        self.collect_character_localisation()
        chars, loc = self.characters(), self.localisations()
        ownership, names = {}, {}
        for c in sorted(chars.values(), key=lambda c: c.key):
            group = c.countries[0] if c.countries else 'UNASSIGNED'
            for base in (c.key, c.name_key, c.description_key):
                ownership.setdefault(base, group)
                names.setdefault(base, c.name)
        source = self.docs.text(CHAR_LOC) or 'l_english:\n'
        groups, notes = {}, []
        for line in source.splitlines()[1:]:
            match = LOC.match(line)
            if not match:
                if line.strip().startswith('#') and not re.match(r'^\s*#(?:[A-Z0-9]{3}|UNASSIGNED) - ', line):
                    notes.append(line)
                continue
            key = match[1]
            base = matching_base(key, ownership)
            tag = ownership[base] if base else key[:3] if key[:3] in self.world.country_paths and key[3:4] == '_' else 'UNASSIGNED'
            groups.setdefault(tag, []).append((sort_name(names.get(base, unescape(match[3]))), key, list(notes), line.rstrip()))
            notes.clear()
        lines = ['l_english:']
        for tag in sorted(t for t in groups if t != 'UNASSIGNED') + ['UNASSIGNED']:
            title = self.neutral_name(tag, loc) if tag != 'UNASSIGNED' else 'Not recruited at start / other localisation'
            lines.extend(['', f'#{tag} - {title}'])
            for _, key, comments, line in sorted(groups.get(tag, [])):
                lines.extend(comments)
                lines.append(line)
        lines.extend(notes)
        self.docs.replace(CHAR_LOC, '\n'.join(lines) + '\n')

    def edit_character(self, key, name, description, art_source, country, gender=None, create=False):
        with self.docs.grouped():
            self.collect_character_localisation()
            if create:
                if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', key) or key in self.characters():
                    raise ValueError('Choose a unique character ID using letters, digits and underscores')
                if key in self.localisations() and self.localisations()[key] != name:
                    raise ValueError('That localisation key already contains another authored name; choose another ID')
                path = 'common/characters/zz_painter_characters.txt'
                text = self.docs.text(path) or 'characters = {\n}\n'
                root = block(parse(text), 'characters')
                text = text[:root.end - 1] + f'\t{key} = {{\n\t\tname = {key}\n\t}}\n' + text[root.end - 1:]
                self.docs.replace(path, text)
            c = self.characters()[key]
            if not name.strip():
                raise ValueError('A character needs a display name')
            if name != c.name or create:
                name_key = c.name_key if c.name_key in self.loc_records() else key
                self.set_loc(name_key, name)
                self._character_field(key, 'name', name_key)
            self.set_loc(c.description_key, description)
            for index in range(len(self.characters()[key].roles)):
                current = self.characters()[key]
                role = current.roles[index]
                if role.key.casefold() in {'country_leader', 'scientist'} and not atom(current.text, role.children, 'desc'):
                    self.docs.replace(current.path, patch_field(current.text, current.roles[index], 'desc', c.description_key))
            if gender:
                self._character_field(key, 'gender', gender)
            data = self.metadata()
            data['characters'].setdefault(key, {}).update(art_source=art_source, description_key=c.description_key)
            self.save_metadata(data)
            memberships = self.recruitments().get(key, ())
            # Opening/applying an existing character must not collapse native
            # multi-country recruitment just because the picker shows its first tag.
            if not memberships or country != memberships[0]:
                self.set_recruitment(key, country)
            self.organise_localisation()

    def _character_field(self, key, field, raw):
        c = self.characters()[key]
        self.docs.replace(c.path, patch_field(c.text, c.node, field, raw))

    def edit_role(self, key, index, kind, fields, traits, extra=None):
        if kind not in ROLES:
            raise ValueError('Unsupported role: ' + kind)
        c = self.characters()[key]
        with self.docs.grouped():
            if index is None:
                newline = '\r\n' if '\r\n' in c.text else '\n'
                addition = '\t\t' + kind + ' = {' + newline + '\t\t}' + newline
                at = c.text.rfind('\n', 0, c.node.end - 1) + 1
                if c.text[at:c.node.end - 1].strip():
                    at = c.node.end - 1
                    addition = newline + addition + '\t'
                text = c.text[:at] + addition + c.text[at:]
                self.docs.replace(c.path, text)
                index = len(self.characters()[key].roles) - 1
            c = self.characters()[key]
            role = c.roles[index]
            if role.key.casefold() != kind:
                raise ValueError('Role type cannot be silently renamed')
            token = fields.get('idea_token', '')
            if token and token != atom(c.text, role.children, 'idea_token'):
                existing = {atom(person.text, r.children, 'idea_token')
                            for person in self.characters().values() for r in person.roles}
                if token in existing:
                    raise ValueError('Advisor idea_token already belongs to another role: ' + token)
            body = value(c.text, role)
            if extra is not None:
                parse(extra)
                body = '{\n' + extra + '\n\t\t}'
            snippet = '\t\t' + kind + ' = ' + body
            for field, raw in {**fields, 'traits': '{ ' + ' '.join(traits) + ' }'}.items():
                if raw == '':
                    continue
                snippet = patch_field(snippet, parse(snippet)[0], field, raw)
            updated = value(snippet, parse(snippet)[0])
            self.docs.replace(c.path, c.text[:role.value_start] + updated + c.text[role.end:])

    def remove_role(self, key, index):
        c = self.characters()[key]
        role = c.roles[index]
        self.docs.replace(c.path, c.text[:role.start] + c.text[role.end:])

    def assign_portrait(self, key, slot, portrait_key):
        if slot not in PORTRAIT_SLOTS:
            raise ValueError('Choose civilian, army or navy')
        portrait = self.portraits()[portrait_key]
        c = self.characters()[key]
        container = block(c.node.children, 'portraits')
        body = '{ large = ' + quote(portrait.large) + (' small = ' + quote(portrait.small) if portrait.small else '') + ' }'
        with self.docs.grouped():
            if container:
                self.docs.replace(c.path, patch_field(c.text, container, slot, body))
            else:
                self._character_field(key, 'portraits', '{ ' + slot + ' = ' + body + ' }')
            self.link_variant(key, portrait_key)

    def variants(self, key):
        c = self.characters()[key]
        variants = list(self.metadata()['characters'].get(key, {}).get('portrait_variants', []))
        portraits = block(c.node.children, 'portraits')
        for slot in portraits.children if portraits else []:
            if slot.children:
                ref = atom(c.text, slot.children, 'large')
                if ref in self.portraits() and ref not in variants:
                    variants.append(ref)
        return variants

    def link_variant(self, key, portrait_key):
        if portrait_key not in self.portraits():
            raise ValueError('Choose a valid portrait definition')
        data = self.metadata()
        variants = data['characters'].setdefault(key, {}).setdefault('portrait_variants', [])
        if portrait_key not in variants:
            variants.append(portrait_key)
        self.save_metadata(data)

    def sprites(self):
        if (cached := self.cached('sprites')) is not None:
            return cached
        out = {}
        for relative in self.files('interface', '.gfx'):
            try:
                text, roots = self.parsed(relative)
                nodes = walk(roots)
            except ValueError:
                if relative == PORTRAIT_GFX:
                    raise
                continue
            for _, node in nodes:
                if node.key.casefold() not in {'spritetype', 'frameanimatedspritetype'}:
                    continue
                name = atom(text, node.children, 'name')
                if name:
                    out.setdefault(name, []).append({'path': relative, 'node': node, 'text': text,
                                                     'texture': atom(text, node.children, 'texturefile')})
        self._cache['sprites'] = out
        return out

    @staticmethod
    def infer_tag(key, path):
        match = re.match(r'GFX_portrait_([A-Z0-9]{3})_', key)
        if match:
            return match[1]
        for part in Path(path).parts:
            if TAG.fullmatch(part):
                return part
        return 'GEN'

    def portraits(self):
        if (cached := self.cached('portraits')) is not None:
            return cached
        meta, out = self.metadata()['portraits'], {}
        for name, entries in self.sprites().items():
            if not name.startswith('GFX_portrait_'):
                continue
            base = re.sub(r'_small$', '', name, flags=re.I)
            entry = entries[0]
            record = out.setdefault(base, Portrait(base, self.infer_tag(base, entry['texture'])))
            if name.lower().endswith('_small'):
                record.small, record.small_path = name, entry['texture']
            else:
                record.large, record.large_path = name, entry['texture']
        for key, record in out.items():
            data = meta.get(key, {})
            record.tag = data.get('tag', record.tag)
            record.art_source = data.get('art_source', '')
            record.description = data.get('description', '')
        self._cache['portraits'] = out
        return out

    def portrait_for_character(self, character):
        portraits = block(character.node.children, 'portraits')
        if portraits:
            for slot in ('civilian', 'army', 'navy'):
                n = block(portraits.children, slot)
                if n:
                    ref = atom(character.text, n.children, 'large')
                    if ref:
                        return ref
        return ''

    def image(self, reference, size=None):
        entries = self.sprite_entries(reference) if reference.startswith('GFX_') else []
        texture = entries[0]['texture'] if entries else reference
        if not texture or not texture.startswith('gfx/'):
            return None
        blob = self.docs.binary(texture)
        if blob is None and (self.game_root / texture).is_file():
            native = (self.game_root / texture).resolve()
            if native.is_relative_to(self.game_root.resolve()):
                blob = native.read_bytes()
        if blob is None:
            return None
        frames = int(atom(entries[0]['text'], entries[0]['node'].children, 'noOfFrames', '1')) if entries else 1
        token = (texture, id(blob), frames, size)
        if token in self._images:
            self._images.move_to_end(token)
            return self._images[token][1].copy()
        with Image.open(io.BytesIO(blob)) as source:
            image = source.convert('RGBA')
            if entries:
                if frames > 1 and image.width % frames == 0:
                    image = image.crop((0, 0, image.width // frames, image.height))
            if size:
                image = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
            self._images[token] = (blob, image.copy())
            if len(self._images) > 192: self._images.popitem(last=False)
            return image.copy()

    def image_token(self, reference):
        entries = self.sprite_entries(reference) if reference.startswith('GFX_') else []
        texture = entries[0]['texture'] if entries else reference
        blob = self.docs.binary(texture) if texture.startswith('gfx/') else None
        frames = atom(entries[0]['text'], entries[0]['node'].children, 'noOfFrames', '1') if entries else '1'
        return texture, id(blob), frames

    def choices(self, kind):
        """Localized display choices; code remains the only stored value."""
        from select_ui import Choice
        cache_key = 'choices:' + kind
        if (cached := self.cached(cache_key)) is not None:
            return cached
        loc = self.localisations()
        if kind == 'countries':
            result = [Choice(tag, self.neutral_name(tag, loc)) for tag in self.world.countries]
        elif kind in {'traits', 'ideologies'}:
            keys = self.trait_ids() if kind == 'traits' else self.ideology_ids()
            native = inherited_localisations(str(self.game_root)) if any(k not in loc for k in keys) else {}
            result = [Choice(k, loc.get(k, native.get(k, k))) for k in keys]
        elif kind == 'portraits':
            chars = self.characters()
            result = []
            for key in self.portraits():
                base = key.removeprefix('GFX_portrait_')
                character_key = matching_base(base, chars)
                name = chars[character_key].name if character_key else loc.get(base, base.replace('_', ' '))
                result.append(Choice(key, name))
        else:
            raise ValueError('Unknown choice catalog: ' + kind)
        self._cache[cache_key] = tuple(sorted(result, key=lambda c: (sort_name(c.name), sort_name(c.code))))
        return self._cache[cache_key]

    def _put_sprite(self, name, texture, static=False):
        entries = self.sprites().get(name, [])
        if entries:
            if len({e['texture'] for e in entries}) > 1:
                raise ValueError('Ambiguous existing sprite: ' + name)
            for entry in entries:
                text = self.docs.text(entry['path'])
                # Resolve the current node because earlier edits may move its span.
                node = next(n for _, n in walk(parse(text)) if n.children and atom(text, n.children, 'name') == name)
                if static and node.key.casefold() == 'frameanimatedspritetype':
                    replacement = f'spriteType = {{ name = {quote(name)}\t\ttexturefile = {quote(texture)} }}'
                    self.docs.replace(entry['path'], text[:node.start] + replacement + text[node.end:])
                else:
                    self.docs.replace(entry['path'], patch_field(text, node, 'texturefile', quote(texture)))
        else:
            text = self.docs.text(PORTRAIT_GFX) or 'spriteTypes = {\n}\n'
            root = block(parse(text), 'spriteTypes')
            raw = f'\tspriteType = {{ name = {quote(name)}\t\ttexturefile = {quote(texture)} }}\n'
            self.docs.replace(PORTRAIT_GFX, text[:root.end - 1] + raw + text[root.end - 1:])

    def portrait_destination(self, key, tag, large, current=''):
        stem = re.sub(r'[^A-Za-z0-9_]', '_', key.removeprefix('GFX_portrait_'))
        folder = 'large_portraits' if large else 'small_portraits'
        destination = f'gfx/leaders/{folder}/{tag}/{stem}.tga'
        suffix = 2
        while destination != current and self.docs.binary(destination) is not None:
            destination = f'gfx/leaders/{folder}/{tag}/{stem}__{suffix}.tga'
            suffix += 1
        return destination

    def edit_portrait(self, key, tag, art_source='', description='', large_file=None, small_file=None,
                      create=False, generate_small=False):
        if not TAG.fullmatch(tag):
            raise ValueError('Portrait tag must contain exactly three uppercase letters')
        portraits = self.portraits()
        if create:
            if not re.fullmatch(r'GFX_portrait_[A-Za-z0-9_]+', key) or self.sprite_entries(key) or self.sprite_entries(key + '_Small'):
                raise ValueError('Choose a unique portrait sprite ID')
            record = Portrait(key, tag, large=key, small=key + '_Small')
        else:
            record = portraits[key]
        with self.docs.grouped():
            for large, source in ((True, large_file), (False, small_file)):
                if source is None:
                    continue
                size = LARGE_SIZE if large else SMALL_SIZE
                with Image.open(source) as image:
                    fitted = ImageOps.contain(image.convert('RGBA'), size, Image.Resampling.LANCZOS)
                    canvas = Image.new('RGBA', size)
                    canvas.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
                    output = io.BytesIO(); canvas.save(output, format='TGA')
                destination = self.portrait_destination(key, tag, large, record.large_path if large else record.small_path)
                self.docs.stage_bytes(destination, output.getvalue())
                sprite = (record.large or key) if large else (record.small or key + '_Small')
                self._put_sprite(sprite, destination, static=True)
                if large:
                    record.large, record.large_path = sprite, destination
                else:
                    record.small, record.small_path = sprite, destination
            if generate_small:
                image = self.image(record.large)
                if image is None:
                    raise ValueError('Choose a valid large portrait before generating its small image')
                canvas = generate_small_portrait(image)
                output = io.BytesIO(); canvas.save(output, format='TGA')
                destination = self.portrait_destination(key, tag, False, record.small_path)
                self.docs.stage_bytes(destination, output.getvalue())
                self._put_sprite(record.small or key + '_Small', destination, static=True)
            if create and (not large_file or not (small_file or generate_small)):
                raise ValueError('A new portrait pair needs a large and a small image')
            data = self.metadata()
            data['portraits'].setdefault(key, {}).update(tag=tag, art_source=art_source, description=description)
            self.save_metadata(data)
            self.organise_gfx()

    def organise_gfx(self):
        text = self.docs.text(PORTRAIT_GFX)
        if not text:
            return
        root = block(parse(text), 'spriteTypes')
        meta, groups, seen = self.metadata()['portraits'], {}, {}
        for node in root.children:
            if node.children is None:
                continue
            name, texture = atom(text, node.children, 'name'), atom(text, node.children, 'texturefile')
            if name in seen:
                if seen[name] == texture:
                    continue
                # Legacy small sprite accidentally reused its paired large sprite's name.
                if '/small_portraits/' in texture or '/interface/ministers/' in texture:
                    name += '_Small'
                else:
                    raise ValueError('Conflicting sprite declaration: ' + name)
            seen[name] = texture
            base = re.sub(r'_small$', '', name, flags=re.I)
            tag = meta.get(base, {}).get('tag', self.infer_tag(base, texture))
            if node.key.casefold() == 'spritetype':
                extras = ' '.join(n.key + ' ' + n.op + ' ' + value(text, n) for n in node.children
                                  if n.key.casefold() not in {'name', 'texturefile'})
                raw = f'\tspriteType = {{ name = {quote(name)}\t\t\ttexturefile = {quote(texture)}\t\t' + extras + ' }'
            else:
                raw = '\t' + text[node.start:node.end]
            groups.setdefault(tag, []).append((base.casefold(), name.lower().endswith('_small'), name, raw))
        loc, lines = self.localisations(), ['spriteTypes = {']
        for tag in sorted(groups):
            lines.extend(['', f'\t#{tag} - {self.neutral_name(tag, loc)}'])
            for _, _, _, raw in sorted(groups[tag]):
                lines.append(raw)
        lines.append('}')
        self.docs.replace(PORTRAIT_GFX, '\n'.join(lines) + '\n')

    def prepare_save(self):
        self.organise_localisation()
        self.organise_gfx()
        if hasattr(self, '_trait_store'):
            from trait_model import TRAIT_PATHS
            for path in TRAIT_PATHS.values():
                if path in self.docs.drafts and self.docs.text(path):
                    self.trait_store.organise(path)

    def trait_ids(self):
        if (cached := self.cached('traits')) is not None:
            return cached
        out = {t.key for t in self.trait_store.records() if t.active}
        self._cache['traits'] = sorted(out)
        return self._cache['traits']

    def ideology_ids(self):
        if (cached := self.cached('ideologies')) is not None:
            return cached
        out = set()
        for relative in self.files('common/ideologies', '.txt'):
            for _, node in walk(self.parsed(relative)[1]):
                if node.key == 'types' and node.children:
                    out.update(n.key for n in node.children if n.children is not None)
        self._cache['ideologies'] = sorted(out)
        return self._cache['ideologies']
