"""Clausewitz data access, editable drafts and guarded source-file saves."""
from __future__ import annotations

import colorsys
import csv
import hashlib
import json
import os
import re
from contextlib import contextmanager
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


@lru_cache(maxsize=8192)
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
        self.before_save = None
        self.revision = 0
        self._parsed = {}

    def _path(self, relative):
        relative = str(relative).replace('\\', '/')
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('Source path escapes mod root')
        return relative, path

    @staticmethod
    def _decode(blob):
        try:
            return blob.decode('utf-8-sig')
        except UnicodeDecodeError:
            return blob.decode('cp1252')

    def text(self, relative):
        relative = str(relative).replace('\\', '/')
        if relative not in self.originals:
            relative, path = self._path(relative)
            blob = path.read_bytes() if path.is_file() else None
            self.snapshots[relative] = blob
            self.originals[relative] = self._decode(blob) if blob is not None else ''
        current = self.drafts.get(relative, self.originals[relative])
        if current is None:
            return ''
        return self._decode(current) if isinstance(current, bytes) else current

    def binary(self, relative):
        relative = str(relative).replace('\\', '/')
        if relative not in self.originals:
            relative, path = self._path(relative)
            self.snapshots[relative] = path.read_bytes() if path.is_file() else None
            self.originals[relative] = self.snapshots[relative]
        return self._blob(relative, self.drafts.get(relative, self.originals[relative]))

    def _blob(self, relative, value):
        if not isinstance(value, str):
            return value
        original = self.snapshots[relative]
        if original is None:
            return value.encode('utf-8-sig' if Path(relative).suffix == '.yml' else 'utf-8')
        return encode_source(value, original)

    @staticmethod
    def validate_text(relative, text):
        suffix = Path(relative).suffix.lower()
        if suffix == '.json':
            json.loads(text)
        elif suffix == '.yml':
            if not text.splitlines() or text.splitlines()[0] != 'l_english:':
                raise ValueError('English localisation header is missing')
            keys = re.findall(r'^\s*([^\s:#]+):\d*\s*"', text, re.M)
            if len(keys) != len(set(keys)):
                raise ValueError('Duplicate localisation keys in ' + relative)
        else:
            return parse(text)

    def parsed(self, relative):
        relative = str(relative).replace('\\', '/')
        text = self.text(relative); cached = self._parsed.get(relative)
        if cached is None or cached[0] is not text:
            cached = self._parsed[relative] = (text, parse(text))
        return cached

    def replace(self, relative, new):
        relative, _ = self._path(relative)
        old = self.text(relative)
        if new == old:
            return
        parsed = self.validate_text(relative, new)
        previous = self.drafts.get(relative, self.originals[relative])
        if relative not in self.drafts and self.snapshots[relative] is None:
            previous = None
        self.undo_stack.append((relative, previous, new))
        self.redo_stack.clear()
        self.drafts[relative] = new
        if parsed is not None: self._parsed[relative] = (new, parsed)
        self.revision += 1

    def stage_bytes(self, relative, new):
        relative, _ = self._path(relative)
        self.binary(relative)
        old = self.drafts.get(relative, self.originals[relative])
        if self._blob(relative, old) == new:
            return
        self.undo_stack.append((relative, old, new))
        self.redo_stack.clear()
        self.drafts[relative] = new
        self.revision += 1

    def edit(self, relative, node, new):
        source = self.text(relative)
        if node.children is None and len(parse(new)) != 1:
            raise ValueError('Enter one scalar value (quote text containing spaces)')
        self.replace(relative, source[:node.value_start] + new + source[node.end:])

    def undo(self):
        if self.undo_stack:
            entry = self.undo_stack.pop()
            for rel, old, new in reversed(entry if isinstance(entry, list) else [entry]):
                self.drafts[rel] = old
            self.redo_stack.append(entry)
            self.revision += 1

    def redo(self):
        if self.redo_stack:
            entry = self.redo_stack.pop()
            for rel, old, new in entry if isinstance(entry, list) else [entry]:
                self.drafts[rel] = new
            self.undo_stack.append(entry)
            self.revision += 1

    @contextmanager
    def grouped(self):
        """Make a multi-file brush action one reversible, exception-safe edit."""
        start = len(self.undo_stack)
        drafts, redo = dict(self.drafts), list(self.redo_stack)
        try:
            yield
        except Exception:
            self.drafts = drafts
            del self.undo_stack[start:]
            self.redo_stack = redo
            self.revision += 1
            raise
        else:
            records = [record for entry in self.undo_stack[start:]
                       for record in (entry if isinstance(entry, list) else [entry])]
            if len(records) > 1:
                self.undo_stack[start:] = [records]

    def reset(self):
        self.revision += 1
        self.drafts.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    @property
    def changed(self):
        return [p for p, t in self.drafts.items() if self._blob(p, t) != self.snapshots[p]]

    def validate_localisation_changes(self):
        changed = {p for p in self.changed if p.startswith('localisation/') and p.endswith('.yml')}
        if not changed:
            return
        paths = {p.relative_to(self.root).as_posix() for p in (self.root/'localisation').rglob('*.yml')}
        paths.update(p for p in self.drafts if p.startswith('localisation/') and p.endswith('.yml'))
        seen = {}
        for path in sorted(paths):
            if path in changed:
                source = self.text(path)
            else:
                if not (self.root/path).is_file():
                    continue
                source = self._decode((self.root/path).read_bytes())
            if not source or source.splitlines()[0] != 'l_english:':
                continue
            if path in changed and not self.binary(path).startswith(b'\xef\xbb\xbf'):
                raise ValueError('English localisation must have a UTF-8 BOM: ' + path)
            # The engine deliberately permits overrides in its replace layer.
            layer = 'replace' if 'replace' in Path(path).parts else 'base'
            for key in re.findall(r'^\s*([^\s:#]+):\d*\s*"', source, re.M):
                previous = seen.get((layer, key))
                if previous and (path in changed or previous in changed):
                    raise ValueError(f'Duplicate localisation key {key}: {previous} and {path}. Edit the existing definition.')
                seen[layer, key] = path

    def save(self):
        if self.before_save is not None:
            self.before_save()
        self.format_script_drafts()
        self.validate_localisation_changes()
        changes = {}
        for relative in self.changed:
            if isinstance(self.drafts[relative], str):
                self.validate_text(relative, self.drafts[relative])
            changes[relative] = (self.snapshots[relative], self.binary(relative))
        backup = write_changes(self.root, changes)
        for relative, (_, blob) in changes.items():
            text = isinstance(self.drafts[relative], str)
            self.snapshots[relative] = blob
            self.originals[relative] = self._decode(blob) if text and blob is not None else blob
        self.reset()
        return len(changes), backup

    def format_script_drafts(self):
        # Format at the operation boundary, never between span-based primitive
        # edits: those may still hold nodes from the pre-edit source.
        from script_format import format_changes,script_path
        for relative in list(self.changed):
            if not script_path(relative) or self.drafts[relative] is None:continue
            original=self.snapshots[relative]
            before=self._decode(original) if original is not None else ''
            current=self.text(relative);formatted=format_changes(relative,before,current)
            if formatted==current:continue
            if isinstance(self.drafts[relative],str):self.replace(relative,formatted)
            else:self.stage_bytes(relative,encode_source(formatted,self.drafts[relative]))


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
        self._boundary_cache = {}
        self._boundary_size = None
        self._map_samples = {}
        self._map_palettes = {}
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
        self._load_strategic_regions()
        self.files = sorted(f.relative_to(self.root).as_posix()
                            for folder in ['common', 'history', 'events', 'interface', 'map', 'country_metadata']
                            for f in (self.root / folder).rglob('*')
                            if f.is_file() and f.suffix.lower() in {'.txt', '.gui', '.gfx', '.asset'})
        self._demographic_catalogs()
        self.docs.before_save = self.prepare_save

    def validate_capitals(self):
        """Edited capitals must exist; ownership is not required for nominal seats."""
        for path in self.docs.changed:
            if not path.startswith('history/countries/'):continue
            before = self.docs.snapshots[path]
            old = self.docs._decode(before) if before is not None else ''
            new = self.docs.text(path)
            capital=scalar(new,parse(new),'capital')
            if capital!=scalar(old,parse(old),'capital') and (not capital.isdigit() or int(capital) not in self.states):
                raise ValueError(f'{Path(path).name[:3]}: choose a defined capital state')

    def prepare_save(self):
        self.validate_capitals()
        self.normalise_demographics()

    def normalise_demographics(self):
        from demographics import repair_redundant_minorities
        return repair_redundant_minorities(self)

    def refresh_countries(self):
        """Include native draft creations/removals after Apply, Cancel or Undo."""
        tags = {p.relative_to(self.root).as_posix() for p in (self.root/'common/country_tags').glob('*.txt')}
        tags.update(p for p in self.docs.originals if p.startswith('common/country_tags/') and p.endswith('.txt'))
        paths = {}
        for path in sorted(tags):
            text = self.docs.text(path)
            for n in parse(text):
                if re.fullmatch('[A-Z0-9]{3}',n.key):
                    if n.key in paths: raise ValueError('Duplicate country tag: '+n.key)
                    paths[n.key] = 'common/'+value(text,n).strip('"')
        histories = {p.relative_to(self.root).as_posix() for p in (self.root/'history/countries').glob('*.txt')}
        histories.update(p for p in self.docs.originals if p.startswith('history/countries/') and p.endswith('.txt'))
        countries = {}
        for path in sorted(histories):
            tag = Path(path).name[:3]
            if tag in paths and self.docs.text(path):
                if tag in countries: raise ValueError('Multiple country history files for '+tag)
                countries[tag] = path
        self.country_paths, self.countries = paths, countries
        scripts = {p for p in self.docs.originals if Path(p).suffix in {'.txt','.gfx','.gui','.asset'} and p.startswith(('common/','history/','interface/'))}
        self.files = sorted(p for p in set(self.files)|scripts if self.docs.snapshots.get(p, b'exists') is not None or self.docs.text(p))

    def _load_strategic_regions(self):
        regions, province_regions, region_states = {}, {}, {}
        for path in sorted((self.root / 'map/strategicregions').glob('*.txt')):
            text = self.docs.text(path.relative_to(self.root))
            region = child(parse(text), 'strategic_region')
            if region is None:
                continue
            rid = int(scalar(text, region.children, 'id'))
            if rid in regions:
                raise ValueError(f'Duplicate strategic region {rid}')
            provinces = child(region.children, 'provinces')
            ids = frozenset(int(n.key) for n in provinces.children) if provinces else frozenset()
            for pid in ids:
                if pid not in self.provinces:
                    raise ValueError(f'Strategic region {rid} references undefined province {pid}')
                if pid in province_regions:
                    raise ValueError(f'Province {pid} belongs to multiple strategic regions')
                province_regions[pid] = rid
            regions[rid] = {'name': scalar(text, region.children, 'name'), 'provinces': ids,'path':path.relative_to(self.root).as_posix()}
            region_states[rid] = frozenset(self.province_states[p] for p in ids if p in self.province_states)
        self.regions, self.province_regions, self.region_states = regions, province_regions, region_states

    def paint_targets(self, pid, scope='State'):
        sid = self.province_states.get(pid)
        if sid is None:
            return ()
        if scope == 'State':
            return (sid,)
        if scope != 'Strategic region':
            raise ValueError('Unknown paint scope: ' + scope)
        rid = self.province_regions.get(pid)
        if rid is None:
            raise ValueError(f'Province {pid} has no strategic region')
        ids = self.regions[rid]['provinces']
        states = tuple(sorted(self.region_states[rid]))
        for state in states:
            if not set(self.states[state].provinces).issubset(ids):
                raise ValueError(f'State {state} crosses strategic region {rid}; region painting would exceed its boundary')
        return states

    def state_relations(self,sid):
        text,nodes=self.state_nodes(sid);history=child(nodes,'history')
        result={'owner':'','cores':set(),'claims':set()}
        if history is None:return result
        for node in history.children:
            if node.children is not None:continue
            tag=value(text,node).strip('"')
            if node.key=='owner':result['owner']=tag
            elif node.key in {'add_core_of','remove_core_of','add_claim_by','remove_claim_by'}:
                pool=result['cores' if 'core' in node.key else 'claims']
                if node.key.startswith('add_'):pool.add(tag)
                else:pool.discard(tag)
        return result

    def set_relation_draft(self,sid,tag,kind,present=True):
        if tag not in self.country_paths:raise ValueError('Choose a registered mod country tag')
        if kind not in {'core','claim'}:raise ValueError('Choose core or claim')
        if (tag in self.state_relations(sid)[kind+'s'])==present:return
        from script_format import indentation
        add,remove=('add_core_of','remove_core_of') if kind=='core' else ('add_claim_by','remove_claim_by')
        text,nodes=self.state_nodes(sid);history=child(nodes,'history')
        if history is None:raise ValueError(f'State {sid} has no history block')
        for node in reversed(history.children):
            if node.key in {add,remove} and node.children is None and value(text,node).strip('"')==tag:
                text=text[:node.start]+text[node.end:]
        if present:
            history=child(child(parse(text),'state').children,'history')
            newline='\r\n' if '\r\n' in text else '\n';indent='\t'*indentation(text,history.start)
            at=text.rfind('\n',0,history.end-1)+1
            if text[at:history.end-1].strip():at=history.end-1;addition=newline+indent+'\t'+add+' = '+tag+newline+indent
            else:addition=indent+'\t'+add+' = '+tag+newline
            text=text[:at]+addition+text[at:]
        self.docs.replace(self.states[sid].path,text)

    def set_owner_draft(self,sid,tag,transfer_cores=True):
        with self.docs.grouped():
            previous=self.state_relations(sid)['owner']
            self._set_owner_field(sid,tag)
            if transfer_cores:self.transfer_owner_cores(sid,previous,tag)

    def transfer_owner_cores(self,sid,previous,tag):
        if previous==tag:return
        with self.docs.grouped():
            if previous and previous!=tag:self.set_relation_draft(sid,previous,'core',False)
            self.set_relation_draft(sid,tag,'core',True)

    def _set_owner_field(self, sid, tag):
        if tag not in self.country_paths:
            raise ValueError('Choose a registered mod country tag')
        state = self.states[sid]
        text, nodes = self.state_nodes(sid)
        history = child(nodes, 'history')
        if history is None:
            raise ValueError(f'State {sid} has no history block')
        owners = [n for n in history.children if n.key == 'owner']
        if owners:
            self.docs.edit(state.path, owners[-1], tag)
        else:
            newline = '\r\n' if '\r\n' in text else '\n'
            at = text.rfind('\n', 0, history.end - 1) + 1
            addition = f'\t\towner = {tag}{newline}'
            if text[at:history.end - 1].strip():
                at = history.end - 1
                addition = newline + addition
            self.docs.replace(state.path, text[:at] + addition + text[at:])

    def paint(self, pid, scope, mode, target, operation='Set', exclude=(),transfer_cores=True):
        from demographics import set_local_draft
        states = tuple(s for s in self.paint_targets(pid, scope) if s not in exclude)
        if mode == 'Wonder':
            return self.catalog_store.paint_wonder(states, target, operation)
        before = {s: {**self.demographics[s], 'culture': list(self.demographics[s]['culture'])} for s in states}
        try:
            with self.docs.grouped():
                for sid in states:
                    if mode == 'Owner':
                        self.set_owner_draft(sid,target,transfer_cores)
                        continue
                    if mode in {'Core','Claim'}:
                        if operation not in {'Add','Remove'}:raise ValueError('Choose Add or Remove')
                        self.set_relation_draft(sid,target,mode.lower(),operation=='Add')
                        continue
                    data = self.demographics[sid]
                    cultures = list(data['culture'])
                    species, minority = data['species'], data['minority']
                    if mode == 'Culture':
                        if operation == 'Set':
                            cultures = [target]
                        elif operation == 'Add':
                            if target not in cultures:
                                cultures.append(target)
                        elif operation == 'Remove':
                            cultures = [c for c in cultures if c != target]
                        else:
                            raise ValueError('Unknown culture operation: ' + operation)
                    elif mode == 'Species':
                        species = target
                    elif mode == 'Minority':
                        minority = target
                    else:
                        raise ValueError('Unknown brush: ' + mode)
                    set_local_draft(self, sid, cultures, species, minority)
        except Exception:
            self.demographics.update(before)
            raise
        return states

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
        paths = list(self.country_paths.values())
        paths.append('common/countries/colors.txt')
        signature = (tuple(self.country_paths.items()),tuple(self.docs.text(p) for p in paths))
        cached = getattr(self, '_country_colour_cache', None)
        if cached is not None and cached[0] == signature:
            return cached[1]
        country_colours = {}
        for tag, relative in self.country_paths.items():
            t = self.docs.text(relative)
            cs = [c for c in parse(t) if c.key=='color' and c.children]
            if cs:country_colours[tag] = self._script_colour(t, cs[-1])
        t = self.docs.text('common/countries/colors.txt')
        for n in parse(t):
            cs = [c for c in n.children or [] if c.key=='color' and c.children]
            if cs:country_colours[n.key] = self._script_colour(t, cs[-1])
        self._country_colour_cache = (signature, country_colours)
        return country_colours

    def boundary_mask(self, kind, size, box=None):
        """Crisp display-space lines: province 1 px, state 2 px, region 3 px."""
        if kind not in {'Province', 'State', 'Strategic region'}:
            raise ValueError('Unknown boundary type: ' + kind)
        self.load_map()
        box = box or (0, 0, *size)
        key = (size, box)
        if key != self._boundary_size:
            self._boundary_cache.clear()
            self._boundary_size = key
        if kind in self._boundary_cache:
            return self._boundary_cache[kind]
        if 'ids' not in self._boundary_cache:
            # Include the incoming edges/thickness from outside a viewport crop.
            halo = (max(0, box[0] - 3), max(0, box[1] - 3), box[2], box[3])
            self._boundary_cache['ids'] = self.map_sample(size, halo)[0]
            self._boundary_cache['halo'] = halo
        ids = self._boundary_cache['ids']
        if kind == 'Province':
            labels = ids
        else:
            lookup = np.zeros(max(self.provinces) + 1, dtype=np.int32)
            mapping = self.province_states if kind == 'State' else self.province_regions
            for pid, group in mapping.items():
                lookup[pid] = group
            labels = lookup[ids]
        edge = np.zeros(labels.shape, dtype=bool)
        edge[:, 1:] |= labels[:, 1:] != labels[:, :-1]
        edge[1:, :] |= labels[1:, :] != labels[:-1, :]
        thickness = {'Province': 1, 'State': 2, 'Strategic region': 3}[kind]
        expanded = edge.copy()
        for dy in range(thickness):
            for dx in range(thickness):
                if dy or dx:
                    expanded[dy:, dx:] |= edge[:edge.shape[0] - dy, :edge.shape[1] - dx]
        halo = self._boundary_cache['halo']
        mask = Image.fromarray(expanded.astype(np.uint8) * 255).crop(
            (box[0] - halo[0], box[1] - halo[1], box[2] - halo[0], box[3] - halo[1]))
        self._boundary_cache[kind] = mask
        return mask

    def boundary_overlay(self, image, province=False, state=False, strategic=False, size=None, box=None):
        if not any((province, state, strategic)):
            return image
        result = image.copy()
        for visible, kind, colour_value in [(province, 'Province', (55, 55, 55)),
                                            (state, 'State', (15, 15, 15)),
                                            (strategic, 'Strategic region', (245, 245, 245))]:
            if visible:
                result.paste(colour_value, mask=self.boundary_mask(kind, size or image.size, box))
        return result

    def map_sample(self, size, box=None):
        """Nearest source IDs/coordinates for a display viewport, cached across edits."""
        self.load_map()
        box = box or (0, 0, *size); key = (size, box)
        if key not in self._map_samples:
            height, width = self.map_ids.shape
            # Pillow's nearest sampler has floating-point tie behavior at some
            # ratios. Resize 1-D coordinates to match the old RGB renderer exactly.
            xs = np.asarray(Image.fromarray(np.arange(width, dtype=np.int32)[None, :]).resize(
                (size[0], 1), Image.Resampling.NEAREST))[0, box[0]:box[2]]
            ys = np.asarray(Image.fromarray(np.arange(height, dtype=np.int32)[None, :]).resize(
                (size[1], 1), Image.Resampling.NEAREST))[0, box[1]:box[3]]
            sample = (self.map_ids[np.ix_(ys, xs)], xs, ys)
            # One viewport plus its boundary halo; do not retain every zoom/pan.
            if len(self._map_samples) >= 2: self._map_samples.clear()
            self._map_samples[key] = sample
        return self._map_samples[key]

    def map_image(self, layer='Owners', size=None, box=None, *, building_key=None, building_scope=None, resource_key=None, slot_warnings=None, resource_highlight=None,country_tag=''):
        self.load_map()
        if not hasattr(self, '_province_state_ids'):
            self._province_state_ids = np.zeros(max(self.provinces) + 1, dtype=np.int32)
            self._land_provinces = np.zeros(len(self._province_state_ids), dtype=bool)
            for pid, record in self.provinces.items():
                self._province_state_ids[pid] = self.province_states.get(pid, 0)
                self._land_provinces[pid] = record['type'] == 'land'
        terrain_catalog={}
        if layer=='Terrain' and hasattr(self,'geography_store'):
            self.geography_store.sync_terrain();terrain_catalog=self.geography_store.terrain_catalog()
        static = layer in {'Provinces', 'Terrain', 'Continents', 'States'}
        palette = self._map_palettes.get(layer) if static else None
        if palette is None:
            state_colors = np.empty((max(self.states, default=0) + 1, 3), dtype=np.uint8)
            state_colors[:] = (65, 69, 78)
            owned_states=np.zeros(len(state_colors),dtype=bool)
            minority_colors = np.zeros_like(state_colors); has_minority = np.zeros(len(state_colors), dtype=bool)
            country_colors = self.country_colours() if layer == 'Owners' else {}
            sites = self.catalog_store.wonder_sites() if layer == 'Wonder' else {}
            categories=self.geography_store.categories() if layer=='State categories' else {}
            slots=self.geography_store.slot_summary() if layer=='State categories' else {}
            imperium_elements=self.imperium_store.elements() if layer=='Katzenartig Imperium' else {}
            imperium_assignments=self.imperium_store.state_assignments() if layer=='Katzenartig Imperium' else {}
            if layer in {'Resources','Population'}:
                from geography_model import RESOURCE_COLORS
                resource_key=resource_key or getattr(self,'resource_key','');resources=self.geography_store.population_counts() if layer=='Population' else self.geography_store.resource_counts(resource_key);resource_max=max(resources.values(),default=1);resource_color=(185,120,220) if layer=='Population' else RESOURCE_COLORS.get(resource_key,(155,195,225))
            for sid in self.states:
                data = getattr(self, 'demographics', {}).get(sid, {})
                if layer == 'Owners':
                    text, nodes = self.state_nodes(sid); history = child(nodes, 'history')
                    tag = scalar(text, history.children, 'owner') if history else ''
                    rgb = country_colors.get(tag) or (colour(tag) if tag else (65, 69, 78))
                elif layer=='Cores/Claims':
                    relations=self.state_relations(sid)
                    rgb=(55,180,90) if country_tag in relations['cores'] else (240,205,55) if country_tag in relations['claims'] else (65,69,78)
                    owned_states[sid]=bool(country_tag) and relations['owner']==country_tag
                elif layer == 'Culture':
                    colors = [self.culture_colours.get(v, (128, 128, 128)) for v in data.get('culture', [])]
                    rgb = tuple(round(sum(v) / len(colors)) for v in zip(*colors)) if colors else (128, 128, 128)
                elif layer in {'Species', 'Minority'}:
                    colors = self.species_colours if layer == 'Species' else self.minority_colours
                    rgb = colors.get(data.get('species' if layer == 'Species' else 'minority'), (128, 128, 128))
                    minor = data.get('minority', 1000)
                    if layer == 'Species' and minor != 1000:
                        minority_colors[sid] = self.minority_colours.get(minor, (128, 128, 128)); has_minority[sid] = True
                elif layer == 'Wonder':
                    ident = sites.get(sid, 0); rgb = colour('wonder_' + str(ident)) if ident else (90, 94, 100)
                elif layer=='Katzenartig Imperium':
                    element=imperium_elements.get(imperium_assignments.get(sid,0));rgb=element.color if element else (65,69,78)
                elif layer=='State categories':rgb=categories.get(slots[sid]['category'],{}).get('color',(128,128,128))
                elif layer in {'Resources','Population'}:
                    amount=resources.get(sid,0);t=.25+.75*float(amount/resource_max) if amount else 0
                    rgb=tuple(round(a+(b-a)*t) for a,b in zip((28,31,37),resource_color))
                else: rgb = colour(sid)
                state_colors[sid] = rgb
            palette = state_colors[self._province_state_ids]
            if layer=='Strategic regions':
                for pid in self.provinces:
                    rid=self.province_regions.get(pid);palette[pid]=colour('region_'+str(rid)) if rid is not None else (60,65,73)
            elif layer=='Koppen presets':
                from geography_model import KOPPEN_COLORS
                matches=self.geography_store.preset_regions();palette[:]=(128,128,128)
                for pid,rid in self.province_regions.items():
                    if rid in matches:palette[pid]=KOPPEN_COLORS[matches[rid][0]]
            elif layer=='Railways':
                from railway_model import railway_color
                palette[:]=railway_color(0)
                for pid,level in self.railway_store.levels().items():palette[pid]=railway_color(level,self.railway_store.max_level())
            elif layer=='VPs':
                from geography_model import vp_color
                records=self.geography_store.victory_points() if hasattr(self,'geography_store') else {}
                maximum=max((d['value'] for d in records.values()),default=1)
                palette[:]=(60,65,73)
                for pid,data in records.items():
                    if pid<len(palette):palette[pid]=vp_color(data['value'],maximum)
            elif layer=='Buildings':
                from geography_model import building_color
                scope=building_scope or getattr(self,'building_scope','State');kind=building_key if building_key is not None else getattr(self,'building_key','')
                counts=self.geography_store.building_counts(kind,scope);maximum=max(counts.values(),default=1)
                if scope=='State':
                    for sid in self.states:state_colors[sid]=building_color(counts.get(sid,0),maximum)
                    palette=state_colors[self._province_state_ids]
                else:
                    palette[:]=building_color(0,maximum)
                    for pid,level in counts.items():palette[pid]=building_color(level,maximum)
            if layer in {'Provinces', 'Terrain', 'Continents'}:
                for pid, record in self.provinces.items():
                    palette[pid] = record['rgb'] if layer == 'Provinces' else terrain_catalog.get(record['terrain'],{}).get('color',(128,128,128)) if layer=='Terrain' else colour(record['continent'])
            if layer not in {'Provinces','Strategic regions','Koppen presets'}: palette[~self._land_provinces] = (26, 43, 60)
            if 0 not in self.provinces: palette[0] = 0
            if static: self._map_palettes[layer] = palette
        height, width = self.map_ids.shape
        if size is None:
            ids = self.map_ids; xs = np.arange(width); ys = np.arange(height)
        else: ids, xs, ys = self.map_sample(size, box)
        pixels = palette[ids]
        if layer=='Cores/Claims':
            stripes=(ys[:,None]+xs[None,:])%32<9
            stripes &= owned_states[self._province_state_ids[ids]] & self._land_provinces[ids]
            pixels[stripes]=(55,125,245)
        if layer == 'Species':
            states = self._province_state_ids[ids]
            stripes = (ys[:, None] + xs[None, :]) % 32 < 9
            stripes &= has_minority[states] & self._land_provinces[ids]
            pixels[stripes] = minority_colors[states[stripes]]
        warnings=slot_warnings if slot_warnings is not None else layer=='State categories' or layer=='Buildings' and (building_scope or getattr(self,'building_scope','State'))=='State'
        if warnings:
            summary=self.geography_store.slot_summary();status=np.zeros(max(self.states,default=0)+1,dtype=np.uint8)
            for sid,d in summary.items():status[sid]=2 if d['status']=='over' else 1 if d['status']=='full' else 0
            kinds=status[self._province_state_ids[ids]];bands=(ys[:,None]+xs[None,:])%24<7
            for key,tint,alpha in [(2,(255,40,40),.65),(1,(255,220,60),.22)]:
                mask=bands&(kinds==key)&self._land_provinces[ids]
                pixels[mask]=np.rint(pixels[mask]*(1-alpha)+np.array(tint)*alpha).astype(np.uint8)
        if layer=='Resources' and resource_highlight is not None:
            counts=self.geography_store.resource_type_counts();marked=np.zeros(max(self.states,default=0)+1,dtype=bool)
            for sid,amount in counts.items():marked[sid]=amount>resource_highlight
            mask=marked[self._province_state_ids[ids]]&self._land_provinces[ids]&((ys[:,None]+xs[None,:])%24<7)
            pixels[mask]=np.rint(pixels[mask]*.35+np.array((255,40,40))*.65).astype(np.uint8)
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
        'game': Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Steam/steamapps/common/Hearts of Iron IV',
        'giga': pdx / 'Stellaris/mod/Gigastructures',
    }
