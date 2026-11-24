"""Clausewitz data access, editable drafts and guarded source-file saves."""
from __future__ import annotations

import colorsys
import csv
import hashlib
import os
import re
from functools import lru_cache
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor
from source_io import encode_source, write_changes

TOKEN = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[<>=!]+|[^\s{}=<>!#"]+')
OPS = {'=', '>', '<', '>=', '<=', '!=', '?='}
FLAG_SIZES = {'large': (82, 52), 'medium': (41, 26), 'small': (10, 7)}


@dataclass
class Node:
    key: str
    op: str
    start: int
    value_start: int
    end: int
    children: list['Node'] | None = None


def parse(text: str) -> list[Node]:
    """Keep duplicate keys, list atoms, operators and exact value spans; skip comments."""
    tokens = [m for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    index = 0

    def block(nested=False):
        nonlocal index
        out = []
        while index < len(tokens):
            token = tokens[index]
            key = token.group()
            if key == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                return out
            index += 1
            op = ''
            if index < len(tokens) and tokens[index].group() in OPS:
                op = tokens[index].group()
                index += 1
                if index == len(tokens):
                    raise ValueError('Missing value for ' + key)
                val = tokens[index]
                index += 1
            else:
                val = token
            typed = val.group() in {'rgb', 'hsv', 'hsv360'} and index < len(tokens) and tokens[index].group() == '{'
            if typed:
                index += 1
            if val.group() == '{' or typed:
                children = block(True)
                if index == len(tokens) or tokens[index].group() != '}':
                    raise ValueError('Unclosed block for ' + key)
                end = tokens[index].end()
                index += 1
            elif val.group() in OPS or val.group() == '}':
                raise ValueError('Invalid value for ' + key)
            else:
                children, end = None, val.end()
            out.append(Node(key, op, token.start(), val.start(), end, children))
        if nested:
            raise ValueError('Unclosed block')
        return out
    return block()


def value(text, node):
    return text[node.value_start:node.end]


def scalar(text, nodes, key, default=''):
    found = [n for n in nodes if n.key == key and n.children is None]
    return value(text, found[-1]).strip('"') if found else default


def child(nodes, key):
    return next((n for n in nodes if n.key == key and n.children is not None), None)


def walk(nodes, prefix=''):
    counts = {}
    for n in nodes:
        counts[n.key] = counts.get(n.key, 0) + 1
        path = f'{prefix}/{n.key}[{counts[n.key]}]'
        yield path, n
        if n.children is not None:
            yield from walk(n.children, path)


def read_text(path):
    data = Path(path).read_bytes()
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1252')


def colour(key):
    hue = int(hashlib.sha256(str(key).encode()).hexdigest()[:8], 16) / 0xffffffff
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(hue, .48, .78))


class Documents:
    """Edits remain in memory until an explicit, backed-up Save."""
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.originals = {}
        self.snapshots = {}
        self.drafts = {}
        self.undo_stack = []
        self.redo_stack = []

    def text(self, relative):
        relative = str(relative).replace('\\', '/')
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('Source path escapes mod root')
        if relative not in self.originals:
            self.snapshots[relative] = path.read_bytes()
            self.originals[relative] = read_text(path)
        return self.drafts.get(relative, self.originals[relative])

    def replace(self, relative, new):
        old = self.text(relative)
        parse(new)
        if new == old:
            return
        self.undo_stack.append((relative, old, new))
        self.redo_stack.clear()
        self.drafts[relative] = new

    def edit(self, relative, node, new):
        source = self.text(relative)
        if node.children is None and len(parse(new)) != 1:
            raise ValueError('Enter one scalar value (quote text containing spaces)')
        self.replace(relative, source[:node.value_start] + new + source[node.end:])

    def undo(self):
        if self.undo_stack:
            rel, old, new = self.undo_stack.pop()
            self.drafts[rel] = old
            self.redo_stack.append((rel, old, new))

    def redo(self):
        if self.redo_stack:
            rel, old, new = self.redo_stack.pop()
            self.drafts[rel] = new
            self.undo_stack.append((rel, old, new))

    def reset(self):
        self.drafts.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    @property
    def changed(self):
        return [p for p, t in self.drafts.items() if t != self.originals[p]]

    def save(self):
        changes = {}
        for relative in self.changed:
            parse(self.drafts[relative])
            changes[relative] = (self.snapshots[relative],
                                 encode_source(self.drafts[relative], self.snapshots[relative]))
        backup = write_changes(self.root, changes)
        for relative, (_, blob) in changes.items():
            self.snapshots[relative] = blob
            self.originals[relative] = read_text(self.root / relative)
        self.reset()
        return len(changes), backup


@dataclass
class State:
    id: int
    path: str
    name: str
    owner: str
    provinces: list[int]


class World:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.docs = Documents(root)
        self.states = {}
        self.countries = {}
        self.country_paths = {}
        self.provinces = {}
        self.province_states = {}
        self.localisation = {}
        self.warnings = []
        self.map_ids = None
        self._state_nodes_cache = {}
        for folder in ['localisation/english', 'localisation/replace']:
            for f in sorted((self.root / folder).rglob('*.yml')):
                for line in read_text(f).splitlines():
                    m = re.match(r'\s*([^\s:#]+):\d*\s*"(.*)"', line)
                    if m:
                        self.localisation[m[1]] = m[2]
        for f in sorted((self.root / 'common/country_tags').glob('*.txt')):
            text = read_text(f)
            for n in parse(text):
                if re.fullmatch('[A-Z0-9]{3}', n.key):
                    self.country_paths[n.key] = 'common/' + value(text, n).strip('"')
        for f in sorted((self.root / 'history/countries').glob('*.txt')):
            tag = f.name[:3]
            if tag in self.country_paths:
                self.countries[tag] = f.relative_to(self.root).as_posix()
        for f in sorted((self.root / 'history/states').glob('*.txt')):
            relative = f.relative_to(self.root).as_posix()
            try:
                t = self.docs.text(relative)
                n = child(parse(t), 'state')
                if n is None:
                    continue
                sid = int(scalar(t, n.children, 'id'))
                if sid in self.states:
                    raise ValueError(f'Duplicate state {sid}')
                hist = child(n.children, 'history')
                prov = child(n.children, 'provinces')
                ids = [int(v.key) for v in prov.children] if prov else []
                self.states[sid] = State(sid, relative, scalar(t, n.children, 'name'),
                                         scalar(t, hist.children, 'owner') if hist else '', ids)
                for pid in ids:
                    self.province_states[pid] = sid
            except (ValueError, OSError) as exc:
                self.warnings.append(f'{relative}: {exc}')
        with (self.root / 'map/definition.csv').open(encoding='utf-8-sig') as stream:
            for row in csv.reader(stream, delimiter=';'):
                if len(row) >= 8 and row[0].isdigit():
                    self.provinces[int(row[0])] = {'rgb': tuple(map(int, row[1:4])),
                        'type': row[4], 'coastal': row[5], 'terrain': row[6], 'continent': row[7]}
        self.files = sorted(f.relative_to(self.root).as_posix()
                            for folder in ['common', 'history', 'events', 'interface', 'map', 'country_metadata']
                            for f in (self.root / folder).rglob('*')
                            if f.is_file() and f.suffix.lower() in {'.txt', '.gui', '.gfx', '.asset'})
        self._demographic_catalogs()

    def _demographic_catalogs(self):
        self.culture_colours, self.species_colours, self.minority_colours = {}, {}, {}
        path = self.root / 'common/map_modes/LOK_culture_map_mode.txt'
        if path.exists():
            text = self.docs.text(path.relative_to(self.root))
            channels = {}
            for _, node in walk(parse(text)):
                if node.key != 'add_to_temp_variable' or not node.children:
                    continue
                for component in node.children:
                    match = re.fullmatch(r'culture_(\d+)_(red|green|blue)', component.key)
                    if match:
                        channels.setdefault(int(match[1]), {})[match[2]] = float(value(text, component))
            self.culture_colours = {key: self._fraction_rgb(rgb) for key, rgb in channels.items()}
        path = self.root / 'common/map_modes/LOK_species_map_mode.txt'
        if path.exists():
            text = self.docs.text(path.relative_to(self.root))
            root = child(child(parse(text), 'scripted_map_modes').children, 'LOK_species_map_mode')
            for part, field, palette in [('bottom', 'species', self.species_colours),
                                         ('top', 'minority', self.minority_colours)]:
                color = child(child(root.children, part).children, 'color')
                for node in color.children:
                    if node.key != 'if':
                        continue
                    limit = child(node.children, 'limit')
                    ids = [int(value(text, n)) for _, n in walk([limit]) if n.key == field]
                    rgb = {c.key: float(value(text, c)) for n in node.children
                           if n.key == 'set_temp_variable' for c in n.children
                           if c.key in {'red', 'green', 'blue'}}
                    if ids and rgb:
                        palette[ids[0]] = self._fraction_rgb(rgb)
        self.culture_names = {int(m[1]): re.sub('§.', '', name)
                              for key, name in self.localisation.items()
                              if (m := re.fullmatch(r'culture_(\d+)_name', key))}
        self.species_names = {int(m[1]): re.sub('§.', '', name)
                              for key, name in self.localisation.items()
                              if (m := re.fullmatch(r'var_species_(\d+)', key))}

    @staticmethod
    def _fraction_rgb(channels):
        values = [channels[key] for key in ('red', 'green', 'blue')]
        if any(not 0 <= v <= 1 for v in values):
            raise ValueError('Map-mode colour component outside 0..1')
        return tuple(round(v * 255) for v in values)

    def label(self, key):
        return self.localisation.get(str(key), str(key))

    def state_nodes(self, sid):
        t = self.docs.text(self.states[sid].path)
        cached = self._state_nodes_cache.get(sid)
        if cached is None or cached[0] != t:
            cached = (t, child(parse(t), 'state').children)
            self._state_nodes_cache[sid] = cached
        return cached

    def load_map(self):
        if self.map_ids is not None:
            return
        with Image.open(self.root / 'map/provinces.bmp') as source:
            rgb = np.asarray(source.convert('RGB'), dtype=np.uint32)
        encoded = rgb[:, :, 0] << 16 | rgb[:, :, 1] << 8 | rgb[:, :, 2]
        keys = np.array([r['rgb'][0] << 16 | r['rgb'][1] << 8 | r['rgb'][2]
                         for r in self.provinces.values()], dtype=np.uint32)
        ids = np.array(list(self.provinces), dtype=np.uint32)
        order = keys.argsort()
        positions = np.searchsorted(keys[order], encoded)
        valid = positions < len(keys)
        positions = np.minimum(positions, len(keys) - 1)
        valid &= keys[order][positions] == encoded
        self.map_ids = np.where(valid, ids[order][positions], 0)

    def country_colours(self):
        country_colours = {}
        for tag, relative in self.country_paths.items():
            if (self.root / relative).exists():
                t = self.docs.text(relative)
                c = child(parse(t), 'color')
                if c:
                    country_colours[tag] = self._script_colour(t, c)
        overrides = self.root / 'common/countries/colors.txt'
        if overrides.exists():
            t = self.docs.text('common/countries/colors.txt')
            for n in parse(t):
                c = child(n.children, 'color') if n.children else None
                if c:
                    country_colours[n.key] = self._script_colour(t, c)
        return country_colours

    def map_image(self, layer='Owners'):
        self.load_map()
        palette = np.zeros((max(self.provinces) + 1, 3), dtype=np.uint8)
        minority_palette = np.zeros_like(palette)
        has_minority = np.zeros(len(palette), dtype=bool)
        owners = {}
        country_colours = self.country_colours() if layer == 'Owners' else {}
        if layer == 'Owners':
            for sid in self.states:
                t, nodes = self.state_nodes(sid)
                h = child(nodes, 'history')
                owners[sid] = scalar(t, h.children, 'owner') if h else ''
        for pid, record in self.provinces.items():
            sid = self.province_states.get(pid)
            if layer == 'Provinces':
                c = record['rgb']
            elif layer in {'Terrain', 'Continents'}:
                c = colour(record['terrain' if layer == 'Terrain' else 'continent'])
            elif layer in {'Culture', 'Species', 'Minority'}:
                data = getattr(self, 'demographics', {}).get(sid, {})
                if layer == 'Culture':
                    colours = [self.culture_colours.get(v, (128, 128, 128)) for v in data.get('culture', [])]
                    c = tuple(round(sum(v) / len(colours)) for v in zip(*colours)) if colours else (128, 128, 128)
                else:
                    key = 'species' if layer == 'Species' else 'minority'
                    colours = self.species_colours if layer == 'Species' else self.minority_colours
                    c = colours.get(data.get(key), (128, 128, 128))
                    minority = data.get('minority', 1000)
                    if layer == 'Species' and minority != 1000 and record['type'] == 'land':
                        minority_palette[pid] = self.minority_colours.get(minority, (128, 128, 128))
                        has_minority[pid] = True
            else:
                key = owners.get(sid, '') if layer == 'Owners' else sid
                c = country_colours.get(key, colour(key)) if key else (65, 69, 78)
            if record['type'] != 'land' and layer != 'Provinces':
                c = (26, 43, 60)
            palette[pid] = c
        pixels = palette[self.map_ids]
        if layer == 'Species':
            height, width = self.map_ids.shape
            stripes = (np.arange(height)[:, None] + np.arange(width)[None, :]) % 32 < 9
            stripes &= has_minority[self.map_ids]
            pixels[stripes] = minority_palette[self.map_ids[stripes]]
        return Image.fromarray(pixels)

    @staticmethod
    def _script_colour(text, node):
        parts = [float(c.key) for c in node.children]
        raw = value(text, node).lstrip()
        if raw.startswith('hsv360'):
            return tuple(round(v * 255) for v in colorsys.hsv_to_rgb(parts[0] / 360, parts[1] / 100, parts[2] / 100))
        if raw.startswith('hsv'):
            return tuple(round(v * 255) for v in colorsys.hsv_to_rgb(*parts[:3]))
        return tuple(max(0, min(255, round(v))) for v in parts[:3])


class Emblems:
    """Read flat masks only. No importing the EU4 module: it writes caches on use."""
    def __init__(self, painter=None, stellaris=None, giga=None):
        self.sources = {}
        if painter:
            for f in sorted((Path(painter) / 'stellaris_flags/emblems').glob('*/*__mask.png')):
                self.sources[f'{f.parent.name}/{f.stem[:-6]}'] = (f, True)
        roots = [Path(stellaris) / 'flags'] if stellaris else []
        for root in roots:
            for f in sorted(root.glob('*/map/*.dds')):
                if (f.parent.parent / f.name).is_file():
                    self.sources.setdefault(f'{f.parent.parent.name}/{f.stem}', (f, False))
        if giga:
            for f in sorted((Path(giga) / 'flags/flusionian/map').glob('*.dds')):
                if (f.parent.parent / f.name).is_file():
                    self.sources.setdefault(f'flusionian/{f.stem}', (f, False))

    @lru_cache(maxsize=512)
    def mask(self, key):
        path, cached = self.sources[key]
        with Image.open(path) as source:
            mask = source.convert('L') if cached else source.convert('RGBA').getchannel('A')
            bbox = mask.getbbox()
            if bbox is None:
                raise ValueError('Empty emblem mask')
            return mask.crop(bbox)

    def render(self, key='', background='#283c63', tint='#ffffff', size=(82, 52), scale=.80):
        canvas = Image.new('RGB', size, ImageColor.getrgb(background))
        if key:
            mask = self.mask(key)
            box = max(1, round(size[1] * scale))
            ratio = box / max(mask.size)
            mask = mask.resize((max(1, round(mask.width * ratio)), max(1, round(mask.height * ratio))), Image.Resampling.LANCZOS)
            canvas.paste(ImageColor.getrgb(tint), ((size[0] - mask.width) // 2, (size[1] - mask.height) // 2), mask)
        return canvas


def default_paths():
    home = Path.home()
    pdx = home / 'Documents/Paradox Interactive'
    return {
        'mod': pdx / 'Hearts of Iron IV/mod/Legacy-of-Kattail',
        'painter': pdx / 'Europa Universalis IV/mod/LegacyOfKattailEU4/tools/culture_painter',
        'stellaris': Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Steam/steamapps/common/Stellaris',
        'giga': pdx / 'Stellaris/mod/Gigastructures',
    }
