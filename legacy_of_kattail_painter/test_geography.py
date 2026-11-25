"""Native geography authoring, isolated in disposable mod/game fixtures."""
from copy import deepcopy
import unittest
from pathlib import Path
import numpy as np

import test_painter as fixtures
from model import World, parse, child, value
from character_model import CharacterStore
from demographics import MapCatalogStore, Setup
from geography_model import GeographyStore, CLIMATES, MONTH_DAYS, WeatherPeriod, climate_preset, VP_LOC, STATE_LOC, REGION_LOC, vp_color, WEATHER_FIELDS


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
                self.assertEqual(set(n.weights),set(WEATHER_FIELDS));self.assertEqual(set(s.weights),set(WEATHER_FIELDS))
                n.validate();s.validate()
                self.assertEqual(n.start,f'0.{m}');self.assertEqual(n.end,f'{MONTH_DAYS[m]-1}.{m}');parse(n.script());parse(s.script())
                self.assertEqual((s.low,s.high,s.weights),(north[(m+6)%12].low,north[(m+6)%12].high,north[(m+6)%12].weights))

    def test_preset_weather_fields_have_climate_appropriate_values(self):
        for code in ('BWh','BWk','BSh','BSk'):
            self.assertTrue(all(float(p.weights['sandstorm'])>0 for p in climate_preset(code)))
        for code in ('Af','Cfb'):
            self.assertTrue(any(float(p.weights['rain_light'])>0 and float(p.weights['rain_heavy'])>0 and float(p.weights['mud'])>0 for p in climate_preset(code)))
        for code in ('Dfd','ET','EF'):
            self.assertTrue(any(all(float(p.weights[k])>0 for k in ('snow','blizzard','arctic_water','min_snow_level')) for p in climate_preset(code)))
        self.assertTrue(all(p.weights['sandstorm']=='0.000' and p.weights['snow']=='0.000' for p in climate_preset('Af')))

    def test_paint_climate_replaces_all_weather_only_undo_redo_and_save(self):
        path=self.world.regions[1]['path'];original=self.world.docs.text(path)
        # Include a native BOM/CRLF source and unknown custom weather fields.
        (self.root/path).write_bytes(('\ufeff'+original.replace('\n','\r\n')).encode('utf-8'))
        self.world=World(self.root);self.c=CharacterStore(self.world)
        self.g=GeographyStore(self.world,self.c,MapCatalogStore(self.world,self.c))
        self.world.docs.before_save=self.g.validate_save
        original=self.world.docs.text(path);node=child(parse(original)[0].children,'weather')
        outside=(original[:node.start],original[node.end:])
        self.assertTrue(self.g.paint_climate(1,'BWh','South'));painted=self.world.docs.text(path)
        weather=child(parse(painted)[0].children,'weather')
        self.assertEqual((painted[:weather.start],painted[weather.end:]),outside)
        self.assertNotIn('mystery = 7',painted);self.assertNotIn('custom_weight',painted)
        self.assertNotIn('\n',painted.replace('\r\n',''))
        self.assertEqual(self.g.preset_regions()[1],('BWh','South'))
        revision=self.world.docs.revision;self.assertFalse(self.g.paint_climate(1,'BWh','South'));self.assertEqual(revision,self.world.docs.revision)
        for rid,code,hemi in [(999,'Af','North'),(1,'bad','North'),(1,'Af','bad')]:
            with self.assertRaises(ValueError):self.g.paint_climate(rid,code,hemi)
            self.assertEqual(painted,self.world.docs.text(path))
        self.world.docs.undo();self.assertEqual(original,self.world.docs.text(path));self.assertNotIn(1,self.g.preset_regions())
        self.world.docs.redo();self.assertEqual(painted,self.world.docs.text(path));self.world.docs.save()
        blob=(self.root/path).read_bytes();self.assertTrue(blob.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\n',blob.replace(b'\r\n',b''))
        fresh=World(self.root);c=CharacterStore(fresh);g=GeographyStore(fresh,c,MapCatalogStore(fresh,c))
        self.assertEqual(g.preset_regions()[1],('BWh','South'));self.assertEqual(fresh.regions[1]['provinces'],{1,3,4})

    def test_koppen_brush_drag_pick_custom_and_sea_region(self):
        from types import SimpleNamespace
        from painter import Painter
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        messages=[];frames=[]
        app=SimpleNamespace(world=self.world,geography_store=self.g,brush=Var('Strategic regions'),koppen_paint=Var(True),koppen_south=Var(True),region_mode=Var('Edit region'),
            pick_only=False,drag_seen=set(),paint_selection={'Koppen presets':'Dfd'},palette_search=Var(''),_status=messages.append,schedule_map=lambda:frames.append(1),refresh_palette=lambda:None)
        app.building_scope=lambda:Painter.building_scope(app);app.palette_key=lambda:Painter.palette_key(app)
        event=SimpleNamespace(state=0)
        Painter.pick_geography(app,1,1,event);revision=self.world.docs.revision
        Painter.pick_geography(app,3,1,event);self.assertEqual(revision,self.world.docs.revision)
        Painter.pick_geography(app,2,2,event);self.assertEqual(self.g.preset_regions(),{1:('Dfd','South'),2:('Dfd','South')});self.assertEqual(len(frames),2)
        self.world.docs.undo();self.assertNotIn(2,self.g.preset_regions());self.world.docs.redo()
        app.drag_seen.clear();app.pick_only=True;app.paint_selection['Koppen presets']='Af';app.koppen_south.set(False);revision=self.world.docs.revision
        Painter.pick_geography(app,1,1,event);self.assertEqual(app.paint_selection['Koppen presets'],'Dfd');self.assertTrue(app.koppen_south.get())
        self.assertEqual(revision,self.world.docs.revision)
        # A custom pick retains the previous brush and hemisphere.
        self.g.edit_region(2,'Second region','',[]);app.drag_seen.clear()
        Painter.pick_geography(app,2,2,event);self.assertIn('custom weather',messages[-1]);self.assertEqual(app.paint_selection['Koppen presets'],'Dfd')
        # Region 1 becomes sea-only: weather painting must not require a state.
        r=self.g.region(2);self.g.edit_region(2,r['name'],r['terrain'],r['weather'],{1:2})
        app.pick_only=False;app.drag_seen.clear();app.koppen_south.set(False);app.paint_selection['Koppen presets']='ET'
        Painter.pick_geography(app,4,None,event);self.assertEqual(self.g.preset_regions()[1],('ET','North'))
        app.koppen_paint.set(False);self.assertEqual(app.palette_key(),'Strategic regions')

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


    def test_state_building_paint_includes_nonshared_counts_limits_save_and_undo(self):
        self.assertEqual({c.code for c in self.g.building_choices('State')},{'infrastructure','industrial_complex'})
        self.assertEqual(self.g.building_counts('infrastructure'),{1:2})
        self.assertEqual(self.g.change_building(1,'infrastructure','State',1),3)
        self.world.docs.undo();self.assertEqual(self.g.building_counts('infrastructure'),{1:2})
        self.world.docs.redo();self.world.docs.save()
        w=World(self.root);c=CharacterStore(w);g=GeographyStore(w,c,MapCatalogStore(w,c))
        self.assertEqual(g.building_counts('infrastructure'),{1:3});g.change_building(1,'infrastructure','State',2)
        with self.assertRaises(ValueError):g.change_building(1,'infrastructure','State',1)
        self.assertIn('1940.1.1 = { victory_points = { 1 99 } buildings = { infrastructure = 4 } }',w.docs.text(w.states[1].path))

    def test_province_paint_scope_caps_coast_supply_and_zero_floor(self):
        self.assertNotIn('rail_way',{c.code for c in self.g.building_choices('Province')})
        self.assertEqual(self.g.building_counts('bunker','Province'),{1:2})
        self.g.change_building(3,'bunker','Province',1);self.assertEqual(self.g.building_counts('bunker','Province'),{1:2,3:1})
        self.g.change_building(3,'bunker','Province',-1);self.g.change_building(3,'bunker','Province',-1)
        self.assertNotIn(3,self.g.building_counts('bunker','Province'))
        with self.assertRaises(ValueError):self.g.change_building(3,'naval_base','Province',1)
        with self.assertRaises(ValueError):self.g.change_building(1,'infrastructure','Province',1)
        self.g.change_building(3,'supply_node','Province',1);self.assertEqual(self.g.building_counts('supply_node','Province'),{2:1,3:1})
        self.g.change_building(3,'supply_node','Province',-1);self.assertEqual(self.g.supply_nodes(),{2:1})

    def test_building_map_gestures_scope_heatmap_and_no_zero_labels(self):
        from types import SimpleNamespace
        from painter import Painter
        from geography_model import building_color
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        app=SimpleNamespace(world=self.world,geography_store=self.g,brush=Var('States'),state_mode=Var('Buildings'),province_mode=Var('Buildings'),region_mode=Var('Assign states'),koppen_paint=Var(False),pick_only=False,drag_seen=set(),_building_delta=1,
            paint_selection={'State buildings':'infrastructure','Province buildings':'bunker','Strategic regions':2},scalar_modes={},_status=lambda *a:None,schedule_map=lambda:None,current_state=None,_paint_feedback=None)
        app.palette_key=lambda:Painter.palette_key(app);app.building_scope=lambda:Painter.building_scope(app);app.scalar_enabled=lambda:Painter.scalar_enabled(app)
        e=SimpleNamespace(state=0)
        Painter.pick_geography(app,1,1,e);Painter.pick_geography(app,3,1,e)
        self.assertEqual(self.g.building_counts('infrastructure'),{1:3})
        app.drag_seen.clear();app._building_delta=-1;Painter.pick_geography(app,1,1,e);self.assertEqual(self.g.building_counts('infrastructure'),{1:2})
        app.brush.set('Provinces');app.drag_seen.clear();app._building_delta=1
        Painter.pick_geography(app,3,1,e);Painter.pick_geography(app,1,1,e);self.assertEqual(self.g.building_counts('bunker','Province'),{1:3,3:1})
        self.world.map_ids=np.array([[1,3,2],[1,3,2]],dtype=np.int32);self.world.building_scope='Province';self.world.building_key='bunker'
        image=np.asarray(self.world.map_image('Buildings'));self.assertEqual(tuple(image[0,0]),building_color(3,3));self.assertEqual(tuple(image[0,1]),building_color(1,3));self.assertEqual(tuple(image[0,2]),building_color(0,3))
        from map_render import MapRenderer,MapConfig
        renderer=MapRenderer(self.world,self.g,self.c,self.g.catalogs)
        labels=renderer.annotations(MapConfig('Buildings',building_key='bunker',building_scope='Province'),1,(0,0,3,2));self.assertTrue(labels);self.assertFalse(any(r.get('text')=='0' for r in labels))
        app.brush.set('States');self.g.change_building(1,'infrastructure','State',-2)
        labels=renderer.annotations(MapConfig('Buildings',building_key='infrastructure'),1,(0,0,3,2));self.assertFalse(any(r.get('source')=='building' for r in labels))
        app.brush.set('Strategic regions');app.drag_seen.clear();Painter.pick_geography(app,1,1,e)
        self.assertEqual(self.world.regions[2]['provinces'],{1,2,3});self.assertEqual(self.world.states[1].provinces,[1,3])


    def test_category_edit_create_paint_and_slot_warning_colors(self):
        from geography_model import CATEGORY_LOC
        self.write(CATEGORY_LOC,'l_english:\n',True)
        self.g.edit_category('town','My town',4,'#123456',extra='\n# keep extra\nbuildings_max_level = { air_base = 2 }\n')
        self.assertEqual(self.g.categories()['town']['color'],(18,52,86));self.assertEqual(self.g.slot_summary()[1]['used'],1)
        self.world.map_ids=np.array([[1,3,2],[1,3,2]],dtype=np.int32)
        free=self.world.map_image('State categories').getpixel((0,0));self.assertEqual(free,(18,52,86))
        self.g.change_building(1,'industrial_complex','State',3);self.assertEqual(self.g.slot_summary()[1]['status'],'full')
        full=self.world.map_image('State categories').getpixel((0,0));self.assertNotEqual(full,free)
        self.g.change_building(1,'industrial_complex','State',1);self.assertEqual(self.g.slot_summary()[1]['status'],'over')
        over=self.world.map_image('State categories').getpixel((0,0));self.assertGreater(over[0],full[0])
        path=self.g.categories()['town']['path'];self.g.edit_category('new_city','New city',8,'#abcdef',path,create=True);self.g.set_category(1,'new_city')
        self.assertEqual(self.g.slot_summary()[1]['total'],8);self.assertIn('keep extra',self.world.docs.text(path))
        with self.assertRaises(ValueError):self.g.edit_category('new_city','Duplicate',3,'#ffffff',path,create=True)
        self.world.docs.save();fresh=World(self.root);c=CharacterStore(fresh);g=GeographyStore(fresh,c,MapCatalogStore(fresh,c))
        self.assertEqual(g.categories()['new_city']['name'],'New city');self.assertEqual(g.slot_summary()[1]['category'],'new_city')
        self.assertTrue((self.root/CATEGORY_LOC).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_resource_population_arithmetic_limits_and_strict_type_highlight(self):
        from decimal import Decimal
        self.g.change_resource(1,'oil',4,'Add');self.g.change_resource(1,'oil',2,'Multiply');self.assertEqual(self.g.resource_counts('oil')[1],8)
        self.g.change_resource(1,'oil',2,'Multiply',True);self.assertEqual(self.g.resource_counts('oil')[1],4)
        snapshot=dict(self.world.docs.drafts)
        with self.assertRaises(ValueError):self.g.change_resource(1,'oil',0,'Multiply',True)
        self.assertEqual(snapshot,self.world.docs.drafts)
        self.g.change_resource(1,'oil',5);self.g.change_resource(1,'oil',2,'Multiply',True);self.assertEqual(self.g.resource_counts('oil')[1],3)
        self.assertEqual(self.g.resource_type_counts()[1],2)
        self.world.map_ids=np.array([[1,3,2]],dtype=np.int32)
        normal=self.world.map_image('Resources',resource_key='steel',resource_highlight=2).getpixel((0,0))
        marked=self.world.map_image('Resources',resource_key='steel',resource_highlight=1).getpixel((0,0));self.assertGreater(marked[0],normal[0])
        self.g.change_resource(1,'oil',100,'Add',True);self.assertNotIn(1,self.g.resource_counts('oil'));self.assertEqual(self.g.resource_type_counts()[1],1)
        self.g.change_population(1,'101');self.g.change_population(1,'.5','Multiply');self.assertEqual(self.g.population_counts()[1],51)
        self.g.change_population(1,1000,'Add',True);self.assertNotIn(1,self.g.population_counts())
        with self.assertRaises(ValueError):self.g.change_population(1,0,'Multiply',True)
        with self.assertRaises(ValueError):self.g.change_population(1,'1.5')
        self.world.docs.save();self.assertEqual(Decimal(self.g.state(1)['attributes']['manpower']),0)

    def test_overlay_compositing_snapshots_live_data_and_number_visibility(self):
        from map_render import MapConfig,MapRenderer
        from PIL import Image
        from dataclasses import FrozenInstanceError
        self.world.map_ids=np.array([[1,3,2],[1,3,2]],dtype=np.int32)
        renderer=MapRenderer(self.world,self.g,self.c,self.g.catalogs);size=(300,200);box=(0,0,*size);zoom=100
        base=MapConfig('Resources',resource_key='steel',numbers=False);overlay=MapConfig('Population',numbers=False)
        a=renderer.render(base,size,box,zoom,False);b=renderer.render(overlay,size,box,zoom,False)
        self.assertEqual(renderer.composite(base,overlay,0,size,box,zoom,False).tobytes(),a.tobytes())
        self.assertEqual(renderer.composite(base,overlay,1,size,box,zoom,False).tobytes(),b.tobytes())
        self.assertEqual(renderer.composite(base,overlay,.5,size,box,zoom,False).tobytes(),Image.blend(a,b,.5).tobytes())
        with self.assertRaises(FrozenInstanceError):overlay.layer='Owners'
        self.g.change_population(1,400);self.g.change_population(2,200)
        self.assertNotEqual(renderer.render(overlay,size,box,zoom,False).tobytes(),b.tobytes())
        config=MapConfig('State categories')
        self.assertTrue(renderer.annotations(config,zoom,box));self.assertEqual(renderer.annotations(config,zoom,box,False),[])
        records=renderer.annotations(MapConfig('Buildings',building_key='industrial_complex'),zoom,box)
        self.assertTrue(any(r.get('text')=='1/4' for r in records));self.assertFalse(any(r.get('text')=='0' for r in records))

    def test_koppen_preset_detection_survives_save_and_custom_weather_is_gray(self):
        from geography_model import KOPPEN_COLORS
        self.world.map_ids=np.array([[1,3,2,4]],dtype=np.int32)
        r=self.g.region(2);self.g.edit_region(2,r['name'],'',climate_preset('Cfb','South'))
        self.assertEqual(self.g.preset_regions()[2],('Cfb','South'))
        self.assertEqual(self.world.map_image('Koppen presets').getpixel((2,0)),KOPPEN_COLORS['Cfb'])
        self.world.docs.save();w=World(self.root);c=CharacterStore(w);g=GeographyStore(w,c,MapCatalogStore(w,c));self.assertEqual(g.preset_regions()[2],('Cfb','South'))
        r=g.region(2);r['weather'][0].low='123';r['weather'][0].high='124';g.edit_region(2,r['name'],'',r['weather']);self.assertNotIn(2,g.preset_regions())
        w.map_ids=self.world.map_ids;self.assertEqual(w.map_image('Koppen presets').getpixel((2,0)),(128,128,128))

    def test_scalar_map_gestures_deduplicate_states_and_precise_editor(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from painter import Painter
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        variables=lambda:{'enabled':Var(True),'operation':Var('Add'),'amount':Var('4'),'precision':Var('0')}
        messages=[];app=SimpleNamespace(world=self.world,geography_store=self.g,brush=Var('States'),state_mode=Var('Resources'),pick_only=False,drag_seen=set(),_building_delta=1,
            paint_selection={'Resources':'oil'},scalar_modes={'Resources':variables(),'Population':variables()},_status=messages.append,schedule_map=lambda:None,current_state=None,root=None)
        app.palette_key=lambda:Painter.palette_key(app);app.building_scope=lambda:Painter.building_scope(app);app.paint_scalar=lambda *a:Painter.paint_scalar(app,*a)
        e=SimpleNamespace(state=0);Painter.pick_geography(app,1,1,e);Painter.pick_geography(app,3,1,e);self.assertEqual(self.g.resource_counts('oil')[1],4)
        app.drag_seen.clear();app._building_delta=-1;Painter.pick_geography(app,1,1,e);self.assertNotIn(1,self.g.resource_counts('oil'))
        app.scalar_modes['Resources']['operation'].set('Multiply');app.scalar_modes['Resources']['amount'].set('0');app.drag_seen.clear();before=dict(self.world.docs.drafts)
        Painter.pick_geography(app,1,1,e);self.assertEqual(before,self.world.docs.drafts);self.assertIn('zero',messages[-1])
        app.state_mode.set('Population');app._building_delta=1;app.drag_seen.clear();app.scalar_modes['Population']['enabled'].set(False)
        with patch('painter.simpledialog.askstring',return_value='321') as ask:Painter.pick_geography(app,1,1,e);Painter.pick_geography(app,3,1,e);ask.assert_called_once()
        self.assertEqual(self.g.population_counts()[1],321)

    def test_precision_range_integer_bounds_exact_zero_and_invalid_input(self):
        import random
        from unittest.mock import Mock
        from geography_model import arithmetic_operand
        rng=Mock();self.assertEqual(arithmetic_operand(50,0,rng),50);rng.randint.assert_not_called()
        for base,precision,bounds in [(50,10,(45,55)),(3,10,(3,3)),(50,200,(0,150)),(0,100,(0,0)),(200,'2.5',(195,205))]:
            rng.randint.return_value=bounds[0];self.assertEqual(arithmetic_operand(base,precision,rng),bounds[0]);rng.randint.assert_called_with(*bounds)
            rng.randint.return_value=bounds[1];self.assertEqual(arithmetic_operand(base,precision,rng),bounds[1])
        source=random.Random(42);values={arithmetic_operand(50,10,source) for _ in range(500)}
        self.assertEqual(values,set(range(45,56)))
        for amount,precision in [(-1,10),(50,-1),('1.5',0),(50,'NaN'),('bad',10),(50,'Infinity')]:
            with self.subTest(amount=amount,precision=precision),self.assertRaises(ValueError):arithmetic_operand(amount,precision)

    def test_text_color_catalog_native_replacements_case_and_global_scope(self):
        catalog=self.g.catalogs;game=self.c.game_root/'interface';game.mkdir()
        (game/'core.gfx').write_text('bitmapfonts={textcolors={V={1 2 3}}}')
        (game/'extra.gfx').write_text('bitmapfonts={textcolors={X={4 5 6} # Extra vanilla\n}}')
        self.write('interface/core.gfx','''bitmapfonts={textcolors={
            B={0 0 255} # Blue
            b={0 0 0} # Black
            h={255 255 183} # Thalothin colour
            0={203 0 203} # Gradient Step 0 - purple
        } bitmapfont={name=test textcolors={B={90 80 70}}}}''')
        colors=catalog.text_colors();self.assertEqual(set(colors),{'B','b','h','0','X'})
        self.assertEqual(colors['B']['color'],(0,0,255));self.assertEqual(colors['b']['color'],(0,0,0));self.assertEqual(colors['h']['name'],'Thalothin colour')
        self.world.docs.replace('interface/core.gfx',self.world.docs.text('interface/core.gfx').replace('255 255 183','200 201 202'))
        self.assertEqual(catalog.text_colors()['h']['color'],(200,201,202));self.world.docs.undo();self.assertEqual(catalog.text_colors()['h']['color'],(255,255,183))

    def test_random_arithmetic_gestures_per_state_and_province_keep_limits(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from painter import Painter
        class Var:
            def __init__(self,v):self.v=v
            def get(self):return self.v
            def set(self,v):self.v=v
        modes={k:{'enabled':Var(True),'operation':Var('Add'),'amount':Var('50'),'precision':Var('10')} for k in ('Resources','Population','State buildings','Province buildings')}
        messages=[];app=SimpleNamespace(world=self.world,geography_store=self.g,brush=Var('States'),state_mode=Var('Resources'),province_mode=Var('Buildings'),pick_only=False,drag_seen=set(),_building_delta=1,
            paint_selection={'Resources':'steel','State buildings':'industrial_complex','Province buildings':'bunker'},scalar_modes=modes,_status=messages.append,schedule_map=lambda:None,current_state=None)
        app.palette_key=lambda:Painter.palette_key(app);app.building_scope=lambda:Painter.building_scope(app);app.scalar_enabled=lambda:Painter.scalar_enabled(app);app.paint_scalar=lambda *a:Painter.paint_scalar(app,*a)
        event=SimpleNamespace(state=0)
        with patch('painter.arithmetic_operand',side_effect=[45,55]) as roll:
            Painter.pick_geography(app,1,1,event);Painter.pick_geography(app,3,1,event);Painter.pick_geography(app,2,2,event)
            self.assertEqual(roll.call_count,2);self.assertEqual(self.g.resource_counts('steel'),{1:47,2:55})
        app.state_mode.set('Population');app.drag_seen.clear()
        with patch('painter.arithmetic_operand',return_value=55):Painter.pick_geography(app,1,1,event)
        self.assertEqual(self.g.population_counts()[1],255)
        for brush,mode,ident,scope in [('States','State buildings',1,'State'),('Provinces','Province buildings',1,'Province')]:
            app.brush.set(brush);app.state_mode.set('Buildings');variables=modes[mode];variables['amount'].set('3');variables['precision'].set('0');app._building_delta=1;app.drag_seen.clear()
            kind=app.paint_selection[mode];initial=self.g.building_counts(kind,scope)[ident]
            Painter.pick_geography(app,1,1,event);Painter.pick_geography(app,3 if scope=='State' else 1,1,event)
            self.assertEqual(self.g.building_counts(kind,scope)[ident],initial+3)
            variables['operation'].set('Multiply');variables['amount'].set('2');app.drag_seen.clear();Painter.pick_geography(app,1,1,event)
            self.assertEqual(self.g.building_counts(kind,scope)[ident],(initial+3)*2)
            app._building_delta=-1;app.drag_seen.clear();Painter.pick_geography(app,1,1,event);self.assertEqual(self.g.building_counts(kind,scope)[ident],initial+3)
            variables['amount'].set('0');app.drag_seen.clear();before=dict(self.world.docs.drafts);Painter.pick_geography(app,1,1,event);self.assertEqual(before,self.world.docs.drafts);self.assertIn('zero',messages[-1])
            variables['amount'].set('50');app._building_delta=1;app.drag_seen.clear();Painter.pick_geography(app,1,1,event);self.assertEqual(before,self.world.docs.drafts);self.assertIn('maximum',messages[-1])
        self.g.change_building_amount(1,'bunker','Province',2,'Multiply',True);self.assertEqual(self.g.building_counts('bunker','Province')[1],3)
        with self.assertRaises(ValueError):self.g.change_building_amount(3,'naval_base','Province',1)
        self.world.docs.undo();self.assertEqual(self.g.building_counts('bunker','Province')[1],5)
        self.world.docs.redo();self.world.docs.save();fresh=World(self.root);c=CharacterStore(fresh);g=GeographyStore(fresh,c,MapCatalogStore(fresh,c))
        self.assertEqual(g.building_counts('bunker','Province')[1],3);self.assertEqual(g.building_counts('industrial_complex')[1],4)


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

    def test_koppen_paint_checkbox_palette_hemisphere_and_map_gestures(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from model import Emblems
        from painter import Painter
        from demographics import CATALOG_PATHS
        from geography_model import KOPPEN_COLORS
        for rel in set(CATALOG_PATHS.values()):
            if not (self.root/rel).exists():self.write(rel,'l_english:\n' if rel.endswith('.yml') else '',rel.endswith('.yml'))
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        self.world.map_ids=np.array([[1,3,2,4]],dtype=np.int32)
        with patch('character_model.default_paths',return_value={'game':self.c.game_root}):app=Painter(self.tkroot,self.world,Emblems())
        self.tkroot.deiconify();self.tkroot.update()
        app.brush.set('Strategic regions');app.brush_changed();self.tkroot.update()
        app.koppen_paint_check.invoke();self.tkroot.update()
        self.assertEqual(app.palette_key(),'Koppen presets');self.assertEqual(set(app.palette_values.values()),set(CLIMATES))
        self.assertTrue(app.koppen_south_check.winfo_ismapped());self.assertTrue(app.koppen_show.get())
        self.assertEqual(app.map_config().layer,'Koppen presets');self.assertEqual(str(app.new_definition_button['state']),'disabled')
        app.palette_search.set('hot desert');app.refresh_palette();self.assertEqual(list(app.palette_values.values()),['BWh'])
        item=next(iter(app.palette_values));app.palette.selection_set(item);app.palette_selected();self.tkroot.update()
        app.koppen_south_check.invoke();self.assertTrue(app.koppen_south.get());self.assertIn('(South)',app.paint_label.get())
        event=SimpleNamespace(x=0,y=0,state=0)
        # Exercise the real canvas coordinate route and release/refresh callbacks.
        app.zoom=1;app.canvas.xview_moveto(0);app.canvas.yview_moveto(0)
        app.paint_press(event);app.paint_release();self.tkroot.update()
        self.assertEqual(app.geography_store.preset_regions()[1],('BWh','South'))
        self.assertEqual(app.world.map_image('Koppen presets').getpixel((0,0)),KOPPEN_COLORS['BWh'])
        app.undo();self.assertNotIn(1,app.geography_store.preset_regions());app.redo()
        app.koppen_south_check.invoke();app.paint_selection['Koppen presets']='Af'
        app.paint_press(SimpleNamespace(x=3,y=0,state=1));app.paint_release();self.tkroot.update()
        self.assertEqual(app.paint_selection['Koppen presets'],'BWh');self.assertTrue(app.koppen_south.get());self.assertEqual(app.palette_search.get(),'')
        # Disabling paint restores the region list and original edit/assignment controls.
        app.koppen_paint_check.invoke();self.tkroot.update()
        self.assertEqual(app.palette_key(),'Strategic regions');self.assertEqual(set(app.palette_values.values()),{1,2})
        self.assertFalse(app.koppen_south_check.winfo_ismapped());self.assertFalse(self.errors)
        app.cancel_map_job();app.destroy()

    def test_category_form_edits_native_source_and_cancel_restores_it(self):
        from geography_ui import CategoryDialog
        from geography_model import CATEGORY_LOC
        self.write(CATEGORY_LOC,'l_english:\n',True)
        d=CategoryDialog(self.tkroot,self.app,'town');d.attributes('-alpha',0);d.slots.set('6');d.color.set('#ff0088');d.ok()
        self.assertEqual(self.g.categories()['town']['slots'],6)
        self.world.docs.undo();self.assertEqual(self.g.categories()['town']['slots'],4)
        d=CategoryDialog(self.tkroot,self.app,'town');d.attributes('-alpha',0);d.slots.set('99');d.cancel();self.assertEqual(self.g.categories()['town']['slots'],4)
        d=CategoryDialog(self.tkroot,self.app,None);d.attributes('-alpha',0);d.ident.set('test');d.name.set('Test');d.ok()
        self.assertIn('test',self.g.categories())


if __name__=='__main__':unittest.main()
