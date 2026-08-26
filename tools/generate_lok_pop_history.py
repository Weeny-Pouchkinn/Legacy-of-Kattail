#!/usr/bin/env python3
"""
Generate Legacy of Kattail population groups as STATIC state-history data.

This intentionally moves game-start population-group construction out of PDX runtime
script.  The Python generator reads the checked-out LoK repo, resolves the current
starting owner/species/minority/cultures and country party popularity, and writes
explicit five-array rows into every state owned by a playable country.

It is deterministic for a given --seed. Re-running replaces only the marked generated
block, so hand edits OUTSIDE the marked block are preserved. If you plan to hand-tune
the generated block itself, stop regenerating that state or move your tuned block out
of the generated markers.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

START_MARKER = "# >>> LOK GENERATED POP GROUPS START >>>"
END_MARKER = "# <<< LOK GENERATED POP GROUPS END <<<"
DEFAULT_SEED = 20260826

IDEOLOGY_KEYS = [
    "communism",
    "socialism",
    "social_democratic",
    "social_liberal",
    "democratic",
    "social_conservative",
    "authoritarian_democratic",
    "neutrality",
    "fascism",
]
IDEOLOGY_NAMES = [
    "Communist",
    "Socialist",
    "Social Democrat",
    "Social Liberal",
    "Market Liberal",
    "Social Conservative",
    "Authoritarian Democratic",
    "Autocratic",
    "National Mysticist",
    "Apolitical",
]
URBAN_IDEOLOGIES = {2, 3, 4}
DEFAULT_NONPLAYABLE = {"MUN", "XEN", "MRI", "AAA", "ZZZ", "WWW"}


# -----------------------------------------------------------------------------
# Tiny PDX parser. We only need ordinary key = value / key = { ... } structure,
# while preserving duplicate keys and order.
# -----------------------------------------------------------------------------

@dataclass
class Entry:
    key: str | None
    value: Any


def strip_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        c = text[i]
        if in_string:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == '#':
            while i < len(text) and text[i] != '\n':
                i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def tokenize(text: str) -> list[str]:
    text = strip_comments(text)
    return re.findall(r'"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=]+', text)


def parse_pdx(text: str) -> list[Entry]:
    toks = tokenize(text)
    pos = 0

    def parse_block(stop_at_brace: bool) -> list[Entry]:
        nonlocal pos
        result: list[Entry] = []
        while pos < len(toks):
            if toks[pos] == '}':
                if stop_at_brace:
                    pos += 1
                    return result
                pos += 1
                continue
            if toks[pos] == '{':
                pos += 1
                result.append(Entry(None, parse_block(True)))
                continue
            key = toks[pos]
            pos += 1
            if pos < len(toks) and toks[pos] == '=':
                pos += 1
                if pos < len(toks) and toks[pos] == '{':
                    pos += 1
                    value: Any = parse_block(True)
                elif pos < len(toks):
                    value = toks[pos]
                    pos += 1
                else:
                    value = ""
                result.append(Entry(key, value))
            else:
                result.append(Entry(None, key))
        return result

    return parse_block(False)


def unquote(v: Any) -> str:
    s = str(v)
    if len(s) >= 2 and s[0] == s[-1] == '"':
        return s[1:-1]
    return s


def as_float(v: Any, default: float | None = None) -> float | None:
    try:
        return float(unquote(v))
    except (TypeError, ValueError):
        return default


def as_int(v: Any, default: int | None = None) -> int | None:
    f = as_float(v, None)
    return int(f) if f is not None else default


def direct(entries: Iterable[Entry], key: str) -> list[Entry]:
    return [e for e in entries if e.key == key]


def first_block(entries: Iterable[Entry], key: str) -> list[Entry] | None:
    for e in entries:
        if e.key == key and isinstance(e.value, list):
            return e.value
    return None


def last_scalar(entries: Iterable[Entry], key: str, default: Any = None) -> Any:
    val = default
    for e in entries:
        if e.key == key and not isinstance(e.value, list):
            val = e.value
    return val


def recursively_find_blocks(entries: Iterable[Entry], key: str) -> Iterable[list[Entry]]:
    for e in entries:
        if e.key == key and isinstance(e.value, list):
            yield e.value
        if isinstance(e.value, list):
            yield from recursively_find_blocks(e.value, key)


# -----------------------------------------------------------------------------
# Repo data
# -----------------------------------------------------------------------------

@dataclass
class StateData:
    sid: int
    filename: str
    path: Path
    text: str
    owner: str | None
    manpower: float
    category: str
    species: int | None = None
    minority: int | None = None
    cultures: list[int] = field(default_factory=list)
    groups: list[tuple[int, int, int, float, int]] = field(default_factory=list)
    political_shares: dict[int, float] = field(default_factory=dict)
    species_shares: list[tuple[int, float]] = field(default_factory=list)
    culture_shares: list[tuple[int, float]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def pop_k(self) -> float:
        return self.manpower / 1000.0


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
    pattern = re.compile(
        r'\n?[ \t]*' + re.escape(START_MARKER) + r'.*?' + re.escape(END_MARKER) + r'[ \t]*\n?',
        re.S,
    )
    return pattern.sub('\n', text)


def find_named_block_span(text: str, name: str) -> tuple[int, int, int] | None:
    """Return (open_brace, close_brace, match_start) for first `name = {` block."""
    # Work on original text; scan comments/strings so braces in comments do not matter.
    m = re.search(r'\b' + re.escape(name) + r'\s*=\s*\{', text)
    if not m:
        return None
    open_pos = text.find('{', m.start(), m.end())
    depth = 0
    in_string = False
    escaped = False
    in_comment = False
    i = open_pos
    while i < len(text):
        c = text[i]
        if in_comment:
            if c == '\n':
                in_comment = False
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if c == '#':
            in_comment = True
        elif c == '"':
            in_string = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return open_pos, i, m.start()
        i += 1
    return None


def parse_state_file(path: Path) -> StateData | None:
    raw = path.read_text(encoding='utf-8-sig', errors='replace')
    text = remove_generated_block(raw)
    try:
        root = parse_pdx(text)
    except Exception as exc:
        print(f"WARNING: failed to parse state file {path}: {exc}", file=sys.stderr)
        return None
    state = first_block(root, 'state')
    if state is None:
        return None
    sid = as_int(last_scalar(state, 'id'), None)
    if sid is None:
        return None
    manpower = as_float(last_scalar(state, 'manpower'), 0.0) or 0.0
    category = unquote(last_scalar(state, 'state_category', 'unknown'))
    history = first_block(state, 'history') or []
    owner_raw = last_scalar(history, 'owner', None)
    owner = unquote(owner_raw) if owner_raw is not None else None
    data = StateData(
        sid=sid,
        filename=path.name,
        path=path,
        text=text,
        owner=owner,
        manpower=manpower,
        category=category,
    )
    # If demographic data has already started moving into state history, use it
    # before applying the still-current startup on_action assignments.
    apply_state_ops(history, data)
    return data


def parse_country_history(path: Path) -> tuple[list[float], str | None]:
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    root = parse_pdx(text)
    popularity_blocks = direct(root, 'set_popularities')
    shares = [0.0] * 10
    if popularity_blocks:
        block = popularity_blocks[-1].value
        if isinstance(block, list):
            for i, key in enumerate(IDEOLOGY_KEYS):
                v = as_float(last_scalar(block, key, 0), 0.0) or 0.0
                shares[i] = max(0.0, v)
    total = sum(shares[:9])
    ruling: str | None = None
    politics_blocks = direct(root, 'set_politics')
    if politics_blocks and isinstance(politics_blocks[-1].value, list):
        r = last_scalar(politics_blocks[-1].value, 'ruling_party', None)
        if r is not None:
            ruling = unquote(r)
    if total <= 0:
        if ruling in IDEOLOGY_KEYS:
            shares[IDEOLOGY_KEYS.index(ruling)] = 1.0
        else:
            shares[9] = 1.0
    else:
        shares = [x / total for x in shares]
    return shares, ruling


def discover_nonplayable(repo: Path) -> set[str]:
    tags = set(DEFAULT_NONPLAYABLE)
    for p in sorted((repo / 'common' / 'scripted_triggers').glob('*.txt')):
        try:
            root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception:
            continue
        for block in recursively_find_blocks(root, 'is_non_playable_country'):
            for tag_block in recursively_find_blocks([Entry('__root__', block)], 'OR'):
                for e in tag_block:
                    if e.key == 'tag' and not isinstance(e.value, list):
                        tag = unquote(e.value)
                        if re.fullmatch(r'[A-Z0-9]{3}', tag):
                            tags.add(tag)
            # Also accept direct tag entries in case the trigger is simplified later.
            def rec(entries: list[Entry]):
                for e in entries:
                    if e.key == 'tag' and not isinstance(e.value, list):
                        tag = unquote(e.value)
                        if re.fullmatch(r'[A-Z0-9]{3}', tag):
                            tags.add(tag)
                    if isinstance(e.value, list):
                        rec(e.value)
            rec(block)
    return tags


# -----------------------------------------------------------------------------
# Resolve LoK's current species/culture startup data.
# -----------------------------------------------------------------------------

def apply_state_ops(entries: list[Entry], state: StateData) -> None:
    for e in entries:
        if e.key == 'set_variable' and isinstance(e.value, list):
            for a in e.value:
                if a.key == 'species' and not isinstance(a.value, list):
                    state.species = as_int(a.value, state.species)
                elif a.key == 'minority' and not isinstance(a.value, list):
                    state.minority = as_int(a.value, state.minority)
        elif e.key == 'clear_array' and not isinstance(e.value, list):
            if unquote(e.value) == 'state_cultures':
                state.cultures.clear()
        elif e.key == 'add_to_array' and isinstance(e.value, list):
            arr = unquote(last_scalar(e.value, 'array', ''))
            if arr == 'state_cultures':
                v = as_int(last_scalar(e.value, 'value', None), None)
                if v is not None and v not in state.cultures:
                    state.cultures.append(v)


def load_scripted_trigger_registry(repo: Path) -> dict[str, list[Entry]]:
    """Load root-level scripted-trigger definitions.

    The history generator only evaluates a deliberately tiny, static subset of
    trigger logic.  This exists mainly for startup demographic assignments such as
    `every_country = { limit = { is_herzlands_warlord = yes } ... }`.
    """
    registry: dict[str, list[Entry]] = {}
    trigger_dir = repo / 'common' / 'scripted_triggers'
    for p in sorted(trigger_dir.glob('*.txt')):
        try:
            root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception:
            continue
        for e in root:
            if e.key and isinstance(e.value, list):
                registry[unquote(e.key)] = e.value
    return registry


def resolve_static_country_selector(
    entries: list[Entry],
    registry: dict[str, list[Entry]],
    stack: tuple[str, ...] = (),
) -> set[str] | None:
    """Resolve simple country selectors to an exact set of tags.

    Supported forms are direct `tag = TAG`, OR blocks, and references to other
    scripted triggers that themselves consist only of those constructs. Multiple
    top-level selectors are treated as AND/intersection. Anything dynamic returns
    None rather than guessing.
    """

    def one(e: Entry) -> set[str] | None:
        if e.key is None:
            return None
        key = unquote(e.key)

        if key == 'tag' and not isinstance(e.value, list):
            tag = unquote(e.value)
            return {tag} if re.fullmatch(r'[A-Z0-9]{3}', tag) else None

        if key == 'OR' and isinstance(e.value, list):
            result: set[str] = set()
            for child in e.value:
                part = one(child)
                if part is None:
                    return None
                result.update(part)
            return result

        # Positive reference to another scripted trigger, e.g.
        # is_herzlands_warlord = yes.
        if not isinstance(e.value, list) and unquote(e.value).lower() == 'yes' and key in registry:
            if key in stack:
                return None
            return resolve_static_country_selector(registry[key], registry, stack + (key,))

        return None

    selectors: list[set[str]] = []
    for e in entries:
        part = one(e)
        if part is None:
            return None
        selectors.append(part)

    if not selectors:
        return None
    result = set(selectors[0])
    for part in selectors[1:]:
        result.intersection_update(part)
    return result


def simulate_startup_demographics(repo: Path, states_by_id: dict[int, StateData]) -> list[str]:
    warnings: list[str] = []
    by_owner: dict[str, list[StateData]] = defaultdict(list)
    for s in states_by_id.values():
        if s.owner:
            by_owner[s.owner].append(s)

    scripted_triggers = load_scripted_trigger_registry(repo)

    def eval_static_state_demographic_limit(entries: list[Entry], state: StateData) -> bool | None:
        """Evaluate the small subset of state limits used by startup demographics.

        This intentionally is NOT a general PDX trigger interpreter.  It only handles
        boolean combinations of exact species/minority variable checks.  That covers
        current LoK setup such as FOD's:

            limit = { NOT = { check_variable = { species = 1 } } }

        Returning None means "unsupported; do not guess".
        """

        def one(e: Entry) -> bool | None:
            if e.key is None:
                return None
            key = unquote(e.key)

            if key == 'check_variable' and isinstance(e.value, list):
                # Supported compact equality form:
                # check_variable = { species = 1 }
                checks = [x for x in e.value if x.key in ('species', 'minority') and not isinstance(x.value, list)]
                if len(checks) != 1 or len(e.value) != 1:
                    return None
                chk = checks[0]
                wanted = as_int(chk.value, None)
                if wanted is None:
                    return None
                actual = state.species if chk.key == 'species' else state.minority
                return actual == wanted

            if key == 'NOT' and isinstance(e.value, list):
                result = eval_static_state_demographic_limit(e.value, state)
                return None if result is None else not result

            if key == 'AND' and isinstance(e.value, list):
                return eval_static_state_demographic_limit(e.value, state)

            if key == 'OR' and isinstance(e.value, list):
                vals = [one(child) for child in e.value]
                if any(v is None for v in vals):
                    return None
                return any(vals)

            return None

        # Top-level entries in a limit block are ANDed.
        values = [one(e) for e in entries]
        if any(v is None for v in values):
            return None
        return all(values)

    def apply_country_ops(tag: str, entries: list[Entry], source: str) -> None:
        for e in entries:
            if e.key == 'every_owned_state' and isinstance(e.value, list):
                limits = direct(e.value, 'limit')
                if not limits:
                    for s in by_owner.get(tag, []):
                        apply_state_ops(e.value, s)
                    continue

                if len(limits) == 1 and isinstance(limits[0].value, list):
                    unsupported = False
                    for s in by_owner.get(tag, []):
                        matches = eval_static_state_demographic_limit(limits[0].value, s)
                        if matches is None:
                            unsupported = True
                            break
                        if matches:
                            apply_state_ops(e.value, s)
                    if not unsupported:
                        continue

                target_text = repr(e.value)
                if any(x in target_text for x in ('species', 'minority', 'state_cultures')):
                    warnings.append(f"Unsupported conditional demographic every_owned_state in {source}, tag {tag}")

    def apply_global(entries: list[Entry], source: str) -> None:
        for e in entries:
            if not isinstance(e.value, list) or e.key is None:
                continue
            key = unquote(e.key)
            if key.isdigit():
                sid = int(key)
                if sid in states_by_id:
                    apply_state_ops(e.value, states_by_id[sid])
            elif re.fullmatch(r'[A-Z0-9]{3}', key):
                apply_country_ops(key, e.value, source)
            elif key == 'every_country':
                # Some demographic setup is intentionally grouped behind static
                # scripted tag selectors.  The important current example is:
                #
                # every_country = {
                #     limit = { is_herzlands_warlord = yes }
                #     every_owned_state = { set_variable = { species = 1 } }
                # }
                #
                # The old generator ignored every_country entirely, which is why
                # Herzlands warlord states were emitted with no pop groups.
                limits = direct(e.value, 'limit')
                if len(limits) == 1 and isinstance(limits[0].value, list):
                    tags = resolve_static_country_selector(limits[0].value, scripted_triggers)
                    if tags is not None:
                        for tag in sorted(tags):
                            apply_country_ops(tag, e.value, source)
                    else:
                        body_text = repr(e.value)
                        if any(x in body_text for x in ('species', 'minority', 'state_cultures')):
                            warnings.append(
                                f"Unsupported every_country demographic selector in {source}: "
                                f"{repr(limits[0].value)[:240]}"
                            )
                continue
            # Other arbitrary if/every_state/etc. remain intentionally ignored.
            # We only evaluate selectors that can be reduced exactly to static tags.

    on_actions_dir = repo / 'common' / 'on_actions'
    for p in sorted(on_actions_dir.glob('*.txt')):
        try:
            root = parse_pdx(p.read_text(encoding='utf-8-sig', errors='replace'))
        except Exception as exc:
            warnings.append(f"Could not parse {p}: {exc}")
            continue
        top = first_block(root, 'on_actions')
        if top is None:
            continue
        for startup_e in direct(top, 'on_startup'):
            if not isinstance(startup_e.value, list):
                continue
            for effect_e in direct(startup_e.value, 'effect'):
                if isinstance(effect_e.value, list):
                    apply_global(effect_e.value, p.name)
    return warnings


def apply_owner_fallbacks(states: list[StateData], playable_tags: set[str]) -> None:
    species_counts: dict[str, Counter[int]] = defaultdict(Counter)
    culture_counts: dict[str, Counter[int]] = defaultdict(Counter)
    for s in states:
        if not s.owner or s.owner not in playable_tags:
            continue
        weight = max(1, int(round(s.manpower)))
        if s.species is not None and s.species != 1000:
            species_counts[s.owner][s.species] += weight
        for c in s.cultures[:2]:
            culture_counts[s.owner][c] += weight

    for s in states:
        if not s.owner or s.owner not in playable_tags:
            continue
        if s.species is None or s.species == 1000:
            if species_counts[s.owner]:
                s.species = species_counts[s.owner].most_common(1)[0][0]
                s.warnings.append(f"species missing; inherited owner modal species {s.species}")
        if not s.cultures:
            if culture_counts[s.owner]:
                c = culture_counts[s.owner].most_common(1)[0][0]
                s.cultures = [c]
                s.warnings.append(f"culture missing; inherited owner modal culture {c}")
        if len(s.cultures) > 2:
            old = list(s.cultures)
            s.cultures = s.cultures[:2]
            s.warnings.append(f"more than two startup cultures {old}; generator kept first two {s.cultures}")
        if s.minority == 1000 or s.minority == s.species:
            s.minority = None


# -----------------------------------------------------------------------------
# Fuzzy state politics while preserving country totals as closely as possible.
# -----------------------------------------------------------------------------

def is_large_urban(s: StateData) -> bool:
    cat = s.category.lower()
    category_urban = any(x in cat for x in ('city', 'metropolis', 'megalopolis', 'urban'))
    return category_urban or s.manpower >= 2_000_000


def weighted_choice_without_replacement(rng: random.Random, weights: dict[int, float], k: int) -> list[int]:
    pool = dict(weights)
    out: list[int] = []
    for _ in range(min(k, len(pool))):
        total = sum(max(0.0, w) for w in pool.values())
        if total <= 0:
            pick = rng.choice(list(pool))
        else:
            r = rng.random() * total
            acc = 0.0
            pick = next(iter(pool))
            for idx, w in pool.items():
                acc += max(0.0, w)
                if r <= acc:
                    pick = idx
                    break
        out.append(pick)
        pool.pop(pick, None)
    return out


def allocate_country_politics(country: CountryData, seed: int) -> None:
    states = [s for s in country.states if s.manpower > 0]
    if not states:
        return
    target = list(country.ideology_shares)
    total_target = sum(target)
    if total_target <= 0:
        target = [0.0] * 9 + [1.0]
    else:
        target = [x / total_target for x in target]

    # Tiny values are still candidates, but a country with too few state slots
    # physically cannot represent nine ideologies at 1-3 ideologies per state.
    active = [i for i, x in enumerate(target) if x > 1e-9]
    base_rng = random.Random((seed * 1000003) ^ sum(ord(c) << (i % 8) for i, c in enumerate(country.tag)))

    best_rows: list[dict[int, float]] | None = None
    best_err = float('inf')
    best_dropped: list[int] = []

    attempts = 180
    for attempt in range(attempts):
        rng = random.Random(base_rng.randrange(1 << 62) ^ attempt)

        ks: list[int] = []
        for s in states:
            n = len(active)
            if n <= 1:
                k = 1
            elif is_large_urban(s):
                # Large urban states usually get 2-3 political tendencies.
                k = 3 if n >= 3 and rng.random() < 0.60 else 2
            else:
                roll = rng.random()
                if roll < 0.14:
                    k = 1
                elif roll < 0.90:
                    k = 2
                else:
                    k = 3
                k = min(k, n)
            ks.append(k)

        # If possible, create enough total slots to cover more national tendencies.
        while sum(ks) < min(len(active), 3 * len(states)):
            candidates = [i for i, k in enumerate(ks) if k < min(3, len(active))]
            if not candidates:
                break
            ks[rng.choice(candidates)] += 1

        representable = min(sum(ks), len(active))
        # If not all can fit, preserve the largest national tendencies.
        kept_active = sorted(active, key=lambda i: target[i], reverse=True)[:representable]
        dropped = [i for i in active if i not in kept_active]
        local_target = list(target)
        for i in dropped:
            local_target[i] = 0.0
        norm = sum(local_target)
        if norm <= 0:
            local_target[9] = 1.0
            norm = 1.0
        local_target = [x / norm for x in local_target]

        supports: list[list[int]] = []
        raw_scores: list[dict[int, float]] = []
        for s, k in zip(states, ks):
            scores: dict[int, float] = {}
            for i in kept_active:
                # Lognormal-ish fuzz around national prevalence.
                noise = math.exp(rng.gauss(0.0, 0.62))
                score = max(local_target[i], 1e-8) ** 0.72 * noise
                if is_large_urban(s) and i in URBAN_IDEOLOGIES:
                    score *= 1.85
                scores[i] = score
            chosen = weighted_choice_without_replacement(rng, scores, k)

            # Explicit urban bias: where the country actually has liberal/centre-left
            # support, make a large urban state likely to include at least one of it.
            urban_candidates = [i for i in kept_active if i in URBAN_IDEOLOGIES]
            if is_large_urban(s) and urban_candidates and not any(i in URBAN_IDEOLOGIES for i in chosen):
                urb = max(urban_candidates, key=lambda i: scores.get(i, 0.0))
                if chosen:
                    chosen[-1] = urb
                else:
                    chosen = [urb]
                chosen = list(dict.fromkeys(chosen))
                while len(chosen) < k:
                    for cand in sorted(scores, key=scores.get, reverse=True):
                        if cand not in chosen:
                            chosen.append(cand)
                            break
            supports.append(chosen)
            raw_scores.append({i: scores[i] for i in chosen})

        # Force every kept ideology to appear in at least one support.
        present = {i for sup in supports for i in sup}
        missing = [i for i in kept_active if i not in present]
        for ideol in missing:
            target_mass = local_target[ideol] * sum(s.manpower for s in states)
            candidate_indices = [j for j, sup in enumerate(supports) if ideol not in sup and sup]
            if not candidate_indices:
                continue
            # Rare tendencies fit best into smaller states; large tendencies into a
            # state whose size is near their total target mass.
            j = min(candidate_indices, key=lambda x: abs(math.log((states[x].manpower + 1) / (target_mass + 1))))
            replace = min(supports[j], key=lambda old: raw_scores[j].get(old, 0.0))
            supports[j][supports[j].index(replace)] = ideol
            raw_scores[j].pop(replace, None)
            raw_scores[j][ideol] = max(local_target[ideol], 1e-8)

        rows: list[dict[int, float]] = []
        for s, sup, scores in zip(states, supports, raw_scores):
            if not sup:
                rows.append({9: 1.0})
                continue
            vals = {i: max(scores.get(i, 1e-8), 1e-8) for i in sup}
            z = sum(vals.values())
            vals = {i: v / z for i, v in vals.items()}

            # Give two-way states visibly fuzzy splits before global correction.
            if len(vals) == 2:
                order = sorted(vals, key=vals.get, reverse=True)
                majority = rng.uniform(0.60, 0.80)
                vals = {order[0]: majority, order[1]: 1.0 - majority}
            rows.append(vals)

        country_pop = sum(s.manpower for s in states)
        target_mass = [x * country_pop for x in local_target]

        # Iterative proportional fitting restricted to each state's 1-3 chosen
        # ideologies. This keeps row totals fixed while steering country totals back
        # toward the current set_popularities distribution.
        for _ in range(160):
            actual = [0.0] * 10
            for s, row in zip(states, rows):
                for i, sh in row.items():
                    actual[i] += s.manpower * sh
            factors = [1.0] * 10
            for i in range(10):
                if target_mass[i] > 0 and actual[i] > 0:
                    factors[i] = target_mass[i] / actual[i]
            for row in rows:
                for i in list(row):
                    row[i] *= factors[i]
                z = sum(row.values())
                if z > 0:
                    for i in list(row):
                        row[i] /= z

        actual = [0.0] * 10
        for s, row in zip(states, rows):
            for i, sh in row.items():
                actual[i] += s.manpower * sh
        actual_share = [x / country_pop for x in actual]
        err = max(abs(actual_share[i] - local_target[i]) for i in range(10))

        # Softly prefer visually meaningful state splits instead of 99.9/0.1 rows.
        extreme_penalty = 0.0
        for row in rows:
            if len(row) >= 2:
                mn = min(row.values())
                if mn < 0.05:
                    extreme_penalty += (0.05 - mn) * 0.03
        score = err + extreme_penalty + len(dropped) * 0.0005

        if score < best_err:
            best_err = score
            best_rows = [dict(r) for r in rows]
            best_dropped = dropped
            if err < 0.002 and not dropped:
                break

    assert best_rows is not None

    for s, row in zip(states, best_rows):
        # Clean numerical dust and normalize.
        row = {i: sh for i, sh in row.items() if sh > 1e-7}
        z = sum(row.values()) or 1.0
        s.political_shares = {i: sh / z for i, sh in row.items()}

    country.dropped_ideologies = best_dropped
    country_pop = sum(s.manpower for s in states)
    actual = [0.0] * 10
    for s in states:
        for i, sh in s.political_shares.items():
            actual[i] += s.manpower * sh
    country.actual_shares = [x / country_pop for x in actual]
    country.allocation_error = max(abs(country.actual_shares[i] - target[i]) for i in range(10))


# -----------------------------------------------------------------------------
# Build explicit pop rows.
# -----------------------------------------------------------------------------

def make_demographic_shares(s: StateData, rng: random.Random) -> None:
    if s.species is None:
        return
    if s.minority is not None and s.minority != s.species:
        majority = rng.uniform(0.60, 0.80)
        s.species_shares = [(s.species, majority), (s.minority, 1.0 - majority)]
    else:
        s.species_shares = [(s.species, 1.0)]

    cultures = list(dict.fromkeys(s.cultures[:2]))
    if len(cultures) >= 2:
        first = rng.uniform(0.40, 0.60)
        s.culture_shares = [(cultures[0], first), (cultures[1], 1.0 - first)]
    elif len(cultures) == 1:
        s.culture_shares = [(cultures[0], 1.0)]


def build_groups(s: StateData, seed: int) -> None:
    rng = random.Random((seed * 2654435761 + s.sid * 1000003) & ((1 << 63) - 1))
    make_demographic_shares(s, rng)
    if not s.species_shares or not s.culture_shares or s.pop_k <= 0:
        s.groups = []
        return
    politics = sorted(s.political_shares.items()) if s.political_shares else [(9, 1.0)]

    weighted: list[tuple[int, int, int, float]] = []
    for sp, sp_w in s.species_shares:
        for cu, cu_w in s.culture_shares:
            for po, po_w in politics:
                w = sp_w * cu_w * po_w
                if w > 1e-10:
                    weighted.append((sp, cu, po, w))

    # Round to one person (0.001k), and give rounding remainder to largest row so
    # the generated arrays sum exactly to the state's vanilla manpower.
    total_k = round(s.pop_k, 3)
    groups: list[list[Any]] = []
    for sp, cu, po, w in weighted:
        amount = round(total_k * w, 3)
        if amount > 0:
            groups.append([sp, cu, po, amount, 0])
    if not groups and weighted:
        sp, cu, po, _ = max(weighted, key=lambda x: x[3])
        groups = [[sp, cu, po, total_k, 0]]
    else:
        diff = round(total_k - sum(g[3] for g in groups), 3)
        if groups and abs(diff) >= 0.0005:
            idx = max(range(len(groups)), key=lambda i: groups[i][3])
            groups[idx][3] = round(groups[idx][3] + diff, 3)

    # Remove numerical zeros and merge any accidental duplicates.
    merged: dict[tuple[int, int, int, int], float] = defaultdict(float)
    for sp, cu, po, amount, reserved in groups:
        if amount > 0:
            merged[(sp, cu, po, reserved)] += amount
    s.groups = [(sp, cu, po, round(am, 3), res) for (sp, cu, po, res), am in merged.items() if am > 0]


def fmt_num(x: float) -> str:
    if abs(x - round(x)) < 0.0005:
        return str(int(round(x)))
    return f"{x:.3f}".rstrip('0').rstrip('.')


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def render_generated_block(s: StateData, seed: int) -> str:
    lines: list[str] = []
    lines.append(START_MARKER)
    lines.append("# AUTO-GENERATED STARTING POPULATION HISTORY. EDITABLE AFTER GENERATION.")
    lines.append("# One population group = the same index across the five arrays below.")
    lines.append("# Fields: species / culture / politics / amount in thousands / reserved(0).")
    lines.append("# This is static history data. Runtime startup code only SUMS these rows into caches.")
    lines.append(f"# Generator seed {seed}; state {s.sid}; owner {s.owner}; category {s.category}; vanilla population {fmt_num(s.pop_k)}k.")
    if s.species_shares:
        lines.append("# Species split: " + ", ".join(f"{sp} {pct(sh)}" for sp, sh in s.species_shares) + ".")
    if s.culture_shares:
        lines.append("# Culture split: " + ", ".join(f"{cu} {pct(sh)}" for cu, sh in s.culture_shares) + ".")
    if s.political_shares:
        lines.append("# Politics: " + ", ".join(f"{IDEOLOGY_NAMES[i]}[{i}] {pct(sh)}" for i, sh in sorted(s.political_shares.items(), key=lambda x: -x[1])) + ".")
    for warning in s.warnings:
        lines.append("# GENERATOR WARNING: " + warning)

    lines += [
        "clear_array = lok_pop_species_array",
        "clear_array = lok_pop_culture_array",
        "clear_array = lok_pop_politics_array",
        "clear_array = lok_pop_amount_array",
        "clear_array = lok_pop_reserved_array",
    ]

    if not s.groups:
        lines.append("# No positive-population groups generated for this state.")
    for idx, (sp, cu, po, amount, reserved) in enumerate(s.groups):
        pname = IDEOLOGY_NAMES[po] if 0 <= po < len(IDEOLOGY_NAMES) else str(po)
        lines.append(f"# group {idx}: species={sp} culture={cu} politics={po} ({pname}) amount={fmt_num(amount)}k reserved={reserved}")
        lines.append(f"add_to_array = {{ array = lok_pop_species_array value = {sp} }}")
        lines.append(f"add_to_array = {{ array = lok_pop_culture_array value = {cu} }}")
        lines.append(f"add_to_array = {{ array = lok_pop_politics_array value = {po} }}")
        lines.append(f"add_to_array = {{ array = lok_pop_amount_array value = {fmt_num(amount)} }}")
        lines.append(f"add_to_array = {{ array = lok_pop_reserved_array value = {reserved} }}")
    lines.append(END_MARKER)
    return '\n'.join(lines)


def inject_into_state_history(text: str, block: str) -> str:
    clean = remove_generated_block(text)
    span = find_named_block_span(clean, 'history')
    if span is None:
        raise ValueError("state has no history = { ... } block")
    _, close_pos, _ = span

    # Derive indentation from the actual history closing brace instead of
    # hardcoding it. The generated rows belong one level *inside* history, so
    # if the history closing brace is indented one tab, the pop block is two.
    # This also preserves the original indentation of the closing brace itself.
    line_start = clean.rfind('\n', 0, close_pos) + 1
    close_indent = clean[line_start:close_pos]
    if close_indent.strip():
        # Defensive fallback for unusually formatted one-line history blocks.
        close_indent = "\t"
    indent = close_indent + "\t"

    rendered = '\n'.join(indent + line if line else '' for line in block.splitlines())
    prefix = clean[:line_start].rstrip()
    suffix = clean[line_start:]
    return prefix + "\n\n" + rendered + "\n" + suffix


# -----------------------------------------------------------------------------
# Output / reports
# -----------------------------------------------------------------------------

def copy_support_files(package_root: Path, out_root: Path) -> None:
    for rel in [
        'common/scripted_effects/LOK_pop_group_effects.txt',
        'common/on_actions/LOK_pop_groups_on_actions.txt',
        'common/on_actions/LOK_DEBUG_state_political_pie_chart.txt',
        'common/scripted_guis/LOK_pop_groups_gui.txt',
        'common/scripted_localisation/LOK_pop_groups_scripted_localisation.txt',
        'events/LOK_pop_groups_events.txt',
        'interface/LOK_pop_groups.gui',
        'localisation/english/LOK_pop_groups_l_english.yml',
    ]:
        src = package_root / rel
        if src.exists():
            dst = out_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)

            # In --in-place mode package_root and out_root are the same mod root.
            # Do not attempt to copy a support file onto itself: Windows raises
            # PermissionError/WinError 32 (and shutil may raise SameFileError).
            try:
                same_file = src.resolve() == dst.resolve()
            except OSError:
                same_file = False

            if same_file:
                continue

            shutil.copy2(src, dst)


def write_reports(out: Path, countries: dict[str, CountryData], states: list[StateData], global_warnings: list[str]) -> None:
    reports = out / '_LOK_pop_generation_reports'
    reports.mkdir(parents=True, exist_ok=True)

    with (reports / 'country_politics.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        header = ['tag', 'states', 'population', 'max_abs_error_pp', 'dropped_ideologies']
        for name in IDEOLOGY_NAMES:
            header += [f'target_{name}', f'actual_{name}']
        w.writerow(header)
        for tag in sorted(countries):
            c = countries[tag]
            if not c.states:
                continue
            row = [tag, len(c.states), int(sum(s.manpower for s in c.states)), c.allocation_error * 100,
                   ';'.join(str(x) for x in c.dropped_ideologies)]
            for i in range(10):
                row += [c.ideology_shares[i] * 100, c.actual_shares[i] * 100]
            w.writerow(row)

    with (reports / 'states.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['state_id', 'file', 'owner', 'population_k', 'category', 'species', 'minority',
                    'cultures', 'politics', 'groups', 'warnings'])
        for s in sorted(states, key=lambda x: x.sid):
            if not s.owner:
                continue
            politics = ';'.join(f'{i}:{sh:.6f}' for i, sh in sorted(s.political_shares.items()))
            w.writerow([s.sid, s.filename, s.owner, s.pop_k, s.category, s.species, s.minority,
                        ';'.join(map(str, s.cultures)), politics, len(s.groups), ' | '.join(s.warnings)])

    (reports / 'warnings.txt').write_text(
        ('\n'.join(global_warnings) + ('\n' if global_warnings else 'No global generator warnings.\n')),
        encoding='utf-8',
    )


def main() -> int:
    ap = argparse.ArgumentParser(description='Generate static LoK pop groups in state history files.')
    ap.add_argument('repo', nargs='?', default='.', help='Path to Legacy-of-Kattail mod root (default: current directory)')
    ap.add_argument('--output', '-o', help='Patch output directory. Default: <repo>/LOK_generated_pop_history_patch')
    ap.add_argument('--seed', type=int, default=DEFAULT_SEED, help=f'Deterministic fuzz seed (default {DEFAULT_SEED})')
    ap.add_argument('--in-place', action='store_true', help='Write directly into repo instead of a patch folder')
    ap.add_argument('--no-support-files', action='store_true', help='Generate only history/states files, not toolkit/GUI files')
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    states_dir = repo / 'history' / 'states'
    countries_dir = repo / 'history' / 'countries'
    if not states_dir.is_dir() or not countries_dir.is_dir():
        ap.error(f'{repo} does not look like the LoK mod root (history/states or history/countries missing)')

    if args.in_place:
        out = repo
    else:
        out = Path(args.output).resolve() if args.output else repo / 'LOK_generated_pop_history_patch'
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)

    print('Reading states...')
    states: list[StateData] = []
    for p in sorted(states_dir.glob('*.txt')):
        s = parse_state_file(p)
        if s is not None:
            states.append(s)
    states_by_id = {s.sid: s for s in states}
    print(f'  {len(states)} state files parsed.')

    nonplayable = discover_nonplayable(repo)
    owner_tags = {s.owner for s in states if s.owner}
    playable_tags = {t for t in owner_tags if t not in nonplayable}
    print('Non-playable tags:', ', '.join(sorted(nonplayable)))

    print('Resolving current species/minority/culture startup assignments...')
    global_warnings = simulate_startup_demographics(repo, states_by_id)
    apply_owner_fallbacks(states, playable_tags)

    country_files: dict[str, Path] = {}
    for p in countries_dir.glob('*.txt'):
        m = re.match(r'([A-Z0-9]{3})\s*-', p.name)
        if m:
            country_files[m.group(1)] = p

    countries: dict[str, CountryData] = {}
    for tag in sorted(playable_tags):
        path = country_files.get(tag)
        if path:
            shares, _ = parse_country_history(path)
        else:
            shares = [0.0] * 9 + [1.0]
            global_warnings.append(f'{tag}: no country history file found; used 100% Apolitical')
        countries[tag] = CountryData(tag=tag, path=path, ideology_shares=shares)

    eligible_states: list[StateData] = []
    for s in states:
        if not s.owner or s.owner not in playable_tags:
            continue
        # Every state owned by a playable country is emitted, including zero-pop
        # states. Missing demographics use owner-mode fallbacks where possible.
        if s.species is None or not s.cultures:
            s.warnings.append('no resolvable starting species/culture; arrays left empty')
        countries[s.owner].states.append(s)
        eligible_states.append(s)

    print(f'Allocating politics for {len(countries)} playable owners / {len(eligible_states)} states...')
    for tag, c in countries.items():
        allocate_country_politics(c, args.seed)
        if c.dropped_ideologies:
            omitted = ", ".join(
                f"{IDEOLOGY_NAMES[i]}[{i}] {c.ideology_shares[i] * 100:.2f}%"
                for i in c.dropped_ideologies
            )
            omitted_total = sum(c.ideology_shares[i] for i in c.dropped_ideologies) * 100
            global_warnings.append(
                f"{tag}: 1-3 ideologies/state cannot represent every nonzero national tendency with this few states; "
                f"omitted {omitted} (combined {omitted_total:.2f}%). This is expected under the per-state ideology cap."
            )

    for s in eligible_states:
        build_groups(s, args.seed)

    print('Writing explicit state-history arrays...')
    for s in eligible_states:
        dst = out / 'history' / 'states' / s.filename
        dst.parent.mkdir(parents=True, exist_ok=True)
        block = render_generated_block(s, args.seed)
        try:
            new_text = inject_into_state_history(s.text, block)
        except Exception as exc:
            global_warnings.append(f'{s.filename}: could not inject generated block: {exc}')
            continue
        # Preserve BOM only if source had one.
        had_bom = s.path.read_bytes().startswith(b'\xef\xbb\xbf')
        dst.write_text(new_text, encoding='utf-8-sig' if had_bom else 'utf-8')

    if not args.no_support_files:
        package_root = Path(__file__).resolve().parent.parent
        copy_support_files(package_root, out)

    write_reports(out, countries, eligible_states, global_warnings)

    # Summary.
    max_error = max((c.allocation_error for c in countries.values() if c.states), default=0.0)
    total_groups = sum(len(s.groups) for s in eligible_states)
    missing = sum(1 for s in eligible_states if not s.groups and s.manpower > 0)
    print(f'Done: {len(eligible_states)} state histories, {total_groups} pop groups.')
    print(f'Largest country ideological-share error: {max_error * 100:.2f} percentage points.')
    if missing:
        print(f'WARNING: {missing} positive-population states got no groups; inspect reports/states.csv.')
    print('Output:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
