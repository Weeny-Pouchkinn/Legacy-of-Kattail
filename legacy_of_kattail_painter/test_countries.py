"""Country authoring tests write only to disposable native-schema fixtures."""
from copy import deepcopy
from decimal import Decimal
import random
import io
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops

from model import World, parse, value, child, FLAG_SIZES
from character_model import CharacterStore, atom, block, METADATA
from demographics import MapCatalogStore, STARTUP
from country_model import (CountryStore, Country, CountrySourceExists, render_flag, symbol_alpha, PATTERNS, SPECIES_HISTORY_FLAG, ATTRIBUTE_HISTORY_FLAG,
                           copy_ideology_names, definite_name, distribute_popularities, COUNTRY_LOC, IDEA_LOC, IDEAS)
import test_painter as fixtures


class PopularityTests(unittest.TestCase):
    def test_engine_roundtrip_totals_and_gestalt_is_manual_only(self):
        from country_model import engine_popularities
        from decimal import ROUND_DOWN
        source={'a':'33.333333','b':'33.333333','c':'33.333334','gestalt':'0'}
        self.assertNotEqual(sum(Decimal(v).quantize(Decimal('.001'),rounding=ROUND_DOWN) for v in source.values()),100)
        fixed=engine_popularities(source)
        self.assertEqual(sum(Decimal(v).quantize(Decimal('.001'),rounding=ROUND_DOWN) for v in fixed.values()),100)
        self.assertTrue(all(Decimal(v).as_tuple().exponent>=-3 for v in fixed.values()))
        for seed in range(30):
            result=distribute_popularities({'a':'60','b':'0','c':'0','gestalt':'0'},True,random.Random(seed))
            self.assertEqual(result['gestalt'],'0');self.assertEqual(result['a'],'60');self.assertEqual(sum(map(Decimal,result.values())),100)
        result=distribute_popularities({'a':'20','b':'0','gestalt':'13.5'},True,random.Random(1))
        self.assertEqual(result['gestalt'],'13.5');self.assertEqual(result['b'],'66.5')
        self.assertEqual(distribute_popularities({'a':'0','b':'0','gestalt':'0'})['gestalt'],'0')

    def test_normalize_preserves_proportions_zeros_and_exact_total(self):
        for weights in [{'a':'150','b':'50','c':'0'},{'a':'1','b':'1','c':'1'},dict.fromkeys('abc','0')]:
            result=distribute_popularities(weights)
            self.assertEqual(sum(map(Decimal,result.values())),100)
            if weights['a']=='150':self.assertEqual(result,{'a':'75','b':'25','c':'0'})
            else:self.assertLessEqual(max(map(Decimal,result.values()))-min(map(Decimal,result.values())),Decimal('.001'))

    def test_random_remaining_preserves_entered_values_and_fills_exact_remainder(self):
        original={'a':'37.25000001','b':'0','c':'','d':'0'}
        result=distribute_popularities(original,True,random.Random(42))
        self.assertEqual(result['a'],'37.25');self.assertEqual(sum(map(Decimal,result.values())),100)
        self.assertTrue(all(Decimal(result[k])>0 for k in 'bcd'));self.assertGreater(len({result[k] for k in 'bcd'}),1)
        self.assertEqual(original['c'],'')
        self.assertEqual(distribute_popularities({'a':'100','b':'0'},True),{'a':'100','b':'0'})

    def test_invalid_inputs_and_exhausted_remaining_entries(self):
        for values,remaining in [({'a':'NaN'},False),({'a':'-1'},False),({'a':'bad'},True),({'a':'80','b':'30','c':'0'},True),({'a':'20','b':'30'},True)]:
            with self.subTest(values=values),self.assertRaises(ValueError):distribute_popularities(values,remaining)

    def test_real_buttons_update_fields_and_pie_together(self):
        import tkinter as tk
        from tkinter import ttk
        from types import SimpleNamespace
        from unittest.mock import patch
        from country_ui import CountryDialog
        from select_ui import Choice
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0)
        try:
            dialog=CountryDialog.__new__(CountryDialog);tk.Toplevel.__init__(dialog,root);dialog.attributes('-alpha',0)
            frame=ttk.Frame(dialog);frame.pack(fill='both',expand=True);dialog.frames={'politics':frame};dialog.boxes=[]
            dialog.ruling=tk.StringVar(value='a');dialog.data=SimpleNamespace(popularities={'a':'40','b':'0','c':'0'})
            dialog.ideology_choices=lambda:[Choice(k,k.upper()) for k in 'abc']
            dialog.countries=SimpleNamespace(ideologies=lambda:{k:{'color':rgb} for k,rgb in zip('abc',[(255,0,0),(0,255,0),(0,0,255)])})
            dialog.build_politics();root.deiconify();root.update()
            left=frame.winfo_children()[0];actions={w.cget('text'):w for w in left.winfo_children() if isinstance(w,ttk.Button)}
            actions['Assign random weights to remaining ideologies'].invoke()
            self.assertEqual(dialog.pop['a'].get(),'40');self.assertEqual(sum(Decimal(v.get()) for v in dialog.pop.values()),100)
            self.assertTrue(dialog.pie.find_all());self.assertIn('Total: 100%',dialog.total.get())
            for v in dialog.pop.values():v.set('1')
            actions['Normalize to 100'].invoke();self.assertEqual(sum(Decimal(v.get()) for v in dialog.pop.values()),100)
            self.assertIn('Total: 100%',dialog.total.get())
            dialog.pop['a'].set('bad');before={k:v.get() for k,v in dialog.pop.items()}
            with patch('country_ui.messagebox.showerror') as error:actions['Normalize to 100'].invoke();error.assert_called_once()
            self.assertEqual(before,{k:v.get() for k,v in dialog.pop.items()})
        finally:root.update_idletasks();root.destroy()


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


    def test_create_collision_confirmation_guard_accept_save_and_undo(self):
        history='history/countries/CCC - Existing.txt';definition='common/countries/CCC.txt'
        (self.root/history).write_text('capital = 2\nunknown = { keep = yes }\n1940.1.1 = { set_stability = .8 }\n')
        (self.root/definition).write_text('graphical_culture = custom_gfx\nunknown = yes\n')
        d=Country('CCC','','Gamma',capital='1',ruling='neutrality',popularities={'neutrality':'100'},names={'':{'name':'Gamma','def':'Gamma'}})
        with self.assertRaises(CountrySourceExists) as caught:self.store.apply(d,'#123456',d.names,create=True)
        self.assertEqual(set(caught.exception.paths),{history,definition});self.assertFalse(self.world.docs.changed)
        self.store.apply(d,'#123456',d.names,create=True,overwrite=True)
        self.assertEqual(d.path,history);self.assertIn('unknown = { keep = yes }',self.world.docs.text(history));self.assertIn('1940.1.1',self.world.docs.text(history))
        self.assertIn('custom_gfx',self.world.docs.text(definition));self.assertNotIn('history/countries/CCC.txt',self.world.docs.changed)
        self.world.docs.undo();self.world.refresh_countries();self.assertFalse(self.world.docs.changed);self.assertNotIn('CCC',self.world.country_paths)
        self.world.docs.redo();self.world.refresh_countries();self.world.docs.save()
        self.assertIn('capital = 1',(self.root/history).read_text());self.assertFalse((self.root/'history/countries/CCC.txt').exists())

    def test_empty_country_source_prompts_and_decline_keeps_form_open(self):
        import tkinter as tk
        from types import SimpleNamespace
        from unittest.mock import patch
        from country_ui import CountryDialog
        path=self.root/'history/countries/CCC.txt';path.write_bytes(b'')
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0)
        try:
            app=SimpleNamespace(world=self.world,country_store=self.store,character_store=self.characters)
            d=CountryDialog(root,app);d.attributes('-alpha',0);d.tag.set('CCC');d.base_name.set('Gamma');d.capital.set('1')
            root.deiconify();root.update()
            with patch('country_ui.messagebox.askyesno',return_value=False) as ask:d.ok();ask.assert_called_once()
            self.assertTrue(d.winfo_exists());self.assertTrue(d.new);self.assertFalse(self.world.docs.changed);self.assertEqual(path.read_bytes(),b'')
            with patch('country_ui.messagebox.askyesno',return_value=True) as ask:d.ok();ask.assert_called_once()
            self.assertFalse(d.winfo_exists());self.assertIn('CCC',self.world.country_paths);self.assertEqual(path.read_bytes(),b'')
        finally:root.update_idletasks();root.destroy()

    def test_symbol_outline_transforms_and_layer_order(self):
        mask=Image.new('L',(20,40),255)
        a={'mask':mask,'tint':'#ff0000','scale':.5};b={**a,'tint':'#00ff00','scale':.25}
        image=render_flag('Solid',['#000000'],symbols=[a,b]);self.assertEqual(image.getpixel((41,26)),(0,255,0))
        outlined=render_flag('Solid',['#000000'],symbols=[{**a,'outline_width':2,'outline_color':'#0000ff'}])
        self.assertEqual(outlined.getpixel((41,26)),(255,0,0));self.assertGreater(sum(b>100 and r<30 for r,g,b in outlined.getdata()),30)
        wider=symbol_alpha({**a,'stretch_x':2});normal=symbol_alpha(a);rotated=symbol_alpha({**a,'angle':90})
        box=normal.getbbox();wide=wider.getbbox();rot=rotated.getbbox();self.assertGreater(wide[2]-wide[0],box[2]-box[0]);self.assertGreater(rot[2]-rot[0],rot[3]-rot[1])
        shifted=symbol_alpha({**a,'x':.8,'y':.2}).getbbox();self.assertGreater(shifted[0],box[0]);self.assertLess(shifted[1],box[1])
        self.assertIsNotNone(symbol_alpha({**a,'scale':.05,'stretch_x':.1}).getbbox())
        with self.assertRaises(ValueError):render_flag('Solid',['#000000'],symbols=[a]*9)

    def test_new_country_color_preview_before_and_after_save(self):
        self.world.country_colours()
        d=Country('CCC','','Gamma',capital='1',ruling='neutrality',popularities={'neutrality':'100'},names={'':{'name':'Gamma','def':'Gamma'}})
        self.store.apply(d,'#123456',d.names,create=True)
        self.assertEqual(self.world.country_colours()['CCC'],(18,52,86))
        self.world.docs.save();self.assertEqual(self.world.country_colours()['CCC'],(18,52,86))
        self.assertEqual(World(self.root).country_colours()['CCC'],(18,52,86))

    def test_duplicate_color_overrides_and_ui_colors_follow_form(self):
        p=self.root/'common/countries/colors.txt'
        p.write_text('AAA={color=rgb{1 2 3} color_ui=rgb{3 2 1} keep=yes}\nBBB={color=rgb{4 5 6}}\nAAA={color=rgb{7 8 9} color_ui=rgb{9 8 7}}')
        self.world.country_colours();d=self.store.read('AAA');self.store.apply(d,'#123456',d.names)
        self.assertEqual(self.world.country_colours()['AAA'],(18,52,86))
        text=self.world.docs.text('common/countries/colors.txt')
        for root in parse(text):
            if root.key=='AAA':
                for n in root.children:
                    if n.key in {'color','color_ui'}:self.assertEqual([c.key for c in n.children],['18','52','86'])
        self.assertIn('keep=yes',text);self.assertIn('BBB={color=rgb{4 5 6}}',text)

    def test_country_form_color_popularity_save_reopen_and_exact_legend(self):
        import tkinter as tk
        from types import SimpleNamespace
        from country_ui import CountryDialog
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0)
        try:
            app=SimpleNamespace(world=self.world,country_store=self.store,character_store=self.characters)
            d=CountryDialog(root,app,'AAA');d.attributes('-alpha',0);root.deiconify();root.update()
            d.color.set('#ab12cd');d.pop['democratic'].set('12.345678');d.pop['neutrality'].set('87.654322')
            d.ok();self.world.docs.save()
            reopened=CountryDialog(root,app,'AAA');reopened.attributes('-alpha',0);reopened.tabs.select(reopened.frames['politics']);root.update()
            self.assertEqual(reopened.color.get(),'#ab12cd');self.assertEqual(reopened.pop['democratic'].get(),'12.346')
            import numpy as np
            self.world.map_ids=np.array([[1,2]],dtype=np.int32)
            self.assertEqual(self.world.map_image('Owners').getpixel((0,0)),(171,18,205))
            text=[reopened.pie.itemcget(i,'text') for i in reopened.pie.find_all() if reopened.pie.type(i)=='text']
            self.assertTrue(any('12.346%' in t for t in text));self.assertTrue(any('87.654%' in t for t in text));reopened.cancel()
        finally:root.update_idletasks();root.destroy()

    def test_country_summary_uses_owned_drafted_states_and_is_read_only(self):
        import tkinter as tk
        from types import SimpleNamespace
        from country_ui import CountryDialog
        for sid,pop,oil,civs in [(1,100,5,3),(2,50,4,2)]:
            path=self.world.states[sid].path;text=self.world.docs.text(path)
            text=text.replace('state = {',f'state = {{ manpower = {pop} resources = {{ oil = {oil} }}',1)
            text=text.replace('history = {',f'history = {{ buildings = {{ industrial_complex = {civs} arms_factory = 2 dockyard = 1 }}',1);self.world.docs.replace(path,text)
        summary=self.store.summary('AAA');self.assertEqual(summary['population'],100);self.assertEqual(summary['resources']['oil'],5);self.assertEqual(summary['factories']['industrial_complex'],3)
        self.world.set_owner_draft(2,'AAA');summary=self.store.summary('AAA');self.assertEqual(summary['population'],150);self.assertEqual(summary['states'],2);self.assertEqual(summary['resources']['oil'],9)
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0)
        try:
            d=CountryDialog(root,SimpleNamespace(world=self.world,country_store=self.store,character_store=self.characters),'AAA');d.attributes('-alpha',0)
            before=dict(self.world.docs.drafts);root.deiconify();d.tabs.select(d.frames['summary']);root.update()
            self.assertIn('150',d.summary_population.get());self.assertEqual(before,self.world.docs.drafts)
            self.assertEqual(len(d.summary_factories.get_children()),5);d.cancel()
        finally:root.update_idletasks();root.destroy()


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

    def test_pasted_colors_swatches_and_invalid_recovery_are_live(self):
        self.designer.pattern.set('Solid');self.pump()
        var,swatch,entry=self.designer.color_controls[0]
        self.root.clipboard_clear();self.root.clipboard_append(' #12ab34 ');entry.delete(0,'end');entry.event_generate('<<Paste>>');self.pump(.2)
        self.assertEqual(swatch.cget('background'),'#12ab34');self.assertEqual(self.designer.latest.getpixel((0,0)),(18,171,52))
        var.set('#not-a-color');self.pump();self.assertIsNone(self.designer.latest);self.assertEqual(str(self.designer.use_button.cget('state')),'disabled')
        var.set('#ff00aa');self.pump();self.assertEqual(self.designer.latest.getpixel((0,0)),(255,0,170));self.assertEqual(str(self.designer.use_button.cget('state')),'normal')
        self.assertFalse(self.applied)

    def test_eight_symbol_tabs_sliders_drag_and_gallery_composite(self):
        from types import SimpleNamespace
        from country_ui import FlagLibraryPicker
        d=self.designer;d.emblem.set('mask:plantoid_0000');d.tint.set('#ff0000');d.symbols[0]['x'].set('.25')
        d.add_button.invoke();d.emblem.set('mask:plantoid_0001');d.tint.set('#00ff00');layer=d.symbols[1];layer['x'].set('.75');layer['outline'].set(True);layer['outline_color'].set('#0000ff')
        layer['numeric']['angle'][0].set(45);self.pump();self.assertAlmostEqual(float(layer['angle'].get()),45)
        layer['angle'].set('90');self.assertAlmostEqual(layer['numeric']['angle'][0].get(),90)
        layer['angle'].set('0');self.pump();origin=d._preview_origin
        start=SimpleNamespace(x=origin[0]+246*.75,y=origin[1]+156*.5);d.drag_start(start)
        self.assertIsNotNone(d._drag);d.drag_move(SimpleNamespace(x=start.x-25,y=start.y+15));d.drag_end()
        self.assertLess(float(layer['x'].get()),.75);self.assertGreater(float(layer['y'].get()),.5)
        self.assertEqual(d.symbols[0]['x'].get(),'.25');self.assertEqual(d.symbols[0]['tint'].get(),'#ff0000')
        picker=FlagLibraryPicker(d,'background');self.pump();direct=d.render().resize((82,52),Image.Resampling.LANCZOS)
        preview=picker.flag_image(d.pattern.get(),(82,52));self.assertLess(sum(ImageChops.difference(direct,preview).convert('L').getdata())/(82*52),3);picker.destroy()
        for i in range(8):d.add_button.invoke()
        self.assertEqual(len(d.symbols),8);self.assertEqual(str(d.add_button.cget('state')),'disabled')
        d.remove_symbol();self.assertEqual(len(d.symbols),7);self.assertEqual(str(d.add_button.cget('state')),'normal')
        d.use();self.assertEqual(len(self.applied),1);self.assertEqual(self.applied[0].size,(328,208))

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
