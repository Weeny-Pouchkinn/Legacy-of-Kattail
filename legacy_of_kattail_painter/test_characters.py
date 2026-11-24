"""Character/portrait persistence and lossless migration fixtures."""
import json
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image

import test_painter as painter_tests
from model import World, parse, value
from character_model import CharacterStore, CHAR_LOC, PORTRAIT_GFX, METADATA, atom
from refactor_characters import prepare
import source_io
from small_portrait import generate_small_portrait, BORDER_PATH


class CharacterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = painter_tests.FixtureTests(); self.fixture.setUp()
        self.root = self.fixture.root
        for directory in ('common/characters', 'common/country_leader', 'interface', 'localisation/english',
                          'gfx/leaders/AAA', 'gfx/interface/ministers/AAA'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / 'history/countries/AAA-Test.txt').write_text('capital = 1\nrecruit_character = AAA_Zed\n2000.1.1 = { recruit_character = BBB_Alpha }\n')
        (self.root / 'history/countries/BBB-Test.txt').write_text('capital = 2\n')
        (self.root / 'common/characters/people.txt').write_text('''Characters = {
    AAA_Zed = {
        name = AAA_Zed
        portraits = { army = { large = "GFX_portrait_AAA_Zed" small = "GFX_portrait_AAA_Zed_Small" } }
        advisor = { slot = political_advisor cost = 150 traits = { trait_one } visible = { always = yes } }
        country_leader = { ideology = first expire = "1965.1.1" desc = AAA_Zed_desc }
        country_leader = { ideology = second expire = "1965.1.1" }
    }
    BBB_Alpha = { name = BBB_Alpha portraits = { civilian = { large = "GFX_portrait_AAA_Zed" } } }
}''')
        (self.root / 'common/country_leader/traits.txt').write_text('leader_traits = { trait_one = { random = no } trait_two = { random = no } }')
        (self.root / CHAR_LOC).write_text('l_english:\n # authored credit stays\n AAA_Zed:0 "Zéd Person"\n AAA_Zed_desc:0 "Authored £icon£ $TOKEN$ [ROOT.GetName]\\nDescription"\n other_key:0 "Preserved unrelated text"\n', encoding='utf-8-sig')
        (self.root / 'localisation/english/other_l_english.yml').write_text('l_english:\n AAA:0 "Neutral A"\n BBB:0 "Neutral B"\n BBB_Alpha:0 "Alpha Person"\n BBB_Alpha_desc:0 "External authored description"\n untouched:0 "Keep me"\n', encoding='utf-8-sig')
        (self.root / PORTRAIT_GFX).write_text('''spriteTypes = {
    spriteType = { name = "GFX_portrait_AAA_Zed" texturefile = "gfx/leaders/AAA/AAA_Zed.tga" }
    spriteType = { name = "GFX_portrait_AAA_Zed_Small" texturefile = "gfx/interface/ministers/AAA/AAA_Zed.tga" }
    frameAnimatedSpriteType = { name = "GFX_portrait_AAA_Animated" texturefile = "gfx/leaders/AAA/strip.tga" noOfFrames = 2 animation_rate_fps = 24 looping = yes play_on_show = yes }
}''')
        Image.new('RGBA', (156, 210), (60, 120, 180, 255)).save(self.root / 'gfx/leaders/AAA/AAA_Zed.tga')
        Image.new('RGBA', (65, 67), (120, 60, 180, 255)).save(self.root / 'gfx/interface/ministers/AAA/AAA_Zed.tga')
        Image.new('RGBA', (312, 210), (80, 100, 140, 255)).save(self.root / 'gfx/leaders/AAA/strip.tga')
        self.world = World(self.root); self.store = CharacterStore(self.world)

    def tearDown(self):
        self.fixture.tearDown()

    def test_localised_sort_nation_filter_and_unrecruited(self):
        self.assertEqual([c.key for c in self.store.ordered()], ['BBB_Alpha', 'AAA_Zed'])
        self.assertEqual([c.key for c in self.store.ordered(nation='UNASSIGNED')], ['BBB_Alpha'])
        self.assertEqual([c.key for c in self.store.ordered(nation='AAA')], ['AAA_Zed'])
        self.assertEqual(len(self.store.characters()['AAA_Zed'].roles), 3)

    def test_localisation_regroups_and_preserves_every_authored_value_and_bom(self):
        original = self.store.localisations()
        self.store.organise_localisation()
        self.assertEqual(self.store.localisations(), original)
        text = self.world.docs.text(CHAR_LOC)
        self.assertIn('#AAA - Neutral A', text)
        self.assertIn('#UNASSIGNED - ', text)
        self.assertIn('BBB_Alpha:0', text)
        self.assertIn('untouched:0 "Keep me"', self.world.docs.text('localisation/english/other_l_english.yml'))
        self.assertNotIn('BBB_Alpha:0', self.world.docs.text('localisation/english/other_l_english.yml'))
        self.assertTrue(self.world.docs.binary(CHAR_LOC).startswith(b'\xef\xbb\xbf'))
        first = self.world.docs.text(CHAR_LOC)
        self.store.organise_localisation()
        self.assertEqual(self.world.docs.text(CHAR_LOC), first)

    def test_recruitment_moves_only_undated_statement_and_regroups_localisation(self):
        self.store.edit_character('AAA_Zed', 'Zéd Person', self.store.characters()['AAA_Zed'].description, 'Artist https://example.test', 'BBB')
        self.assertEqual(self.store.recruitments()['AAA_Zed'], ('BBB',))
        self.assertIn('2000.1.1 = { recruit_character = BBB_Alpha }', self.world.docs.text('history/countries/AAA-Test.txt'))
        self.assertIn('#BBB - Neutral B', self.world.docs.text(CHAR_LOC))
        self.assertEqual(self.store.characters()['AAA_Zed'].art_source, 'Artist https://example.test')

    def test_repeated_role_edit_preserves_other_roles_and_custom_conditions(self):
        c = self.store.characters()['AAA_Zed']; before = [value(c.text, role) for role in c.roles]
        self.store.edit_role('AAA_Zed', 1, 'country_leader', {'ideology': 'changed'}, [])
        c = self.store.characters()['AAA_Zed']
        self.assertEqual(value(c.text, c.roles[0]), before[0])
        self.assertEqual(value(c.text, c.roles[2]), before[2])
        self.assertIn('visible = { always = yes }', value(c.text, c.roles[0]))
        self.assertEqual(atom(c.text, c.roles[1].children, 'ideology'), 'changed')

    def test_unchanged_primary_country_keeps_all_native_recruitments(self):
        path = 'history/countries/BBB-Test.txt'
        self.world.docs.replace(path, self.world.docs.text(path) + 'recruit_character = AAA_Zed\n')
        self.assertEqual(self.store.recruitments()['AAA_Zed'], ('AAA', 'BBB'))
        c = self.store.characters()['AAA_Zed']
        self.store.edit_character(c.key, c.name, c.description, 'Edited credit', 'AAA')
        self.assertEqual(self.store.recruitments()['AAA_Zed'], ('AAA', 'BBB'))
        self.store.edit_character(c.key, c.name, c.description, 'Edited credit', '')
        self.assertNotIn(c.key, self.store.recruitments())

    def test_create_character_and_arbitrary_tagged_portrait_save_reload_undo(self):
        self.store.edit_character('AAA_New', 'New Person', '', 'Character credit', 'AAA', create=True)
        self.store.edit_portrait('GFX_portrait_XYZ_New', 'XYZ', 'Portrait credit', 'Variant notes',
                                 self.root / 'gfx/leaders/AAA/AAA_Zed.tga', create=True, generate_small=True)
        self.store.assign_portrait('AAA_New', 'civilian', 'GFX_portrait_XYZ_New')
        self.store.edit_role('AAA_New', None, 'corps_commander', {'skill': '3', 'attack_skill': '2'}, ['trait_one'])
        record = self.store.portraits()['GFX_portrait_XYZ_New']
        self.assertEqual(self.store.image(record.small).size, (65, 67))
        self.assertEqual(record.tag, 'XYZ')
        count, backup = self.world.docs.save()
        self.assertGreater(count, 4)
        self.assertIn('common/characters/zz_painter_characters.txt', (backup / 'created_files.txt').read_text())
        fresh = CharacterStore(World(self.root)); c = fresh.characters()['AAA_New']
        self.assertEqual(c.name, 'New Person'); self.assertEqual(c.countries, ('AAA',))
        self.assertEqual(c.art_source, 'Character credit')
        self.assertEqual(fresh.portraits()['GFX_portrait_XYZ_New'].art_source, 'Portrait credit')

    def test_portrait_pair_assignment_and_metadata_undo(self):
        original = self.world.docs.text('common/characters/people.txt')
        with self.world.docs.grouped():
            self.store.assign_portrait('BBB_Alpha', 'navy', 'GFX_portrait_AAA_Zed')
            self.store.edit_portrait('GFX_portrait_AAA_Zed', 'ABC', 'credit')
        self.world.docs.undo()
        self.assertEqual(self.world.docs.text('common/characters/people.txt'), original)
        self.assertEqual(self.store.portraits()['GFX_portrait_AAA_Zed'].tag, 'AAA')
        self.world.docs.redo()
        self.assertEqual(self.store.portraits()['GFX_portrait_AAA_Zed'].tag, 'ABC')

    def test_undo_new_character_removes_new_files_instead_of_saving_empty_files(self):
        with self.world.docs.grouped():
            self.store.edit_character('AAA_New', 'New Person', '', 'Credit', '', create=True)
        self.world.docs.undo()
        self.assertFalse(self.world.docs.changed)
        self.assertIsNone(self.world.docs.binary('common/characters/zz_painter_characters.txt'))
        self.assertIsNone(self.world.docs.binary(METADATA))
        self.world.docs.redo()
        self.assertIn('AAA_New', self.store.characters())

    def test_multiple_variants_are_independent_of_active_native_slot(self):
        self.store.link_variant('AAA_Zed', 'GFX_portrait_AAA_Animated')
        c = self.store.characters()['AAA_Zed']
        self.assertEqual(self.store.portrait_for_character(c), 'GFX_portrait_AAA_Zed')
        self.assertIn('GFX_portrait_AAA_Animated', self.store.variants('AAA_Zed'))
        self.assertIn('GFX_portrait_AAA_Zed', self.store.variants('AAA_Zed'))

    def test_replacing_animated_art_with_static_image_clears_animation_fields(self):
        self.store.edit_portrait('GFX_portrait_AAA_Animated', 'AAA', large_file=self.root / 'gfx/leaders/AAA/AAA_Zed.tga')
        entry = self.store.sprites()['GFX_portrait_AAA_Animated'][0]
        self.assertEqual(entry['node'].key, 'spriteType')
        self.assertEqual(self.store.image('GFX_portrait_AAA_Animated').size, (156, 210))

    def test_gfx_refactor_retains_extra_native_sprite_fields(self):
        text = self.world.docs.text(PORTRAIT_GFX).replace('texturefile = "gfx/leaders/AAA/AAA_Zed.tga"',
                                                         'texturefile = "gfx/leaders/AAA/AAA_Zed.tga" noOfFrames = 1')
        self.world.docs.replace(PORTRAIT_GFX, text)
        self.store.organise_gfx()
        self.assertIn('noOfFrames = 1', self.world.docs.text(PORTRAIT_GFX))

    def test_refactor_moves_exact_asset_bytes_preserves_roles_strings_and_animation(self):
        originals = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        store, audit = prepare(self.world)
        self.assertEqual(len(audit['moves']), 3)
        for move in audit['moves']:
            self.assertEqual(self.world.docs.binary(move['to']), originals[move['from']])
            self.assertIsNone(self.world.docs.binary(move['from']))
            self.assertTrue((self.root / move['from']).is_file())
        self.assertEqual(self.store.localisations()['AAA_Zed_desc'], 'Authored £icon£ $TOKEN$ [ROOT.GetName]\nDescription')
        self.assertIn('noOfFrames = 2', self.world.docs.text(PORTRAIT_GFX))
        self.assertEqual(store.image('GFX_portrait_AAA_Animated').size, (156, 210))
        self.world.docs.save()
        self.assertFalse((self.root / 'gfx/leaders/AAA/AAA_Zed.tga').exists())
        self.assertTrue((self.root / 'gfx/leaders/large_portraits/AAA/AAA_Zed.tga').is_file())
        fresh = CharacterStore(World(self.root))
        self.assertEqual(fresh.image('GFX_portrait_AAA_Animated').size, (156, 210))

    def test_binary_move_failure_rolls_back_new_files_and_deleted_originals(self):
        path = 'gfx/leaders/AAA/AAA_Zed.tga'; new = 'gfx/leaders/large_portraits/AAA/AAA_Zed.tga'
        original = self.world.docs.binary(path)
        self.world.docs.stage_bytes(new, original)
        self.world.docs.stage_bytes(path, None)
        self.world.docs.stage_bytes('gfx/leaders/small_portraits/XYZ/fail.tga', b'fixture')
        atomic = source_io.atomic_bytes
        def fail_last(destination, blob):
            if destination.name == 'fail.tga': raise OSError('fixture failure')
            atomic(destination, blob)
        with patch('source_io.atomic_bytes', side_effect=fail_last):
            with self.assertRaisesRegex(OSError, 'fixture failure'): self.world.docs.save()
        self.assertEqual((self.root / path).read_bytes(), original)
        self.assertFalse((self.root / new).exists())

    def test_ministermaker_exact_reference_pixels_and_original_border(self):
        image = Image.new('RGBA', (156, 210))
        image.putdata([((x * 3) % 256, (y * 5) % 256, ((x + y) * 7) % 256, 255)
                       for y in range(210) for x in range(156)])
        result = generate_small_portrait(image)
        self.assertEqual(result.size, (65, 67))
        # Golden pixels captured by running the supplied ministermaker.py with
        # this image and its original border; catches offset/resampling changes.
        self.assertEqual(hashlib.sha256(result.tobytes()).hexdigest(),
                         '41ca0f401dc237ace68f4f32267f7a6cc0da760ed3c543ecd784e0583fa2effa')
        self.assertEqual(hashlib.sha256(BORDER_PATH.read_bytes()).hexdigest(),
                         '6a505780b8c3cd758416393c4eb0d56195d697d6a877c3a8358f47f6d9dec0f2')

    def test_generated_small_saved_pixels_match_preview_and_keep_large(self):
        before = self.world.docs.binary('gfx/leaders/AAA/AAA_Zed.tga')
        expected = generate_small_portrait(self.store.image('GFX_portrait_AAA_Zed'))
        self.store.edit_portrait('GFX_portrait_AAA_Zed', 'AAA', generate_small=True)
        self.assertEqual(self.world.docs.binary('gfx/leaders/AAA/AAA_Zed.tga'), before)
        self.assertEqual(self.store.image('GFX_portrait_AAA_Zed_Small').tobytes(), expected.tobytes())
        self.world.docs.save()
        fresh = CharacterStore(World(self.root))
        self.assertEqual(fresh.image('GFX_portrait_AAA_Zed_Small').tobytes(), expected.tobytes())

    def test_refactor_missing_small_declaration_reuses_authored_art(self):
        text = self.world.docs.text(PORTRAIT_GFX)
        text = '\n'.join(line for line in text.splitlines() if 'GFX_portrait_AAA_Zed_Small' not in line) + '\n'
        self.world.docs.replace(PORTRAIT_GFX, text)
        original = self.world.docs.binary('gfx/interface/ministers/AAA/AAA_Zed.tga')
        store, audit = prepare(self.world)
        self.assertEqual(store.docs.binary('gfx/leaders/small_portraits/AAA/AAA_Zed.tga'), original)
        self.assertEqual(store.image('GFX_portrait_AAA_Zed_Small').getpixel((0, 0)), (120, 60, 180, 255))
        self.assertTrue(any(row['sprite'] == 'GFX_portrait_AAA_Zed_Small' for row in audit['reused_small']))

    def test_portrait_import_never_overwrites_an_unrelated_asset(self):
        with self.assertRaisesRegex(ValueError, 'three uppercase letters'):
            self.store.edit_portrait('GFX_portrait_AAA_Zed', 'A12')
        occupied = 'gfx/leaders/small_portraits/AAA/AAA_Zed.tga'
        self.world.docs.stage_bytes(occupied, b'unrelated original art')
        self.store.edit_portrait('GFX_portrait_AAA_Zed', 'AAA', generate_small=True)
        self.assertEqual(self.world.docs.binary(occupied), b'unrelated original art')
        self.assertNotEqual(self.store.portraits()['GFX_portrait_AAA_Zed'].small_path, occupied)

    def test_new_file_conflict_blocks_all_writes(self):
        self.store.edit_character('AAA_New', 'New Person', '', '', '', create=True)
        target = self.root / 'common/characters/zz_painter_characters.txt'
        target.write_text('characters = { external = { name = external } }')
        original = (self.root / CHAR_LOC).read_bytes()
        with self.assertRaisesRegex(ValueError, 'outside the painter'): self.world.docs.save()
        self.assertEqual((self.root / CHAR_LOC).read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
