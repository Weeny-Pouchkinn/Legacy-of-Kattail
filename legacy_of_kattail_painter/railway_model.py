"""Native railway links, province brushes and deterministic route compaction."""
from __future__ import annotations

from collections import defaultdict
import re

import numpy as np

from geography_model import numeric


RAILWAY_PATH = 'map/railways.txt'


def edge_key(a, b):
    return (a, b) if a < b else (b, a)


def railway_color(level, maximum=5):
    if not level:
        return (55, 60, 68)
    colors = ((80, 190, 235), (85, 205, 125), (235, 215, 65), (240, 145, 55), (220, 65, 90))
    return colors[min(4, round(4 * (level - 1) / max(1, maximum - 1)))]


def compact_routes(edges):
    """Join maximal equal-level chains; retain every undirected link exactly once.

    Branches terminate paths. Split cycles before repeating a province, so even
    a loop uses ordinary simple native paths. No new connection is inferred.
    """
    by_level = defaultdict(set)
    for pair, level in edges.items():
        if level:
            by_level[level].add(pair)
    routes = []
    for level, remaining in sorted(by_level.items()):
        neighbors = defaultdict(set)
        for a, b in remaining:
            neighbors[a].add(b); neighbors[b].add(a)

        def follow(a, b):
            path = [a]
            while edge_key(a, b) in remaining:
                remaining.remove(edge_key(a, b)); path.append(b)
                if len(neighbors[b]) != 2:
                    break
                c = next(n for n in neighbors[b] if n != a)
                if c in path:
                    break
                a, b = b, c
            routes.append((level, tuple(path)))

        for a in sorted(neighbors):
            if len(neighbors[a]) != 2:
                for b in sorted(neighbors[a]):
                    if edge_key(a, b) in remaining:
                        follow(a, b)
        while remaining:
            follow(*min(remaining))
    return routes


class RailwayStore:
    def __init__(self, world, geography, characters):
        self.world, self.geo, self.characters, self.docs = world, geography, characters, world.docs
        self._text = None; self._edges = {}; self._levels = {}; self._neighbors = {}
        self._adjacency = None; self._maximum = None; self._baseline_invalid = None
        self._baseline_topology = None
        self._bitmap_adjacency = None; self._rule_revision = -1; self._rule_signature = None
        self._original_adjacency = None; self._original_rule_signature = None
        world.railway_store = self

    def max_level(self):
        if self._maximum is None:
            # NSupply defines the network cap; rail_way/province_max is not it.
            native = self.characters.game_root / 'common/defines'
            files = {p.name: p for p in native.glob('*.lua')}
            files.update({p.name: p for p in (self.world.root / 'common/defines').glob('*.lua')})
            maximum = None
            for name, path in sorted(files.items()):
                text = re.sub(r'--[^\r\n]*', '', path.read_text(encoding='utf-8-sig'))
                section = re.search(r'\bNSupply\s*=\s*\{(.*?)\n\s*\}', text, re.S)
                if section:
                    match = re.search(r'\bMAX_RAILWAY_LEVEL\s*=\s*(\d+)', section[1])
                    if match: maximum = int(match[1])
                for match in re.finditer(r'NDefines\.NSupply\.MAX_RAILWAY_LEVEL\s*=\s*(\d+)', text):
                    maximum = int(match[1])
            if maximum is None or maximum < 1:
                raise ValueError('Cannot find NSupply.MAX_RAILWAY_LEVEL in game/mod defines')
            self._maximum = maximum
        return self._maximum

    def parse_edges(self, text):
        edges = {}
        for number, line in enumerate(text.splitlines(), 1):
            body = line.split('#', 1)[0].strip()
            if not body: continue
            try: values = [int(v) for v in body.split()]
            except ValueError: raise ValueError(f'railways.txt:{number}: expected integers') from None
            if len(values) < 4 or values[1] != len(values) - 2:
                raise ValueError(f'railways.txt:{number}: route needs at least two provinces and an exact count')
            level, _, *provinces = values
            if not 1 <= level <= self.max_level():
                raise ValueError(f'railways.txt:{number}: level outside 1–{self.max_level()}')
            for pid in provinces:
                if pid not in self.world.province_states or self.world.provinces[pid]['type'] != 'land':
                    raise ValueError(f'railways.txt:{number}: province {pid} is not state-owned land')
            for a, b in zip(provinces, provinces[1:]):
                if a == b: raise ValueError(f'railways.txt:{number}: repeated adjacent province {a}')
                pair = edge_key(a, b); edges[pair] = max(level, edges.get(pair, 0))
        return edges

    def edges(self):
        text = self.docs.text(RAILWAY_PATH)
        if text is not self._text:
            edges = self.parse_edges(text); levels = {}; neighbors = defaultdict(set)
            for (a, b), level in edges.items():
                for p, n in ((a, b), (b, a)):
                    levels[p] = max(levels.get(p, 0), level); neighbors[p].add(n)
            self._text, self._edges, self._levels, self._neighbors = text, edges, levels, neighbors
        return self._edges

    def levels(self):
        self.edges(); return self._levels

    def adjacency(self):
        if self._bitmap_adjacency is None:
            self.world.load_map(); ids = self.world.map_ids; stride = max(self.world.provinces) + 1
            pairs = set()
            for left, right in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :]), (ids[:, -1:], ids[:, :1])):
                mask = left != right
                a, b = left[mask].astype(np.int64), right[mask].astype(np.int64)
                for packed in np.unique(np.minimum(a, b) * stride + np.maximum(a, b)):
                    p, q = divmod(int(packed), stride)
                    if p in self.world.province_states and q in self.world.province_states and self.world.provinces[p]['type'] == self.world.provinces[q]['type'] == 'land':
                        pairs.add((p, q))
            self._bitmap_adjacency = pairs
        if self._adjacency is None or self._rule_revision != self.docs.revision:
            paths = [state.path for state in self.world.states.values()] + ['map/adjacencies.csv']
            signature = tuple(self.docs.text(path) for path in paths)
            if self._adjacency is None or signature != self._rule_signature:
                self._adjacency = self.filter_rules(False); self._rule_signature = signature
            originals = tuple(id(self.docs.snapshots[path]) for path in paths)
            if originals != self._original_rule_signature:
                self._original_adjacency = self.filter_rules(True); self._original_rule_signature = originals
            self._rule_revision = self.docs.revision
        return self._adjacency

    def filter_rules(self, original):
        from model import child, parse, scalar
        def source(path):
            current = self.docs.text(path)
            if not original:return current
            return self.docs._decode(self.docs.snapshots[path] or b'')
        blocked_edges = set()
        for line in source('map/adjacencies.csv').splitlines()[1:]:
            fields = line.split(';')
            if len(fields)>2 and fields[2].strip()=='impassable':
                try:blocked_edges.add(edge_key(int(fields[0]),int(fields[1])))
                except ValueError:continue
        blocked = set()
        for sid,state in self.world.states.items():
            text,nodes = self.world.state_nodes(sid)
            if original:
                initial = source(state.path)
                if initial != text:
                    text=initial;nodes=child(parse(text),'state').children
            if scalar(text,nodes,'impassable')=='yes':blocked.update(state.provinces)
        return {pair for pair in self._bitmap_adjacency if pair not in blocked_edges and not blocked.intersection(pair)}

    def invalid_links(self):
        return set(self.edges()) - self.adjacency()

    def baseline_invalid(self):
        self.docs.text(RAILWAY_PATH)
        original = self.docs.snapshots[RAILWAY_PATH] or b''
        self.adjacency();signature = (id(original), self._original_rule_signature)
        if self._baseline_topology != signature:
            self._baseline_topology = signature
            self._baseline_invalid = set(self.parse_edges(self.docs._decode(original))) - self._original_adjacency
        return self._baseline_invalid

    def write_edges(self, edges):
        for (a,b),level in edges.items():
            if a>=b or a not in self.world.province_states or b not in self.world.province_states or self.world.provinces[a]['type']!='land' or self.world.provinces[b]['type']!='land':
                raise ValueError('Railway links require two distinct state-owned land provinces')
            if not isinstance(level,int) or not 1<=level<=self.max_level():
                raise ValueError('Railway link has an invalid level')
        extra = set(edges) - self.adjacency() - self.baseline_invalid()
        if extra: raise ValueError('New railway crosses a non-neighbor or impassable border: ' + str(min(extra)))
        current = self.docs.text(RAILWAY_PATH); newline = '\r\n' if '\r\n' in current else '\n'
        # Comments survive recomputation, including annotations from overlapping routes.
        comments = [line[line.index('#'):] for line in current.splitlines() if '#' in line]
        valid = {pair: level for pair, level in edges.items() if pair in self.adjacency()}
        routes = compact_routes(valid)
        # Preserve pre-existing broken links explicitly, without routing over them.
        routes.extend((level, pair) for pair, level in sorted(edges.items()) if pair not in self.adjacency())
        rows = comments + [f'{level} {len(provinces)} ' + ' '.join(map(str, provinces)) for level, provinces in routes]
        text = newline.join(rows) + (newline if rows else '')
        self.docs.replace(RAILWAY_PATH, text)

    def change_province(self, pid, level, operation='Set', amount=1, reverse=False, existing_only=False, seen=None, anchor=None):
        if pid not in self.world.province_states or self.world.provinces[pid]['type'] != 'land':
            raise ValueError('Choose a land province belonging to a state')
        if operation not in {'Set', 'Change'}: raise ValueError('Choose Paint level or Add/remove levels')
        maximum = self.max_level(); level = int(numeric(level, 0, True))
        amount = int(numeric(amount, 1, True)) if operation=='Change' else 1
        if level > maximum or amount > maximum: raise ValueError(f'Choose railway levels/amounts from 0/1 to {maximum}')
        edges = dict(self.edges()); levels = self.levels(); seen = seen if seen is not None else set()
        candidates = {edge_key(pid, n) for n in self._neighbors.get(pid, ())}
        if not existing_only and not reverse and (operation != 'Set' or level):
            for pair in self.adjacency():
                if pid in pair:
                    other = pair[1] if pair[0] == pid else pair[0]
                    if other in levels or other == anchor: candidates.add(pair)
        changed = set()
        for pair in sorted(candidates - seen):
            old = edges.get(pair, 0)
            new = (0 if reverse else level) if operation == 'Set' else max(0, min(maximum, old + (-amount if reverse else amount)))
            if old != new:
                if new: edges[pair] = new
                else: edges.pop(pair, None)
                changed.add(pair)
        if changed: self.write_edges(edges)
        seen.update(candidates)
        return len(changed)

    def prepare_save(self):
        if RAILWAY_PATH not in self.docs.changed: return
        self.write_edges(dict(self.edges()))
