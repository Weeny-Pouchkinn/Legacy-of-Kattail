"""Dry-run/apply the reviewed character localisation and portrait asset refactor."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re

from PIL import Image, ImageOps

from model import World, parse, walk, value
from character_model import CharacterStore, CHAR_LOC, PORTRAIT_GFX, SMALL_SIZE, atom, block, LOC
from small_portrait import generate_small_portrait


def fingerprint(blob):
    return hashlib.sha256(blob).hexdigest() if blob is not None else None


def prepare(world):
    store = CharacterStore(world)
    original_loc = {key: entries[-1][2] for key, entries in store.loc_records().items()}
    characters = store.characters()
    original_characters = {key: (c.name, c.countries, [(n.key, value(c.text, n)) for n in c.roles]) for key, c in characters.items()}
    moves = {}
    for source_root, destination_root in [('gfx/leaders', 'gfx/leaders/large_portraits'),
                                           ('gfx/interface/ministers', 'gfx/leaders/small_portraits')]:
        candidates = {p.relative_to(world.root).as_posix() for p in (world.root / source_root).rglob('*') if p.is_file()}
        candidates.update(p for p in world.docs.drafts if p.startswith(source_root + '/') and world.docs.binary(p) is not None)
        for relative in sorted(candidates):
            if world.docs.binary(relative) is None:
                continue
            if relative.startswith(('gfx/leaders/large_portraits/', 'gfx/leaders/small_portraits/')):
                continue
            destination = destination_root + '/' + relative.removeprefix(source_root + '/')
            moves[relative] = destination
    audit = {'version': 1, 'characters': len(characters), 'moves': [], 'generated_small': [], 'reused_small': [], 'aliases': [], 'warnings': []}
    with world.docs.grouped():
        for old, new in moves.items():
            blob = world.docs.binary(old)
            existing = world.docs.binary(new)
            if existing is not None and existing != blob:
                raise ValueError('Portrait destination contains different art: ' + new)
            world.docs.stage_bytes(new, blob)
            world.docs.stage_bytes(old, None)
            audit['moves'].append({'from': old, 'to': new, 'sha256': fingerprint(blob)})
        if moves:
            # Exact file path replacement only, longest first; no ID or lore rewriting.
            pattern = re.compile('|'.join(re.escape(old) for old in sorted(moves, key=len, reverse=True)))
            for folder in ('common', 'history', 'events', 'interface', 'gfx', 'map', 'tutorial', 'portraits'):
                for path in sorted((world.root / folder).rglob('*')):
                    if not path.is_file() or path.suffix.lower() not in {'.txt', '.gui', '.gfx', '.asset'}:
                        continue
                    relative = path.relative_to(world.root).as_posix()
                    text = world.docs.text(relative)
                    if 'gfx/leaders/' not in text and 'gfx/interface/ministers/' not in text:
                        continue
                    updated = pattern.sub(lambda m: moves[m[0]], text)
                    if updated != text:
                        world.docs.replace(relative, updated)
        store.organise_gfx()
        records = store.portraits()
        # Preserve misspelled legacy Small IDs by adding their unambiguous matching
        # large alias, rather than renaming public references used by scripts.
        for key, record in list(records.items()):
            if not record.large and record.small_path:
                matches = {p.large_path for p in records.values() if p.large and
                           Path(p.large_path).stem.casefold() == Path(record.small_path).stem.casefold()}
                if len(matches) == 1:
                    store._put_sprite(key, next(iter(matches)))
                    audit['aliases'].append(key)
        # Existing large-only definitions gain a small image derived from the actual
        # large art. Animation strips use the first frame in the editor and thumbnail.
        records = store.portraits()
        missing = [p for p in records.values() if p.large and (not p.small or world.docs.binary(p.small_path) is None)]
        generated = []
        reused = []
        for record in missing:
            mirror = record.large_path.replace('gfx/leaders/large_portraits/', 'gfx/leaders/small_portraits/')
            candidates = [mirror, str(Path(mirror).with_suffix('.tga')).replace('\\', '/')]
            existing = next((p for p in candidates if world.docs.binary(p) is not None), None)
            if existing:
                reused.append((record.small or record.key + '_Small', existing))
                audit['reused_small'].append({'sprite': record.small or record.key + '_Small', 'path': existing,
                                             'sha256': fingerprint(world.docs.binary(existing))})
                continue
            image = store.image(record.large)
            if image is None:
                audit['warnings'].append('Missing large source: ' + record.key)
                continue
            canvas = generate_small_portrait(image)
            output = io.BytesIO(); canvas.save(output, format='TGA')
            stem = re.sub(r'[^A-Za-z0-9_]', '_', record.key.removeprefix('GFX_portrait_'))
            destination = f'gfx/leaders/small_portraits/{record.tag}/{stem}.tga'
            suffix = 2
            while world.docs.binary(destination) is not None:
                destination = f'gfx/leaders/small_portraits/{record.tag}/{stem}__derived_{suffix}.tga'
                suffix += 1
            generated.append((record.small or record.key + '_Small', destination, output.getvalue()))
        for name, destination in reused:
            store._put_sprite(name, destination)
        for name, destination, blob in generated:
            world.docs.stage_bytes(destination, blob)
            store._put_sprite(name, destination)
            audit['generated_small'].append({'sprite': name, 'path': destination, 'sha256': fingerprint(blob)})
        data = store.metadata()
        for key, record in store.portraits().items():
            data['portraits'].setdefault(key, {}).setdefault('tag', record.tag)
        store.save_metadata(data)
        store.prepare_save()
        after_loc = {key: entries[-1][2] for key, entries in store.loc_records().items()}
        if original_loc != after_loc:
            raise ValueError('Refactor changed localisation keys or authored string values')
        after_characters = {key: (c.name, c.countries, [(n.key, value(c.text, n)) for n in c.roles]) for key, c in store.characters().items()}
        if after_characters != original_characters:
            raise ValueError('Refactor changed character identities, recruitment or roles')
        if world.docs.binary(CHAR_LOC)[:3] != b'\xef\xbb\xbf':
            raise ValueError('Character localisation lost its UTF-8 BOM')
        # No sprite may still resolve to a deleted path. Missing pre-existing
        # references outside the moved asset set are reported, never guessed.
        sprites = store.sprites()
        for name, entries in sprites.items():
            for entry in entries:
                if entry['texture'] in moves:
                    raise ValueError('Stale moved texture reference: ' + name)
        for key, c in store.characters().items():
            reference = store.portrait_for_character(c)
            if reference and reference.startswith('GFX_') and not store.sprite_entries(reference):
                audit['warnings'].append('Pre-existing missing large sprite: ' + key + ': ' + reference)
        audit['portrait_pairs'] = len(store.portraits())
        for moved in audit['moves']:
            if fingerprint(world.docs.binary(moved['to'])) != moved['sha256']:
                raise ValueError('Refactor overwrote original portrait art: ' + moved['to'])
        audit['localisation_keys_preserved'] = len(original_loc)
        world.docs.format_script_drafts()
        audit['files'] = {p: {'before': fingerprint(world.docs.snapshots[p]), 'after': fingerprint(world.docs.binary(p))}
                          for p in world.docs.changed}
    return store, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    world = World(args.mod)
    store, report = prepare(world)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Reviewed {len(report["moves"])} asset moves, {len(report["generated_small"])} derived small images, '
          f'{report["characters"]} characters, {report["portrait_pairs"]} portrait pairs, {len(report["files"])} changed paths.', flush=True)
    if args.apply:
        world.docs.before_save = store.prepare_save
        print('Saved with backups:', world.docs.save(), flush=True)
    else:
        print('Dry run only; source files unchanged.', flush=True)
    print('Warnings:', report['warnings'], flush=True)


if __name__ == '__main__':
    main()
