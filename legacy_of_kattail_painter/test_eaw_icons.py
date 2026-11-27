"""EaW source catalog, attribution UI and atomic native import/credit records."""
import hashlib
import importlib.util
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

from character_model import CharacterStore
from country_model import CountryStore,EAW_IDEAS,EAW_TEXTURES,EAW_CREDITS,IDEAS
from country_ui import IconPicker,SpiritDialog,spirit_icon_preview
from demographics import MapCatalogStore
from model import World
import test_countries as country_fixtures


class EawIconTests(unittest.TestCase):
    def setUp(self):
        self.fixture=country_fixtures.CountryTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.root=self.fixture.root;self.world=self.fixture.world;self.store=self.fixture.store
        self.paths={}
        for relative,size in [('EQS/royal_guard.dds',(60,60)),('GRF/royal_guard.tga',(60,60)),
                              ('generic_political_advisor_test.dds',(60,60)),('minister_plain.dds',(65,67))]:
            path=self.root/EAW_IDEAS/relative;path.parent.mkdir(parents=True,exist_ok=True)
            Image.new('RGBA',size,(12,34,56,255)).save(path);self.paths[relative]=path
        (self.root/EAW_IDEAS/'unused.psd').write_bytes(b'not a supported game texture')

    def apply(self,key='AAA_eaw',icon='eaw:EQS/royal_guard.dds',create=True):
        self.store.edit_spirit(key,'Guard spirit','Authored description',icon,{'test_modifier':'.1'},create)

    def test_recursive_catalog_duplicate_names_portrait_filter_and_unmodified_preview(self):
        catalog=self.store.icon_catalog()
        self.assertIn('eaw:EQS/royal_guard.dds',catalog);self.assertIn('eaw:GRF/royal_guard.tga',catalog)
        self.assertNotIn('eaw:unused.psd',catalog)
        self.assertEqual(catalog['eaw:EQS/royal_guard.dds']['origin'],'EaW')
        choices=self.store.spirit_icon_catalog()
        self.assertNotIn('eaw:minister_plain.dds',choices)
        self.assertNotIn('eaw:generic_political_advisor_test.dds',choices)
        preview=self.store.icon_image('eaw:EQS/royal_guard.dds')
        self.assertEqual(preview.getpixel((2,2)),(12,34,56,255))
        self.assertEqual(self.store.import_spirit_icon(self.paths['EQS/royal_guard.dds']),'eaw:EQS/royal_guard.dds')
        self.assertFalse(self.world.docs.changed)

    def test_apply_undo_redo_save_reload_and_exact_asset_credits(self):
        credit=self.root/EAW_CREDITS;credit.parent.mkdir(parents=True,exist_ok=True)
        authored='EaW Credits\r\n\r\nExisting human note {keep this} "quoted"\r\n'
        credit.write_bytes(authored.encode('utf-8-sig'))
        asset=self.paths['EQS/royal_guard.dds'].read_bytes()
        destination=EAW_TEXTURES+'/royal_guard.dds'
        self.apply()
        self.assertEqual(self.world.docs.binary(destination),asset)
        self.assertFalse((self.root/destination).exists())
        credits=self.world.docs.text(EAW_CREDITS)
        self.assertIn('EaW path: gfx\\interface\\ideas\\EQS\\royal_guard.dds',credits)
        self.assertIn('Asset: royal_guard.dds',credits);self.assertIn('Used for: National spirit AAA_eaw (Guard spirit)',credits)
        self.assertIn('Existing human note {keep this} "quoted"',credits)
        self.world.docs.undo();self.assertNotIn('AAA_eaw',self.store.ideas())
        self.assertIsNone(self.world.docs.binary(destination));self.assertEqual(self.world.docs.text(EAW_CREDITS),authored)
        self.world.docs.redo();self.assertEqual(self.world.docs.binary(destination),asset)
        self.world.docs.save()
        self.assertEqual((self.root/destination).read_bytes(),asset)
        self.assertEqual(self.paths['EQS/royal_guard.dds'].read_bytes(),asset)
        self.assertTrue(credit.read_bytes().startswith(b'\xef\xbb\xbf'))
        world=World(self.root);characters=CharacterStore(world)
        store=CountryStore(world,characters,MapCatalogStore(world,characters))
        entry=store.icon_catalog()['GFX_idea_AAA_eaw']
        self.assertEqual(entry['origin'],'EaW');self.assertEqual(entry['eaw_asset'],'EQS/royal_guard.dds')
        self.assertEqual(entry['texture'],destination)
        with patch.object(store,'eaw_icon_catalog',return_value={}):
            self.assertEqual(store.icon_catalog()['GFX_idea_AAA_eaw']['eaw_asset'],'EQS/royal_guard.dds')
            self.assertIsNotNone(store.icon_image('GFX_idea_AAA_eaw'))
        store.edit_spirit('AAA_eaw','Guard spirit','Authored description','GFX_idea_AAA_eaw',{'test_modifier':'.1'})
        self.assertEqual(world.docs.text(EAW_CREDITS).count('Used for: National spirit AAA_eaw'),1)
        store.edit_spirit('AAA_second','Second use','', 'eaw:EQS/royal_guard.dds',{},True)
        self.assertIn('Used for: National spirit AAA_second (Second use)',world.docs.text(EAW_CREDITS))
        self.assertEqual(world.docs.binary(destination),asset)

    def test_missing_source_rolls_back_and_existing_art_gets_a_readable_collision_suffix(self):
        self.store.icon_catalog();path=self.paths['EQS/royal_guard.dds'];asset=path.read_bytes();path.unlink()
        with self.assertRaisesRegex(ValueError,'missing'):self.apply()
        self.assertFalse(self.world.docs.changed);self.assertEqual(self.world.docs.text(EAW_CREDITS),'')
        path.write_bytes(asset)
        destination=self.root/EAW_TEXTURES/'royal_guard.dds'
        destination.parent.mkdir(parents=True);destination.write_bytes(b'handwritten existing art')
        # Missing-source reads are snapshots; a fresh store sees the restored art.
        world=World(self.root);characters=CharacterStore(world)
        self.store=CountryStore(world,characters,MapCatalogStore(world,characters))
        self.apply()
        self.assertEqual(destination.read_bytes(),b'handwritten existing art')
        self.assertEqual(world.docs.binary(EAW_TEXTURES+'/royal_guard_2.dds'),asset)
        self.assertIn('Mod texture: '+EAW_TEXTURES+'/royal_guard_2.dds',world.docs.text(EAW_CREDITS))

    def test_same_basename_imports_keep_per_spirit_source_and_reuse_identical_bytes(self):
        for folder,color in [('AAA','red'),('BBB','blue')]:
            path=self.root/EAW_IDEAS/folder/'shared.tga';path.parent.mkdir()
            Image.new('RGBA',(60,60),color).save(path)
        self.apply('AAA_first','eaw:AAA/shared.tga');self.apply('AAA_second','eaw:BBB/shared.tga')
        self.apply('AAA_third','eaw:BBB/shared.tga')
        self.world.docs.save();world=World(self.root);characters=CharacterStore(world)
        store=CountryStore(world,characters,MapCatalogStore(world,characters));icons=store.icon_catalog()
        for key,asset,filename in [('AAA_first','AAA/shared.tga','shared.tga'),('AAA_second','BBB/shared.tga','shared_2.tga'),('AAA_third','BBB/shared.tga','shared_2.tga')]:
            self.assertEqual(icons['GFX_idea_'+key]['eaw_asset'],asset)
            self.assertEqual(icons['GFX_idea_'+key]['texture'],EAW_TEXTURES+'/'+filename)
        self.assertFalse((self.root/EAW_TEXTURES/'shared_3.tga').exists())

    def migration_module(self):
        spec=importlib.util.spec_from_file_location('flatten_eaw_icons_test',Path(__file__).resolve().parents[1]/'tools/flatten_eaw_icons.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def test_flatten_saved_legacy_paths_credits_guarded_writes_and_idempotence(self):
        asset=self.paths['EQS/royal_guard.dds'].read_bytes()
        old=EAW_TEXTURES+'/'+hashlib.sha256(asset).hexdigest()[:16]+'/EQS/royal_guard.dds'
        oldfile=self.root/old;oldfile.parent.mkdir(parents=True);oldfile.write_bytes(asset)
        script=self.root/'interface/lok_ideas.gfx'
        original=script.read_text()+'\n# Keep this historical note: '+old+'\n'
        original=original.replace('gfx/interface/ideas/native.dds',old);script.write_text(original)
        credit=self.root/EAW_CREDITS;credit.parent.mkdir(parents=True)
        credits='EaW Credits\r\n\r\nAsset: royal_guard.dds\r\nEaW path: gfx\\interface\\ideas\\EQS\\royal_guard.dds\r\nUsed for: National spirit native (Old native)\r\nMod texture: '+old+'\r\n'
        credit.write_bytes(credits.encode('utf-8-sig'))
        module=self.migration_module();changes,report=module.build(self.root)
        self.assertEqual(report['migrated_textures'],1);self.assertTrue(report['credits_updated'])
        from source_io import write_changes
        # A changed reference blocks the entire batch before the new texture is written.
        script.write_text(original+'# concurrent human change\n')
        with self.assertRaisesRegex(ValueError,'changed outside'):write_changes(self.root,changes,label='eaw_flat_fixture')
        flat=self.root/EAW_TEXTURES/'royal_guard.dds';self.assertFalse(flat.exists());self.assertTrue(oldfile.exists())
        script.write_text(original)
        import sys
        with patch.object(sys,'argv',['flatten_eaw_icons.py','--root',str(self.root),'--apply','--report',str(self.root/'audit.json')]),patch('builtins.print'):
            module.main()
        self.assertEqual(flat.read_bytes(),asset);self.assertFalse(oldfile.exists());self.assertFalse(oldfile.parent.parent.exists())
        self.assertIn('texturefile = "'+EAW_TEXTURES+'/royal_guard.dds"',script.read_text())
        self.assertIn('# Keep this historical note: '+old,script.read_text())
        self.assertEqual(credit.read_bytes(),credits.replace(old,EAW_TEXTURES+'/royal_guard.dds').encode('utf-8-sig'))
        self.assertEqual(module.build(self.root)[1]['changed_files'],0)
        world=World(self.root);characters=CharacterStore(world);store=CountryStore(world,characters,MapCatalogStore(world,characters))
        self.assertEqual(store.icon_catalog()['GFX_idea_native']['eaw_asset'],'EQS/royal_guard.dds')

    def test_migration_rejects_dangling_nested_references(self):
        script=self.root/'interface/lok_ideas.gfx'
        script.write_text(script.read_text().replace('gfx/interface/ideas/native.dds',EAW_TEXTURES+'/missing/CTL/absent.tga'))
        with self.assertRaisesRegex(ValueError,'Unresolved nested'):self.migration_module().build(self.root)

    def test_badge_filters_selection_and_parent_cancel_are_ui_only(self):
        root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('country_ui.messagebox.showerror',side_effect=AssertionError('Unexpected EaW dialog error')):
                dialog=SpiritDialog(root,self.store);root.update()
                picker=IconPicker(dialog,self.store);root.update()
                all_rows=set(picker.tree.get_children());self.assertIn('eaw:EQS/royal_guard.dds',all_rows)
                for source in ('Mod','Vanilla'):picker.source_checks[source].invoke()
                only_eaw=set(picker.tree.get_children());self.assertTrue(only_eaw)
                self.assertTrue(all(self.store.icon_catalog()[k]['origin']=='EaW' for k in only_eaw))
                picker.source_checks['EaW'].invoke();self.assertEqual(picker.tree.get_children(),())
                with patch('country_ui.filedialog.askopenfilename',return_value=str(self.paths['EQS/royal_guard.dds'])):picker.import_icon()
                self.assertTrue(picker.sources['EaW'].get());self.assertEqual(picker.tree.selection(),('eaw:EQS/royal_guard.dds',))
                picker.source_checks['EaW'].invoke()
                picker.source_checks['Vanilla'].invoke()
                self.assertTrue(all(k.startswith('vanilla:') for k in picker.tree.get_children()))
                picker.source_checks['EaW'].invoke();picker.query.set('royal');picker.refresh()
                picker.tree.selection_set('eaw:EQS/royal_guard.dds');picker.ok();dialog.grab_set()
                self.assertEqual(picker.result,'eaw:EQS/royal_guard.dds')
                dialog.icon_box.set(picker.result);dialog.key.set('AAA_eaw_cancel');dialog.name.set('Cancelled use')
                preview=spirit_icon_preview(self.store,picker.result)
                self.assertEqual(preview.size,(60,44))
                self.assertTrue(preview.crop((0,28,16,44)).getbbox())
                self.assertEqual(preview.getpixel((22,2)),(12,34,56,255))
                native=spirit_icon_preview(self.store,'GFX_idea_native')
                self.assertIsNone(native.crop((0,28,16,44)).getbbox())
                self.assertEqual(self.store.icon_image(picker.result).getpixel((2,2)),(12,34,56,255))
                dialog.cancel();self.assertFalse(self.world.docs.changed)
                self.assertEqual(self.world.docs.text(EAW_CREDITS),'')
                # Accepting a spirit stages credits; cancelling an outer editor restores all drafts.
                from character_ui import DraftDialog
                outer=DraftDialog(root,self.fixture.characters,'Outer editor')
                accepted=SpiritDialog(outer,self.store);accepted.key.set('AAA_eaw');accepted.name.set('Guard spirit')
                accepted.icon_box.set('eaw:EQS/royal_guard.dds');accepted.ok();root.update()
                self.assertIn('AAA_eaw',self.world.docs.text(EAW_CREDITS))
                outer.cancel();self.assertFalse(self.world.docs.changed)
                self.assertFalse(errors)
        finally:root.update_idletasks();root.destroy()

    def test_installer_keeps_library_hierarchy_badge_and_credits(self):
        from install import install
        package=self.root/'legacy_of_kattail_painter';(package/'painter.py').write_text('# disposable fixture\n')
        badge=package/'assets/eaw_sun.png';badge.write_bytes(b'fixture badge copy')
        credit=self.root/EAW_CREDITS;credit.parent.mkdir(exist_ok=True);credit.write_text('EaW Credits\n')
        destination=self.root/'another_mod';destination.mkdir();(destination/'descriptor.mod').write_text('name="test"')
        with patch('install.FILES',['painter.py','assets/eaw_sun.png']):installed=install(destination,package=package)
        self.assertEqual((installed/'assets/eaw_ideas/EQS/royal_guard.dds').read_bytes(),self.paths['EQS/royal_guard.dds'].read_bytes())
        self.assertEqual((installed/'assets/eaw_sun.png').read_bytes(),badge.read_bytes())
        self.assertEqual((installed/'credits/EaW Credits.txt').read_bytes(),credit.read_bytes())


if __name__=='__main__':unittest.main()
