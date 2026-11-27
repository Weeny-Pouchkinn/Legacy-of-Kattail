"""Ownership transfers, independent cores/claims, landless tags and core audit."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import tkinter as tk
import unittest
from unittest.mock import patch

import numpy as np

import test_countries as fixtures
from model import World,Emblems,child
from character_model import CharacterStore
from country_model import CountryStore
from demographics import MapCatalogStore,Setup,CATALOG_PATHS
from geography_model import GeographyStore
from map_render import MapConfig,MapRenderer
from script_format import tokens


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.CountryTests();self.f.setUp();self.addCleanup(self.f.tearDown);self.root=self.f.root
        tags=self.root/'common/country_tags/tags.txt';tags.write_text(tags.read_text()+'\nCCC = "countries/CCC.txt"\n')
        (self.root/'common/countries/CCC.txt').write_text('color = rgb { 10 20 30 }\n')
        (self.root/'history/countries/CCC.txt').write_text('capital = 2\nset_politics = { ruling_party = neutrality }\nset_popularities = { neutrality = 100 }\n')
        self.world=World(self.root);self.world.demographics=Setup(self.world).load()

    def raster(self):
        self.world.map_ids=np.tile(np.array([1]*40+[2]*40,dtype=np.int32),(40,1))
        self.world.map_ids[0,-1]=0

    def test_default_transfer_removes_only_previous_core_off_preserves_all_and_undo_is_atomic(self):
        self.world.set_relation_draft(1,'CCC','core');self.world.set_relation_draft(1,'AAA','claim')
        before=self.world.docs.text(self.world.states[1].path)
        self.world.set_owner_draft(1,'BBB')
        self.assertEqual(self.world.state_relations(1),{'owner':'BBB','cores':{'BBB','CCC'},'claims':{'AAA'}})
        self.world.docs.undo();self.assertEqual(self.world.docs.text(self.world.states[1].path),before)
        self.world.docs.redo();self.assertEqual(self.world.state_relations(1)['cores'],{'BBB','CCC'})
        self.world.set_owner_draft(1,'AAA',False)
        self.assertEqual(self.world.state_relations(1),{'owner':'AAA','cores':{'BBB','CCC'},'claims':{'AAA'}})
        revision=self.world.docs.revision;self.world.set_owner_draft(1,'AAA')
        self.assertNotIn('AAA',self.world.state_relations(1)['cores']);self.assertEqual(revision,self.world.docs.revision)
        self.world.set_owner_draft(1,'BBB',False);self.world.set_owner_draft(1,'AAA')
        self.assertEqual(self.world.state_relations(1)['cores'],{'AAA','CCC'})

    def test_ordered_flags_base_only_duplicates_comments_and_repaint_noop(self):
        path=self.world.states[1].path;text=self.world.docs.text(path)
        text=text.replace('owner = AAA','owner = AAA add_core_of = CCC remove_core_of = CCC add_core_of = CCC # keep comment\n add_claim_by = CCC remove_claim_by = CCC\n 1939.1.1 = { add_core_of = CCC add_claim_by = CCC owner = BBB }')
        self.world.docs.replace(path,text)
        self.assertIn('CCC',self.world.state_relations(1)['cores']);self.assertNotIn('CCC',self.world.state_relations(1)['claims'])
        dated='1939.1.1 = { add_core_of = CCC add_claim_by = CCC owner = BBB }'
        self.world.set_relation_draft(1,'CCC','core',False)
        after=self.world.docs.text(path);self.assertIn(dated,after);self.assertIn('# keep comment',after)
        self.assertEqual(self.world.state_relations(1)['cores'],{'AAA'})
        self.world.set_relation_draft(1,'CCC','claim',True);self.assertIn('CCC',self.world.state_relations(1)['claims'])
        revision=self.world.docs.revision;self.world.set_relation_draft(1,'CCC','claim',True)
        self.assertEqual(revision,self.world.docs.revision)
        self.world.docs.save();reopened=World(self.root)
        self.assertEqual(reopened.state_relations(1),{'owner':'AAA','cores':{'AAA'},'claims':{'CCC'}})
        saved,nodes=reopened.state_nodes(1);history=child(nodes,'history');date=child(history.children,'1939.1.1')
        self.assertEqual(tokens(saved[date.start:date.end]),tokens(dated))

    def test_landless_country_foreign_capital_save_reload_and_registration_validation(self):
        characters=CharacterStore(self.world);store=CountryStore(self.world,characters,MapCatalogStore(self.world,characters))
        data=store.read('CCC');self.assertEqual(store.summary('CCC')['states'],0)
        data.capital='1';store.apply(data,'#123456',data.names)
        self.world.paint(1,'State','Core','CCC','Add');self.world.paint(2,'State','Claim','CCC','Add')
        self.world.docs.save();reopened=World(self.root)
        self.assertEqual(reopened.state_relations(1)['owner'],'AAA')
        self.assertIn('CCC',reopened.state_relations(1)['cores']);self.assertIn('CCC',reopened.state_relations(2)['claims'])
        self.assertIn('capital = 1',reopened.docs.text('history/countries/CCC.txt'))
        before=dict(self.world.docs.drafts)
        with self.assertRaises(ValueError):self.world.set_owner_draft(1,'BAD')
        with self.assertRaises(ValueError):self.world.set_relation_draft(1,'BAD','core')
        self.assertEqual(before,self.world.docs.drafts)

    def test_state_editor_ownership_uses_the_shared_transfer_policy(self):
        c=CharacterStore(self.world);cat=MapCatalogStore(self.world,c);geo=GeographyStore(self.world,c,cat)
        self.world.set_relation_draft(1,'CCC','core')
        data=geo.state(1)
        geo.edit_state(1,data['name'],data['attributes'],data['resources'],data['buildings'],owner='BBB',cores=data['cores'])
        self.assertEqual(self.world.state_relations(1)['cores'],{'BBB','CCC'})
        data=geo.state(1)
        geo.edit_state(1,data['name'],data['attributes'],data['resources'],data['buildings'],owner='AAA',transfer_cores=False)
        self.assertEqual(self.world.state_relations(1)['cores'],{'BBB','CCC'})

    def test_map_colours_owned_stripes_crops_core_priority_and_saved_overlay_country(self):
        self.raster();self.world.set_relation_draft(1,'CCC','core');self.world.set_relation_draft(2,'CCC','claim')
        self.world.set_owner_draft(1,'CCC',False)
        full=np.asarray(self.world.map_image('Cores/Claims',country_tag='CCC'))
        self.assertEqual(tuple(full[0,0]),(55,125,245));self.assertEqual(tuple(full[0,15]),(55,180,90))
        self.assertEqual(tuple(full[0,50]),(240,205,55));self.assertEqual(tuple(full[0,-1]),(26,43,60))
        crop=np.asarray(self.world.map_image('Cores/Claims',(80,40),(40,0,80,40),country_tag='CCC'))
        np.testing.assert_array_equal(crop,full[:,40:])
        c=CharacterStore(self.world);cat=MapCatalogStore(self.world,c);geo=GeographyStore(self.world,c,cat)
        renderer=MapRenderer(self.world,geo,c,cat);saved=MapConfig('Cores/Claims',country_tag='CCC',names=False)
        before=np.asarray(renderer.render(saved,(80,40),(0,0,80,40),1,False))
        renderer.render(MapConfig('Cores/Claims',country_tag='BBB'),(80,40),(0,0,80,40),1,False)
        np.testing.assert_array_equal(before,np.asarray(renderer.render(saved,(80,40),(0,0,80,40),1,False)))
        self.world.set_relation_draft(2,'CCC','core');self.assertEqual(self.world.map_image('Cores/Claims',country_tag='CCC').getpixel((50,0)),(55,180,90))
        self.assertIn('CCC',saved.label)

    def test_native_audit_dry_run_proof_exceptions_and_idempotence(self):
        tags=self.root/'common/country_tags/tags.txt';tags.write_text(tags.read_text()+'\nSIL="countries/SIL.txt" KTW="countries/KTW.txt"')
        for sid in (34,36,44,45):
            (self.root/f'history/states/{sid}-exception.txt').write_text(f'state={{id={sid} name=EXCEPTION provinces={{}} history={{owner=SIL add_core_of=KTW set_demilitarized_zone=yes}}}}')
        spec=importlib.util.spec_from_file_location('audit_owner_cores_test',Path(__file__).resolve().parents[1]/'tools/audit_owner_cores.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        changes,report=module.build(self.root)
        self.assertEqual(report['changed_states'],1);self.assertEqual(len(report['exceptions']),4)
        path=self.world.states[2].path;self.assertNotIn('add_core_of',self.world.docs.text(path))
        from source_io import write_changes
        write_changes(self.root,changes,label='core_audit_fixture')
        self.assertEqual(module.build(self.root)[1]['changed_states'],0)

    def test_real_owners_categories_landless_palette_gestures_and_transfer_checkbox(self):
        from painter import Painter
        for relative in set(CATALOG_PATHS.values()):
            path=self.root/relative
            if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_text('l_english:\n' if path.suffix=='.yml' else '',encoding='utf-8-sig' if path.suffix=='.yml' else 'utf-8')
        (self.root/CATALOG_PATHS['species_map']).write_text('scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        self.raster();root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('character_model.default_paths',return_value={'game':self.f.game}),patch('painter.messagebox.showerror',side_effect=AssertionError('Unexpected owner paint error')):
                app=Painter(root,self.world,Emblems());root.update()
                app.layer.set('Owners');app.layer_changed();app.owner_mode.set('Cores/Claims');app.map_mode_changed();root.update()
                self.assertTrue(app.transfer_cores.get());self.assertEqual(app.palette_key(),'Cores/Claims')
                item=next(k for k,v in app.palette_values.items() if v=='CCC');app.palette.selection_set(item);app.palette_selected()
                self.assertEqual(app.map_config().country_tag,'CCC')
                app.zoom=10;app.draw_map();root.update();app.canvas.xview_moveto(0);app.canvas.yview_moveto(0)
                left=SimpleNamespace(x=10,y=20,state=0);shift=SimpleNamespace(x=410,y=20,state=1)
                app.paint_press(left);app.paint_release();self.assertIn('CCC',self.world.state_relations(1)['cores'])
                app.paint_press(shift);app.paint_release();self.assertIn('CCC',self.world.state_relations(2)['claims'])
                app.right_press(left);app.paint_release();self.assertNotIn('CCC',self.world.state_relations(1)['cores'])
                app.right_press(shift);app.paint_release();self.assertNotIn('CCC',self.world.state_relations(2)['claims'])
                app.undo();self.assertIn('CCC',self.world.state_relations(2)['claims'])
                self.assertEqual(self.world.state_relations(1)['owner'],'AAA')
                app.owner_mode.set('Ownership');app.map_mode_changed();app.paint_selection['Owner']='BBB'
                app.paint_press(left);app.paint_release();self.assertEqual(self.world.state_relations(1)['cores'],{'BBB'})
                app.transfer_cores_check.invoke();app.paint_selection['Owner']='AAA'
                app.paint_press(left);app.paint_release();self.assertEqual(self.world.state_relations(1)['cores'],{'BBB'})
                self.assertEqual(self.world.state_relations(1)['owner'],'AAA')
                # The native-field inspector also obeys the same global checkbox.
                app.transfer_cores.set(True);self.world.set_relation_draft(1,'AAA','core')
                app.inspect_state(1);app.open_document(self.world.states[1].path)
                item=next(k for k,node in app.rows.items() if node.key=='owner')
                app.fields.selection_set(item);app.field_editor.delete('1.0','end');app.field_editor.insert('1.0','CCC')
                app.apply_field();self.assertEqual(self.world.state_relations(1)['cores'],{'BBB','CCC'})
                source=self.world.docs.text(self.world.states[1].path).replace('owner = CCC','owner = BBB')
                app.source_editor.delete('1.0','end');app.source_editor.insert('1.0',source);app.apply_source()
                self.assertEqual(self.world.state_relations(1)['cores'],{'BBB'})
                self.assertFalse(errors);app.cancel_map_job();app.destroy()
        finally:root.update_idletasks();root.destroy()


if __name__=='__main__':unittest.main()
