"""Stage the initial demographic definitions in state histories; never edits the input mod.

Output is a reviewable patch directory, manifest and unified diff. The separate
installer verifies every original hash before applying any staged source changes.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

from model import World, child, parse, value, walk, read_text
from demographics import STARTUP, Setup, set_local_draft, targets_demographics
from source_io import confined, write_changes


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(mod, output):
    world = World(mod)
    if world.warnings:
        raise ValueError('Resolve state load warnings first: ' + '; '.join(world.warnings))
    setup = Setup(world)
    world.demographics = setup.load()
    if setup.missing_states:
        raise ValueError('Startup references missing states: ' + str(sorted(setup.missing_states)))
    if not setup.selected:
        raise ValueError('No startup demographics found; the mod may already be migrated')
    baseline = {sid: {k: list(v) if isinstance(v, list) else v for k, v in r.items()}
                for sid, r in world.demographics.items()}
    output = Path(output).resolve()
    if output == world.root or output.is_relative_to(world.root):
        raise ValueError('Stage outside the source mod so inspection cannot affect game loading')
    if (output / 'manifest.json').exists():
        raise ValueError('Use a new output directory; existing migration stages are preserved')
    # Preserve original text/comments outside each selected statement. Later game effects,
    # country species ideas, culture registries and runtime readers are not changed.
    text = setup.text
    for n in sorted(setup.selected, key=lambda n: n.start, reverse=True):
        start = text.rfind('\n', 0, n.start) + 1
        end = text.find('\n', n.end)
        end = len(text) if end < 0 else end + 1
        before, after = text[start:n.start].strip(), text[n.end:end].strip()
        if not before and (not after or after.startswith('#')):
            text = text[:start] + text[end:]
        else:
            text = text[:n.start] + text[n.end:]
    world.docs.replace(STARTUP, text)
    for sid, data in sorted(baseline.items()):
        set_local_draft(world, sid, data['culture'], data['species'], data['minority'])
    world.docs.format_script_drafts()
    # Replay only remaining startup initializers plus the new authoritative state files.
    replay = Setup(world)
    after = replay.load()
    if replay.selected or after != baseline:
        raise ValueError('Migration changed initial demographics or left startup initializers')
    manifest = {
        'schema': 1,
        'mod': str(world.root),
        'scope': 'Initial ownership and undated history only; offline engine validation pending',
        'states': len(world.states),
        'removed_startup_statements': len(setup.selected),
        'runtime_containers': ['state_cultures', 'species', 'minority'],
        'files': [],
        'caveats': [
            'Static evaluator supports only observed setup syntax and fails on unknown constructs.',
            'Does not execute earlier scripted effect calls or other on_action files.',
            'Country species ideas, gameplay culture/species changes and derived modifiers remain intact.',
            'Review the diff and test a new offline campaign; this is not in-game validation.',
        ],
    }
    diff = []
    for relative in world.docs.changed:
        source = world.root / relative
        original = source.read_bytes()
        if read_text(source) != world.docs.originals[relative]:
            raise ValueError('Source changed during migration staging: ' + relative)
        text = world.docs.text(relative)
        encoding = 'utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8'
        try:
            original.decode(encoding)
        except UnicodeDecodeError:
            encoding = 'cp1252'
        # read_text decoded bytes without newline translation; preserve original CRLF/LF.
        newline = '\r\n' if b'\r\n' in original else '\n'
        text = text.replace('\r\n', '\n').replace('\n', newline)
        blob = text.encode(encoding)
        staged = output / 'files' / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(blob)
        manifest['files'].append({'path': relative, 'before_sha256': digest(original),
                                  'after_sha256': digest(blob), 'encoding': encoding})
        diff.extend(difflib.unified_diff(world.docs.originals[relative].splitlines(True),
                    text.splitlines(True), fromfile='a/' + relative, tofile='b/' + relative))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (output / 'migration.diff').write_text(''.join(diff), encoding='utf-8', newline='')
    (output / 'initial_demographics.json').write_text(json.dumps(baseline, indent=2), encoding='utf-8')
    return manifest


def apply_stage(mod, output):
    """Apply a reviewed stage to an existing painter installation with backups."""
    root, output = Path(mod).resolve(), Path(output).resolve()
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    if Path(manifest['mod']).resolve() != root:
        raise ValueError('Migration stage belongs to another mod')
    changes = {}
    for entry in manifest['files']:
        relative = entry['path']
        if relative in changes:
            raise ValueError('Duplicate migration destination: ' + relative)
        original = confined(root, relative).read_bytes()
        updated = confined(output / 'files', relative).read_bytes()
        if digest(original) != entry['before_sha256'] or digest(updated) != entry['after_sha256']:
            raise ValueError('Source/stage changed; regenerate migration: ' + relative)
        parse(updated.decode(entry['encoding']))
        changes[relative] = (original, updated)
    return write_changes(root, changes, 'migration')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mod', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--apply', action='store_true', help='Apply an existing reviewed stage instead of generating one')
    args = ap.parse_args()
    if args.apply:
        print('Applied migration; originals backed up at:', apply_stage(args.mod, args.output))
    else:
        result = build(args.mod, args.output)
        print(f'Staged {len(result["files"])} files; {result["states"]} states; '
              f'{result["removed_startup_statements"]} startup statements relocated. Input mod unchanged.')
