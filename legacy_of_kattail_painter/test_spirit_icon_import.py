"""Own-image national spirit imports, native sprites and transactional UI behavior."""
import io
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

from character_model import CharacterStore
from country_model import CountryStore,CUSTOM_IDEAS,EAW_CREDITS,SPIRIT_ICON_SIZE
from country_ui import SpiritDialog,IconPicker,spirit_icon_preview
from demographics import MapCatalogStore
from model import World
import test_countries as fixtures


class OwnSpiritIconTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.CountryTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.root=self.fixture.root;self.world=self.fixture.world;self.store=self.fixture.store
        self.source=Path(self.fixture.fixture.tmp.name)/'portrait_Own Icon.png'
        Image.new('RGBA',(120,60),(20,100,200,255)).save(self.source);self.original=self.source.read_bytes()

    def test_import_fits_without_stretch_preserves_source_and_reuses_art_with_readable_names(self):
        key=self.store.import_spirit_icon(self.source);entry=self.store.icon_catalog()[key]
        self.assertEqual(entry['origin'],'Mod');self.assertIn(key,self.store.spirit_icon_catalog())
        self.assertEqual(entry['texture'],CUSTOM_IDEAS+'/portrait_Own_Icon.dds')
        blob=self.world.docs.binary(entry['texture'])
        with Image.open(io.BytesIO(blob)) as image:
            self.assertEqual(image.size,SPIRIT_ICON_SIZE)
            self.assertEqual(image.getpixel((30,34)),(20,100,200,255));self.assertEqual(image.getpixel((30,0))[3],0)
        self.assertEqual(self.store.import_spirit_icon(self.source),key)
        preview=spirit_icon_preview(self.store,key);self.assertIsNone(preview.crop((0,28,16,44)).getbbox())
        self.assertEqual(self.source.read_bytes(),self.original)
        Image.new('RGBA',(120,60),'red').save(self.source)
        second=self.store.import_spirit_icon(self.source)
        self.assertEqual(self.store.icon_catalog()[second]['texture'],CUSTOM_IDEAS+'/portrait_Own_Icon_2.dds')
        self.assertEqual(self.world.docs.binary(entry['texture']),blob)
        self.assertEqual(self.world.docs.text(EAW_CREDITS),'')

    def test_corrupt_image_fails_before_staging_any_changes(self):
        self.source.write_bytes(b'not an image')
        with self.assertRaises((OSError,ValueError)):self.store.import_spirit_icon(self.source)
        self.assertFalse(self.world.docs.changed);self.assertFalse(self.world.docs.undo_stack)

    def test_both_import_buttons_cancel_apply_undo_save_reload(self):
        root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('country_ui.messagebox.showerror',side_effect=AssertionError('Unexpected custom icon error')):
                dialog=SpiritDialog(root,self.store);root.update()
                with patch('country_ui.filedialog.askopenfilename',return_value=str(self.source)):dialog.import_icon()
                root.update();self.assertTrue(dialog.icon_preview.cget('image'));self.assertIn(dialog.icon.get(),self.store.spirit_icon_catalog())
                dialog.cancel();self.assertFalse(self.world.docs.changed)
                picker=IconPicker(root,self.store);root.update();picker.source_checks['Mod'].invoke()
                with patch('country_ui.filedialog.askopenfilename',return_value=''):picker.import_icon()
                self.assertFalse(self.world.docs.changed)
                with patch('country_ui.filedialog.askopenfilename',return_value=str(self.source)):picker.import_icon()
                self.assertTrue(picker.sources['Mod'].get());self.assertTrue(picker.tree.selection())
                picker.cancel();self.assertFalse(self.world.docs.changed)
                dialog=SpiritDialog(root,self.store);dialog.key.set('AAA_custom');dialog.name.set('Custom spirit')
                with patch('country_ui.filedialog.askopenfilename',return_value=str(self.source)):dialog.import_icon()
                dialog.ok();root.update();self.assertIn('AAA_custom',self.store.ideas())
                self.world.docs.undo();self.assertFalse(self.world.docs.changed)
                self.world.docs.redo();self.world.docs.save()
                world=World(self.root);characters=CharacterStore(world);store=CountryStore(world,characters,MapCatalogStore(world,characters))
                self.assertEqual(store.icon_catalog()['GFX_idea_AAA_custom']['origin'],'Mod')
                self.assertIsNotNone(store.icon_image('GFX_idea_AAA_custom'))
                self.assertFalse((self.root/EAW_CREDITS).exists());self.assertEqual(self.source.read_bytes(),self.original)
                self.assertFalse(errors)
        finally:root.update_idletasks();root.destroy()


if __name__=='__main__':unittest.main()
