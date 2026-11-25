"""Native railway topology, province gestures, compaction and hub rendering."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest

import numpy as np
from PIL import Image

from model import World, Emblems
from character_model import CharacterStore
from demographics import MapCatalogStore, CATALOG_PATHS, Setup
from geography_model import GeographyStore
from map_render import MapConfig, MapRenderer
from railway_model import RailwayStore, RAILWAY_PATH, compact_routes, edge_key, railway_color


class RailwayTests(unittest.TestCase):
    def write(self, name, text, bom=False):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(text.encode('utf-8-sig' if bom else 'utf-8'))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'mod';self.root.mkdir()
        self.game=Path(self.temp.name)/'game';(self.game/'common/defines').mkdir(parents=True)
        (self.game/'common/defines/00_defines.lua').write_text('NSupply = {\n MAX_RAILWAY_LEVEL = 5,\n}\n')
        self.write('descriptor.mod','name="Fixture"')
        self.write('common/on_actions/LOK_on_actions.txt','on_actions={on_startup={effect={}}}')
        self.write('common/country_tags/tags.txt','AAA="countries/AAA.txt"')
        self.write('common/countries/AAA.txt','color={100 120 140}')
        self.write('history/countries/AAA.txt','capital=1')
        self.write('common/buildings/buildings.txt','buildings={rail_way={level_cap={province_max=1}} supply_node={level_cap={province_max=1} supply_node=yes}}')
        self.write('history/states/one.txt','state={id=1 name=ONE provinces={1 2 3 4 5 6 7 8 9} history={owner=AAA}}')
        self.write('history/states/two.txt','state={id=2 name=TWO provinces={11} history={owner=AAA}}')
        self.write('map/strategicregions/one.txt','strategic_region={id=1 name=REG provinces={1 2 3 4 5 6 7 8 9 10 11}}')
        definitions=''.join(f'{i};{i};{i+20};{i+40};'+('sea' if i in {0,10} else 'land')+';false;plains;1\n' for i in range(12))
        self.write('map/definition.csv',definitions)
        self.ids=np.array([[1,2,3,10],[4,5,6,10],[7,8,9,11]],dtype=np.int32)
        rgb=np.array([[(int(p),int(p)+20,int(p)+40) for p in row] for row in self.ids],dtype=np.uint8)
        Image.fromarray(rgb).save(self.root/'map/provinces.bmp')
        self.write('map/railways.txt','2 3 1 2 3\n1 3 2 5 8\n3 2 5 6\n1 2 8 9\n')
        self.write('map/supply_nodes.txt','1 5\n');self.write('map/adjacencies.csv','From;To;Type\n')
        for rel in set(CATALOG_PATHS.values()):
            if not (self.root/rel).exists():self.write(rel,'l_english:\n' if rel.endswith('.yml') else '',rel.endswith('.yml'))
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        self.world=World(self.root);self.world.demographics=Setup(self.world).load()
        self.characters=CharacterStore(self.world);self.characters.game_root=self.game
        self.catalog=MapCatalogStore(self.world,self.characters);self.geo=GeographyStore(self.world,self.characters,self.catalog)
        self.rail=RailwayStore(self.world,self.geo,self.characters)
        self.world.docs.before_save=self.prepare_save

    def prepare_save(self):
        self.geo.validate_save();self.rail.prepare_save()

    def tearDown(self):self.temp.cleanup()

    def test_native_level_cap_overrides_building_cap(self):
        self.assertEqual(self.rail.max_level(),5)
        self.write('common/defines/z.lua','NDefines.NSupply.MAX_RAILWAY_LEVEL = 7')
        self.rail._maximum=None;self.assertEqual(self.rail.max_level(),7)

    def test_exact_and_add_remove_levels_are_incident_and_once_per_stroke(self):
        before=dict(self.rail.edges());seen=set()
        self.rail.change_province(2,1,'Change',2,existing_only=True,seen=seen)
        self.assertEqual(self.rail.edges()[(1,2)],4);self.assertEqual(self.rail.edges()[(2,5)],3)
        self.rail.change_province(1,1,'Change',2,existing_only=True,seen=seen)
        self.assertEqual(self.rail.edges()[(1,2)],4)
        self.assertEqual(self.rail.edges()[(5,6)],before[(5,6)])
        self.rail.change_province(2,1,'Change',5,existing_only=True)
        self.assertEqual(self.rail.levels()[2],5)
        self.rail.change_province(2,1,'Change',5,reverse=True,existing_only=True)
        self.assertNotIn(2,self.rail.levels())
        self.world.docs.undo();self.assertEqual(self.rail.levels()[2],5)
        self.world.docs.redo();self.assertNotIn(2,self.rail.levels())
        self.rail.change_province(5,4,existing_only=True)
        self.assertEqual(self.rail.edges()[(5,6)],4)

    def test_existing_only_never_creates_links_or_provinces(self):
        before=dict(self.rail.edges());vertices=set(self.rail.levels())
        for pid in range(1,10):self.rail.change_province(pid,5,existing_only=True)
        self.assertEqual(set(before),set(self.rail.edges()));self.assertEqual(vertices,set(self.rail.levels()))
        self.assertEqual(self.rail.change_province(7,5,existing_only=True),0)
        self.rail.change_province(7,2)
        self.assertIn((7,8),self.rail.edges());self.assertNotIn((4,7),self.rail.edges())

    def test_new_route_uses_neighboring_painted_points_only_and_right_never_creates(self):
        self.world.docs.replace(RAILWAY_PATH,'')
        self.assertEqual(self.rail.change_province(7,3),0)
        self.assertEqual(self.rail.change_province(8,3,anchor=7),1)
        self.rail.change_province(9,3,anchor=8)
        self.assertEqual(self.rail.edges(),{(7,8):3,(8,9):3})
        self.rail.change_province(4,3,reverse=True,anchor=7)
        self.assertNotIn(4,self.rail.levels())
        self.rail.change_province(1,3,anchor=9)
        self.assertNotIn(1,self.rail.levels())

    def test_topology_uses_bitmap_wrap_no_diagonals_and_explicit_impassable(self):
        adjacency=self.rail.adjacency()
        self.assertIn((1,2),adjacency);self.assertNotIn((1,5),adjacency)
        self.assertIn((7,11),adjacency)  # horizontal wrap
        self.assertNotIn((3,10),adjacency)
        self.write('map/adjacencies.csv','From;To;Type\n7;8;impassable\n')
        self.world.docs.originals.pop('map/adjacencies.csv',None);self.rail._adjacency=None
        self.assertNotIn((7,8),self.rail.adjacency())
        self.world.map_ids=self.ids.copy();self.world.map_ids[0,0]=9
        # Immutable geometry changes only on reload; no disk graph caches.
        self.assertNotIn((1,5),self.rail.adjacency())

    def test_compaction_keeps_branches_loops_levels_and_each_edge_once(self):
        cases=[{(1,2):2,(2,3):2,(2,5):2,(5,8):2},
               {(1,2):1,(2,5):1,(4,5):1,(1,4):1},
               {(1,2):1,(2,3):3,(2,5):1,(5,8):2}]
        for edges in cases:
            routes=compact_routes(edges);out={};count=0
            for level,provinces in routes:
                self.assertGreaterEqual(len(provinces),2);self.assertEqual(len(provinces),len(set(provinces)))
                for a,b in zip(provinces,provinces[1:]):out[edge_key(a,b)]=level;count+=1
            self.assertEqual(out,edges);self.assertEqual(count,len(edges));self.assertEqual(routes,compact_routes(dict(reversed(list(edges.items())))))

    def test_overlaps_max_level_and_save_reload_preserve_network_comments_encoding(self):
        original=b'\xef\xbb\xbf# railway note\r\n1 3 1 2 3 # inline\r\n4 2 1 2\r\n'
        (self.root/RAILWAY_PATH).write_bytes(original)
        self.assertEqual(self.rail.edges(),{(1,2):4,(2,3):1})
        self.rail.change_province(3,2,existing_only=True)
        expected=dict(self.rail.edges());self.world.docs.save()
        blob=(self.root/RAILWAY_PATH).read_bytes();self.assertTrue(blob.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\n',blob.replace(b'\r\n',b''));self.assertIn(b'# inline',blob);self.assertIn(b'# railway note',blob)
        fresh=World(self.root);characters=CharacterStore(fresh);characters.game_root=self.game
        geo=GeographyStore(fresh,characters,MapCatalogStore(fresh,characters));rail=RailwayStore(fresh,geo,characters)
        self.assertEqual(rail.edges(),expected)
        revision=fresh.docs.revision;rail.write_edges(dict(rail.edges()));self.assertEqual(fresh.docs.revision,revision)

    def test_known_bad_links_preserved_new_bad_links_rejected(self):
        self.write(RAILWAY_PATH,'2 3 1 2 3\n3 2 1 9\n')
        self.assertEqual(self.rail.invalid_links(),{(1,9)})
        self.rail.change_province(2,4,existing_only=True)
        self.assertIn((1,9),self.rail.edges());self.assertEqual(self.rail.edges()[(1,9)],3)
        before=self.world.docs.text(RAILWAY_PATH)
        with self.assertRaises(ValueError):self.rail.write_edges({**self.rail.edges(),(1,8):1})
        self.assertEqual(before,self.world.docs.text(RAILWAY_PATH))

    def test_wrap_link_draws_at_map_edges_and_impassable_states_reject_new_links(self):
        self.world.docs.replace(RAILWAY_PATH,'2 2 7 11\n')
        self.world.load_map();renderer=MapRenderer(self.world,self.geo,self.characters,self.catalog)
        canvas=Image.new('RGB',(160,120),'black');renderer.railway_lines(canvas,(0,0,160,120),40)
        self.assertEqual(canvas.getpixel((80,80)),(0,0,0))
        self.assertEqual(canvas.getpixel((0,80)),railway_color(2,5))
        path='history/states/one.txt'
        self.world.docs.replace(path,self.world.docs.text(path).replace('name=ONE','name=ONE impassable=yes'))
        self.assertNotIn((7,11),self.rail.adjacency())
        self.assertNotIn((7,11),self.rail.baseline_invalid())
        self.assertEqual(self.rail.change_province(9,2,anchor=11),0)
        with self.assertRaises(ValueError):self.rail.prepare_save()
        self.world.docs.undo();self.assertIn((7,11),self.rail.adjacency())
        self.rail.prepare_save()

    def test_invalid_inputs_and_malformed_routes_are_atomic(self):
        before=self.world.docs.text(RAILWAY_PATH)
        for args in [(10,2),(999,1),(1,6),(1,-1),(1,'NaN'),(1,1,'Change',0),(1,1,'Change',1.5)]:
            with self.assertRaises(ValueError):self.rail.change_province(*args)
            self.assertEqual(before,self.world.docs.text(RAILWAY_PATH))
        for text in ['1 1 1','1 3 1 2','0 2 1 2','6 2 1 2','1 2 1 10','1 2 1 1','1 2 1 x']:
            with self.assertRaises(ValueError):self.rail.parse_edges(text)

    def test_guarded_save_rejects_external_changes(self):
        self.rail.change_province(2,4,existing_only=True)
        (self.root/RAILWAY_PATH).write_text('external\n')
        with self.assertRaises((ValueError,OSError)):self.world.docs.save()
        self.assertEqual((self.root/RAILWAY_PATH).read_text(),'external\n')

    def test_railway_colors_annotations_hub_logo_crop_and_overlay(self):
        from PIL import ImageDraw
        art=Image.new('RGBA',(52,26));ImageDraw.Draw(art).rectangle((0,0,25,25),fill='red');ImageDraw.Draw(art).rectangle((26,0,51,25),fill='blue')
        path=self.root/'gfx/interface/hub.dds';path.parent.mkdir(parents=True);art.save(path)
        self.write('interface/supply.gfx','spriteTypes={spriteType={name="GFX_supply_hub_icon_strip" texturefile="gfx/interface/hub.dds" noOfFrames=2}}')
        renderer=MapRenderer(self.world,self.geo,self.characters,self.catalog)
        config=MapConfig('Railways',supply_hubs=True,numbers=False)
        self.world.load_map();image=self.world.map_image('Railways')
        self.assertEqual(image.getpixel((1,0)),railway_color(2,5));self.assertEqual(image.getpixel((0,2)),railway_color(0))
        rows=renderer.annotations(config,20,(0,0,80,60));hubs=[r for r in rows if r.get('source')=='supply_hub']
        self.assertEqual(len(hubs),1);self.assertEqual(hubs[0]['province'],5);self.assertEqual(hubs[0]['image'].getpixel((12,12)),(255,0,0,255))
        self.assertFalse(any(r.get('source')=='supply_hub' for r in renderer.annotations(MapConfig('Railways'),20,(0,0,80,60))))
        self.assertTrue(any(r.get('source')=='railway' for r in renderer.annotations(MapConfig('Railways'),20,(0,0,80,60))))
        size=(80,60);full=renderer.render(config,size,(0,0,*size),20);crop=renderer.render(config,size,(15,5,65,55),20)
        self.assertEqual(crop.tobytes(),full.crop((15,5,65,55)).tobytes())
        self.assertEqual(renderer.composite(config,MapConfig('Provinces'),0,size,(0,0,*size),20).tobytes(),full.tobytes())

    def test_history_defined_vp_hub_overlay_updates_when_removed(self):
        path=self.root/'gfx/interface/hub.dds';path.parent.mkdir(parents=True)
        Image.new('RGBA',(26,26),'yellow').save(path)
        self.write('interface/supply.gfx','spriteTypes={spriteType={name="GFX_supply_hub_icon_strip" texturefile="gfx/interface/hub.dds"}}')
        state='history/states/one.txt';text=self.world.docs.text(state)
        self.world.docs.replace(state,text.replace('history={owner=AAA}','history={owner=AAA victory_points={2 5} buildings={2={supply_node=1}}}'))
        renderer=MapRenderer(self.world,self.geo,self.characters,self.catalog);config=MapConfig('VPs',supply_hubs=True)
        rows=renderer.annotations(config,20,(0,0,80,60))
        self.assertEqual({r['province'] for r in rows if r.get('source')=='supply_hub'},{2,5})
        self.assertTrue(any(r['kind']=='vp' for r in rows))
        self.geo.change_building(2,'supply_node','Province',-1)
        self.assertEqual({r['province'] for r in renderer.annotations(config,20,(0,0,80,60)) if r.get('source')=='supply_hub'},{5})
        self.assertIn(2,self.geo.victory_points())

    def test_actual_ui_exact_delta_guard_drag_and_hub_toggle(self):
        import tkinter as tk
        from painter import Painter
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0);errors=[]
        root.report_callback_exception=lambda typ,val,tb:errors.append(val)
        try:
            with patch('character_model.default_paths',return_value={'game':self.game}):app=Painter(root,self.world,Emblems())
            root.deiconify();root.update();app.layer.set('Provinces');app.province_mode.set('Railways');app.layer_changed();root.update()
            self.assertEqual(app.brush.get(),'Provinces');self.assertEqual(app.map_config().layer,'Railways');self.assertEqual(set(app.palette_values.values()),set(range(6)))
            self.assertEqual(app.paint_scope_box.cget('state'),'disabled');self.assertTrue(app.railway_existing_check.winfo_ismapped())
            app.railway_existing_check.invoke();app.railway_operation.set('Change');app.railway_amount.set('2')
            app.zoom=20;app.draw_map();root.update();e=SimpleNamespace(x=20,y=0,state=0)
            app.paint_press(e);app.paint_release();self.assertEqual(app.railway_store.edges()[(1,2)],4)
            app.right_press(e);app.paint_release();self.assertEqual(app.railway_store.edges()[(1,2)],2)
            app.supply_hubs_check.invoke();self.assertTrue(app.map_config().supply_hubs);app.save_overlay();self.assertTrue(app.overlay_config.supply_hubs)
            app.railway_existing_check.invoke();self.world.docs.replace(RAILWAY_PATH,'');app._sync()
            app.railway_operation.set('Set');item=next(i for i,v in app.palette_values.items() if v==3)
            app.palette.selection_set(item);app.palette_selected();app.zoom=20;app.draw_map();root.update()
            app.paint_press(SimpleNamespace(x=0,y=40,state=0));app.pick(SimpleNamespace(x=40,y=40,state=0));app.paint_release()
            self.assertEqual(app.railway_store.edges(),{(7,8):3,(8,9):3})
            app.paint_press(SimpleNamespace(x=20,y=40,state=1));app.paint_release();self.assertEqual(app.paint_selection['Railways'],3)
            self.assertFalse(errors,errors);app.cancel_map_job()
        finally:root.destroy()


if __name__=='__main__':unittest.main()
