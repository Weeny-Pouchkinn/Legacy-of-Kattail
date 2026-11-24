"""Country authoring tests write only to disposable native-schema fixtures."""
from copy import deepcopy
import io
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from model import World, parse, value, child, FLAG_SIZES
from character_model import CharacterStore, atom, block, METADATA
from demographics import MapCatalogStore, STARTUP
from country_model import (CountryStore, Country, render_flag, PATTERNS, SPECIES_HISTORY_FLAG, ATTRIBUTE_HISTORY_FLAG,
                           copy_ideology_names, definite_name, COUNTRY_LOC, IDEA_LOC, IDEAS)
import test_painter as fixtures


class CountryTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.FixtureTests();self.fixture.setUp();self.root=self.fixture.root
        self.game=Path(self.fixture.tmp.name)/'game'
        files={
            'common/countries/AAA.txt':'graphical_culture = western_european_gfx\ncolor = rgb { 20 40 60 }\n',
            'common/countries/BBB.txt':'color = rgb { 70 80 90 }\n',
            'common/ideologies/native.txt':'ideologies = { democratic = { types = { liberal = {} conservative = {} } color = { 10 40 200 } } neutrality = { types = { despotic = {} } color = { 90 90 90 } } }',
            'common/ideas/lok_misc_ideas.txt':'''ideas = {
                country = { old_spirit = { picture = native allowed = { always = yes } modifier = { test_modifier = 0.1 } on_add = { preserve = yes } } }
                economy = { law = yes civilian_economy = { modifier = {} } war_economy = { modifier = {} } }
                mobilization_laws = { law = yes volunteer_only = { modifier = {} } extensive_conscription = { modifier = {} } }
                specialty = { law = yes specialty_nothing = { modifier = {} } specialty_nuclear = { modifier = {} } }
                species = { law = yes var_species_0 = { modifier = {} } var_species_1 = { modifier = {} } var_species_2 = { modifier = {} } }
            }''',
            'common/technologies/native.txt':'technologies = { tech_a = { start_year = 1936 } tech_b = { start_year = 1937 } }',
            'common/modifier_definitions/native.txt':'test_modifier = { category = country } other_modifier = { category = country }',
            STARTUP:'''on_actions = { on_startup = { effect = {
                every_possible_country = { add_ideas = specialty_nothing }
                every_possible_country = { add_ideas = var_species_0 }
                AAA = { remove_ideas = var_species_0 add_ideas = { var_species_2 old_spirit } }
                BBB = { remove_ideas = var_species_0 add_ideas = var_species_1 }
                preserve_startup = yes
            } } on_weekly = { effect = { untouched = yes } } }''',
            'history/countries/AAA - Native.txt':'''capital = 1
                set_stability = 0.6
                set_war_support = 0.3
                set_politics = { ruling_party = democratic elections_allowed = yes last_election = "1932.1.1" }
                set_popularities = { democratic = 70 neutrality = 30 }
                set_technology = { tech_a = 1 popup = no }
                if = { limit = { has_dlc = "test" } set_technology = { tech_b = 1 } }
                1939.1.1 = { set_stability = 0.8 }
                add_ideas = { old_spirit civilian_economy volunteer_only var_species_1 specialty_nothing }
                set_country_flag = authored_flag
                recruit_character = AAA_One
                unrelated = { keep = yes }
            ''',
            'history/countries/BBB.txt':'capital = 2\nset_politics = { ruling_party = neutrality }\nset_popularities = { neutrality = 100 }\n',
            COUNTRY_LOC:'l_english:\n AAA:0 "Alpha"\n AAA_DEF:0 "Alpha"\n AAA_democratic:7 "Authored Republic" # keep comment\n BBB:0 "Beta"\n',
            IDEA_LOC:'l_english:\n old_spirit:0 "Old spirit"\n old_spirit_desc:0 "Authored description"\n test_modifier:0 "Test modifier"\n',
            'localisation/english/characters_l_english.yml':'l_english:\n AAA_One:0 "One"\n AAA_One_desc:0 "One desc"\n',
            'common/characters/AAA - characters.txt':'''characters = { AAA_One = { name = AAA_One
                portraits = { army = { large = GFX_army_keep small = GFX_army_small_keep } }
                country_leader = { ideology = liberal expire = "2100.1.1" traits = {} }
                corps_commander = { skill = 3 traits = {} }
            } }''',
            'interface/lok_ideas.gfx':'spriteTypes = { spriteType = { name = "GFX_idea_native" texturefile = "gfx/interface/ideas/native.dds" } }',
            'interface/lok_misc_icons.gfx':'spriteTypes = { }',
            'interface/lok_leader_portraits.gfx':'spriteTypes = { spriteType = { name = "GFX_portrait_AAA_One" texturefile = "gfx/leaders/large_portraits/AAA/One.tga" } spriteType = { name = "GFX_portrait_AAA_One_Small" texturefile = "gfx/leaders/small_portraits/AAA/One.tga" } }',
        }
        for relative,text in files.items():
            p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig' if p.suffix=='.yml' else 'utf-8')
        for base,relative,text in [(self.game,'interface/vanilla_ideas.gfx','spriteTypes = { spriteType = { name = "GFX_idea_native" texturefile = "gfx/interface/ideas/vanilla.dds" } spriteType = { name = "GFX_idea_vanilla" texturefile = "gfx/interface/ideas/vanilla.dds" } }')]:
            p=base/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        for base,relative,size,color in [(self.root,'gfx/interface/ideas/native.dds',(60,60),'red'),(self.game,'gfx/interface/ideas/vanilla.dds',(60,60),'blue'),(self.root,'gfx/flags/AAA.tga',(82,52),'green'),(self.root,'gfx/flags/AAA_democratic.tga',(82,52),'red'),(self.root,'gfx/leaders/large_portraits/AAA/One.tga',(156,210),'white'),(self.root,'gfx/leaders/small_portraits/AAA/One.tga',(65,67),'white')]:
            p=base/relative;p.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',size,color).save(p)
        self.world=World(self.root);self.characters=CharacterStore(self.world);self.characters.game_root=self.game
        self.store=CountryStore(self.world,self.characters,MapCatalogStore(self.world,self.characters))
        self.before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def tearDown(self):self.fixture.tearDown()

    def test_edit_history_preserves_conditional_dated_content_and_politics_fields(self):
        d=self.store.read('AAA');d.capital='2';d.stability='72.5';d.war_support='44';d.popularities={'democratic':'60.5','neutrality':'39.5'};d.technologies={'tech_b':'1'}
        d.laws['economy']='war_economy';d.laws['mobilization_laws']='extensive_conscription'
        self.store.apply(d,'#123456',d.names)
        text=self.world.docs.text(d.path)
        self.assertIn('unrelated = { keep = yes }',text);self.assertIn('1939.1.1 = { set_stability = 0.8 }',text)
        self.assertIn('if = { limit = { has_dlc = "test" } set_technology = { tech_b = 1 } }',text)
        self.assertIn('elections_allowed = yes',text);self.assertIn('last_election = "1932.1.1"',text)
        self.assertIn('set_stability = 0.725',text);self.assertIn('authored_flag',text)
        loaded=self.store.read('AAA');self.assertEqual(loaded.laws['economy'],'war_economy');self.assertEqual(loaded.laws['mobilization_laws'],'extensive_conscription')
        self.assertEqual(loaded.technologies,{'tech_b':'1'});self.assertEqual(loaded.popularities,{'democratic':'60.5','neutrality':'39.5'})
        self.assertEqual(self.before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_new_country_native_save_reload_flags_and_undo_registration(self):
        d=Country('CCC','','Gamma',capital='2',ruling='neutrality',popularities={'neutrality':'100'},laws={'mobilization_laws':'volunteer_only','economy':'civilian_economy','specialty':'specialty_nothing','species':'var_species_1'},names={i:{'name':None,'def':None} for i in ('','democratic','neutrality')})
        d.names['']['name']='Gamma';flag=render_flag('Vertical tricolor',['#ff0000','#ffffff','#0000ff'])
        self.store.apply(d,'#334455',d.names,{'democratic':flag},True)
        self.assertIn('CCC',self.world.country_paths);self.assertIn('CCC',self.world.countries);self.assertEqual(len(self.world.docs.undo_stack),1)
        changed=set(self.world.docs.changed);self.assertFalse(any(p.endswith('.json') or 'painter' in p for p in changed))
        self.world.docs.undo();self.world.refresh_countries();self.assertNotIn('CCC',self.world.country_paths)
        self.world.docs.redo();self.world.refresh_countries();self.assertIn('CCC',self.world.countries)
        for group in ('','democratic'):
            for size,dimensions in FLAG_SIZES.items():
                with Image.open(io.BytesIO(self.world.docs.binary(self.store.flag_path('CCC',group,size)))) as image:self.assertEqual(image.size,dimensions);self.assertEqual(image.mode,'RGB')
        self.world.docs.save();loaded=World(self.root);chars=CharacterStore(loaded);chars.game_root=self.game;store=CountryStore(loaded,chars,MapCatalogStore(loaded,chars))
        self.assertEqual(store.read('CCC').capital,'2');self.assertEqual(store.read('CCC').laws['species'],'var_species_1');self.assertEqual(chars.localisations()['CCC_DEF'],'Gamma')
        self.assertTrue((self.root/COUNTRY_LOC).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_species_lives_in_history_and_defaults_do_not_override_it(self):
        self.assertEqual(self.store.read('AAA').laws['species'],'var_species_2')
        d=self.store.read('AAA');d.laws['species']='var_species_1';self.store.apply(d,'#123456',d.names)
        history=self.world.docs.text(d.path);self.assertIn('var_species_1',history);self.assertIn(SPECIES_HISTORY_FLAG,history);self.assertIn('authored_flag',history)
        self.assertEqual(self.store.read('AAA').laws['species'],'var_species_1');self.assertEqual(self.store.read('BBB').laws['species'],'var_species_1')
        startup=self.world.docs.text(STARTUP);self.assertIn('add_ideas = { old_spirit }',startup);self.assertIn('on_weekly = { effect = { untouched = yes } }',startup)
        d=self.store.read('AAA');d.laws['species']='var_species_0';self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.world.docs.text(STARTUP),startup);self.assertEqual(self.store.read('AAA').laws['species'],'var_species_0')

    def test_name_bulk_undefined_preserves_authored_empty_and_def_article(self):
        names=self.store.names('AAA');names['']={'name':'Alpha','def':'the Alpha'};names['neutrality']={'name':'','def':None}
        copy_ideology_names(names,'',self.store.ideologies(),True)
        self.assertEqual(names['democratic']['name'],'Authored Republic');self.assertEqual(names['democratic']['def'],'the Alpha');self.assertEqual(names['neutrality']['name'],'')
        self.store.write_names('AAA',names);text=self.world.docs.text(COUNTRY_LOC)
        self.assertIn('AAA_democratic:7 "Authored Republic" # keep comment',text)
        self.assertEqual(definite_name('The Republic',True),'the Republic');self.assertEqual(definite_name('the Republic',False),'Republic')
        copy_ideology_names(names,'',self.store.ideologies());self.assertEqual(names['democratic']['name'],'Alpha')

    def test_attribute_changes_carry_native_bonus_and_suppress_old_default_bonus(self):
        text=self.world.docs.text(STARTUP);template='add_tech_bonus = { name = specialty_nuclear bonus = 0 uses = 1000 ahead_reduction = 1 category = nuclear }'
        text=text.replace('preserve_startup = yes','every_possible_country = { limit = { tag = AAA } add_ideas = specialty_nuclear '+template+' } preserve_startup = yes')
        self.world.docs.replace(STARTUP,text)
        d=self.store.read('AAA');self.assertEqual(d.laws['specialty'],'specialty_nuclear');d.laws['specialty']='specialty_nothing';self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.store.read('AAA').laws['specialty'],'specialty_nothing');self.assertIn(ATTRIBUTE_HISTORY_FLAG,self.world.docs.text(d.path))
        startup=self.world.docs.text(STARTUP);self.assertEqual(startup.count('add_tech_bonus'),1)
        self.assertIn('NOT = { has_country_flag = '+ATTRIBUTE_HISTORY_FLAG+' }',startup)
        d=self.store.read('AAA');d.laws['specialty']='specialty_nuclear';self.store.apply(d,'#123456',d.names)
        startup=self.world.docs.text(STARTUP);self.assertEqual(startup.count(template),2)
        self.assertIn('has_country_flag = '+ATTRIBUTE_HISTORY_FLAG+' has_idea = specialty_nuclear',startup)
        d=self.store.read('AAA');d.laws['specialty']='specialty_nothing';self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.world.docs.text(STARTUP).count('add_tech_bonus'),1)

    def test_technology_edit_keeps_assignments_before_equipment_variants(self):
        text='set_technology = { tech_a = 1 popup = no }\ncreate_equipment_variant = { name = "Authored" }\nset_technology = { tech_b = 1 }\n'
        result=self.store.rewrite_technologies(text,{'tech_a':'2','tech_b':'1','added_tech':'1'})
        self.assertLess(result.index('tech_a = 2'),result.index('create_equipment_variant'))
        self.assertLess(result.index('added_tech = 1'),result.index('create_equipment_variant'))
        self.assertGreater(result.index('tech_b = 1'),result.index('create_equipment_variant'))
        self.assertIn('popup = no',result)

    def test_native_leader_creation_assignment_and_other_roles_preserved(self):
        self.store.set_leader('AAA','AAA_One','despotic',portrait='GFX_portrait_AAA_One')
        c=self.characters.characters()['AAA_One'];self.assertEqual(len(c.roles),3)
        self.assertIn('GFX_army_keep',c.text);self.assertIn('civilian',c.text)
        self.assertEqual(self.store.leaders('AAA')['neutrality'][-1],('AAA_One','despotic'))
        self.store.set_leader('AAA','AAA_Two','liberal','Two','Second description')
        c=self.characters.characters()['AAA_Two'];self.assertIn('AAA',c.countries);self.assertEqual(c.name,'Two');self.assertEqual(c.description,'Second description')
        self.assertIn('promote_character = { character = AAA_Two ideology = liberal }',self.world.docs.text(self.world.countries['AAA']))
        self.assertNotIn(METADATA,self.world.docs.changed);self.assertFalse(any('painter' in p for p in self.world.docs.changed))

    def test_spirit_icons_include_vanilla_and_mod_and_writes_native_idea(self):
        icons=self.store.icon_catalog();self.assertIn('GFX_idea_native',icons);self.assertIn('vanilla:GFX_idea_native',icons)
        self.assertEqual(self.store.icon_image('GFX_idea_native').getpixel((1,1)),(255,0,0,255));self.assertEqual(self.store.icon_image('vanilla:GFX_idea_native').getpixel((1,1)),(0,0,255,255))
        self.store.edit_spirit('AAA_added','Added','Description','vanilla:GFX_idea_vanilla',{'test_modifier':'.25'},True)
        definition=self.store.ideas()['AAA_added'];self.assertEqual(definition[1],IDEAS)
        self.assertIn('test_modifier = 0.25',definition[2]);self.assertIn('AAA_added_desc',self.world.docs.text(IDEA_LOC))
        self.store.edit_spirit('old_spirit','Renamed','Changed','GFX_idea_native',{'other_modifier':'2'})
        text=self.world.docs.text(IDEAS);self.assertIn('on_add = { preserve = yes }',text);node=next(n for _,n in __import__('model').walk(parse(text)) if n.key=='old_spirit')
        self.assertIn('other_modifier = 2',text[node.start:node.end]);self.assertNotIn('test_modifier',text[node.start:node.end])
        d=self.store.read('AAA');d.ideas={'AAA_added'};self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.store.read('AAA').ideas,{'AAA_added'})

    def test_imported_emblem_is_native_reusable_and_tintable(self):
        source=Path(self.fixture.tmp.name)/'Source Emblem.png';image=Image.new('RGBA',(20,20),(255,255,255,0));image.paste((255,255,255,255),(7,3,13,17));image.save(source)
        key=self.store.import_emblem(source);mask=self.store.emblem_mask(key)
        self.assertTrue(any(c.code==key for c in self.store.emblem_choices()))
        flag=render_flag('Solid',['#000000'],mask,'#00ff00')
        self.assertEqual(flag.getpixel((41,26)),(0,255,0));self.assertFalse(any('painter' in p or p.endswith('.json') for p in self.world.docs.changed))

    def test_background_patterns_keep_geometry_and_all_native_flag_sizes(self):
        for pattern in PATTERNS:
            for size in FLAG_SIZES.values():self.assertEqual(render_flag(pattern,['#ff0000','#00ff00','#0000ff','#ffffff'],size=size).size,size)
        image=render_flag('Vertical tricolor',['#ff0000','#ffffff','#0000ff'],size=(90,60))
        self.assertEqual([image.getpixel((x,30)) for x in (10,45,80)],[(255,0,0),(255,255,255),(0,0,255)])
        image=render_flag('Horizontal bicolor',['#ff0000','#0000ff'],size=(90,60));self.assertEqual(image.getpixel((45,10)),(255,0,0));self.assertEqual(image.getpixel((45,50)),(0,0,255))

    def test_validation_failure_leaves_every_source_untouched(self):
        for field,value_ in [('capital','9999'),('stability','101')]:
            d=self.store.read('AAA');setattr(d,field,value_)
            with self.assertRaises(ValueError):self.store.apply(d,'#123456',d.names)
            self.assertFalse(self.world.docs.changed)
        d=self.store.read('AAA');d.popularities['democratic']='80'
        with self.assertRaises(ValueError):self.store.apply(d,'#123456',d.names)
        self.assertFalse(self.world.docs.changed)

    def test_failure_after_country_registration_rolls_back_all_native_drafts(self):
        d=Country('CCC','','Gamma',capital='2',ruling='neutrality',popularities={'neutrality':'100'},names={'':{'name':'Gamma','def':'Gamma'}})
        with self.assertRaises(ValueError):self.store.apply(d,'#123456',d.names,{'not_an_ideology':Image.new('RGB',(82,52))},True)
        self.assertFalse(self.world.docs.changed);self.assertNotIn('CCC',self.world.country_paths)

    def test_existing_intentionally_blank_base_name_can_be_preserved(self):
        d=self.store.read('AAA');d.names['']['name']='';d.names['']['def']=''
        self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.store.names('AAA')['']['name'],'')
        self.assertEqual(self.store.names('AAA')['']['def'],'')


class FlagGalleryTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from select_ui import Choice
        from country_ui import FlagDesigner
        try:self.root=tk.Tk()
        except tk.TclError as exc:self.skipTest('Tk display unavailable: '+str(exc))
        self.root.withdraw();self.root.geometry('1050x760');self.root.attributes('-alpha',0)
        self.callback_errors=[];self.root.report_callback_exception=lambda exc,value,tb:self.callback_errors.append(value)
        class Store:
            def __init__(self):self.mask_reads=[]
            def emblem_choices(self):
                return [Choice('','No emblem'),Choice('file:example.png','EU4 imported'),Choice('GFX_lok_flag_emblem_imported','Native imported'),Choice('missing','Missing asset')]+[Choice(f'mask:plantoid_{i:04d}',f'Plantoid {i:04d}') for i in range(1000)]
            def emblem_mask(self,key):
                if not key:return None
                if key=='missing':raise ValueError('Missing test image')
                self.mask_reads.append(key)
                mask=Image.new('L',(40,60));mask.paste(255,(10,5,30,55));return mask
        self.store=Store();self.applied=[];self.designer=FlagDesigner(self.root,self.store,self.applied.append);self.designer.pack(fill='both',expand=True)
        self.root.deiconify();self.root.update()

    def tearDown(self):
        if hasattr(self,'root'):
            self.root.destroy();self.assertFalse(self.callback_errors)

    def pump(self,seconds=.12):
        import time
        end=time.perf_counter()+seconds
        while time.perf_counter()<end:self.root.update()

    def test_galleries_are_visual_lazy_searchable_and_bounded(self):
        from country_ui import FlagLibraryPicker
        self.designer.tint.set('#00ff00')
        picker=FlagLibraryPicker(self.designer,'emblem');self.pump()
        self.assertEqual(len(picker.matches),1004);self.assertTrue(picker.photos)
        self.assertLess(len(self.store.mask_reads),100)
        for photo in picker.photos.values():self.assertEqual((photo.width(),photo.height()),picker.THUMB)
        for position in (.2,.4,.6,.8,1):picker.scroll('moveto',position);self.pump(.06)
        self.assertLessEqual(len(picker.photos),128);self.assertLessEqual(len(picker.masks),96)
        self.assertLess(len(self.store.mask_reads),1000)
        picker.query.set('plantoid_0999');picker.refresh();self.pump()
        self.assertEqual([c.code for c in picker.matches],['mask:plantoid_0999'])
        picker.select('mask:plantoid_0999')
        self.assertEqual(picker.flag_image(picker.selected,(82,52)).getpixel((41,26)),(0,255,0))
        self.assertEqual(self.designer.emblem.get(),'');picker.destroy()
        picker=FlagLibraryPicker(self.designer,'background');self.pump()
        self.assertEqual(len(picker.matches),len(PATTERNS));self.assertTrue(picker.photos)
        picker.select('Vertical tricolor');self.assertEqual(self.designer.pattern.get(),'Horizontal tricolor')
        picker.destroy();self.assertEqual(self.applied,[])

    def test_dropdown_arrows_open_galleries_apply_and_cancel_without_using_flag(self):
        from country_ui import FlagLibraryPicker
        failures=[]
        def choose(code,accept):
            def action():
                picker=None
                try:
                    picker=next(w for w in self.designer.winfo_children() if isinstance(w,FlagLibraryPicker))
                    self.assertTrue(picker.photos);picker.select(code)
                    if accept:picker.accept()
                except Exception as exc:failures.append(exc)
                finally:
                    if picker is not None and picker.winfo_exists():picker.destroy()
            self.root.after(90,action)
        choose('Vertical tricolor',True);self.designer.pattern_box.arrow.invoke()
        self.assertEqual(self.designer.pattern.get(),'Vertical tricolor')
        choose('mask:plantoid_0004',False);self.designer.emblem_box.arrow.invoke();self.assertEqual(self.designer.emblem.get(),'')
        choose('mask:plantoid_0004',True);self.designer.emblem_box.arrow.invoke();self.assertEqual(self.designer.emblem.get(),'mask:plantoid_0004')
        choose('',True);self.designer.emblem_box.arrow.invoke();self.assertEqual(self.designer.emblem.get(),'')
        self.assertFalse(failures);self.assertFalse(self.applied);self.assertIsNone(self.root.grab_current())

    def test_source_filters_keyboard_and_missing_asset_recovery(self):
        from country_ui import FlagLibraryPicker
        picker=FlagLibraryPicker(self.designer,'emblem');self.pump()
        picker.group.set('Native imports');picker.refresh();self.assertEqual({c.code for c in picker.matches},{'GFX_lok_flag_emblem_imported','missing'})
        picker.select('missing');self.assertEqual(str(picker.use_button.cget('state')),'disabled')
        picker.accept();self.assertTrue(picker.winfo_exists());self.assertIsNone(picker.result)
        picker.group.set('Stellaris masks');picker.refresh();picker.select('mask:plantoid_0000');picker.step(1)
        self.assertEqual(picker.selected,'mask:plantoid_0001')
        picker.query.set('plantoid_0999');picker.search_accept();self.assertEqual(picker.result,'mask:plantoid_0999')


if __name__=='__main__':unittest.main()
