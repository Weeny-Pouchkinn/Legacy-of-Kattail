#!/usr/bin/env python3
"""Generate Legacy of Kattail state-level species/culture/politics share arrays.

Authoritative state arrays:
  lok_state_species_array : 61 entries, each value is a 0..1 population share
  lok_state_culture_array : 103 entries, each value is a 0..1 population share
  lok_state_parties_array : 10 entries, each value is a 0..1 population share

The generator resolves the mod's current startup species/minority/culture assignments,
creates fuzzy 70/30 majority/minority species splits and fuzzy 50/50 hybrid-culture
splits, then assigns 1-3 ideologies per positive-population state while keeping each
country's population-weighted political shares close to its starting popularity.

Re-running is idempotent. Both the old POP GROUPS generated block and this generator's
STATE DISTRIBUTIONS block are removed before new output is injected.
"""
from __future__ import annotations
import argparse, csv, math, random, re, shutil, sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

OLD_START_MARKER = "# >>> LOK GENERATED POP GROUPS START >>>"
OLD_END_MARKER = "# <<< LOK GENERATED POP GROUPS END <<<"
START_MARKER = "# >>> LOK GENERATED STATE DISTRIBUTIONS START >>>"
END_MARKER = "# <<< LOK GENERATED STATE DISTRIBUTIONS END <<<"
DEFAULT_SEED = 20260826
SPECIES_COUNT = 61
CULTURE_COUNT = 103
POLITICS_COUNT = 10
IDEOLOGY_KEYS = [
    "communism", "socialism", "social_democratic", "social_liberal", "democratic",
    "social_conservative", "authoritarian_democratic", "neutrality", "fascism",
]
IDEOLOGY_NAMES = [
    "Communist", "Socialist", "Social Democrat", "Social Liberal", "Market Liberal",
    "Social Conservative", "Authoritarian Democratic", "Autocratic",
    "National Mysticist", "Apolitical",
]
URBAN_IDEOLOGIES = {2, 3, 4}
DEFAULT_NONPLAYABLE = {"MUN", "XEN", "MRI", "AAA", "ZZZ", "WWW"}

@dataclass
class Entry:
    key: str | None
    value: Any


def strip_comments(text: str) -> str:
    out, i, in_string, escaped = [], 0, False, False
    while i < len(text):
        c = text[i]
        if in_string:
            out.append(c)
            if escaped: escaped = False
            elif c == "\\": escaped = True
            elif c == '"': in_string = False
            i += 1; continue
        if c == '"':
            in_string = True; out.append(c); i += 1; continue
        if c == '#':
            while i < len(text) and text[i] != '\n': i += 1
            continue
        out.append(c); i += 1
    return ''.join(out)


def tokenize(text: str) -> list[str]:
    return re.findall(r'"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=]+', strip_comments(text))


def parse_pdx(text: str) -> list[Entry]:
    toks, pos = tokenize(text), 0
    def parse_block(stop: bool) -> list[Entry]:
        nonlocal pos
        result = []
        while pos < len(toks):
            if toks[pos] == '}':
                pos += 1
                if stop: return result
                continue
            if toks[pos] == '{':
                pos += 1; result.append(Entry(None, parse_block(True))); continue
            key = toks[pos]; pos += 1
            if pos < len(toks) and toks[pos] == '=':
                pos += 1
                if pos < len(toks) and toks[pos] == '{':
                    pos += 1; value = parse_block(True)
                elif pos < len(toks):
                    value = toks[pos]; pos += 1
                else: value = ""
                result.append(Entry(key, value))
            else:
                result.append(Entry(None, key))
        return result
    return parse_block(False)


def unquote(v: Any) -> str:
    s = str(v)
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == '"' else s


def as_float(v: Any, default=None):
    try: return float(unquote(v))
    except (TypeError, ValueError): return default


def as_int(v: Any, default=None):
    f = as_float(v, None)
    return int(f) if f is not None else default


def direct(entries: Iterable[Entry], key: str) -> list[Entry]:
    return [e for e in entries if e.key == key]


def first_block(entries: Iterable[Entry], key: str):
    for e in entries:
        if e.key == key and isinstance(e.value, list): return e.value
    return None


def last_scalar(entries: Iterable[Entry], key: str, default=None):
    val = default
    for e in entries:
        if e.key == key and not isinstance(e.value, list): val = e.value
    return val


def recursively_find_blocks(entries: Iterable[Entry], key: str):
    for e in entries:
        if e.key == key and isinstance(e.value, list): yield e.value
        if isinstance(e.value, list): yield from recursively_find_blocks(e.value, key)


@dataclass
class StateData:
    sid: int
    filename: str
    path: Path
    text: str
    owner: str | None
    manpower: float
    category: str
    had_generated_block: bool = False
    species: int | None = None
    minority: int | None = None
    cultures: list[int] = field(default_factory=list)
    political_shares: dict[int, float] = field(default_factory=dict)
    species_shares: list[tuple[int, float]] = field(default_factory=list)
    culture_shares: list[tuple[int, float]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    @property
    def pop_k(self): return self.manpower / 1000.0


@dataclass
class CountryData:
    tag: str
    path: Path | None
    ideology_shares: list[float]
    states: list[StateData] = field(default_factory=list)
    actual_shares: list[float] = field(default_factory=lambda: [0.0] * 10)
    allocation_error: float = 0.0
    dropped_ideologies: list[int] = field(default_factory=list)


def remove_generated_block(text: str) -> str:
    for start, end in ((OLD_START_MARKER, OLD_END_MARKER), (START_MARKER, END_MARKER)):
        pat = re.compile(r'\n?[ \t]*' + re.escape(start) + r'.*?' + re.escape(end) + r'[ \t]*\n?', re.S)
        text = pat.sub('\n', text)
    return text


def find_named_block_span(text: str, name: str):
    m = re.search(r'\b' + re.escape(name) + r'\s*=\s*\{', text)
    if not m: return None
    open_pos = text.find('{', m.start(), m.end())
    depth = 0; in_string = False; escaped = False; in_comment = False
    for i in range(open_pos, len(text)):
        c = text[i]
        if in_comment:
            if c == '\n': in_comment = False
            continue
        if in_string:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': in_string = False
            continue
        if c == '#': in_comment = True
        elif c == '"': in_string = True
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return open_pos, i, m.start()
    return None


def apply_state_ops(entries: list[Entry], state: StateData) -> None:
    for e in entries:
        if e.key == 'set_variable' and isinstance(e.value, list):
            for a in e.value:
                if a.key == 'species' and not isinstance(a.value, list): state.species = as_int(a.value, state.species)
                elif a.key == 'minority' and not isinstance(a.value, list): state.minority = as_int(a.value, state.minority)
        elif e.key == 'clear_array' and not isinstance(e.value, list) and unquote(e.value) == 'state_cultures':
            state.cultures.clear()
        elif e.key == 'add_to_array' and isinstance(e.value, list):
            arr = unquote(last_scalar(e.value, 'array', ''))
            if arr == 'state_cultures':
                v = as_int(last_scalar(e.value, 'value', None), None)
                if v is not None and v not in state.cultures: state.cultures.append(v)


def parse_state_file(path: Path):
    raw = path.read_text(encoding='utf-8-sig', errors='replace')
    text = remove_generated_block(raw)
    try: root = parse_pdx(text)
    except Exception as exc:
        print(f"WARNING: failed to parse state file {path}: {exc}", file=sys.stderr); return None
    state = first_block(root, 'state')
    if state is None: return None
    sid = as_int(last_scalar(state, 'id'), None)
    if sid is None: return None
    history = first_block(state, 'history') or []
    owner_raw = last_scalar(history, 'owner', None)
    data = StateData(
        sid=sid, filename=path.name, path=path, text=text,
        owner=unquote(owner_raw) if owner_raw is not None else None,
        manpower=as_float(last_scalar(state, 'manpower'), 0.0) or 0.0,
        category=unquote(last_scalar(state, 'state_category', 'unknown')),
        had_generated_block=(raw != text),
    )
    apply_state_ops(history, data)
    return data


def parse_country_history(path: Path):
    root = parse_pdx(path.read_text(encoding='utf-8-sig', errors='replace'))
    shares = [0.0] * 10
    popularity = direct(root, 'set_popularities')
    if popularity and isinstance(popularity[-1].value, list):
        block = popularity[-1].value
        for i, key in enumerate(IDEOLOGY_KEYS): shares[i] = max(0.0, as_float(last_scalar(block, key, 0), 0.0) or 0.0)
    ruling = None
    politics = direct(root, 'set_politics')
    if politics and isinstance(politics[-1].value, list):
        r = last_scalar(politics[-1].value, 'ruling_party', None)
        if r is not None: ruling = unquote(r)
    total = sum(shares[:9])
    if total <= 0:
        if ruling in IDEOLOGY_KEYS: shares[IDEOLOGY_KEYS.index(ruling)] = 1.0
        else: shares[9] = 1.0
    else: shares = [x / total for x in shares]
    return shares, ruling


def discover_nonplayable(repo: Path) -> set[str]:
    tags = set(DEFAULT_NONPLAYABLE)
    for p in sorted((repo/'common/scripted_triggers').glob('*.txt')):
        try: root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception: continue
        for block in recursively_find_blocks(root, 'is_non_playable_country'):
            def rec(entries):
                for e in entries:
                    if e.key == 'tag' and not isinstance(e.value, list):
                        tag = unquote(e.value)
                        if re.fullmatch(r'[A-Z0-9]{3}', tag): tags.add(tag)
                    if isinstance(e.value, list): rec(e.value)
            rec(block)
    return tags


def load_scripted_trigger_registry(repo: Path):
    registry = {}
    for p in sorted((repo/'common/scripted_triggers').glob('*.txt')):
        try: root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception: continue
        for e in root:
            if e.key and isinstance(e.value, list): registry[unquote(e.key)] = e.value
    return registry


def resolve_static_country_selector(entries, registry, stack=()):
    def one(e):
        if e.key is None: return None
        key = unquote(e.key)
        if key == 'tag' and not isinstance(e.value, list):
            tag = unquote(e.value); return {tag} if re.fullmatch(r'[A-Z0-9]{3}', tag) else None
        if key == 'OR' and isinstance(e.value, list):
            out = set()
            for child in e.value:
                part = one(child)
                if part is None: return None
                out.update(part)
            return out
        if not isinstance(e.value, list) and unquote(e.value).lower() == 'yes' and key in registry:
            if key in stack: return None
            return resolve_static_country_selector(registry[key], registry, stack + (key,))
        return None
    selectors = []
    for e in entries:
        part = one(e)
        if part is None: return None
        selectors.append(part)
    if not selectors: return None
    result = set(selectors[0])
    for part in selectors[1:]: result.intersection_update(part)
    return result


def simulate_startup_demographics(repo: Path, states_by_id: dict[int, StateData]):
    warnings = []
    by_owner = defaultdict(list)
    for s in states_by_id.values():
        if s.owner: by_owner[s.owner].append(s)
    registry = load_scripted_trigger_registry(repo)

    def eval_limit(entries, state):
        def one(e):
            if e.key is None: return None
            key = unquote(e.key)
            if key == 'check_variable' and isinstance(e.value, list):
                checks = [x for x in e.value if x.key in ('species', 'minority') and not isinstance(x.value, list)]
                if len(checks) != 1 or len(e.value) != 1: return None
                chk = checks[0]; wanted = as_int(chk.value, None)
                if wanted is None: return None
                return (state.species if chk.key == 'species' else state.minority) == wanted
            if key == 'NOT' and isinstance(e.value, list):
                r = eval_limit(e.value, state); return None if r is None else not r
            if key == 'AND' and isinstance(e.value, list): return eval_limit(e.value, state)
            if key == 'OR' and isinstance(e.value, list):
                vals = [one(c) for c in e.value]
                return None if any(v is None for v in vals) else any(vals)
            return None
        vals = [one(e) for e in entries]
        return None if any(v is None for v in vals) else all(vals)

    def apply_country_ops(tag, entries, source):
        for e in entries:
            if e.key != 'every_owned_state' or not isinstance(e.value, list): continue
            limits = direct(e.value, 'limit')
            if not limits:
                for s in by_owner.get(tag, []): apply_state_ops(e.value, s)
                continue
            if len(limits) == 1 and isinstance(limits[0].value, list):
                unsupported = False
                for s in by_owner.get(tag, []):
                    match = eval_limit(limits[0].value, s)
                    if match is None: unsupported = True; break
                    if match: apply_state_ops(e.value, s)
                if not unsupported: continue
            if any(x in repr(e.value) for x in ('species','minority','state_cultures')):
                warnings.append(f"Unsupported conditional demographic every_owned_state in {source}, tag {tag}")

    def apply_global(entries, source):
        for e in entries:
            if not isinstance(e.value, list) or e.key is None: continue
            key = unquote(e.key)
            if key.isdigit() and int(key) in states_by_id: apply_state_ops(e.value, states_by_id[int(key)])
            elif re.fullmatch(r'[A-Z0-9]{3}', key): apply_country_ops(key, e.value, source)
            elif key == 'every_country':
                limits = direct(e.value, 'limit')
                if len(limits) == 1 and isinstance(limits[0].value, list):
                    tags = resolve_static_country_selector(limits[0].value, registry)
                    if tags is not None:
                        for tag in sorted(tags): apply_country_ops(tag, e.value, source)
                    elif any(x in repr(e.value) for x in ('species','minority','state_cultures')):
                        warnings.append(f"Unsupported every_country demographic selector in {source}: {repr(limits[0].value)[:240]}")

    for p in sorted((repo/'common/on_actions').glob('*.txt')):
        try: root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception as exc: warnings.append(f"Could not parse {p}: {exc}"); continue
        top = first_block(root, 'on_actions')
        if top is None: continue
        for startup in direct(top, 'on_startup'):
            if not isinstance(startup.value, list): continue
            for effect in direct(startup.value, 'effect'):
                if isinstance(effect.value, list): apply_global(effect.value, p.name)
    return warnings


def apply_owner_fallbacks(states, playable_tags):
    species_counts, culture_counts = defaultdict(Counter), defaultdict(Counter)
    for s in states:
        if not s.owner or s.owner not in playable_tags: continue
        weight = max(1, int(round(s.manpower)))
        if s.species is not None and s.species != 1000: species_counts[s.owner][s.species] += weight
        for c in s.cultures[:2]: culture_counts[s.owner][c] += weight
    for s in states:
        if not s.owner or s.owner not in playable_tags: continue
        if s.species is None or s.species == 1000:
            if species_counts[s.owner]:
                s.species = species_counts[s.owner].most_common(1)[0][0]
                s.warnings.append(f"species missing; inherited owner modal species {s.species}")
        if not s.cultures and culture_counts[s.owner]:
            c = culture_counts[s.owner].most_common(1)[0][0]
            s.cultures = [c]; s.warnings.append(f"culture missing; inherited owner modal culture {c}")
        if len(s.cultures) > 2:
            old = list(s.cultures); s.cultures = s.cultures[:2]
            s.warnings.append(f"more than two startup cultures {old}; kept first two {s.cultures}")
        if s.minority == 1000 or s.minority == s.species: s.minority = None


def is_large_urban(s):
    cat = s.category.lower()
    return any(x in cat for x in ('city','metropolis','megalopolis','urban')) or s.manpower >= 2_000_000


def weighted_choice_without_replacement(rng, weights, k):
    pool, out = dict(weights), []
    for _ in range(min(k, len(pool))):
        total = sum(max(0.0,w) for w in pool.values())
        if total <= 0: pick = rng.choice(list(pool))
        else:
            r = rng.random()*total; acc = 0.0; pick = next(iter(pool))
            for idx,w in pool.items():
                acc += max(0.0,w)
                if r <= acc: pick = idx; break
        out.append(pick); pool.pop(pick, None)
    return out


def allocate_country_politics(country: CountryData, seed: int):
    states = [s for s in country.states if s.manpower > 0]
    if not states: return
    target = list(country.ideology_shares); z = sum(target)
    target = ([0.0]*9+[1.0]) if z <= 0 else [x/z for x in target]
    active = [i for i,x in enumerate(target) if x > 1e-9]
    base_rng = random.Random((seed*1000003) ^ sum(ord(c) << (i%8) for i,c in enumerate(country.tag)))
    best_rows, best_score, best_dropped = None, float('inf'), []
    for attempt in range(180):
        rng = random.Random(base_rng.randrange(1<<62) ^ attempt)
        ks = []
        for s in states:
            n = len(active)
            if n <= 1: k = 1
            elif is_large_urban(s): k = 3 if n >= 3 and rng.random() < .60 else 2
            else:
                roll = rng.random(); k = 1 if roll < .14 else (2 if roll < .90 else 3); k = min(k,n)
            ks.append(k)
        while sum(ks) < min(len(active), 3*len(states)):
            cand = [i for i,k in enumerate(ks) if k < min(3,len(active))]
            if not cand: break
            ks[rng.choice(cand)] += 1
        representable = min(sum(ks), len(active))
        kept = sorted(active, key=lambda i: target[i], reverse=True)[:representable]
        dropped = [i for i in active if i not in kept]
        local_target = list(target)
        for i in dropped: local_target[i] = 0.0
        nrm = sum(local_target)
        if nrm <= 0: local_target[9] = 1.0; nrm = 1.0
        local_target = [x/nrm for x in local_target]
        supports, raw_scores = [], []
        for s,k in zip(states,ks):
            scores = {}
            for i in kept:
                score = max(local_target[i],1e-8)**.72 * math.exp(rng.gauss(0.0,.62))
                if is_large_urban(s) and i in URBAN_IDEOLOGIES: score *= 1.85
                scores[i] = score
            chosen = weighted_choice_without_replacement(rng,scores,k)
            urban = [i for i in kept if i in URBAN_IDEOLOGIES]
            if is_large_urban(s) and urban and not any(i in URBAN_IDEOLOGIES for i in chosen):
                u = max(urban, key=lambda i:scores.get(i,0.0))
                if chosen: chosen[-1] = u
                else: chosen=[u]
                chosen=list(dict.fromkeys(chosen))
                while len(chosen)<k:
                    for cand in sorted(scores,key=scores.get,reverse=True):
                        if cand not in chosen: chosen.append(cand); break
            supports.append(chosen); raw_scores.append({i:scores[i] for i in chosen})
        present = {i for sup in supports for i in sup}
        for ideol in [i for i in kept if i not in present]:
            mass = local_target[ideol]*sum(s.manpower for s in states)
            cand = [j for j,sup in enumerate(supports) if ideol not in sup and sup]
            if not cand: continue
            j=min(cand,key=lambda x:abs(math.log((states[x].manpower+1)/(mass+1))))
            repl=min(supports[j],key=lambda old:raw_scores[j].get(old,0.0))
            supports[j][supports[j].index(repl)] = ideol
            raw_scores[j].pop(repl,None); raw_scores[j][ideol]=max(local_target[ideol],1e-8)
        rows=[]
        for sup,scores in zip(supports,raw_scores):
            if not sup: rows.append({9:1.0}); continue
            vals={i:max(scores.get(i,1e-8),1e-8) for i in sup}; z=sum(vals.values()); vals={i:v/z for i,v in vals.items()}
            if len(vals)==2:
                order=sorted(vals,key=vals.get,reverse=True); majority=rng.uniform(.60,.80); vals={order[0]:majority,order[1]:1-majority}
            rows.append(vals)
        country_pop=sum(s.manpower for s in states); target_mass=[x*country_pop for x in local_target]
        for _ in range(160):
            actual=[0.0]*10
            for s,row in zip(states,rows):
                for i,sh in row.items(): actual[i]+=s.manpower*sh
            factors=[1.0]*10
            for i in range(10):
                if target_mass[i]>0 and actual[i]>0: factors[i]=target_mass[i]/actual[i]
            for row in rows:
                for i in list(row): row[i]*=factors[i]
                z=sum(row.values())
                if z>0:
                    for i in list(row): row[i]/=z
        actual=[0.0]*10
        for s,row in zip(states,rows):
            for i,sh in row.items(): actual[i]+=s.manpower*sh
        actual_share=[x/country_pop for x in actual]
        err=max(abs(actual_share[i]-local_target[i]) for i in range(10))
        penalty=sum(max(0.0,.05-min(row.values()))*.03 for row in rows if len(row)>=2)
        score=err+penalty+len(dropped)*.0005
        if score<best_score:
            best_score=score; best_rows=[dict(r) for r in rows]; best_dropped=dropped
            if err<.002 and not dropped: break
    assert best_rows is not None
    for s,row in zip(states,best_rows):
        row={i:sh for i,sh in row.items() if sh>1e-7}; z=sum(row.values()) or 1.0
        s.political_shares={i:sh/z for i,sh in row.items()}
    country.dropped_ideologies=best_dropped
    cp=sum(s.manpower for s in states); actual=[0.0]*10
    for s in states:
        for i,sh in s.political_shares.items(): actual[i]+=s.manpower*sh
    country.actual_shares=[x/cp for x in actual]
    country.allocation_error=max(abs(country.actual_shares[i]-target[i]) for i in range(10))


def make_demographic_shares(s: StateData, seed: int):
    rng=random.Random((seed*2654435761+s.sid*1000003)&((1<<63)-1))
    if s.species is not None:
        if s.minority is not None and s.minority != s.species:
            majority=rng.uniform(.60,.80); s.species_shares=[(s.species,majority),(s.minority,1-majority)]
        else: s.species_shares=[(s.species,1.0)]
    cultures=list(dict.fromkeys(s.cultures[:2]))
    if len(cultures)>=2:
        first=rng.uniform(.40,.60); s.culture_shares=[(cultures[0],first),(cultures[1],1-first)]
    elif len(cultures)==1: s.culture_shares=[(cultures[0],1.0)]


def fmt_num(x):
    if abs(x-round(x))<.0005: return str(int(round(x)))
    return f"{x:.3f}".rstrip('0').rstrip('.')


def fmt_share(x): return f"{x:.6f}".rstrip('0').rstrip('.')
def pct(x): return f"{x*100:.1f}%"


def normalized_entries(entries, size):
    vals={int(i):max(0.0,float(v)) for i,v in entries if 0<=int(i)<size and float(v)>1e-10}
    total=sum(vals.values())
    if total<=0: return []
    vals={i:v/total for i,v in vals.items()}
    rounded={i:round(v,6) for i,v in vals.items()}
    largest=max(rounded,key=rounded.get); rounded[largest]=round(rounded[largest]+(1.0-sum(rounded.values())),6)
    return sorted((i,v) for i,v in rounded.items() if v>0)


def render_share_array(lines, name, size, entries):
    vals=normalized_entries(entries,size)
    lines.append(f"clear_array = {name}")
    lines.append(f"resize_array = {{ array = {name} value = 0 size = {size} }}")
    for i,v in vals: lines.append(f"add_to_variable = {{ {name}^{i} = {fmt_share(v)} }}")


def render_generated_block(s: StateData, seed: int):
    lines=[START_MARKER,
           "# AUTO-GENERATED STARTING STATE DISTRIBUTIONS. EDITABLE AFTER GENERATION.",
           "# Array index = category ID; value = population share from 0 to 1.",
           f"# Generator seed {seed}; state {s.sid}; owner {s.owner}; category {s.category}; vanilla population {fmt_num(s.pop_k)}k."]
    if s.species_shares: lines.append("# Species: "+", ".join(f"{i} {pct(v)}" for i,v in s.species_shares)+".")
    if s.culture_shares: lines.append("# Culture: "+", ".join(f"{i} {pct(v)}" for i,v in s.culture_shares)+".")
    if s.political_shares: lines.append("# Politics: "+", ".join(f"{IDEOLOGY_NAMES[i]}[{i}] {pct(v)}" for i,v in sorted(s.political_shares.items(),key=lambda x:-x[1]))+".")
    for w in s.warnings: lines.append("# GENERATOR WARNING: "+w)
    render_share_array(lines,'lok_state_species_array',SPECIES_COUNT,s.species_shares)
    render_share_array(lines,'lok_state_culture_array',CULTURE_COUNT,s.culture_shares)
    render_share_array(lines,'lok_state_parties_array',POLITICS_COUNT,s.political_shares.items() if s.political_shares else [(9,1.0)])
    lines.append(END_MARKER)
    return '\n'.join(lines)


def inject_into_state_history(text, block):
    clean=remove_generated_block(text); span=find_named_block_span(clean,'history')
    if span is None: raise ValueError('state has no history = { ... } block')
    _,close_pos,_=span; line_start=clean.rfind('\n',0,close_pos)+1; close_indent=clean[line_start:close_pos]
    if close_indent.strip(): close_indent='\t'
    indent=close_indent+'\t'; rendered='\n'.join(indent+line if line else '' for line in block.splitlines())
    return clean[:line_start].rstrip()+"\n\n"+rendered+"\n"+clean[line_start:]


def write_preserving_bom(path: Path, source: Path, text: str):
    path.parent.mkdir(parents=True,exist_ok=True)
    had_bom=source.read_bytes().startswith(b'\xef\xbb\xbf')
    path.write_text(text,encoding='utf-8-sig' if had_bom else 'utf-8')


def write_reports(out, countries, states, warnings):
    reports=out/'_LOK_distribution_generation_reports'; reports.mkdir(parents=True,exist_ok=True)
    with (reports/'country_politics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); header=['tag','states','population','max_abs_error_pp','dropped_ideologies']
        for name in IDEOLOGY_NAMES: header += [f'target_{name}',f'actual_{name}']
        w.writerow(header)
        for tag in sorted(countries):
            c=countries[tag]
            if not c.states: continue
            row=[tag,len(c.states),int(sum(s.manpower for s in c.states)),c.allocation_error*100,';'.join(map(str,c.dropped_ideologies))]
            for i in range(10): row += [c.ideology_shares[i]*100,c.actual_shares[i]*100]
            w.writerow(row)
    with (reports/'states.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['state_id','file','owner','population_k','category','species_shares','culture_shares','politics','warnings'])
        for s in sorted(states,key=lambda x:x.sid):
            politics=';'.join(f'{i}:{sh:.6f}' for i,sh in sorted(s.political_shares.items()))
            species=';'.join(f'{i}:{sh:.6f}' for i,sh in s.species_shares); cultures=';'.join(f'{i}:{sh:.6f}' for i,sh in s.culture_shares)
            w.writerow([s.sid,s.filename,s.owner,s.pop_k,s.category,species,cultures,politics,' | '.join(s.warnings)])
    (reports/'warnings.txt').write_text('\n'.join(warnings)+('\n' if warnings else 'No global generator warnings.\n'),encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description='Generate static LoK state demographic/political distributions.')
    ap.add_argument('repo',nargs='?',default='.',help='Path to Legacy-of-Kattail mod root')
    ap.add_argument('--output','-o',help='Patch output directory. Default: <repo>/LOK_generated_state_distributions_patch')
    ap.add_argument('--seed',type=int,default=DEFAULT_SEED)
    ap.add_argument('--in-place',action='store_true')
    args=ap.parse_args(); repo=Path(args.repo).resolve(); states_dir=repo/'history/states'; countries_dir=repo/'history/countries'
    if not states_dir.is_dir() or not countries_dir.is_dir(): ap.error(f'{repo} does not look like the LoK mod root')
    out=repo if args.in_place else (Path(args.output).resolve() if args.output else repo/'LOK_generated_state_distributions_patch')
    if not args.in_place and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    print('Reading states...')
    states=[]
    for p in sorted(states_dir.glob('*.txt')):
        s=parse_state_file(p)
        if s is not None: states.append(s)
    states_by_id={s.sid:s for s in states}; print(f'  {len(states)} state files parsed.')
    nonplayable=discover_nonplayable(repo); owner_tags={s.owner for s in states if s.owner}; playable={t for t in owner_tags if t not in nonplayable}
    warnings=simulate_startup_demographics(repo,states_by_id); apply_owner_fallbacks(states,playable)
    country_files={}
    for p in countries_dir.glob('*.txt'):
        m=re.match(r'([A-Z0-9]{3})\s*-',p.name)
        if m: country_files[m.group(1)]=p
    countries={}
    for tag in sorted(playable):
        path=country_files.get(tag); shares,_=parse_country_history(path) if path else ([0.0]*9+[1.0],None)
        if not path: warnings.append(f'{tag}: no country history file found; used 100% Apolitical')
        countries[tag]=CountryData(tag,path,shares)
    eligible=[]
    for s in states:
        if not s.owner or s.owner not in playable: continue
        if s.species is None or not s.cultures: s.warnings.append('no resolvable starting species/culture; relevant array left all-zero')
        countries[s.owner].states.append(s); eligible.append(s)
    print(f'Allocating politics for {len(countries)} playable owners / {len(eligible)} states...')
    for tag,c in countries.items():
        allocate_country_politics(c,args.seed)
        if c.dropped_ideologies:
            omitted=', '.join(f'{IDEOLOGY_NAMES[i]}[{i}] {c.ideology_shares[i]*100:.2f}%' for i in c.dropped_ideologies)
            warnings.append(f'{tag}: ideology cap omitted {omitted}.')
    for s in eligible: make_demographic_shares(s,args.seed)
    eligible_ids={s.sid for s in eligible}
    print('Writing state-history share arrays and removing old pop-group generated blocks...')
    for s in states:
        dst=out/'history/states'/s.filename
        if s.sid in eligible_ids:
            try: text=inject_into_state_history(s.text,render_generated_block(s,args.seed))
            except Exception as exc: warnings.append(f'{s.filename}: could not inject generated block: {exc}'); continue
            write_preserving_bom(dst,s.path,text)
        elif s.had_generated_block:
            write_preserving_bom(dst,s.path,s.text)
    write_reports(out,countries,eligible,warnings)
    maxerr=max((c.allocation_error for c in countries.values() if c.states),default=0.0)
    print(f'Done: {len(eligible)} playable-state distributions.')
    print(f'Largest country ideological-share error: {maxerr*100:.2f} percentage points.')
    print('Output:',out)
    return 0

if __name__=='__main__': raise SystemExit(main())
