"""Reserved portrait groups, native country pools, art and mapped forms."""
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

import test_countries as country_fixtures
from model import World, parse, value
from character_model import CharacterStore
from country_model import Country, CountryStore
from demographics import MapCatalogStore, CATALOG_PATHS
from generic_portrait_model import PORTRAITS, GENERIC_GFX, PLACEHOLDERS
from small_portrait import generate_small_portrait


class GenericPortraitTests(unittest.TestCase):
    def setUp(self):
        self.fixture=country_fixtures.CountryTests();self.fixture.setUp()
        self.root=self.fixture.root;self.world=self.fixture.world;self.c=self.fixture.characters
        self.countries=self.fixture.store;self.store=self.c.generic_portraits
        self.body='''{ political={democratic={male={"GFX_portrait_species_0_civilian_1"} female={"GFX_portrait_species_0_civilian_4"}}}
 army={male={"GFX_portrait_species_0_military_1"} female={"GFX_portrait_species_0_military_4"}}
 navy={male={"GFX_portrait_species_0_military_1"} female={"GFX_portrait_species_0_military_3"}}
 operative={male={"GFX_portrait_species_0_spy_1"} female={"GFX_portrait_species_0_spy_2"}}
 scientist={male={"GFX_portrait_species_0_scientist_1"} female={"GFX_portrait_species_0_scientist_3"}} }'''
        self.write(PORTRAITS,'# keep heading\n### Species_0 ########\nAAA = '+self.body+'\nBBB = '+self.body.replace('army={','private_field = yes # BBB note\n army={',1)+'\n### Species_61 ########\n### Species_100 ########\n### Amphibian_Species ########\nCCC = '+self.body.replace('species_0_','species_amphibian_')+'\n### Roqualian_Species ########\n')
        self.write('portraits/misc_portraits.txt','# untouched external\nDDD={army={male={"GFX_other"}}}\nEEE={preserve=yes}\n')
        self.write('localisation/english/generic_test_l_english.yml','l_english:\n var_species_61:0 "\u00154Altarian\u0015!"\n',True)
        sprites=[]
        for prefix in ('species_0','species_61','species_100','species_amphibian','species_roqualian'):
            for kind,count in PLACEHOLDERS.items():
                for index in range(1,count+1):
                    for suffix in ('','_small'):
                        sprites.append('spriteType={name="GFX_portrait_'+prefix+'_'+kind+str('_'+str(index))+suffix+'" texturefile="gfx/placeholder.tga"}')
        self.write(GENERIC_GFX,'spriteTypes={'+''.join(sprites)+'}')
        p=self.root/'gfx/placeholder.tga';p.parent.mkdir(exist_ok=True);Image.new('RGBA',(156,210),'gray').save(p)
        for folder,size in [('large_portraits',(156,210)),('small_portraits',(65,67))]:
            for kind,count in PLACEHOLDERS.items():
                for index in range(1,count+1):
                    p=self.root/f'gfx/leaders/{folder}/generic/placeholder/{kind}_{index}.tga'
                    p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGBA',size,'gray').save(p)
        self.source=self.root/'upload.png';Image.new('RGBA',(220,250),(12,80,190,255)).save(self.source)

    def write(self,path,text,bom=False):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig' if bom else 'utf-8')

    def tearDown(self):self.fixture.tearDown()

    def test_reserved_slots_special_groups_and_species_names_are_native_and_read_only(self):
        groups=self.store.groups()
        self.assertEqual(groups['Species_61'].name,'Altarian');self.assertEqual(groups['Species_61'].tags,())
        self.assertEqual(groups['Species_0'].tags,('AAA','BBB'));self.assertIn('Roqualian_Species',groups)
        self.assertEqual(len(groups['Species_61'].pools),26)
        before=dict(self.world.docs.drafts);self.store.ensure_species(61);self.assertEqual(self.world.docs.drafts,before)
        self.store.ensure_species(101);self.assertIn('Species_101',self.store.groups())
        for refs in self.store.groups()['Species_101'].pools.values():
            for ref in refs:self.assertTrue(self.c.sprite_entries(ref));self.assertTrue(self.c.sprite_entries(ref+'_small'))
        self.world.docs.undo();self.assertNotIn('Species_101',self.store.groups())

    def test_shared_pool_update_preserves_country_specific_fields_and_sections(self):
        before=self.world.docs.text(PORTRAITS);special=before[before.index('### Amphibian_Species'):]
        refs=['GFX_portrait_species_0_military_2','GFX_portrait_species_0_military_3']
        self.store.set_pool('Species_0','army/male',refs)
        after=self.world.docs.text(PORTRAITS);self.assertIn('private_field = yes # BBB note',after)
        self.assertEqual(after[after.index('### Amphibian_Species'):],special)
        for n in parse(after):
            if n.key in {'AAA','BBB'}:self.assertEqual(self.store.pools(value(after,n))['army/male'],tuple(refs))
        self.world.docs.undo();self.assertEqual(self.world.docs.text(PORTRAITS),before)
        self.world.docs.redo();self.assertEqual(self.store.groups()['Species_0'].pools['army/male'],tuple(refs))

    def test_upload_replace_generates_small_never_overwrites_shared_placeholder_and_is_atomic(self):
        original=(self.root/'gfx/placeholder.tga').read_bytes()
        ref=self.store.groups()['Species_61'].pools['army/male'][0]
        self.store.upload('Species_61','army/male',[self.source],replace=ref)
        image=self.c.image(ref);small=self.c.image(ref+'_small')
        self.assertEqual(image.size,(156,210));self.assertEqual(small.size,(65,67))
        self.assertEqual(small.tobytes(),generate_small_portrait(image).tobytes())
        self.assertEqual((self.root/'gfx/placeholder.tga').read_bytes(),original)
        self.assertEqual(self.c.image('GFX_portrait_species_0_military_1').getpixel((20,20)),(128,128,128,255))
        before=dict(self.world.docs.drafts)
        with self.assertRaises(OSError):self.store.upload('Species_61','army/female',[self.source,self.root/'missing.png'])
        self.assertEqual(self.world.docs.drafts,before)
        self.world.docs.undo();self.assertEqual(self.c.sprite_entries(ref)[0]['texture'],'gfx/placeholder.tga')

    def test_unassigned_pool_persists_then_assigns_to_country_and_save_reload(self):
        refs=self.store.upload('Species_61','political/neutrality/female',[self.source])
        self.assertEqual(len(refs),4);self.assertEqual(self.store.groups()['Species_61'].tags,())
        self.world.docs.save();world=World(self.root);c=CharacterStore(world);c.game_root=self.fixture.game
        store=c.generic_portraits
        self.assertEqual(store.groups()['Species_61'].pools['political/neutrality/female'],refs)
        store.assign_country('DDD','Species_61')
        self.assertEqual(store.group_for_country('DDD'),'Species_61')
        external=world.docs.text('portraits/misc_portraits.txt');self.assertIn('EEE={preserve=yes}',external);self.assertNotIn('DDD=',external)
        self.assertIn(refs[0],world.docs.text(PORTRAITS));world.docs.save()
        fresh=CharacterStore(World(self.root));self.assertEqual(fresh.generic_portraits.group_for_country('DDD'),'Species_61')
        fresh.generic_portraits.assign_country('DDD','')
        self.assertIsNone(fresh.generic_portraits.group_for_country('DDD'))
        self.assertEqual(fresh.generic_portraits.groups()['Species_61'].pools['political/neutrality/female'],refs)

    def test_country_creation_selection_native_tag_membership_atomic_undo_and_reassignment(self):
        names={i:{'name':None,'def':None} for i in ('','democratic','neutrality')};names['']['name']='New country'
        d=Country('QQQ','','New country',capital='2',ruling='neutrality',popularities={'neutrality':'100'},names=names,portrait_group='Species_61')
        before=self.world.docs.text(PORTRAITS);self.countries.apply(d,'#123456',names,create=True)
        self.assertEqual(self.countries.read('QQQ').portrait_group,'Species_61')
        self.world.docs.undo();self.world.refresh_countries();self.assertEqual(self.world.docs.text(PORTRAITS),before);self.assertNotIn('QQQ',self.world.country_paths)
        self.world.docs.redo();self.world.refresh_countries()
        d=self.countries.read('QQQ');d.portrait_group='Amphibian_Species';self.countries.apply(d,'#123456',d.names)
        self.assertEqual(self.store.group_for_country('QQQ'),'Amphibian_Species')
        self.assertEqual(sum(n.key=='QQQ' for n in parse(self.world.docs.text(PORTRAITS))),1)

    def test_invalid_group_pool_reference_and_empty_pool_do_not_mutate_drafts(self):
        before=dict(self.world.docs.drafts)
        for action in [lambda:self.store.assign_country('AAA','missing'),lambda:self.store.set_pool('Species_0','army/male',[]),lambda:self.store.set_pool('Species_0','army/male',['GFX_missing']),lambda:self.store.set_pool('Species_0','unsupported/male',['GFX_portrait_species_0_military_1'])]:
            with self.assertRaises(ValueError):action()
            self.assertEqual(self.world.docs.drafts,before)

    def test_vacant_species_defaults_and_new_placeholders_are_independent_of_species_zero_edits(self):
        before=dict(self.store.groups()['Species_61'].pools)
        self.store.upload('Species_0','army/male',[self.source],replace='GFX_portrait_species_0_military_1')
        self.store.set_pool('Species_0','army/male',['GFX_portrait_species_0_military_2'])
        self.assertEqual(self.store.groups()['Species_61'].pools,before)
        self.store.ensure_species(101)
        texture=self.c.sprite_entries('GFX_portrait_species_101_military_1')[0]['texture']
        self.assertEqual(texture,'gfx/leaders/large_portraits/generic/placeholder/military_1.tga')
        self.assertEqual(len(self.store.groups()['Species_101'].pools['army/male']),3)

    def test_new_species_creation_allocates_matching_slot_in_same_undo(self):
        for path in set(CATALOG_PATHS.values()):
            if not (self.root/path).exists():self.write(path,'l_english:\n' if path.endswith('.yml') else '',path.endswith('.yml'))
        self.write(CATALOG_PATHS['species_loc'],'l_english:\n var_species_0:0 "Diverse"\n',True)
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={'+''.join(part+'={color={if={limit={FROM={check_variable={'+field+'=0}}} set_temp_variable={red=.2} set_temp_variable={green=.3} set_temp_variable={blue=.4}}}}' for part,field in [('bottom','species'),('top','minority')])+'}}')
        self.write(CATALOG_PATHS['species_ideas'],'ideas={species={var_species_0={}}}')
        self.write(CATALOG_PATHS['effects'],'clear_all_species_ideas={for_loop_effect={start=0 end=100}}')
        self.write(CATALOG_PATHS['species_text'],''.join('defined_text={name='+f+' text={localization_key=fallback}}\n' for f in ['GetSpecies','GetSpeciesDesc','GetMinority','GetMinorityDesc','GetSpeciesTemp']))
        self.write(CATALOG_PATHS['species_gfx'],'spriteTypes={}')
        catalogs=MapCatalogStore(self.world,self.c)
        catalogs.edit_species(101,'New species','','#335577','#112233','',[],self.source,create=True)
        self.assertIn(101,catalogs.species());self.assertEqual(self.store.groups()['Species_101'].name,'New species')
        self.assertTrue(self.c.sprite_entries('GFX_portrait_species_101_military_1'))
        self.world.docs.undo();self.assertNotIn(101,catalogs.species());self.assertNotIn('Species_101',self.store.groups())


class GenericPortraitFormTests(unittest.TestCase):
    def setUp(self):
        self.f=GenericPortraitTests();self.f.setUp();self.root=tk.Tk();self.root.attributes('-alpha',0)
        self.errors=[];self.root.report_callback_exception=lambda typ,val,tb:self.errors.append(str(val))
        self.app=SimpleNamespace(character_store=self.f.c,country_store=self.f.countries,_sync=lambda:None,search_list=lambda *args:None)

    def tearDown(self):
        self.root.update_idletasks();self.root.destroy();self.f.tearDown();self.assertEqual(self.errors,[])

    def test_mapped_group_database_upload_controls_preview_cancel_and_apply(self):
        from generic_portrait_ui import GenericPortraitWorkspace,GenericPortraitDialog
        panel=GenericPortraitWorkspace(self.root,self.app);panel.pack(fill='both',expand=True);self.root.update();panel.refresh()
        self.assertIn('Altarian',panel.rows.item('Species_61','text'))
        d=GenericPortraitDialog(panel,self.app,'Species_61');d.attributes('-alpha',0);self.root.update();d.pool.set('army/female');d.refresh()
        before=dict(self.f.world.docs.drafts)
        with patch('generic_portrait_ui.filedialog.askopenfilenames',return_value=[str(self.f.source)]):d.add()
        self.assertEqual(len(d.rows.get_children()),4);self.assertTrue(d.photos)
        d.cancel();self.assertEqual(self.f.world.docs.drafts,before)
        d=GenericPortraitDialog(panel,self.app,'Species_61');d.attributes('-alpha',0);self.root.update();d.pool.set('navy/female');d.refresh()
        with patch('generic_portrait_ui.filedialog.askopenfilename',return_value=str(self.f.source)):d.replace()
        d.accept('Species_61');self.assertEqual(d.result,'Species_61');self.assertTrue(self.f.world.docs.changed)

    def test_country_picker_existing_preserved_new_species_suggestion_and_manual_override(self):
        from country_ui import CountryDialog
        self.app.world=self.f.world
        self.app.catalog_store=self.f.countries.catalogs
        d=CountryDialog(self.root,self.app,'AAA');d.attributes('-alpha',0);self.root.update()
        self.assertEqual(d.portrait_group.get(),'Species_0');d.laws['species'].set('var_species_61');self.assertEqual(d.portrait_group.get(),'Species_0')
        d.use_species_portraits();self.assertEqual(d.portrait_group.get(),'Species_61')
        d.auto_portrait_group=False;d.portrait_group.set('Amphibian_Species');d.laws['species'].set('var_species_1')
        self.assertEqual(d.collect().portrait_group,'Amphibian_Species');d.cancel()
        d=CountryDialog(self.root,self.app);d.attributes('-alpha',0);self.root.update()
        self.assertEqual(d.portrait_group.get(),'Species_0');d.laws['species'].set('var_species_61');self.assertEqual(d.portrait_group.get(),'Species_61');d.cancel()


if __name__=='__main__':unittest.main()
