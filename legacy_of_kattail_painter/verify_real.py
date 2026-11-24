"""Explicit real-data checks. Creates diagnostics only under --output, never in the mod."""
import argparse
import hashlib
import json
from pathlib import Path
import tkinter as tk

from model import World, Emblems, FLAG_SIZES, child, default_paths, parse, scalar
from demographics import Setup
from painter import Painter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mod', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    paths = default_paths()
    w = World(args.mod)
    print('Loaded world', flush=True)
    setup = Setup(w)
    w.demographics = setup.load()
    tracked = [args.mod / p for p in w.files]
    tracked += list((args.mod / 'gfx/flags').rglob('*.tga'))
    tracked += list((args.mod / 'localisation/english').rglob('*.yml'))
    tracked += [args.mod / 'map/provinces.bmp', args.mod / 'map/definition.csv']
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    print('Hashed', len(tracked), 'source files', flush=True)
    errors = []
    for rel in w.files:
        try:
            parse(w.docs.text(rel))
        except ValueError as exc:
            errors.append((rel, str(exc)))
    e = Emblems(paths['painter'], paths['stellaris'], paths['giga'])
    print('Parsed all scripts; errors:', len(errors), flush=True)
    for key in e.sources:
        for size in FLAG_SIZES.values():
            assert e.render(key, '#223344', '#08c4ed', size).size == size
    print('Rendered all mask sizes', flush=True)
    root = tk.Tk()
    root.withdraw()
    app = Painter(root, w, e)
    print('Constructed hidden Tk application', flush=True)
    root.update_idletasks()
    app.inspect_state(409)
    assert app.species.get() == '20'
    app.culture.set('85 2')
    app.species.set('19')
    app.apply_demographics()
    print('Applied state draft', flush=True)
    assert w.demographics[409]['culture'] == [85, 2]
    app.undo()
    assert w.demographics[409]['culture'] == [85]
    app.redo()
    print('Undo/redo passed', flush=True)
    assert w.demographics[409]['species'] == 19
    app.symbol.set(next(k for k in e.sources if k.startswith('flusionian/')))
    app.tint.set('#08c4ed')
    assert app._flag()
    app.keep_flag()
    assert app.flag_drafts
    app.open_document(w.countries['KTN'])
    field_count = len(app.rows)
    assert field_count > 100
    app.field_search.set('set_politics')
    app.populate_fields()
    assert app.rows
    w.docs.reset()
    w.demographics = Setup(w).load()
    app.layer.set('Species')
    app.refresh_map()
    w.map_image('Owners').resize((1024, 768)).save(args.output / 'map_preview.png')
    e.render(app.symbol.get(), '#283c63', '#08c4ed', (820, 520)).save(args.output / 'flag_preview.png')
    root.destroy()
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    assert before == after, 'A source file changed during read-only checks'
    report = {'states': len(w.states), 'countries': len(w.countries), 'scripts': len(w.files),
              'flat_masks': len(e.sources), 'mask_renders': len(e.sources) * 3,
              'source_files_hashed_unchanged': len(tracked), 'parse_errors': errors,
              'hidden_tk': 'passed demographics/undo/redo/flags/field-filter checks',
              'country_field_rows_KTN': field_count, 'map_size': list(w.map_ids.shape[::-1]),
              'game_validation': 'not run', 'source_warnings': w.warnings}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
