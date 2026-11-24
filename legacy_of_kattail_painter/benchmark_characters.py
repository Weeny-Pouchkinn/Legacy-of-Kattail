"""Time real character operations using unsaved drafts only; never saves sources."""
import argparse
import cProfile
import json
from pathlib import Path
import time

from model import World
from character_model import CharacterStore


def benchmark(root, profiled=False):
    world = World(root); store = CharacterStore(world)
    profiler = cProfile.Profile() if profiled else None
    results = {}

    def measure(name, function):
        start = time.perf_counter()
        if profiler: profiler.enable()
        function()
        if profiler: profiler.disable()
        results[name] = round(time.perf_counter() - start, 6)

    measure('cold_characters', store.characters)
    measure('cold_portraits', store.portraits)
    measure('traits', store.trait_ids)
    measure('ideologies', store.ideology_ids)
    c = store.characters()['AUR_Pawtton']
    measure('apply_character', lambda: store.edit_character(c.key, c.name, c.description, c.art_source,
            c.countries[0] if c.countries else '', 'male'))
    index = next(i for i, role in enumerate(c.roles) if role.key in {'corps_commander', 'field_marshal'})
    measure('edit_role', lambda: store.edit_role(c.key, index, c.roles[index].key,
            {'skill': '4', 'attack_skill': '3', 'defense_skill': '2', 'planning_skill': '2', 'logistics_skill': '2'}, []))
    measure('warm_portraits_after_edit', store.portraits)
    measure('prepare_save', store.prepare_save)
    measure('country_choices', lambda: store.choices('countries'))
    measure('portrait_choices', lambda: store.choices('portraits'))
    measure('trait_choices', lambda: store.choices('traits'))
    # The main operations above modify memory only. Verify every loaded source.
    for relative, original in world.docs.snapshots.items():
        path = world.root / relative
        actual = path.read_bytes() if path.is_file() else None
        if actual != original:
            raise ValueError('Source changed during benchmark: ' + relative)
    return {'profiled': profiled, 'seconds': results, 'source_writes': 0,
            'source_snapshots_checked': len(world.docs.snapshots),
            'characters': len(store.characters()), 'portrait_pairs': len(store.portraits())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--profile', action='store_true', help='Include cProfile overhead, matching the original baseline')
    args = parser.parse_args()
    print(json.dumps(benchmark(args.mod, args.profile), indent=2))
