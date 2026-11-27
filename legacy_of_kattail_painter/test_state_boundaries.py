"""Boundary edits exercised against disposable native maps, histories and UI."""
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

import test_geography as fixtures
from character_model import CharacterStore,block
from demographics import MapCatalogStore,Setup,CATALOG_PATHS,STARTUP
from geography_model import GeographyStore,STATE_LOC
from model import World,Emblems,parse,colour
from state_boundary_model import StateBoundaryStore,Recalculate,state_data,apportioned,scopes


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.GeographyTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.root=self.fixture.root;self.write=self.fixture.write
        self.write(STARTUP,'on_actions = { on_startup = { effect = { } } }')
        self.write('map/definition.csv','0;0;0;0;sea;false;ocean;0\n'+''.join(
            f'{pid};{pid};{pid+1};{pid+2};land;true;{terrain};1\n'
            for pid,terrain in [(1,'plains'),(2,'mountain'),(3,'forest'),(4,'hills'),(5,'urban'),(6,'jungle')]))
        self.write('history/states/one.txt','''state = { id = 1 name = ONE manpower = 10001 state_category = town
            provinces = { 1 2 3 } resources = { steel = 7 oil = 1.25 } capital = 2
            history = { owner = AAA add_core_of = AAA add_claim_by = BBB
                mystery = { value = yes } # Keep human note
                buildings = { infrastructure = 2 industrial_complex = 4 air_base = 0
                    2 = { bunker = 3 naval_base = 1 } }
                victory_points = { 1 1 2 50 }
                1940.1.1 = { owner = BBB victory_points = { 2 60 }
                    buildings = { 2 = { bunker = 5 } infrastructure = 4 } }
            } }''')
        self.write('history/states/two.txt','''state = { id = 2 name = TWO manpower = 300 state_category = town
            provinces = { 4 5 } resources = { steel = 3 }
            history = { owner = BBB add_core_of = BBB buildings = { infrastructure = 1 air_base = 5 industrial_complex = 2 } } }''')
        self.write('history/states/three.txt','state = { id = 3 name = THREE manpower = 20 provinces = { 6 } history = { owner = BBB } }')
        self.write('map/strategicregions/one.txt','strategic_region = { id = 1 name = REG_ONE provinces = { 0 1 2 3 4 5 } weather = {} }')
        self.write('map/strategicregions/two.txt','strategic_region = { id = 2 name = REG_TWO provinces = { 6 } weather = {} }')
        self.write('map/supplyareas/one.txt','supply_area = { id = 1 states = { 1 2 } value = 1 }')
        self.write('map/supply_nodes.txt','1 2\n');self.write('map/railways.txt','1 2 1 2\n');self.write('map/unitstacks.txt','2;keep;unchanged\n')
        self.write('map/buildings.txt','# Keep placement header\n')
        buildings='common/buildings/buildings.txt';text=(self.root/buildings).read_text()
        text=text.replace('industrial_complex = {','industrial_complex = { show_on_map = 3')
        text=text.replace('naval_base = {','naval_base = { show_on_map = 1')
        text=text.replace('bunker = {','bunker = { show_on_map = 1')
        text=text.replace('buildings = {','buildings = { air_base = { show_on_map = 1 level_cap = { state_max = 10 } }',1)
        text+='\nspawn_points = { special_project_facility_spawn = { type = province max = 1 } }'
        self.write(buildings,text)
        self.world=World(self.root);self.world.demographics=Setup(self.world).load()
        self.world.map_ids=np.zeros((24,72),dtype=np.int32)
        for pid in range(1,7):self.world.map_ids[2:22,(pid-1)*12:pid*12]=pid
        colors=np.array([self.world.provinces[p]['rgb'] for p in range(7)],dtype=np.uint8)
        Image.fromarray(colors[self.world.map_ids]).save(self.root/'map/provinces.bmp')
        Image.new('L',(72,24),110).save(self.root/'map/heightmap.bmp')
        self.c=CharacterStore(self.world);self.c.game_root=self.fixture.c.game_root
        self.catalog=MapCatalogStore(self.world,self.c);self.g=GeographyStore(self.world,self.c,self.catalog)
        self.store=StateBoundaryStore(self.world,self.g,self.catalog);self.world.docs.before_save=self.g.validate_save

    def data(self,sid):return state_data(self.world.docs.text(self.world.states[sid].path))

    def test_payload_dates_pop_vp_resources_models_and_airbase_levels(self):
        originals={p:(self.root/p).read_bytes() for p in ['map/provinces.bmp','map/definition.csv','map/railways.txt','map/supply_nodes.txt','map/unitstacks.txt']}
        before=dict(self.world.docs.drafts);self.world.map_image('States')
        result=self.store.move_provinces([2],2)
        self.assertEqual(result['provinces'],1);self.assertEqual(self.world.province_states[2],2)
        a,b=self.data(1),self.data(2)
        self.assertEqual(int(a['population'])+int(b['population']),10301)
        self.assertGreater(int(b['population']),9500)
        self.assertEqual(Decimal(a['resources']['steel'])+Decimal(b['resources']['steel']),10)
        self.assertEqual(Decimal(a['resources']['oil'])+Decimal(b['resources']['oil']),Decimal('1.25'))
        self.assertEqual(a['buildings']['industrial_complex'],'4');self.assertEqual(b['buildings']['industrial_complex'],'2')
        self.assertEqual(a['buildings']['air_base'],'0');self.assertEqual(b['buildings']['air_base'],'5')
        self.assertNotIn(2,a['vps']);self.assertEqual(b['vps'][2],'50')
        self.assertNotIn((2,'bunker'),self.g.state(1)['buildings']);self.assertEqual(self.g.state(2)['buildings'][(2,'bunker')],'3')
        target=self.world.docs.text(self.world.states[2].path)
        date=dict(scopes(target))['1940.1.1'];self.assertIn('60',target[date.start:date.end]);self.assertIn('bunker = 5',target[date.start:date.end])
        source=self.world.docs.text(self.world.states[1].path);self.assertIn('mystery = { value = yes }',source)
        self.assertIn('# Keep human note',source);self.assertIn('infrastructure = 4',source)
        self.assertNotEqual(self.world.map_image('States').getpixel((13,5)),colour(1))
        self.store.positions.validate({1,2});self.g.validate_save()
        for sid in (1,2):self.assertIn(f'{sid};air_base;',self.world.docs.text('map/buildings.txt'))
        self.assertEqual(originals,{p:(self.root/p).read_bytes() for p in originals})
        self.world.docs.undo();self.store.sync_world();self.assertEqual(self.world.province_states[2],1);self.assertEqual(self.world.docs.changed,[])
        self.world.docs.redo();self.store.sync_world();self.assertEqual(self.world.province_states[2],2)
        self.world.docs.save();fresh=World(self.root);self.assertEqual(fresh.province_states[2],2)

    def test_multimove_conservation_industry_on_and_disabled_flags(self):
        self.store.move_provinces([2,3],2,Recalculate(industry=True))
        self.assertEqual(sum(int(self.data(s)['buildings'].get('industrial_complex',0)) for s in (1,2)),6)
        self.assertGreaterEqual(int(self.data(2)['buildings']['industrial_complex']),5)
        self.assertEqual(self.world.states[1].provinces,[1])
        self.world.docs.undo();self.store.sync_world()
        self.store.move_provinces([2],2,Recalculate(False,False,False))
        self.assertEqual(self.data(1)['population'],'10001');self.assertEqual(self.data(2)['population'],'300')
        self.assertEqual(self.data(1)['resources'],{'steel':'7','oil':'1.25'});self.assertEqual(self.data(2)['resources'],{'steel':'3'})

    def test_invalid_regions_empty_water_and_atomic_rollback(self):
        for provinces,target in [([1,2,3],2),([2],3),([0],2),([99],2),([2],99)]:
            with self.subTest(provinces=provinces,target=target),self.assertRaises(ValueError):self.store.move_provinces(provinces,target)
            self.assertFalse(self.world.docs.changed);self.assertEqual(self.world.province_states[2],1)
        with patch.object(self.store.positions,'regenerate',side_effect=ValueError('placement failed')):
            with self.assertRaisesRegex(ValueError,'placement failed'):self.store.move_provinces([2],2)
        self.assertFalse(self.world.docs.changed);self.assertEqual(self.world.province_states[2],1)
        self.assertFalse(self.world.docs.undo_stack)

    def test_new_state_inherits_setup_no_airbase_level_and_survives_save_undo(self):
        sid,result=self.store.create_state('User supplied name',2)
        self.assertEqual(sid,4);self.assertEqual(self.world.states[sid].provinces,[2])
        self.assertEqual(self.world.state_relations(sid),self.world.state_relations(1))
        self.assertEqual(self.world.demographics[sid],self.world.demographics[1])
        data=self.data(sid);self.assertNotIn('air_base',data['buildings']);self.assertNotIn('industrial_complex',data['buildings'])
        self.assertEqual(data['buildings']['infrastructure'],'2');self.assertEqual(data['vps'][2],'50')
        self.assertIn(f'{sid};air_base;',self.world.docs.text('map/buildings.txt'))
        self.assertIn('STATE_4:0 "User supplied name"',self.world.docs.text(STATE_LOC))
        self.assertIn('1 2 4',self.world.docs.text('map/supplyareas/one.txt'))
        self.g.validate_save();self.world.docs.undo();self.store.sync_world();self.assertNotIn(sid,self.world.states)
        self.assertEqual(self.world.province_states[2],1);self.world.docs.redo();self.store.sync_world()
        self.world.docs.save();self.store.sync_world(force=True);self.assertIn(sid,self.world.states)
        fresh=World(self.root);self.assertEqual(fresh.province_states[2],sid)
        self.assertTrue((self.root/STATE_LOC).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_ids_localisation_collision_and_creation_rollback(self):
        self.g.set_loc(STATE_LOC,'STATE_4','Existing human text')
        before=dict(self.world.docs.drafts)
        with patch.object(self.g,'set_loc',side_effect=ValueError('loc fail')):
            with self.assertRaisesRegex(ValueError,'loc fail'):self.store.create_state('Draft',2)
        self.assertEqual(self.world.docs.drafts,before);self.assertEqual(set(self.world.states),{1,2,3})
        sid,_=self.store.create_state('Draft',2);self.assertGreater(sid,4)
        self.assertIn('STATE_4:0 "Existing human text"',self.world.docs.text(STATE_LOC))

    def test_every_terrain_deterministic_rounding_and_unknown_numeric_rejection(self):
        self.write('common/terrain/custom.txt','categories = { custom_terrain = { movement_cost = 2 } }')
        weights=self.store.terrain_weights();self.assertEqual(weights['custom_terrain'],Decimal('.25'))
        self.assertLess(weights['mountain'],weights['forest']);self.assertLess(weights['forest'],weights['plains'])
        self.assertTrue(all(p['terrain'] in weights for p in self.world.provinces.values()))
        self.assertEqual(apportioned(7,{1:1,2:1}),{1:Decimal(4),2:Decimal(3)})
        p=self.world.states[1].path;self.world.docs.replace(p,self.world.docs.text(p).replace('manpower = 10001','manpower = scripted_population'))
        before=dict(self.world.docs.drafts)
        with self.assertRaises(ValueError):self.store.move_provinces([2],2)
        self.assertEqual(self.world.docs.drafts,before)
        self.store.move_provinces([2],2,Recalculate(False,False,False))

    def test_preview_does_not_modify_data_and_undo_clears_cached_boundaries(self):
        before=self.world.map_image('States');preview=self.world.map_image('States',state_preview=(2,),state_target=2)
        self.assertEqual(preview.getpixel((13,5)),colour(2));self.assertEqual(before.getpixel((13,5)),colour(1))
        self.assertFalse(self.world.docs.changed)
        self.store.move_provinces([2],2);self.world.boundary_overlay(self.world.map_image('States'),False,True,False)
        self.world.docs.undo();self.g.sync_world();self.assertEqual(self.world.map_image('States').getpixel((13,5)),colour(1))

    def test_native_lake_memberships_survive_without_water_model_placements(self):
        self.world.provinces[3]['type']='lake';self.store.sync_world(force=True)
        self.world.docs.replace('map/buildings.txt','1;air_base;25;11;18;0;0\n')
        self.store.move_provinces([2],2);self.assertEqual(self.world.province_states[3],1)
        for line in self.world.docs.text('map/buildings.txt').splitlines():
            fields=line.split(';')
            if len(fields)==7 and fields[1]!='floating_harbor':
                self.assertEqual(self.world.provinces[self.store.positions.point_province(fields)]['type'],'land')
        self.world.docs.undo();self.store.sync_world()
        with self.assertRaisesRegex(ValueError,'empty of land'):self.store.move_provinces([1,2],2)

    def test_coastal_industry_can_follow_last_coast_or_blocks_without_redistribution(self):
        path='common/buildings/buildings.txt'
        self.world.docs.replace(path,self.world.docs.text(path).replace('buildings = {','buildings = { dockyard = { only_costal = yes level_cap = { shares_slots = yes state_max = 20 } }',1))
        self.world.docs.replace(self.world.states[1].path,self.world.docs.text(self.world.states[1].path).replace('industrial_complex = 4','industrial_complex = 4 dockyard = 3'))
        # Only the transferred province retains ocean access in this geometry.
        geometry=self.store.positions.geometry();geometry['coasts']={2:geometry['coasts'][2]}
        before=dict(self.world.docs.drafts)
        with self.assertRaisesRegex(ValueError,'inland dockyard'):self.store.move_provinces([2],2)
        self.assertEqual(self.world.docs.drafts,before)
        self.store.move_provinces([2],2,Recalculate(industry=True))
        self.assertNotIn('dockyard',self.data(1)['buildings']);self.assertEqual(self.data(2)['buildings']['dockyard'],'3')

    def test_real_ui_defaults_multimove_one_stroke_and_new_state_dialog(self):
        from painter import Painter
        from state_boundary_ui import NewStateDialog
        for relative in set(CATALOG_PATHS.values()):
            path=self.root/relative
            if not path.exists():self.write(relative,'l_english:\n' if path.suffix=='.yml' else '',bom=path.suffix=='.yml')
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('character_model.default_paths',return_value={'game':self.c.game_root}),patch('painter.messagebox.showerror',side_effect=AssertionError('Unexpected boundary error')):
                app=Painter(root,self.world,Emblems());root.update()
                app.layer.set('States');app.layer_changed();app.state_mode.set('State boundaries');app.map_mode_changed()
                self.assertTrue(app.recalculate_population.get());self.assertTrue(app.recalculate_resources.get());self.assertFalse(app.recalculate_industry.get())
                app.paint_selection['State boundaries']=2
                event=SimpleNamespace(state=0);app.pick_geography(2,1,event);app.pick_geography(3,1,event)
                self.assertEqual(app._boundary_pending,{2,3});self.assertEqual(self.world.province_states[2],1)
                self.assertEqual(app.map_config().state_preview,(2,3));app.paint_release()
                self.assertEqual(self.world.states[1].provinces,[1]);app.undo();self.assertEqual(self.world.states[1].provinces,[1,2,3])
                app.pick_only=True;app.pick_geography(1,1,SimpleNamespace(state=1));app.pick_only=False
                self.assertEqual(app.paint_selection['State boundaries'],1)
                dialog=NewStateDialog(root,app);dialog.name.set('Dialog state');dialog.receive_seed(2);dialog.ok()
                self.assertEqual(dialog.result,4);app._sync();self.assertEqual(self.world.province_states[2],4)
                app.undo();self.assertNotIn(4,self.world.states);app.redo();self.assertIn(4,self.world.states)
                self.assertFalse(errors);app.cancel_map_job();app.destroy()
        finally:root.update_idletasks();root.destroy()


if __name__=='__main__':unittest.main()
