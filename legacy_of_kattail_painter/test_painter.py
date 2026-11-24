"""Meaningful isolation, parser, mask and migration checks using disposable fixtures."""
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
from PIL import Image

from model import Documents, Emblems, FLAG_SIZES, World, child, parse, scalar, value, walk
from demographics import STARTUP, Setup, set_local_draft
from migrate_state_setup import apply_stage, build
import source_io


class ParserTests(unittest.TestCase):
    def test_comments_quotes_duplicates_and_operators(self):
        text = '# ignored = {\nroot = { add = A add = B text = "{ # literal }" check > 3 list = { 1 2 3 } }'
        ns = parse(text)[0].children
        self.assertEqual([n.key for n in ns[:2]], ['add', 'add'])
        self.assertEqual(value(text, ns[2]), '"{ # literal }"')
        self.assertEqual(ns[3].op, '>')
        self.assertEqual([n.key for n in ns[4].children], ['1', '2', '3'])
        paths = [p for p, _ in walk(parse(text))]
        self.assertIn('/root[1]/add[2]', paths)

    def test_rejects_unbalanced_script(self):
        for source in ['x = { y = 1', 'x = 1 }', 'x =']:
            with self.assertRaises(ValueError):
                parse(source)

    def test_typed_colour_block_keeps_type_and_child_components(self):
        t = 'color = rgb { 60 159 226 } other = yes'
        ns = parse(t)
        self.assertEqual(len(ns), 2)
        self.assertEqual(value(t, ns[0]), 'rgb { 60 159 226 }')
        self.assertEqual([n.key for n in ns[0].children], ['60', '159', '226'])


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'mod'
        self.root.mkdir()
        for p in ['history/states', 'history/countries', 'common/country_tags', 'common/scripted_triggers', 'map', 'common/on_actions']:
            (self.root / p).mkdir(parents=True, exist_ok=True)
        (self.root / 'common/country_tags/tags.txt').write_text('AAA = "countries/AAA.txt" BBB = "countries/BBB.txt"')
        (self.root / 'map/definition.csv').write_text('0;0;0;0;sea;false;ocean;0\n1;1;2;3;land;false;plains;1\n2;4;5;6;land;false;hills;1\n')
        (self.root / 'history/states/one.txt').write_bytes(b'state = {\r\n\tid = 1 name = "ONE" provinces = { 1 }\r\n\thistory = { owner = AAA add_core_of = AAA }\r\n}\r\n')
        (self.root / 'history/states/two.txt').write_text('state = { id = 2 name = TWO provinces = { 2 } history = { owner = BBB } }')
        (self.root / STARTUP).write_text('''on_actions = { on_startup = { effect = {
            add_to_array = { array = global.culture_group_1_array value = 4 }
            every_state = { clear_array = state_cultures add_to_array = { array = state_cultures value = 4 } }
            every_state = { set_variable = { species = 0 } set_variable = { minority = 1000 } }
            AAA = { every_owned_state = { set_variable = { species = 1 } } }
            1 = { add_to_array = { array = state_cultures value = 7 } }
            1 = { add_to_array = { array = state_cultures value = 9 } }
            2 = { if = { limit = { NOT = { check_variable = { species = 1 } } }
                      add_to_array = { array = state_cultures value = 8 } } }
            every_state = { limit = { is_core_of = AAA } set_variable = { minority = 9 } }
            AAA = { add_ideas = var_species_1 }
        } } on_weekly = { effect = { 1 = { set_variable = { species = 2 } } } } }''', encoding='utf-8-sig')
        self.world = World(self.root)
        self.world.demographics = Setup(self.world).load()

    def tearDown(self):
        self.tmp.cleanup()

    def test_initial_order_scopes_conditions_and_three_cultures(self):
        self.assertEqual(self.world.demographics[1], {'culture': [4, 7, 9], 'species': 1, 'minority': 9})
        self.assertEqual(self.world.demographics[2], {'culture': [4, 8], 'species': 0, 'minority': 1000})

    def test_draft_changes_do_not_touch_source_and_undo_redo(self):
        rel = 'history/states/one.txt'
        original = (self.root / rel).read_bytes()
        set_local_draft(self.world, 1, [4, 7, 9], 8, 1000)
        self.assertEqual((self.root / rel).read_bytes(), original)
        self.assertEqual(Setup(self.world).load()[1]['species'], 8)
        self.world.docs.undo()
        self.assertEqual(Setup(self.world).load()[1]['species'], 1)
        self.world.docs.redo()
        self.assertEqual(Setup(self.world).load()[1]['species'], 8)

    def test_repeated_local_update_has_one_managed_section(self):
        for species in [3, 7, 5]:
            set_local_draft(self.world, 1, [4, 7, 9], species, 1000)
        text = self.world.docs.text('history/states/one.txt')
        self.assertEqual(text.count('# LOK PAINTER DEMOGRAPHICS BEGIN'), 1)
        self.assertEqual(Setup(self.world).load()[1]['species'], 5)

    def test_equal_species_clear_minority_including_diverse_zero(self):
        for species in (0, 1, 3):
            set_local_draft(self.world, 1, [4, 7, 9], species, species)
            self.assertEqual(self.world.demographics[1]['minority'], 1000)
            self.assertEqual(Setup(self.world).load()[1]['minority'], 1000)
        with self.assertRaisesRegex(ValueError, 'cannot be the majority'):
            set_local_draft(self.world, 1, [4], 1000, 1000)

    def test_loaded_and_raw_edited_duplicates_are_repaired_on_save(self):
        set_local_draft(self.world, 1, [4, 7, 9], 3, 1000)
        rel = self.world.states[1].path
        raw = self.world.docs.text(rel).replace('minority = 1000', 'minority = 3')
        self.world.docs.replace(rel, raw)
        setup = Setup(self.world)
        self.assertEqual(setup.load()[1]['minority'], 1000)
        self.assertEqual(setup.redundant_minorities, {1})
        count, _ = self.world.docs.save()
        self.assertEqual(count, 1)
        self.assertIn('minority = 1000', (self.root / rel).read_text())
        fresh = Setup(World(self.root))
        self.assertEqual(fresh.load()[1]['minority'], 1000)
        self.assertFalse(fresh.redundant_minorities)

    def regional_world(self):
        with (self.root / 'map/definition.csv').open('a') as stream:
            stream.write('3;7;8;9;land;false;plains;1\n4;10;11;12;land;false;plains;1\n')
        path = self.root / 'history/states/one.txt'
        path.write_bytes(path.read_bytes().replace(b'provinces = { 1 }', b'provinces = { 1 4 }'))
        (self.root / 'history/states/three.txt').write_text(
            'state = { id = 3 name = THREE provinces = { 3 } history = { owner = BBB } }')
        regions = self.root / 'map/strategicregions'
        regions.mkdir()
        (regions / 'first.txt').write_text('strategic_region = { id = 10 name = FIRST provinces = { 1 4 2 } }')
        (regions / 'second.txt').write_text('strategic_region = { id = 20 name = SECOND provinces = { 3 } }')
        world = World(self.root)
        world.demographics = Setup(world).load()
        world.map_ids = np.tile(np.repeat(np.array([1, 4, 2, 3], dtype=np.int32), 8), (12, 1))
        return world

    def test_region_scope_paints_only_members_and_undoes_as_one_action(self):
        world = self.regional_world()
        before = Setup(world).load()
        self.assertEqual(world.paint_targets(1, 'State'), (1,))
        self.assertEqual(world.paint_targets(4, 'Strategic region'), (1, 2))
        self.assertEqual(world.paint(1, 'Strategic region', 'Culture', 7), (1, 2))
        self.assertEqual(world.demographics[1]['culture'], [7])
        self.assertEqual(world.demographics[2]['culture'], [7])
        self.assertEqual(world.demographics[3], before[3])
        self.assertEqual(len(world.docs.undo_stack), 1)
        world.docs.undo()
        self.assertEqual(Setup(world).load(), before)
        world.docs.redo()
        self.assertEqual(Setup(world).load()[2]['culture'], [7])
        self.assertEqual(world.paint(2, 'Strategic region', 'Culture', 7, exclude={1, 2}), ())
        self.assertEqual(len(world.docs.undo_stack), 1)
        self.assertEqual(world.docs.save()[0], 2)
        self.assertEqual(Setup(World(self.root)).load()[2]['culture'], [7])

    def test_region_species_brushes_enforce_invariant_per_state(self):
        world = self.regional_world()
        # State 1 starts with minority 9, state 2 with no minority.
        world.paint(1, 'Strategic region', 'Species', 9)
        self.assertEqual([world.demographics[s]['species'] for s in (1, 2)], [9, 9])
        self.assertEqual([world.demographics[s]['minority'] for s in (1, 2)], [1000, 1000])
        world.paint(1, 'Strategic region', 'Minority', 9)
        self.assertEqual([world.demographics[s]['minority'] for s in (1, 2)], [1000, 1000])
        world.paint(1, 'Strategic region', 'Minority', 3)
        self.assertEqual([world.demographics[s]['minority'] for s in (1, 2)], [3, 3])
        self.assertEqual(world.demographics[3]['species'], 0)

    def test_region_owner_brush_and_drag_exclusion(self):
        world = self.regional_world()
        self.assertEqual(world.paint(1, 'Strategic region', 'Owner', 'AAA', exclude={1}), (2,))
        for sid, expected in ((1, 'AAA'), (2, 'AAA'), (3, 'BBB')):
            text, nodes = world.state_nodes(sid)
            self.assertEqual(scalar(text, child(nodes, 'history').children, 'owner'), expected)

    def test_region_scope_refuses_split_states_before_editing(self):
        self.regional_world()
        regions = self.root / 'map/strategicregions'
        (regions / 'first.txt').write_text('strategic_region = { id = 10 name = FIRST provinces = { 1 2 } }')
        (regions / 'second.txt').write_text('strategic_region = { id = 20 name = SECOND provinces = { 3 4 } }')
        world = World(self.root)
        world.demographics = Setup(world).load()
        with self.assertRaisesRegex(ValueError, 'crosses strategic region'):
            world.paint(1, 'Strategic region', 'Culture', 7)
        self.assertFalse(world.docs.changed)
        self.assertEqual(world.paint_targets(1, 'State'), (1,))

    def test_region_edit_failure_rolls_back_whole_group(self):
        world = self.regional_world()
        apply = world.set_owner_draft
        def fail_second(sid, tag):
            if sid == 2:
                raise ValueError('simulated second state failure')
            apply(sid, tag)
        with patch.object(world, 'set_owner_draft', side_effect=fail_second):
            with self.assertRaisesRegex(ValueError, 'simulated second'):
                world.paint(1, 'Strategic region', 'Owner', 'BBB')
        self.assertFalse(world.docs.changed)
        self.assertFalse(world.docs.undo_stack)

    def test_boundary_levels_are_independent_and_keep_display_pixel_widths(self):
        world = self.regional_world()
        image = Image.new('RGB', (32, 12), (100, 150, 200))
        self.assertEqual(np.flatnonzero(np.asarray(world.boundary_mask('Province', image.size))[5]).tolist(), [8, 16, 24])
        self.assertEqual(np.flatnonzero(np.asarray(world.boundary_mask('State', image.size))[5]).tolist(), [16, 17, 24, 25])
        self.assertEqual(np.flatnonzero(np.asarray(world.boundary_mask('Strategic region', image.size))[5]).tolist(), [24, 25, 26])
        self.assertIs(world.boundary_overlay(image), image)
        for flags, point, expected in [((True, False, False), (8, 5), (55, 55, 55)),
                                       ((False, True, False), (16, 5), (15, 15, 15)),
                                       ((False, False, True), (24, 5), (245, 245, 245))]:
            self.assertEqual(world.boundary_overlay(image, *flags).getpixel(point), expected)
        self.assertEqual(image.getpixel((24, 5)), (100, 150, 200))
        for size, first in [((64, 24), 48), ((16, 6), 12)]:
            row = np.asarray(world.boundary_mask('Strategic region', size))[size[1] // 2]
            self.assertEqual(np.flatnonzero(row).tolist(), [first, first + 1, first + 2])

    def test_arbitrary_unknown_field_and_duplicates_remain_editable(self):
        rel = 'history/states/one.txt'
        original = self.world.docs.text(rel)
        custom = original.replace('owner = AAA', 'owner = AAA mystery = { alien_energy = 12 alien_energy = 15 }')
        self.world.docs.replace(rel, custom)
        node = [n for _, n in walk(parse(custom)) if n.key == 'alien_energy'][1]
        self.world.docs.edit(rel, node, '27')
        self.assertIn('alien_energy = 12 alien_energy = 27', self.world.docs.text(rel))

    def test_source_path_escape_is_rejected(self):
        with self.assertRaises(ValueError):
            self.world.docs.text('../secret.txt')

    def test_unknown_initial_effect_blocks_migration(self):
        rel = STARTUP
        t = self.world.docs.text(rel).replace('species = 0', 'species = 0 unexpected = 1')
        self.world.docs.replace(rel, t)
        with self.assertRaises(ValueError):
            Setup(self.world).load()

    def test_migration_preserves_values_source_bytes_bom_newlines_and_other_effects(self):
        originals = {f.relative_to(self.root).as_posix(): f.read_bytes() for f in self.root.rglob('*') if f.is_file()}
        out = Path(self.tmp.name) / 'stage'
        manifest = build(self.root, out)
        self.assertEqual(manifest['states'], 2)
        self.assertTrue((out / 'files' / STARTUP).read_bytes().startswith(b'\xef\xbb\xbf'))
        state = (out / 'files/history/states/one.txt').read_bytes()
        self.assertNotIn(b'\n', state.replace(b'\r\n', b''))
        startup = (out / 'files' / STARTUP).read_text(encoding='utf-8-sig')
        self.assertIn('add_ideas = var_species_1', startup)
        self.assertIn('global.culture_group_1_array', startup)
        self.assertIn('on_weekly', startup)
        self.assertIn('species = 2', startup)
        self.assertEqual({p: (self.root / p).read_bytes() for p in originals}, originals)
        for item in manifest['files']:
            self.assertEqual(hashlib.sha256(originals[item['path']]).hexdigest(), item['before_sha256'])
        migrated = World(self.root)
        for item in manifest['files']:
            migrated.docs.replace(item['path'], (out / 'files' / item['path']).read_text(encoding='utf-8-sig'))
        self.assertEqual(Setup(migrated).load(), self.world.demographics)

    def test_save_preserves_encoding_newlines_backups_and_reloads(self):
        path = self.root / 'history/states/one.txt'
        original = b'\xef\xbb\xbf' + path.read_bytes()
        path.write_bytes(original)
        world = World(self.root)
        world.demographics = Setup(world).load()
        set_local_draft(world, 1, [4, 7, 9], 8, 3)
        count, backup = world.docs.save()
        self.assertEqual(count, 1)
        self.assertEqual((backup / 'history/states/one.txt').read_bytes(), original)
        saved = path.read_bytes()
        self.assertTrue(saved.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\n', saved.replace(b'\r\n', b''))
        self.assertEqual(Setup(World(self.root)).load()[1], {'culture': [4, 7, 9], 'species': 8, 'minority': 3})
        self.assertFalse(world.docs.changed)
        self.assertFalse(world.docs.undo_stack)
        self.assertEqual(world.docs.save(), (0, None))
        set_local_draft(world, 1, [4, 7, 9], 8, 3)
        self.assertFalse(world.docs.changed)

    def test_save_rejects_external_edit_before_any_writes(self):
        one = self.root / 'history/states/one.txt'
        original = one.read_bytes()
        for sid in (1, 2):
            set_local_draft(self.world, sid, [4], 8, 1000)
        other = self.root / 'history/states/two.txt'
        other.write_bytes(other.read_bytes() + b'\n# external edit')
        with self.assertRaisesRegex(ValueError, 'outside the painter'):
            self.world.docs.save()
        self.assertEqual(one.read_bytes(), original)
        self.assertIn(b'# external edit', other.read_bytes())
        self.assertEqual(len(self.world.docs.changed), 2)

    def test_save_failure_rolls_back_written_sources_and_keeps_drafts(self):
        original = {s.path: (self.root / s.path).read_bytes() for s in self.world.states.values()}
        for sid in (1, 2):
            set_local_draft(self.world, sid, [4], 8, 1000)
        atomic = source_io.atomic_bytes
        calls = []
        def fail_second(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError('simulated write failure')
            atomic(path, data)
        with patch('source_io.atomic_bytes', side_effect=fail_second):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.world.docs.save()
        self.assertEqual({p: (self.root / p).read_bytes() for p in original}, original)
        self.assertEqual(len(self.world.docs.changed), 2)

    def test_apply_migration_matches_baseline_and_rejects_reapplication(self):
        stage = Path(self.tmp.name) / 'stage'
        build(self.root, stage)
        original = (self.root / STARTUP).read_bytes()
        backup = apply_stage(self.root, stage)
        self.assertEqual((backup / STARTUP).read_bytes(), original)
        world = World(self.root)
        setup = Setup(world)
        self.assertEqual(setup.load(), self.world.demographics)
        self.assertFalse(setup.selected)
        with self.assertRaisesRegex(ValueError, 'Source/stage changed'):
            apply_stage(self.root, stage)

    def test_defined_colours_minority_stripes_no_minority_and_water(self):
        folder = self.root / 'common/map_modes'
        folder.mkdir()
        (folder / 'LOK_culture_map_mode.txt').write_text('''
            add_to_temp_variable = { culture_4_red = 0.4 }
            add_to_temp_variable = { culture_4_green = 0.2 }
            add_to_temp_variable = { culture_4_blue = 0.6 }
            add_to_temp_variable = { culture_7_red = 0 }
            add_to_temp_variable = { culture_7_green = 1 }
            add_to_temp_variable = { culture_7_blue = 0 }
        ''')
        (folder / 'LOK_species_map_mode.txt').write_text('''scripted_map_modes = {
            LOK_species_map_mode = {
                bottom = { color = {
                    if = { limit = { FROM = { check_variable = { species = 1 } } }
                           set_temp_variable = { red = 0 } set_temp_variable = { green = 0.29 } set_temp_variable = { blue = 0.5 } }
                } }
                top = { color = {
                    if = { limit = { FROM = { check_variable = { minority = 2 } } }
                           set_temp_variable = { red = 0.8 } set_temp_variable = { green = 0.16 } set_temp_variable = { blue = 0.24 } }
                } }
            }
        }''')
        self.world._demographic_catalogs()
        self.world.map_ids = np.ones((40, 64), dtype=np.int32)
        self.world.map_ids[:, 32:] = 2
        self.world.map_ids[-1, :] = 0
        set_local_draft(self.world, 1, [4], 1, 2)
        set_local_draft(self.world, 2, [7], 1, 1000)
        image = self.world.map_image('Species')
        self.assertEqual(image.getpixel((0, 0)), (204, 41, 61))
        self.assertEqual(image.getpixel((12, 0)), (0, 74, 128))
        self.assertEqual(image.getpixel((40, 0)), (0, 74, 128))
        self.assertEqual(image.getpixel((0, 39)), (26, 43, 60))
        image = self.world.map_image('Culture')
        self.assertEqual(image.getpixel((0, 0)), (102, 51, 153))
        self.assertEqual(image.getpixel((40, 0)), (0, 255, 0))


class FlagTests(unittest.TestCase):
    def test_flat_mask_tints_background_dimensions_and_excludes_gold(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cache = root / 'stellaris_flags/emblems/test'
            cache.mkdir(parents=True)
            Image.new('L', (4, 4), 255).save(cache / 'one__mask.png')
            Image.new('RGB', (4, 4), '#d4af37').save(cache / 'gold__gilded.png')
            catalog = Emblems(root)
            self.assertEqual(list(catalog.sources), ['test/one'])
            for size in FLAG_SIZES.values():
                flag = catalog.render('test/one', '#102030', '#19a0e0', size)
                self.assertEqual(flag.size, size)
                self.assertEqual(flag.getpixel((0, 0)), (16, 32, 48))
                self.assertEqual(flag.getpixel((size[0] // 2, size[1] // 2)), (25, 160, 224))


if __name__ == '__main__':
    unittest.main()
