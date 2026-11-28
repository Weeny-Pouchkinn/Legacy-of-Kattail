"""Native land templates, isolated shared OOB edits, names and actual map UI."""
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import patch

import numpy as np

import test_geography
from character_model import CharacterStore
from demographics import Setup,MapCatalogStore,CATALOG_PATHS
from geography_model import GeographyStore
from land_oob_model import LandOobStore,ordinal,SHORT_MARKER
from model import World,Emblems,parse
from map_render import MapConfig,MapRenderer


class LandOobTests(unittest.TestCase):
    def setUp(self):
        self.f=test_geography.GeographyTests();self.f.setUp();self.addCleanup(self.f.tearDown);self.root=self.f.root;self.write=self.f.write
        tags='common/country_tags/tags.txt';self.write(tags,(self.root/tags).read_text()+'\nCCC = "countries/CCC.txt"')
        self.write('history/countries/AAA.txt','capital = 1\noob = "shared"\nset_popularities = { neutrality = 100 }\n1939.1.1 = { set_stability = .5 }\n')
        self.write('history/countries/BBB.txt','capital = 2\nset_oob = "shared"\n')
        self.write('history/countries/CCC.txt','capital = 1\n')
        self.write('history/units/shared.txt','''# Keep OOB header
division_template = {
    # LOK_PAINTER_SHORT_NAME = "Regulars"
    name = "Infantry"
    priority = 2
    is_locked = yes
    mystery = { authored = yes }
    regiments = {
        infantry = { x = 0 y = 0 custom = yes } # battalion note
        infantry = { x = 0 y = 1 }
    }
    support = { engineer = { x = 0 y = 0 } }
}
units = {
    division = { name = "Authored \\"Guard\\"" location = 1 division_template = "Infantry" start_experience_factor = .4 officer = { name = OFFICER } }
    division = { division_name = { is_name_ordered = yes name_order = 12 } location = 3 division_template = "Infantry" force_equipment_variants = { infantry_equipment_0 = { owner = AAA } } }
    fleet = { name = "Keep fleet" naval_base = 1 }
}
instant_effect = { add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 10 } }
''')
        self.write('common/units/land.txt','''sub_units = {
            infantry = { group = infantry map_icon_category = infantry }
            artillery_brigade = { group = infantry map_icon_category = infantry }
            cavalry = { group = mobile map_icon_category = infantry }
            engineer = { group = support }
            artillery = { group = support }
        }''')
        self.write('common/units/names_divisions/fragment.txt','not_a_subunit = {')
        self.world=World(self.root);self.world.demographics=Setup(self.world).load()
        self.world.map_ids=np.tile(np.array([1]*20+[3]*20+[2]*20+[4]*20,dtype=np.int32),(40,1))
        self.c=CharacterStore(self.world);self.c.game_root=self.f.c.game_root;self.catalog=MapCatalogStore(self.world,self.c)
        self.g=GeographyStore(self.world,self.c,self.catalog);self.s=LandOobStore(self.world,self.c)
        self.world.docs.before_save=self.s.validate_save

    def test_existing_shared_templates_divisions_escaped_names_global_counts_without_drafts(self):
        self.assertEqual(self.s.templates('AAA')['Infantry'].short,'Regulars')
        self.assertEqual(self.s.divisions('AAA')[0].name,'Authored "Guard"')
        self.assertEqual(self.s.counts('AAA','Infantry'),{1:1,3:1})
        self.assertEqual(self.s.counts(global_view=True),{1:2,3:2})
        self.assertEqual(self.s.divisions('CCC'),[]);self.assertFalse(self.world.docs.changed)
        self.assertIn('cavalry',self.s.subunits())

    def test_place_isolates_shared_source_generated_ordinals_and_undo_redo_save_reload(self):
        original=(self.root/'history/units/shared.txt').read_bytes()
        names=self.s.place('AAA','Infantry',1,2)
        self.assertEqual(names,['3rd First state Regulars','4th First state Regulars'])
        self.assertNotEqual(self.s.source('AAA').path,self.s.source('BBB').path)
        self.assertEqual(len(self.s.divisions('BBB')),2);self.assertEqual(self.s.counts('AAA'),{1:3,3:1})
        private=self.world.docs.text(self.s.source('AAA').path)
        self.assertIn('Keep fleet',private);self.assertIn('instant_effect',private);self.assertEqual((self.root/'history/units/shared.txt').read_bytes(),original)
        self.world.docs.undo();self.assertEqual(self.s.source('AAA').path,'history/units/shared.txt');self.world.docs.redo()
        self.world.docs.save();fresh=World(self.root);s=LandOobStore(fresh,CharacterStore(fresh))
        self.assertEqual(s.counts('AAA'),{1:3,3:1});self.assertEqual((self.root/'history/units/shared.txt').read_bytes(),original)

    def test_template_create_copy_rename_links_preserves_cells_comments_and_other_oob_content(self):
        self.s.copy_template('AAA','Infantry','CCC',new_name='Copied infantry',short='Guards')
        copy=self.s.templates('CCC')['Copied infantry'];self.assertEqual(copy.short,'Guards');self.assertIn('mystery',copy.raw)
        self.assertIn('# battalion note',copy.raw);self.assertIn('custom = yes',copy.raw)
        self.assertEqual(self.s.divisions('CCC'),[]);self.assertIn('oob =',self.world.docs.text(self.world.countries['CCC']))
        self.s.place('CCC','Copied infantry',2)
        self.s.edit_template('CCC','Renamed','Regulars',[('artillery_brigade',0,0),('infantry',0,1)],copy.support,'Copied infantry')
        self.assertEqual(self.s.divisions('CCC')[0].template,'Renamed');self.assertIn('custom = yes',self.s.templates('CCC')['Renamed'].raw)
        self.assertIn('# battalion note',self.s.templates('CCC')['Renamed'].raw)
        self.assertEqual(self.s.divisions('CCC')[0].name,'1st Second state Guards')
        self.assertEqual(ordinal(11),'11th');self.assertEqual(ordinal(12),'12th');self.assertEqual(ordinal(13),'13th');self.assertEqual(ordinal(21),'21st')

    def test_manual_names_replace_ordered_name_only_selected_division_and_can_regenerate(self):
        self.s.rename('AAA',1,'Handwritten "Reserve"')
        first,second=self.s.divisions('AAA');self.assertEqual(first.name,'Authored "Guard"');self.assertEqual(second.name,'Handwritten "Reserve"')
        self.assertNotIn('division_name =',second.raw);self.assertIn('force_equipment_variants',second.raw)
        self.s.rename('AAA',1,'',generated=True);self.assertEqual(self.s.divisions('AAA')[1].name,'2nd First state Regulars')
        self.s.delete_division('AAA',0);self.assertEqual(len(self.s.divisions('AAA')),1);self.assertEqual(len(self.s.divisions('BBB')),2)

    def test_bad_cells_groups_supports_water_counts_and_template_names_reject_without_changes(self):
        for reg,support in [([],[]),([('infantry',5,0)],[]),([('infantry',0,0),('cavalry',0,1)],[]),([('engineer',0,0)],[]),([('infantry',0,0)],[('engineer',0,0),('engineer',0,1)]),([('unknown',0,0)],[])]:
            with self.subTest(reg=reg,support=support),self.assertRaises(ValueError):self.s.edit_template('CCC','New','Short',reg,support)
            self.assertFalse(self.world.docs.changed)
        for pid,amount in [(4,1),(0,1),(999,1),(1,0),(1,-1),(1,1001),(1,True)]:
            with self.subTest(pid=pid,amount=amount),self.assertRaises(ValueError):self.s.place('AAA','Infantry',pid,amount)
        with self.assertRaises(ValueError):self.s.remove('AAA',1,amount=-1)
        with self.assertRaises(ValueError):self.s.place('AAA','Unknown',1)
        self.assertFalse(self.world.docs.changed)

    def test_existing_private_destination_not_overwritten_and_failed_copy_rolls_back(self):
        self.world.docs.replace('history/units/CCC_painter_land.txt','# reserved user file\n')
        self.s.copy_template('AAA','Infantry','CCC');self.assertEqual(self.s.source('CCC').path,'history/units/CCC_painter_land_2.txt')
        self.assertEqual(self.world.docs.text('history/units/CCC_painter_land.txt'),'# reserved user file\n')
        before=dict(self.world.docs.drafts)
        with self.assertRaises(ValueError):self.s.copy_template('AAA','Infantry','CCC')
        self.assertEqual(self.world.docs.drafts,before)

    def test_conditional_dated_sources_are_visible_not_double_counted_and_keep_conditions(self):
        path=self.world.countries['CCC'];self.world.docs.replace(path,self.world.docs.text(path)+'if = { limit = { has_dlc = "test" } set_oob = "shared" }\n1940.1.1 = { set_oob = "shared" }')
        self.assertEqual(len(self.s.sources('CCC')),2);self.assertIsNone(self.s.source('CCC'))
        self.assertEqual(self.s.counts('CCC'),{});self.assertEqual(len(self.s.templates('CCC','history/units/shared.txt')),1)
        self.s.rename('CCC',0,'Conditional name','history/units/shared.txt')
        self.assertIn('has_dlc = "test"',self.world.docs.text(path));self.assertIn('1940.1.1',self.world.docs.text(path))
        # The dated source still shares the original file. Keep that variant
        # selected when its first UI name edit makes another private copy.
        from land_oob_ui import DivisionsDialog
        root=tk.Tk();root.attributes('-alpha',0)
        try:
            dialog=DivisionsDialog(root,self.s,'CCC',1,'history/units/shared.txt')
            iid=next(iter(dialog.values));dialog.rows.selection_set(iid);dialog.pick();dialog.name.set('Dated UI name');dialog.rename()
            self.assertNotEqual(dialog.path,'history/units/shared.txt');self.assertEqual(len(dialog.values),1)
            self.assertEqual(next(iter(dialog.values.values()))[1].name,'Dated UI name');dialog.cancel()
        finally:root.destroy()

    def test_map_gradient_counts_filter_and_numbers_and_global_config(self):
        image=self.world.map_image('Land OOB',country_tag='AAA',oob_template='Infantry')
        self.assertNotEqual(image.getpixel((3,3)),image.getpixel((43,3)))
        renderer=MapRenderer(self.world,self.g,self.c,self.catalog)
        rows=renderer.annotations(MapConfig('Land OOB',country_tag='AAA',oob_template='Infantry'),1,(0,0,80,40))
        self.assertEqual([r['text'] for r in rows],['1','1'])
        rows=renderer.annotations(MapConfig('Land OOB',oob_global=True),1,(0,0,80,40));self.assertEqual([r['text'] for r in rows],['2','2'])

    def test_real_mapmode_template_ui_placement_removal_global_and_name_dialog(self):
        from painter import Painter
        from land_oob_ui import TemplateDialog,DivisionsDialog,CopyTemplateDialog
        for relative in set(CATALOG_PATHS.values()):
            p=self.root/relative
            if not p.exists():self.write(relative,'l_english:\n' if p.suffix=='.yml' else '',bom=p.suffix=='.yml')
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('character_model.default_paths',return_value={'game':self.c.game_root}),patch('land_oob_ui.messagebox.showerror',side_effect=AssertionError('Unexpected OOB UI error')):
                app=Painter(root,self.world,Emblems());root.update();app.layer.set('Land OOB');app.layer_changed();app.oob_controls.country.set('AAA');app.oob_controls.country_changed()
                item=next(k for k,v in app.palette_values.items() if v=='Infantry');app.palette.selection_set(item);app.palette_selected()
                app.zoom=10;app.draw_map();root.update();app.canvas.xview_moveto(0);app.canvas.yview_moveto(0)
                event=SimpleNamespace(x=50,y=50,state=0);app.paint_press(event);app.paint_release();self.assertEqual(app.land_oob_store.counts('AAA')[1],2)
                app.right_press(event);app.paint_release();self.assertEqual(app.land_oob_store.counts('AAA')[1],1)
                app.oob_controls.global_view.set(True);before=dict(self.world.docs.drafts);app.paint_press(event);app.paint_release();self.assertEqual(self.world.docs.drafts,before)
                self.assertTrue(app.map_config().oob_global);app.oob_controls.global_view.set(False)
                designer=TemplateDialog(root,app.land_oob_store,'CCC');designer.name.set('Cavalry');designer.short.set('Riders');designer.editors['regiments'][2].set('cavalry');designer.set_cell('regiments');designer.ok()
                self.assertEqual(designer.result,'Cavalry');self.assertEqual(app.land_oob_store.templates('CCC')['Cavalry'].short,'Riders')
                names=DivisionsDialog(root,app.land_oob_store,'AAA',1);iid=next(iter(names.values));names.rows.selection_set(iid);names.pick();names.name.set('Handwritten UI name');names.rename();names.accept()
                self.assertEqual(app.land_oob_store.divisions('AAA')[0].name,'Handwritten UI name')
                copier=CopyTemplateDialog(root,app.land_oob_store,'CCC');copier.country.set('AAA');copier.country_changed();copier.template.set('Infantry');copier.template_changed();copier.ok()
                self.assertEqual(copier.result,'Infantry');self.assertIn('Infantry',app.land_oob_store.templates('CCC'))
                app._sync();app.undo();app.redo();self.assertFalse(errors);app.cancel_map_job();app.destroy()
        finally:root.update_idletasks();root.destroy()


if __name__=='__main__':unittest.main()
