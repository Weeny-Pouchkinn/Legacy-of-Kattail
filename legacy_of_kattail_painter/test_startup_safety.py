"""Save-time regressions for engine errors exposed by the current startup log."""
import io
import unittest
from types import SimpleNamespace

from PIL import Image

from country_model import CountryStore
from model import Documents, FLAG_SIZES, World
import test_painter as fixtures


class StartupSaveTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.FixtureTests()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.write('history/countries/AAA.txt', 'capital = 1\n')
        self.write('history/countries/BBB.txt', 'capital = 2\n')
        self.world = World(self.root)

    def tearDown(self):
        self.fixture.tearDown()

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding='utf-8-sig' if path.suffix == '.yml' else 'utf-8')

    def two_states_for_aaa(self):
        path = self.root/'history/states/two.txt'
        path.write_text(path.read_text().replace('owner = BBB', 'owner = AAA'))
        self.world = World(self.root)

    def test_owner_brush_cannot_save_a_foreign_capital(self):
        self.two_states_for_aaa()
        path = self.root/'history/states/one.txt'
        before = path.read_bytes()
        self.world.set_owner_draft(1, 'BBB')
        with self.assertRaisesRegex(ValueError, 'AAA no longer owns capital state 1'):
            self.world.docs.save()
        self.assertEqual(path.read_bytes(), before)

    def test_capital_can_be_reassigned_in_the_same_transaction(self):
        self.two_states_for_aaa()
        self.world.set_owner_draft(1, 'BBB')
        self.world.docs.replace('history/countries/AAA.txt', 'capital = 2\n')
        self.world.docs.replace('history/countries/BBB.txt', 'capital = 1\n')
        self.world.docs.save()
        loaded = World(self.root)
        self.assertEqual(loaded.states[1].owner, 'BBB')
        self.assertEqual(loaded.states[2].owner, 'AAA')

    def test_raw_country_edit_cannot_save_a_foreign_capital(self):
        self.world.docs.replace('history/countries/AAA.txt', 'capital = 2\n')
        with self.assertRaisesRegex(ValueError, 'owned capital'):
            self.world.docs.save()
        self.assertEqual((self.root/'history/countries/AAA.txt').read_text(), 'capital = 1\n')

    def test_painter_save_hook_runs_the_capital_guard(self):
        from painter import Painter
        self.two_states_for_aaa()
        self.world.set_owner_draft(1, 'BBB')
        noop = lambda: None
        app = SimpleNamespace(
            world=self.world, geography_store=SimpleNamespace(validate_save=noop),
            imperium_store=SimpleNamespace(validate_save=noop),
            railway_store=SimpleNamespace(prepare_save=noop),
            character_store=SimpleNamespace(prepare_save=noop))
        with self.assertRaisesRegex(ValueError, 'owned capital'):
            Painter.prepare_save(app)

    def test_dormant_country_may_keep_a_nominal_capital(self):
        self.world.set_owner_draft(1, 'BBB')
        self.world.docs.save()
        self.assertEqual(World(self.root).states[1].owner, 'BBB')

    def test_undo_owner_paint_restores_save_validity(self):
        self.two_states_for_aaa()
        self.world.set_owner_draft(1, 'BBB')
        self.world.docs.undo()
        self.world.validate_capitals()

    def test_cross_file_localisation_collision_fails_before_writing(self):
        self.write('localisation/english/first_l_english.yml', 'l_english:\n KEY:0 "Authored"\n')
        docs = Documents(self.root)
        docs.replace('localisation/english/second_l_english.yml', 'l_english:\n KEY:0 "Other"\n')
        with self.assertRaisesRegex(ValueError, 'Duplicate localisation key KEY'):
            docs.save()
        self.assertFalse((self.root/'localisation/english/second_l_english.yml').exists())

    def test_intentional_replace_layer_and_bom_survive(self):
        self.write('localisation/english/first_l_english.yml', 'l_english:\n KEY:0 "Authored"\n')
        docs = Documents(self.root)
        path = 'localisation/english/replace/override_l_english.yml'
        docs.replace(path, 'l_english:\n KEY:0 "Override"\n')
        docs.save()
        self.assertTrue((self.root/path).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_collision_check_reads_external_changes_to_untouched_files(self):
        path = 'localisation/english/first_l_english.yml'
        self.write(path, 'l_english:\n ORIGINAL:0 "Authored"\n')
        docs = Documents(self.root)
        docs.text(path)
        self.write(path, 'l_english:\n KEY:0 "Edited elsewhere"\n')
        docs.replace('localisation/english/second_l_english.yml', 'l_english:\n KEY:0 "Other"\n')
        with self.assertRaisesRegex(ValueError, 'Duplicate localisation key KEY'):
            docs.save()

    def test_replacing_an_existing_value_does_not_create_a_collision(self):
        path = 'localisation/english/first_l_english.yml'
        self.write(path, 'l_english:\n KEY:0 "Authored"\n')
        docs = Documents(self.root)
        docs.replace(path, 'l_english:\n KEY:0 "Edited"\n')
        docs.save()
        self.assertIn('Edited', (self.root/path).read_text(encoding='utf-8-sig'))

    def test_undone_localisation_creation_does_not_block_another_save(self):
        docs = Documents(self.root)
        ghost = 'localisation/english/undone_l_english.yml'
        docs.replace(ghost, 'l_english:\n KEY:0 "Undone"\n')
        docs.undo()
        active = 'localisation/english/active_l_english.yml'
        docs.replace(active, 'l_english:\n KEY:0 "Saved"\n')
        docs.save()
        self.assertFalse((self.root/ghost).exists())
        self.assertTrue((self.root/active).is_file())

    def test_header_must_remain_on_the_first_line(self):
        with self.assertRaisesRegex(ValueError, 'header'):
            Documents.validate_text('localisation/english/test.yml', '\nl_english:\n KEY:0 "Text"\n')

    def test_flag_writer_uses_32_bits_and_preserves_pixels_at_all_sizes(self):
        store = CountryStore(self.world, None, None)
        store.ideologies = lambda: {'democratic': {}}
        for mode, color in [('RGB', (17, 93, 201)), ('RGBA', (17, 93, 201, 0))]:
            store.write_flag('AAA', 'democratic', Image.new(mode, (82, 52), color))
            for size, dimensions in FLAG_SIZES.items():
                blob = self.world.docs.binary(store.flag_path('AAA', 'democratic', size))
                self.assertEqual(blob[16], 32)
                with Image.open(io.BytesIO(blob)) as image:
                    self.assertEqual(image.size, dimensions)
                    self.assertEqual(image.getpixel((0, 0)), (17, 93, 201, 255))


if __name__ == '__main__':
    unittest.main()
