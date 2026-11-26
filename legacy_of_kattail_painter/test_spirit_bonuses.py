"""Native spirit research/equipment pools, source-preserving writes and UI."""
import tkinter as tk
import unittest
from unittest.mock import patch

import test_countries as country_fixtures
from model import World,parse,child,value
from character_model import CharacterStore
from country_model import CountryStore,IDEAS
from demographics import MapCatalogStore


class SpiritBonusTests(unittest.TestCase):
    def setUp(self):
        self.f=country_fixtures.CountryTests();self.f.setUp()
        self.root=self.f.root;self.world=self.f.world;self.store=self.f.store
        self.write('common/technology_tags/categories.txt','technology_categories={industry infantry_weapons armor}')
        self.write('common/units/equipment/native.txt','''equipments={infantry_equipment={type=infantry is_archetype=yes year=1936 soft_attack=3 defense=2 reliability=.9 build_cost_ic=.5 priority=1 air_map_icon_frame=2} light_tank_chassis={type={armor} armor_value=10}}''')
        self.write('common/units/equipment/modules/module.txt','equipment_modules={test={add_stats={air_range=100} multiply_stats={air_agility=.1}}}')
        original=self.world.docs.text(IDEAS)
        self.original=original.replace('old_spirit = {','''old_spirit = {
 research_bonus={infantry_weapons=.1 industry=@research # research comment
 unknown_nested={keep=yes}} research_bonus={infantry_weapons=.2}
 equipment_bonus={infantry_equipment={instant=yes soft_attack=.1 reliability=@reliability # equipment comment
 custom_nested={keep=yes}}}
 equipment_bonus={infantry_equipment={soft_attack=.2} light_tank_chassis={armor_value=.1}}
''',1)
        self.world.docs.replace(IDEAS,self.original);self.world.docs.save();self.original=self.world.docs.text(IDEAS)

    def write(self,rel,text,base=None):
        p=(base or self.root)/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')

    def tearDown(self):self.f.tearDown()

    def edit(self,research=None,equipment=None):
        self.store.edit_spirit('old_spirit','Old spirit','Authored description','GFX_idea_native',{'test_modifier':'.1'},research_bonuses=research,equipment_bonuses=equipment)

    def test_catalogs_respect_native_overlay_empty_files_replacement_and_module_stats(self):
        self.write('common/technology_tags/categories.txt','technology_categories={hidden_by_same_path}',self.f.game)
        self.write('common/technology_tags/extra.txt','technology_categories={vanilla_extra}',self.f.game)
        self.write('common/units/equipment/empty.txt','equipments={hidden_equipment={soft_attack=2}}',self.f.game)
        self.write('common/units/equipment/empty.txt','')
        cat=self.store.spirit_bonus_catalog();self.assertIn('industry',cat['research']);self.assertIn('vanilla_extra',cat['research'])
        self.assertNotIn('hidden_by_same_path',cat['research']);self.assertNotIn('hidden_equipment',cat['equipment'])
        self.assertTrue({'infantry_equipment','light_tank_chassis','armor','infantry'}<=cat['equipment'])
        self.assertTrue({'soft_attack','reliability','air_range','air_agility'}<=cat['stats']);self.assertNotIn('year',cat['stats']);self.assertNotIn('air_map_icon_frame',cat['stats'])
        self.world.docs.replace('descriptor.mod','replace_path="common/technology_tags"')
        self.assertNotIn('vanilla_extra',self.store.spirit_bonus_catalog()['research'])
        self.world.docs.undo();self.assertIn('vanilla_extra',self.store.spirit_bonus_catalog()['research'])

    def test_old_api_preserves_bonus_blocks_without_parsing_or_rewriting(self):
        self.assertEqual(self.store.spirit_bonuses('old_spirit')[0],{'infantry_weapons':'.2','industry':'@research'})
        before=self.world.docs.text(IDEAS);self.edit();after=self.world.docs.text(IDEAS)
        for key in ['research_bonus','equipment_bonus']:
            def bodies(text):
                node=next(n for _,n in __import__('model').walk(parse(text)) if n.key=='old_spirit')
                return [text[c.start:c.end] for c in node.children if c.key==key]
            self.assertEqual(bodies(before),bodies(after))

    def test_repeated_blocks_changed_leaves_updated_preserving_variables_comments_and_nested_data(self):
        research,equipment=self.store.spirit_bonuses('old_spirit');research['infantry_weapons']='.3';research['armor']='.05'
        equipment['infantry_equipment']['soft_attack']='.4';equipment['infantry_equipment']['instant']='no';equipment['light_tank_chassis']['build_cost_ic']='-.15'
        self.edit(research,equipment);text=self.world.docs.text(IDEAS)
        self.assertEqual(text.count('infantry_weapons = 0.3'),2);self.assertEqual(text.count('soft_attack = 0.4'),2)
        self.assertIn('industry = @research # research comment',text);self.assertIn('reliability = @reliability # equipment comment',text)
        from script_format import tokens
        for expected in ['custom_nested={keep=yes}','unknown_nested={keep=yes}','on_add={preserve=yes}']:
            entries=[text[n.start:n.end] for _,n in __import__('model').walk(parse(text)) if n.key==parse(expected)[0].key]
            self.assertTrue(any(tokens(entry)==tokens(expected) for entry in entries))
        self.assertEqual(self.store.spirit_bonuses('old_spirit')[1]['infantry_equipment']['instant'],'no')
        self.world.docs.undo();self.assertEqual(self.world.docs.text(IDEAS),self.original)
        self.world.docs.redo();self.world.docs.save()
        w=World(self.root);c=CharacterStore(w);c.game_root=self.f.game;store=CountryStore(w,c,MapCatalogStore(w,c))
        self.assertEqual(store.spirit_bonuses('old_spirit')[0]['armor'],'0.05')
        self.assertEqual(store.spirit_bonuses('old_spirit')[1]['light_tank_chassis']['build_cost_ic'],'-0.15')

    def test_removal_of_numeric_leaves_does_not_remove_other_bonus_fields(self):
        research,equipment=self.store.spirit_bonuses('old_spirit');research.pop('infantry_weapons');equipment['infantry_equipment'].pop('soft_attack');equipment['infantry_equipment'].pop('instant')
        self.edit(research,equipment);text=self.world.docs.text(IDEAS)
        self.assertNotIn('infantry_weapons =',text);self.assertNotIn('soft_attack =',text);self.assertIn('reliability = @reliability',text)
        self.assertIn('equipment comment',text);self.assertIn('custom_nested = {',text);self.assertIn('keep = yes',text)

    def test_invalid_new_targets_stats_numbers_and_flags_are_atomic(self):
        research,equipment=self.store.spirit_bonuses('old_spirit');before=dict(self.world.docs.drafts)
        for r,e in [({'invented':'.1'},equipment),({'industry':'nan'},equipment),(research,{'invented':{'soft_attack':'.1'}}),(research,{'infantry_equipment':{'invented':'.1'}}),(research,{'infantry_equipment':{'instant':'maybe'}}),(research,{'infantry_equipment':{'soft_attack':'infinity'}})]:
            with self.assertRaises(ValueError):self.edit(r,e)
            self.assertEqual(self.world.docs.drafts,before)

    def test_new_spirit_research_and_equipment_write_without_existing_blocks(self):
        self.store.edit_spirit('new_bonus_spirit','New spirit','','GFX_idea_native',{},True,research_bonuses={'industry':'.1'},equipment_bonuses={'infantry_equipment':{'soft_attack':'.2','instant':'yes'}})
        research,equipment=self.store.spirit_bonuses('new_bonus_spirit')
        self.assertEqual(research,{'industry':'0.1'});self.assertEqual(equipment,{'infantry_equipment':{'instant':'yes','soft_attack':'0.2'}})
        self.world.docs.undo();self.assertNotIn('new_bonus_spirit',self.store.ideas())


class SpiritBonusFormTests(unittest.TestCase):
    def setUp(self):
        self.f=SpiritBonusTests();self.f.setUp();self.root=tk.Tk();self.root.attributes('-alpha',0)
        self.errors=[];self.root.report_callback_exception=lambda *args:self.errors.append(args)
        patcher=patch('country_ui.messagebox.showerror',side_effect=AssertionError('Unexpected spirit bonus form error'));patcher.start();self.addCleanup(patcher.stop)

    def tearDown(self):
        self.root.destroy();self.f.tearDown();self.assertFalse(self.errors)

    def test_bonus_tabs_add_edit_instant_remove_cancel_and_apply(self):
        from country_ui import SpiritDialog
        d=SpiritDialog(self.root,self.f.store,'old_spirit');self.root.update();before=dict(self.f.world.docs.drafts)
        self.assertEqual([d.bonus_tabs.tab(tab,'text') for tab in d.bonus_tabs.tabs()],['Modifiers','Research bonuses','Equipment bonuses'])
        d.research_box.set('armor');d.research_amount.set('.25');d.add_research_bonus();self.assertEqual(d.research_bonuses['armor'],'0.25')
        d.equipment_box.set('light_tank_chassis');d.equipment_stat_box.set('build_cost_ic');d.equipment_amount.set('-.15');d.instant_box.set('no');d.add_equipment_bonus()
        self.assertEqual(d.equipment_bonuses['light_tank_chassis']['instant'],'no')
        self.assertEqual(d.equipment_bonuses['light_tank_chassis']['build_cost_ic'],'-0.15')
        d.research_rows.selection_set('armor');d.remove_research_bonus();self.assertNotIn('armor',d.research_bonuses)
        self.assertEqual(self.f.world.docs.drafts,before);d.cancel();self.assertEqual(self.f.world.docs.drafts,before)
        d=SpiritDialog(self.root,self.f.store,'old_spirit');self.root.update()
        d.research_box.set('armor');d.research_amount.set('.15');d.add_research_bonus()
        d.equipment_box.set('infantry_equipment');d.equipment_stat_box.set('soft_attack');d.equipment_amount.set('.3');d.instant_box.set('');d.add_equipment_bonus()
        self.assertNotIn('instant',d.equipment_bonuses['infantry_equipment'])
        d.ok();self.root.update();self.assertFalse(d.winfo_exists())
        research,equipment=self.f.store.spirit_bonuses('old_spirit');self.assertEqual(research['armor'],'0.15');self.assertEqual(equipment['infantry_equipment']['soft_attack'],'0.3');self.assertNotIn('instant',equipment['infantry_equipment'])
