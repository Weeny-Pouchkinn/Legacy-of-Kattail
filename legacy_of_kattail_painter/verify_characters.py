"""Read-only verification of the applied character/portrait migration audit.

Requires the local original-byte backup. Run before further authored edits;
later deliberate changes correctly invalidate the recorded snapshot hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path

from model import World, value, parse
from character_model import CharacterStore, CHAR_LOC, PORTRAIT_GFX, atom, block
from small_portrait import BORDER_PATH


def verify(root):
    root = Path(root).resolve()
    audit = json.loads((root / 'modding_documentation/agent_memory/plans/character-refactor-audit.json').read_text(encoding='utf-8'))
    backup = root / audit['initial_backup']
    sha = lambda b: hashlib.sha256(b).hexdigest() if b is not None else None
    for relative, hashes in audit['files'].items():
        path = root / relative
        blob = path.read_bytes() if path.is_file() else None
        assert sha(blob) == hashes['after'], 'Changed output: ' + relative
        if hashes['before'] is not None:
            assert sha((backup / relative).read_bytes()) == hashes['before'], 'Changed backup: ' + relative
    for moved in audit['moves']:
        assert not (root / moved['from']).exists(), moved['from']
        assert sha((root / moved['to']).read_bytes()) == moved['sha256'], moved['to']
    world = World(root); store = CharacterStore(world)
    current_loc = {k: records[-1][2] for k, records in store.loc_records().items()}
    current_characters = {k: (c.name, c.countries, [(n.key, value(c.text, n)) for n in c.roles])
                          for k, c in store.characters().items()}
    assert len(current_characters) == audit['characters']
    assert len(store.portraits()) == audit['portrait_pairs']
    assert world.docs.binary(CHAR_LOC).startswith(b'\xef\xbb\xbfl_english:')
    # Every native pair declaration in the main file has a globally unique ID.
    text = world.docs.text(PORTRAIT_GFX)
    names = [atom(text, n.children, 'name') for n in block(parse(text), 'spriteTypes').children if n.children]
    assert len(names) == len(set(names)), 'Duplicate main portrait sprite ID'
    assert 'noOfFrames' in text, 'Animated sprite fields lost'
    store.prepare_save()
    assert not world.docs.changed, 'Non-idempotent organisation'
    # Reconstruct only our pre-migration files in memory. No current source is written.
    for relative, hashes in audit['files'].items():
        original = (backup / relative).read_bytes() if hashes['before'] is not None else None
        world.docs.stage_bytes(relative, original)
    before = CharacterStore(world)
    original_loc = {k: records[-1][2] for k, records in before.loc_records().items()}
    assert original_loc == current_loc, 'Authored localisation values or keys changed'
    original_characters = {k: (c.name, c.countries, [(n.key, value(c.text, n)) for n in c.roles])
                           for k, c in before.characters().items()}
    assert original_characters == current_characters, 'Native identities/recruitment/roles changed'
    return {'characters': len(current_characters), 'portrait_pairs': audit['portrait_pairs'],
            'verified_output_paths': len(audit['files']), 'original_asset_hashes': len(audit['moves']),
            'authored_localisation_values_preserved': len(current_loc),
            'generated_small': len(audit['generated_small']), 'reused_small': len(audit['reused_small']),
            'ministermaker_border_sha256': sha(BORDER_PATH.read_bytes()),
            'organisation_idempotent': True, 'source_writes': 0, 'warnings': audit['warnings']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.mod), ensure_ascii=False, indent=2))
