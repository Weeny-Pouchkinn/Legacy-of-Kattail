"""Native geography authoring, isolated in disposable mod/game fixtures."""
from copy import deepcopy
import unittest
from pathlib import Path
import numpy as np

import test_painter as fixtures
from model import World, parse, child, value
from character_model import CharacterStore
from demographics import MapCatalogStore, Setup
from geography_model import GeographyStore, CLIMATES, MONTH_DAYS, WeatherPeriod, climate_preset, VP_LOC, STATE_LOC, REGION_LOC, vp_color


class GeographyTests(unittest.TestCase):
    def setUp(self):
        fixtures.FixtureTests.setUp(self)
        self.write('descriptor.mod','name="Fixture"')
        self.write('map/definition.csv','0;0;0;0;sea;false;ocean;0\n1;1;2;3;land;true;plains;1\n2;4;5;6;land;false;hills;1\n3;7;8;9;land;false;plains;1\n4;10;11;12;sea;false;ocean;0\n')
        self.write('history/states/one.txt','''state = { id = 1 name = "ONE" provinces = { 1 3 }
 manpower = 200 state_category = town buildings_max_level_factor = 1
 resources = { steel = 2 } # retained resource comment
 history = { owner = AAA add_core_of = AAA mystery = { value = yes }
 buildings = { infrastructure = 2 industrial_complex = 1 1 = { naval_base = 1 bunker = 2 } }
 victory_points = { 1 3 3 2 }
 1940.1.1 = { victory_points = { 1 99 } buildings = { infrastructure = 4 } }
 } }''')
        for rel,text in {
            'common/state_category/categories.txt':'state_categories = { town = { local_building_slots = 4 } rural = { local_building_slots = 2 } }',
            'common/resources/resources.txt':'resources = { steel = { } oil = { } }',
            'common/buildings/buildings.txt':'''buildings = {
                industrial_complex = { level_cap = { shares_slots = yes state_max = 20 } }
                infrastructure = { level_cap = { state_max = 5 } }
                naval_base = { level_cap = { province_max = 10 } only_costal = yes }
                bunker = { level_cap = { province_max = 10 } }
                supply_node = { level_cap = { province_max = 1 } supply_node = yes }
                rail_way = { level_cap = { province_max = 5 } }
                land_facility = { level_cap = { province_max = 1 state_max = 1 group_by = facility } spawn_point = special_project_facility_spawn }
                air_facility = { level_cap = { province_max = 1 state_max = 1 group_by = facility } spawn_point = special_project_facility_spawn }
            }''',
            'common/terrain/terrain.txt':'categories = { ocean = { naval_terrain = yes } plains = { } }',
            'map/supply_nodes.txt':'# keep supply comment\n1 2\n',
            'map/buildings.txt':'1;special_project_facility_spawn;1;1;1;1;0\n',
            'map/strategicregions/one.txt':'''strategic_region = { id = 1 name = REG_ONE provinces = { 1 3 4 }
                unknown = yes weather = { mystery = 7 period = { between = { 0.0 30.0 } temperature = { -6 12 } rain_light = 2 # keep weather comment
                custom_weight = 3 } } }''',
            'map/strategicregions/two.txt':'strategic_region = { id = 2 name = REG_TWO provinces = { 2 } weather = { } }',
            'localisation/english/extras_l_english.yml':'l_english:\n VICTORY_POINTS_3:0 "Zulu" # original comment\n VICTORY_POINTS_1_AAA:0 "Variant untouched"\n OTHER:0 "Keep"\n',
            VP_LOC:'l_english:\n # Country: AAA\n VICTORY_POINTS_1:2 "Beta" # version and note\n',
            STATE_LOC:'l_english:\n ONE:0 "First state"\n TWO:0 "Second state"\n',
            REGION_LOC:'l_english:\n REG_ONE:0 "First region"\n REG_TWO:0 "Second region"\n',
        }.items():self.write(rel,text,bom=rel.endswith('.yml'))
        self.world=World(self.root);self.world.demographics=Setup(self.world).load()
        self.c=CharacterStore(self.world);self.c.game_root=Path(self.tmp.name)/'game';self.c.game_root.mkdir()
        self.g=GeographyStore(self.world,self.c,MapCatalogStore(self.world,self.c));self.g.sync_world()
        self.world.docs.before_save=self.g.validate_save

    def tearDown(self):fixtures.FixtureTests.tearDown(self)

    def write(self,relative,text,bom=False):
        p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig' if bom else 'utf-8')

    def edit(self,**kwargs):
        data=self.g.state(1);values={k:data[k] for k in ['name','attributes','resources','buildings']};values.update(kwargs)
        self.g.edit_state(1,**values)

    def test_state_save_reload_preserves_dates_unknown_scopes_and_geometry(self):
        original=(self.root/'history/states/one.txt').read_bytes();data=self.g.state(1)
        levels={**data['buildings'],(None,'industrial_complex'):'4',(None,'infrastructure'):'3',(1,'naval_base'):'5'}
        self.edit(name='A renamed state',attributes={**data['attributes'],'manpower':'123456'},resources={'oil':'4'},buildings=levels,owner='BBB',cores={'AAA','BBB'})
        text=self.world.docs.text('history/states/one.txt')
        self.assertIn('1940.1.1 = { victory_points = { 1 99 } buildings = { infrastructure = 4 } }',text)
        self.assertIn('mystery = { value = yes }',text);self.assertEqual(self.g.state(1)['resources'],{'oil':'4'})
        self.assertEqual((self.root/'history/states/one.txt').read_bytes(),original)
        self.world.docs.save();fresh=World(self.root);c=CharacterStore(fresh);g=GeographyStore(fresh,c,MapCatalogStore(fresh,c))
        self.assertEqual(g.state(1)['name'],'A renamed state');self.assertEqual(g.state(1)['buildings'][(1,'naval_base')],'5')
        self.assertEqual(fresh.states[1].provinces,[1,3]);self.assertTrue((self.root/STATE_LOC).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_building_limits_scopes_coasts_groups_and_unknowns(self):
        old=self.g.state(1)['buildings']
        for key,level in [((None,'infrastructure'),'6'),((3,'naval_base'),'1'),((2,'bunker'),'1'),((None,'bunker'),'1'),((1,'rail_way'),'2'),((1,'bunker'),'1.5')]:
            with self.subTest(key=key),self.assertRaises(ValueError):self.edit(buildings={**old,key:level})
        with self.assertRaises(ValueError):self.edit(buildings={**old,(1,'land_facility'):'1',(3,'air_facility'):'1'})
        self.edit(buildings={**old,(1,'land_facility'):'1'})
        self.assertEqual(self.g.state(1)['buildings'][(1,'land_facility')],'1')

    def test_supply_nodes_use_native_file_and_atomic_undo(self):
        old=self.g.state(1)['buildings'];self.edit(name='Supply',buildings={**old,(1,'supply_node'):'1'})
        self.assertEqual(self.g.supply_nodes(),{1:1,2:1});self.assertNotIn('supply_node',self.world.docs.text('history/states/one.txt'))
        self.world.docs.undo();self.assertEqual(self.g.supply_nodes(),{2:1});self.assertEqual(self.g.state(1)['name'],'First state')

    def test_state_structural_fields_and_nonfinite_values_rejected_transactionally(self):
        for attrs in [{'provinces':'2'},{'manpower':'NaN'},{'manpower':'1.2'},{'manpower':'-1'}]:
            with self.assertRaises(ValueError):self.edit(attributes=attrs)
            self.assertFalse(self.world.docs.changed)

    def test_whole_state_transfer_preserves_seas_and_updates_paint_scope_undo(self):
        data=self.g.region(2);self.g.edit_region(2,'Combined region',data['terrain'],data['weather'],{1:2})
        self.assertEqual(self.world.regions[1]['provinces'],{4});self.assertEqual(self.world.regions[2]['provinces'],{1,2,3})
        self.assertEqual(self.world.paint_targets(1,'Strategic region'),(1,2));self.g.validate_save()
        self.world.docs.undo();self.g.sync_world();self.assertEqual(self.world.regions[1]['provinces'],{1,3,4})
        self.assertEqual(self.c.localisations()['REG_TWO'],'Second region')

    def test_empty_split_or_unassigned_region_membership_rejected(self):
        with self.assertRaises(ValueError):self.g.edit_region(1,'First region','',[],{2:1})
        with self.assertRaises(ValueError):self.g.validate_region_membership({1:{1,4},2:{2,3}})
        with self.assertRaises(ValueError):self.g.validate_region_membership({1:{1,4},2:{2}})
        self.assertFalse(self.world.docs.changed)

    def test_weather_preserves_unknowns_and_rejects_invalid_values(self):
        r=self.g.region(1);periods=deepcopy(r['weather']);periods[0].low='-20';periods[0].weights['rain_light']='3'
        self.g.edit_region(1,r['name'],'',periods)
        text=self.world.docs.text(r['path']);self.assertIn('mystery = 7',text);self.assertIn('# keep weather comment',text);self.assertIn('custom_weight = 3',text)
        for period in [WeatherPeriod('30.1','0.2','0','1'),WeatherPeriod('0.0','0.1','2','1'),WeatherPeriod('0.0','0.1','0','1',{'rain_light':'-1'})]:
            with self.assertRaises(ValueError):period.validate()

    def test_all_30_climates_both_hemispheres_cover_calendar(self):
        self.assertEqual(len(CLIMATES),30)
        for code in CLIMATES:
            north=climate_preset(code,'North');south=climate_preset(code,'South')
            self.assertEqual(len(north),12)
            for m,(n,s) in enumerate(zip(north,south)):
                self.assertEqual(n.start,f'0.{m}');self.assertEqual(n.end,f'{MONTH_DAYS[m]-1}.{m}');parse(n.script());parse(s.script())
                self.assertEqual((s.low,s.high,s.weights),(north[(m+6)%12].low,north[(m+6)%12].high,north[(m+6)%12].weights))

    def test_vanilla_import_shifts_complete_month_and_does_not_import_shapes(self):
        path=self.c.game_root/'map/strategicregions/vanilla.txt';path.parent.mkdir(parents=True)
        path.write_text('strategic_region = { id=9 name=FOREIGN provinces={99999} naval_terrain=ocean weather={period={between={0.7 30.7} temperature={20 30} snow=2}} }')
        periods,terrain=self.g.import_weather(9,True);self.assertEqual((periods[0].start,periods[0].end),('0.1','27.1'));self.assertEqual(terrain,'ocean')
        self.assertFalse(self.world.docs.changed);self.g.edit_region(2,'Second region','',periods)
        self.assertEqual(self.world.regions[2]['provinces'],{2});self.assertNotIn('99999',self.world.docs.text(self.g.region(2)['path']))

    def test_vp_save_reload_sort_consolidate_versions_variants_and_remove(self):
        original=(self.root/VP_LOC).read_bytes();self.g.set_vp(2,'Alpha',10)
        self.assertEqual((self.root/VP_LOC).read_bytes(),original)
        self.assertEqual({p:d['value'] for p,d in self.g.victory_points().items()},{1:3,2:10,3:2})
        text=self.world.docs.text(VP_LOC);self.assertLess(text.index('"Alpha"'),text.index('"Beta"'));self.assertLess(text.index('"Beta"'),text.index('"Zulu"'))
        self.assertIn('VICTORY_POINTS_1:2 "Beta" # version and note',text);self.assertIn('"Zulu" # original comment',text)
        extras=self.world.docs.text('localisation/english/extras_l_english.yml');self.assertIn('VICTORY_POINTS_1_AAA:0 "Variant untouched"',extras);self.assertNotIn('VICTORY_POINTS_3:',extras)
        self.g.set_vp(1,'Changed',7);self.assertIn('victory_points = { 1 99 }',self.world.docs.text('history/states/one.txt'))
        self.assertEqual(self.g.victory_points()[3]['value'],2)
        self.world.docs.save();self.assertTrue((self.root/VP_LOC).read_bytes().startswith(b'\xef\xbb\xbf'))
        w=World(self.root);c=CharacterStore(w);g=GeographyStore(w,c,MapCatalogStore(w,c));self.assertEqual(g.victory_points()[1]['name'],'Changed')
        g.set_vp(1,'',None);self.assertNotIn(1,g.victory_points());self.assertIn('VICTORY_POINTS_1:',w.docs.text(VP_LOC).replace(':2',':'))

    def test_vp_conflict_rolls_back_entire_operation(self):
        self.write('localisation/english/conflict_l_english.yml','l_english:\n VICTORY_POINTS_3:0 "Conflict"\n',True)
        self.c._inventories.clear()
        with self.assertRaises(ValueError):self.g.set_vp(2,'Alpha',5)
        self.assertFalse(self.world.docs.changed)

    def test_vp_geometry_gradient_and_sea_regions(self):
        self.world.map_ids=np.array([[1,3,3,4],[1,2,2,4],[1,3,3,4]],dtype=np.int32)
        for pid,(x,y) in self.g.province_points().items():self.assertEqual(int(self.world.map_ids[y,x]),pid)
        self.g.set_vp(2,'Alpha',10);im=np.asarray(self.world.map_image('VPs'))
        self.assertEqual(tuple(im[1,1]),vp_color(10,10));self.assertNotEqual(tuple(im[0,0]),tuple(im[1,1]))
        regions=np.asarray(self.world.map_image('Strategic regions'));self.assertEqual(tuple(regions[0,0]),tuple(regions[0,3]))

    def test_capital_map_pick_takes_precedence_over_vp_editing(self):
        from types import SimpleNamespace
        from painter import Painter
        received=[];self.world.map_ids=np.array([[1]],dtype=np.int32)
        app=SimpleNamespace(world=self.world,zoom=1,geography_picker=None,capital_picker=SimpleNamespace(receive_capital=received.append),
                            canvas=SimpleNamespace(canvasx=lambda x:x,canvasy=lambda y:y),root=SimpleNamespace(unbind=lambda *a:None),
                            _capital_escape='binding',_status=lambda *a:None,brush=SimpleNamespace(get=lambda:'VPs'))
        Painter.pick(app,SimpleNamespace(x=0,y=0,state=0));self.assertEqual(received,[1]);self.assertIsNone(app.capital_picker)


class GeographyFormTests(unittest.TestCase):
    write=GeographyTests.write

    def setUp(self):
        GeographyTests.setUp(self)
        import tkinter as tk
        from types import SimpleNamespace
        self.tkroot=tk.Tk();self.tkroot.withdraw();self.tkroot.attributes('-alpha',0)
        self.errors=[];self.tkroot.report_callback_exception=lambda typ,val,tb:self.errors.append(val)
        catalog=SimpleNamespace(species=lambda:{0:SimpleNamespace(name='Species zero'),1:SimpleNamespace(name='Species one')},cultures=lambda:{4:SimpleNamespace(name='Culture four')})
        self.app=SimpleNamespace(world=self.world,geography_store=self.g,character_store=self.c,catalog_store=catalog)
        from unittest.mock import patch
        self.error_patch=patch('geography_ui.messagebox.showerror',side_effect=AssertionError('Unexpected form error'))
        self.error_patch.start();self.addCleanup(self.error_patch.stop)

    def tearDown(self):
        self.tkroot.update_idletasks()
        self.tkroot.destroy();GeographyTests.tearDown(self)

    def test_nested_vp_apply_is_part_of_state_cancel_transaction(self):
        from geography_ui import StateDialog,VictoryPointDialog
        d=StateDialog(self.tkroot,self.app,1);d.attributes('-alpha',0);self.tkroot.deiconify();self.tkroot.update()
        def nested():
            try:
                vp=next(c for c in d.winfo_children() if isinstance(c,VictoryPointDialog));vp.attributes('-alpha',0)
                vp.name.set('Nested name');vp.amount.set('8');vp.ok()
            except Exception as exc:self.errors.append(exc);d.destroy()
        self.tkroot.after(30,nested);d.edit_vp(1)
        self.assertFalse(self.errors);self.assertEqual(self.g.victory_points()[1]['name'],'Nested name');self.assertEqual(d.grab_current(),d)
        d.cancel();self.assertFalse(self.world.docs.changed);self.assertEqual(self.g.victory_points()[1]['name'],'Beta')

    def test_region_form_preset_transfer_apply_and_undo(self):
        from geography_ui import RegionDialog
        d=RegionDialog(self.tkroot,self.app,2);d.attributes('-alpha',0);self.tkroot.deiconify();self.tkroot.update()
        d.climate.set('Cfb');d.hemisphere.set('South');d.preset();d.add_state(1);d.name.set('Changed region');d.ok()
        self.assertFalse(d.winfo_exists());self.assertFalse(self.errors);self.assertEqual(self.world.province_regions[1],2)
        self.assertEqual(len(self.g.region(2)['weather']),12);self.assertEqual(self.g.region(2)['name'],'Changed region')
        self.world.docs.undo();self.g.sync_world();self.assertEqual(self.world.province_regions[1],1);self.assertFalse(self.world.docs.changed)


if __name__=='__main__':unittest.main()
