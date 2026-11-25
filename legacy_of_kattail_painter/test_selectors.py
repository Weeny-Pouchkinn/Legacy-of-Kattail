"""Localized selection, cache coherence and Tk interaction regressions."""
import tkinter as tk
import unittest
from unittest.mock import patch
import io

from PIL import Image

import test_characters as character_tests
import character_model
from character_model import CharacterStore, CHAR_LOC
from select_ui import Choice, ChoiceIndex, ChoiceBox, TraitChoices
from character_ui import CharacterDialog, RoleDialog


class IndexTests(unittest.TestCase):
    def test_names_codes_accents_alphabetic_and_near_matches(self):
        values = [Choice('trait_harsh_leader', 'Harsh Leader'), Choice('LAU', 'Laurandar'),
                  Choice('ZZZ', 'Éclair'), Choice('ABC', 'Alpha')]
        index = ChoiceIndex(values)
        self.assertEqual([c.code for c in index.matching()], ['ABC', 'ZZZ', 'trait_harsh_leader', 'LAU'])
        for query in ('Harsh', 'trait_harsh', 'HARSH LEADER'):
            self.assertEqual(index.matching(query)[0].code, 'trait_harsh_leader')
        self.assertEqual(index.matching('eclair')[0].code, 'ZZZ')
        self.assertEqual(index.matching('Laurandr')[0].code, 'LAU')
        self.assertEqual(index.preferred('Laurandr', index.matching('Laurandr')), 'LAU')
        self.assertEqual(index.resolve('Laurandar (LAU)'), 'LAU')
        self.assertEqual(index.resolve('Laurandar'), 'LAU')
        self.assertEqual(index.resolve('lau'), 'LAU')
        self.assertEqual(index.by_code['LAU'].label, 'Laurandar (LAU)')


# Bind the fixture functions without inheriting its test methods.
class StoreCacheTests(unittest.TestCase):
    setUp = character_tests.CharacterTests.setUp
    tearDown = character_tests.CharacterTests.tearDown

    def test_stat_edit_retains_localisation_sprites_traits_and_unchanged_parses(self):
        people = self.store.characters(); loc = self.store.loc_records()
        sprites = self.store.sprites(); traits = self.store.trait_ids()
        with patch.object(character_model, 'parse', wraps=character_model.parse) as parser:
            self.store.edit_role('AAA_Zed', 1, 'country_leader', {'ideology': 'updated', 'expire': '"1970.1.1"'}, [])
            self.assertEqual(self.store.characters()['AAA_Zed'].roles[1].key, 'country_leader')
            self.assertLess(parser.call_count, 12)
        self.assertIs(self.store.loc_records(), loc)
        self.assertIs(self.store.sprites(), sprites)
        self.assertIs(self.store.trait_ids(), traits)
        self.assertIsNot(self.store.characters(), people)

    def test_localized_choices_follow_edit_undo_redo_and_cancel(self):
        before = self.store.choices('countries')
        path = 'localisation/english/other_l_english.yml'
        self.world.docs.replace(path, self.world.docs.text(path).replace('Neutral A', 'Aardvark Nation'))
        self.assertEqual(self.store.choices('countries')[0].label, 'Aardvark Nation (AAA)')
        self.world.docs.undo()
        self.assertEqual(self.store.choices('countries'), before)
        self.world.docs.redo()
        self.assertEqual(self.store.choices('countries')[0].name, 'Aardvark Nation')
        self.world.docs.reset()
        self.assertEqual(self.store.choices('countries'), before)

    def test_decoded_images_survive_stat_edits_but_follow_binary_undo(self):
        with patch.object(Image, 'open', wraps=Image.open) as opened:
            first = self.store.image('GFX_portrait_AAA_Zed')
            self.store.image('GFX_portrait_AAA_Zed')
            self.store.edit_role('AAA_Zed', 1, 'country_leader', {'ideology': 'updated'}, [])
            self.store.image('GFX_portrait_AAA_Zed')
            self.assertEqual(opened.call_count, 1)
        output = io.BytesIO(); Image.new('RGBA', first.size, 'red').save(output, format='TGA')
        self.world.docs.stage_bytes('gfx/leaders/AAA/AAA_Zed.tga', output.getvalue())
        self.assertEqual(self.store.image('GFX_portrait_AAA_Zed').getpixel((0, 0)), (255, 0, 0, 255))
        self.world.docs.undo()
        self.assertEqual(self.store.image('GFX_portrait_AAA_Zed').tobytes(), first.tobytes())
        first.putpixel((0, 0), (0, 0, 0, 0))
        self.assertNotEqual(self.store.image('GFX_portrait_AAA_Zed').getpixel((0, 0)), (0, 0, 0, 0))

    def test_new_file_remains_indexed_after_save_and_deletion_invalidates(self):
        self.store.characters()
        self.store.edit_character('AAA_New', 'New', '', '', '', create=True)
        self.world.docs.save()
        self.assertIn('AAA_New', self.store.characters())
        self.world.docs.stage_bytes('common/characters/zz_painter_characters.txt', None)
        self.assertNotIn('AAA_New', self.store.characters())
        self.world.docs.undo()
        self.assertIn('AAA_New', self.store.characters())

    def test_same_localized_country_names_keep_separate_alphabetical_groups(self):
        path = 'localisation/english/other_l_english.yml'
        text = self.world.docs.text(path).replace('Neutral A', 'Same Name').replace('Neutral B', 'Same Name')
        self.world.docs.replace(path, text)
        self.store.set_recruitment('BBB_Alpha', 'BBB')
        self.assertEqual([c.key for c in self.store.ordered(by_nation=True)], ['AAA_Zed', 'BBB_Alpha'])
        index = ChoiceIndex(self.store.choices('countries'))
        self.assertIsNone(index.resolve('Same Name'))
        self.assertEqual(index.resolve('Same Name (AAA)'), 'AAA')


class TkChoiceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = character_tests.CharacterTests(); self.fixture.setUp()
        self.root = tk.Tk(); self.root.attributes('-alpha', 0)
        self.errors = []
        self.root.report_callback_exception = lambda *error: self.errors.append(error)

    def tearDown(self):
        self.root.destroy(); self.fixture.tearDown()
        self.assertEqual(self.errors, [])

    def test_typing_suggestions_keyboard_cancel_and_code_only_binding(self):
        variable = tk.StringVar(value='AAA')
        box = ChoiceBox(self.root, textvariable=variable, values=[Choice('AAA', 'Zulu'), Choice('LAU', 'Laurandar'), Choice('ALP', 'A Laurandar Neighbour')])
        box.pack(); self.root.update()
        box.display.set('laur'); box.show(box.display.get())
        self.assertIn('Laurandar (LAU)', box.listbox.get(0, 'end'))
        self.assertEqual(variable.get(), 'AAA')
        box.show('LAU'); box.enter(); self.assertEqual(variable.get(), 'LAU')
        self.assertEqual(box.display.get(), 'Laurandar (LAU)')
        box.display.set('Zulu'); box.commit(); self.assertEqual(variable.get(), 'AAA')
        box.show('LAU'); box.escape(); self.assertEqual(variable.get(), 'AAA')
        box.display.set('not a valid ID'); box.commit(); self.assertEqual(variable.get(), 'AAA')
        box.configure(values=[Choice('XYZ', 'New Nation')]); box.set('XYZ')
        self.assertEqual(box.display.get(), 'New Nation (XYZ)')
        box.destroy(); self.root.update()

    def test_all_choices_scroll_and_traits_keep_ids(self):
        values = [Choice('t' + str(i), 'Trait ' + str(i)) for i in range(250)]
        variable = tk.StringVar(value='t1 t2')
        widget = TraitChoices(self.root, variable, values); widget.pack(); self.root.update()
        widget.picker.show(''); self.assertEqual(widget.picker.listbox.size(), 250)
        widget.picker.show('t99'); widget.picker.choose()
        self.assertEqual(variable.get(), 't1 t2 t99')
        widget.listbox.selection_set(widget.selected.index('t2')); widget.remove()
        self.assertEqual(variable.get(), 't1 t99')

    def test_text_color_picker_case_sensitive_codes_paste_and_live_preview(self):
        from select_ui import TextColorPicker
        colors={'B':{'name':'Blue','color':(0,0,255)},'b':{'name':'Black','color':(0,0,0)},'h':{'name':'Thalothin','color':(255,255,183)}}
        variable=tk.StringVar(value='B');sample=tk.StringVar(value='Example name');picker=TextColorPicker(self.root,colors,variable,sample);picker.pack(fill='x');self.root.update()
        self.assertEqual(picker.preview.cget('foreground'),'#0000ff')
        self.root.clipboard_clear();self.root.clipboard_append('b');picker.box.entry.delete(0,'end');picker.box.entry.event_generate('<<Paste>>');self.root.update()
        self.assertEqual(picker.preview.cget('foreground'),'#000000');picker.commit();self.assertEqual(variable.get(),'b')
        variable.set('h');sample.set('Changed name');self.assertEqual(picker.swatch.cget('background'),'#ffffb7');self.assertEqual(picker.preview.cget('text'),'Changed name')
        picker.box.show('');self.assertEqual(picker.box.listbox.size(),4)
        row=next(i for i,c in enumerate(picker.box._matches) if c.code=='h');self.assertEqual(picker.box.listbox.itemcget(row,'background'),'#ffffb7')
        picker.box.display.set('Unknown');self.assertIn('Unknown',picker.preview.cget('text'));variable.set('');self.assertIn('default',picker.preview.cget('text'))
        picker.destroy();self.root.update()

    def test_unchanged_identity_never_calls_editor_and_nested_cancel_restores(self):
        s = self.fixture.store
        dialog = CharacterDialog(self.root, s, 'AAA_Zed'); self.root.update()
        with patch.object(s, 'edit_character', wraps=s.edit_character) as edit:
            self.assertTrue(dialog.apply_identity()); self.assertTrue(dialog.apply_identity())
            edit.assert_not_called()
        dialog.country_box.display.set('Neutral B'); dialog.apply_identity()
        self.assertEqual(s.characters()['AAA_Zed'].countries, ('BBB',))
        dialog.cancel(); self.assertEqual(s.characters()['AAA_Zed'].countries, ('AAA',))
        self.assertFalse(s.docs.changed)
        dialog = RoleDialog(self.root, s, 'AAA_Zed', 1); self.root.update()
        dialog.variables['ideology'].set('updated'); dialog.ok(); self.root.update()
        self.assertIn('ideology = updated', s.characters()['AAA_Zed'].text)


if __name__ == '__main__':
    unittest.main()
