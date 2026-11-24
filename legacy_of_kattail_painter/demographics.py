"""Conservative evaluator for this mod's initial state demographics, not a game VM."""
from __future__ import annotations

import re
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
        return self.data


def set_local_draft(world, sid, cultures, species, minority):
    if any(c < 0 for c in cultures) or species < 0 or minority < 0:
        raise ValueError('Demographic IDs must be nonnegative')
    rel = world.states[sid].path
    t, ns = world.state_nodes(sid)
    hist = child(ns, 'history')
    if hist is None:
        raise ValueError('State has no history block')
    start_marker = '# LOK PAINTER DEMOGRAPHICS BEGIN'
    end_marker = '# LOK PAINTER DEMOGRAPHICS END'
    snippet = '\n\t\t' + start_marker + '\n'
    snippet += '\t\tclear_array = state_cultures\n'
    for c in cultures:
        snippet += f'\t\tadd_to_array = {{ array = state_cultures value = {c} }}\n'
    snippet += f'\t\tset_variable = {{ species = {species} }}\n'
    snippet += f'\t\tset_variable = {{ minority = {minority} }}\n'
    snippet += '\t\t' + end_marker + '\n\t'
    if start_marker in t:
        a = t.index(start_marker)
        a = t.rfind('\n', 0, a)
        b = t.index(end_marker, a) + len(end_marker)
        b = t.find('\n', b) + 1
        new = t[:a] + snippet.rstrip('\t') + t[b:]
    else:
        # Append last within root history, leaving dated histories intact and distinguishable.
        new = t[:hist.end - 1] + snippet + t[hist.end - 1:]
    world.docs.replace(rel, new)
    world.demographics[sid] = {'culture': cultures, 'species': species, 'minority': minority}
