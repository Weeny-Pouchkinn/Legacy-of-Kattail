"""Native/mod overlays, bounded randomization and guarded trait editing fixtures."""
import io
from pathlib import Path
import random
import tkinter as tk
import unittest

import test_characters as character_tests
from character_model import CharacterStore, atom
from character_ui import RoleDialog
from trait_model import TRAIT_LOC, TRAIT_PATHS, documented_modifiers
from trait_ui import TraitDialog
from model import World, parse, value


class TraitTests(unittest.TestCase):
    def setUp(self):
        self.fixture = character_tests.CharacterTests(); self.fixture.setUp()
        self.root = self.fixture.root; self.world = self.fixture.world; self.characters = self.fixture.store
        self.base = self.root.parent / 'game'
        for folder in ('common/unit_leader', 'common/country_leader', 'common/defines', 'documentation', 'localisation/english'):
            (self.base / folder).mkdir(parents=True, exist_ok=True)
        (self.base / 'common/unit_leader/00_traits.txt').write_text('''leader_traits = {
 steady = { type = land trait_type = personality_trait new_commander_weight = { factor = 1 modifier = { has_trait = reckless factor = 0 } } }
 reckless = { type = land trait_type = personality_trait mutually_exclusive = steady new_commander_weight = { factor = 1 } }
 engineer = { type = land trait_type = basic_trait modifier = { army_attack_factor = 0.1 } }
 terrain = { type = land trait_type = basic_terrain_trait }
 mariner = { type = navy trait_type = personality_trait new_commander_weight = { factor = 1 } }
 sea_wolf = { type = navy trait_type = basic_trait }
 national = { type = land trait_type = personality_trait allowed = { FROM = { original_tag = AAA } } new_commander_weight = { factor = 1 } }
 injured = { type = all trait_type = status_trait }
 needs_parent = { type = land trait_type = assignable_trait parent = { traits = { engineer } } }
}''')
        (self.base / 'common/country_leader/base_traits.txt').write_text('@gain = 0.15\nleader_traits = { base_politician = { random = no stability_factor = @gain } }')
        unit = self.root / 'common/unit_leader'; unit.mkdir(exist_ok=True)
        (unit / 'lok_traits.txt').write_text('leader_traits = {\n\t# Authored credit\n\tlok_custom = { type = land trait_type = personality_trait modifier = { army_attack_factor = 0.15 } }\n}\n')
        tables = []
        for name in ('leader_skills', 'leader_attack_skills', 'leader_defense_skills', 'leader_planning_skills', 'leader_logistics_skills', 'leader_maneuvering_skills', 'leader_coordination_skills'):
            limit = 9 if name == 'leader_skills' else 10
            tables.append(name + ' = { ' + ' '.join(str(i) + ' = { type = ' + kind + ' }' for kind in ('navy', 'corps_commander', 'field_marshal') for i in range(1, limit + 1)) + ' }')
        (self.base / 'common/unit_leader/00_skills.txt').write_text('\n'.join(tables))
        (self.base / 'common/defines/00_defines.lua').write_text('''COMMANDER_LEVEL_UP_STAT_COUNT = 3,
COMMANDER_LEVEL_UP_STAT_WEIGHTS = {5,5,5,5},
NAVY_LEADER_LEVEL_UP_STAT_WEIGHTS = {5,5,5,5},''')
        (self.base / 'localisation/english/traits_l_english.yml').write_text('l_english:\n steady:0 "Steady Leader"\n engineer:0 "Engineer"\n MODIFIERS_ARMY_ATTACK_FACTOR:0 "Division Attack"\n MODIFIER_STABILITY_FACTOR:0 "Stability"\n base_politician:0 "Base Politician"\n', encoding='utf-8-sig')
        (self.base / 'documentation/modifiers_documentation.md').write_text('## army_attack_factor\n* **Categories**: army, aggressive\n## stability_factor\n* **Categories**: country\n')
        self.characters.game_root = self.base; self.traits = self.characters.trait_store

    def tearDown(self): self.fixture.tearDown()

    def test_active_overlay_including_empty_files_and_all_source_versions(self):
        self.assertTrue(any(t.key == 'steady' and t.active for t in self.traits.records()))
        self.world.docs.stage_bytes('common/unit_leader/00_traits.txt', b'')
        records = self.traits.records()
        self.assertTrue(any(t.key == 'steady' and not t.active for t in records))
        self.assertNotIn(('unit', 'steady'), self.traits.effective())
        self.assertIn(('unit', 'lok_custom'), self.traits.effective())
        self.world.docs.undo()
        self.assertIn(('unit', 'steady'), self.traits.effective())

    def test_roles_use_appropriate_native_trait_database(self):
        generals = {c.code for c in self.traits.choices_for_role('corps_commander')}
        admirals = {c.code for c in self.traits.choices_for_role('navy_leader')}
        politicians = {c.code for c in self.traits.choices_for_role('advisor')}
        self.assertIn('steady', generals); self.assertNotIn('mariner', generals)
        self.assertIn('mariner', admirals); self.assertNotIn('steady', admirals)
        self.assertIn('base_politician', politicians); self.assertNotIn('steady', politicians)
        cached = self.traits.choices_for_role('corps_commander')
        self.characters.edit_role('AAA_Zed', 1, 'country_leader', {'ideology': 'updated'}, [])
        self.assertIs(self.traits.choices_for_role('corps_commander'), cached)

    def test_level_budget_bounds_and_separate_admiral_fields(self):
        for role in ('corps_commander', 'field_marshal', 'navy_leader'):
            for level in range(1, 10):
                for seed in range(8):
                    result = self.traits.random_skills(role, level, random.Random(seed))
                    self.assertEqual(sum(result.values()), 4 + 3 * (level - 1))
                    self.assertTrue(all(1 <= v <= 10 for v in result.values()))
                    self.assertEqual('coordination_skill' in result, role == 'navy_leader')
        for level in ('bad', '0', '10'):
            with self.assertRaises(ValueError): self.traits.random_skills('corps_commander', level)
        with self.assertRaises(ValueError): self.traits.random_skills('advisor', 3)

    def test_mod_define_drafts_and_undo_change_skill_budget(self):
        self.traits.random_skills('corps_commander', 2)
        self.world.docs.replace('common/defines/lok.lua', 'NDefines.NMilitary.COMMANDER_LEVEL_UP_STAT_COUNT = 2\n')
        self.assertEqual(sum(self.traits.random_skills('corps_commander', 3).values()), 8)
        self.world.docs.undo()
        self.assertEqual(sum(self.traits.random_skills('corps_commander', 3).values()), 10)
        self.world.docs.replace('common/defines/lok.lua', 'NDefines.NMilitary.COMMANDER_LEVEL_UP_STAT_COUNT = arbitrary_expression\n')
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, 'Lua expression'): self.traits.random_skills('corps_commander', 2)

    def test_random_traits_preserve_custom_status_and_restrictions(self):
        for seed in range(40):
            result = self.traits.random_traits('corps_commander', ['lok_custom', 'injured', 'national'], 3, rng=random.Random(seed))
            self.assertTrue({'lok_custom', 'injured', 'national'} <= set(result))
            self.assertFalse({'steady', 'reckless'} <= set(result))
            self.assertNotIn('mariner', result); self.assertNotIn('needs_parent', result)
            self.assertEqual(len(result), len(set(result)))
            naval = self.traits.random_traits('navy_leader', [], 2, rng=random.Random(seed))
            self.assertEqual(set(naval), {'mariner', 'sea_wolf'})
        with self.assertRaises(ValueError): self.traits.random_traits('navy_leader', [], 3)

    def test_added_traits_sorted_native_destinations_and_loc_not_collected_as_character(self):
        original = self.world.docs.text(TRAIT_PATHS['unit'])
        body = '\t\ttype = land\n\t\ttrait_type = personality_trait\n\t\tmodifier = { army_attack_factor = 0.1 }\n'
        self.traits.edit('lok_zed', 'unit', 'Zed Trait', '', body, create=True)
        self.traits.edit('AAA_Zed_alpha', 'unit', 'Alpha Trait', 'Authored $TOKEN$\nDescription', body, create=True)
        self.traits.edit('lok_advisor', 'country', 'Advisor Trait', '', '\t\trandom = no\n\t\tstability_factor = 0.1\n', create=True)
        text = self.world.docs.text(TRAIT_PATHS['unit']); root = parse(text)[0]
        keys = [n.key for n in root.children]; self.assertEqual(keys, sorted(keys, key=str.casefold))
        self.assertIn('# Authored credit', text)
        self.assertIn('army_attack_factor = 0.15', text)
        self.characters.prepare_save()
        self.assertIn('AAA_Zed_alpha:0', self.world.docs.text(TRAIT_LOC))
        self.assertNotIn('AAA_Zed_alpha:0', self.world.docs.text('localisation/english/characters_l_english.yml'))
        self.assertIn('lok_advisor', self.world.docs.text(TRAIT_PATHS['country']))
        self.assertTrue(self.world.docs.binary(TRAIT_LOC).startswith(b'\xef\xbb\xbfl_english:'))
        self.world.docs.save()
        fresh = CharacterStore(World(self.root)); fresh.game_root = self.base
        self.assertIn(('unit', 'AAA_Zed_alpha'), fresh.trait_store.effective())
        self.assertEqual(fresh.localisations()['AAA_Zed_alpha_desc'], 'Authored $TOKEN$\nDescription')

    def test_duplicate_ids_vanilla_edits_and_constant_safe_clone(self):
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.traits.edit('steady', 'unit', 'Other', '', 'type = land', create=True)
        with self.assertRaisesRegex(ValueError, 'clone vanilla'):
            self.traits.edit('steady', 'unit', 'Other', '', 'type = land')
        original = next(t for t in self.traits.records() if t.key == 'base_politician')
        body = self.traits.body(original, clone=True)
        self.assertNotIn('@gain', body); self.assertIn('stability_factor = 0.15', body)
        self.traits.edit('lok_politician_copy', 'country', 'Copied Name', '', body, create=True)
        self.assertIn('stability_factor = 0.15', self.world.docs.text(TRAIT_PATHS['country']))

    def test_modifiers_use_plural_loc_and_custom_definition_and_no_rebuild_on_stats(self):
        directory = self.root / 'common/modifier_definitions'; directory.mkdir()
        (directory / 'lok.txt').write_text('lok_bonus = { category = country value_type = number }')
        self.characters.set_loc('lok_bonus', 'Custom Bonus')
        catalog = self.traits.modifier_catalog()
        self.assertEqual(catalog['army_attack_factor']['choice'].label, 'Division Attack (army_attack_factor)')
        self.assertEqual(catalog['lok_bonus']['choice'].label, 'Custom Bonus (lok_bonus)')
        self.characters.edit_role('AAA_Zed', 1, 'country_leader', {'ideology': 'updated'}, [])
        self.assertIs(self.traits.modifier_catalog(), catalog)

    def test_documented_modifier_templates_categories_case_and_formats(self):
        text='''## Table of Content
## army_core_defence_factor
* Number with 1 decimal places
* **Categories**: army, defensive
##  <span id="production_speed__factor"></span>production_speed_<Building>_factor
* **Description**: Construction speed.
* Number with 2 decimal places
* **Categories**: country
* **Modified types**: arms_factory, industrial_complex
##  <span id="production_speed__factor"></span>production_speed_<Building>_factor
* **Categories**: war_production
* **Modified types**: arms_factory
## <span id="_cost"></span><Operation>_cost
* **Categories**: intelligence_agency
* **Modified types**: FRA_coup_in_central_africa
## Modifiers for scope state
* **Categories**: state
## can_guarantee_other_ideologies
* Boolean
* **Categories**: country
'''
        info=documented_modifiers(text.replace('\n','\r\n'))
        self.assertEqual(set(info),{'army_core_defence_factor','production_speed_arms_factory_factor','production_speed_industrial_complex_factor','FRA_coup_in_central_africa_cost','can_guarantee_other_ideologies'})
        self.assertEqual(info['army_core_defence_factor']['categories'],{'army','defensive'})
        self.assertEqual(info['production_speed_arms_factory_factor']['categories'],{'country','war_production'})
        self.assertEqual(info['production_speed_industrial_complex_factor']['precision'],2)
        self.assertEqual(info['production_speed_industrial_complex_factor']['description'],'Construction speed.')
        self.assertEqual(info['FRA_coup_in_central_africa_cost']['categories'],{'intelligence_agency'})
        self.assertEqual(info['can_guarantee_other_ideologies']['value_type'],'yes_no')

    def test_spirit_choices_use_categories_as_tooltip_tags_and_retain_custom_overrides(self):
        doc=self.base/'documentation/modifiers_documentation.md'
        doc.write_text(doc.read_text()+'\n## army_core_defence_factor\n* **Categories**: army, defensive\n## <span id="_cost"></span><Operation>_cost\n* **Categories**: intelligence_agency\n* **Modified types**: FRA_example\n## can_guarantee_other_ideologies\n* Boolean\n* **Categories**: country\n')
        self.characters.set_loc('MODIFIERS_ARMY_CORE_DEFENCE_FACTOR','Core defense')
        directory=self.root/'common/modifier_definitions';directory.mkdir()
        (directory/'native.txt').write_text('army_core_defence_factor={category=army category=defensive value_type=percentage}')
        choices={c.code:c for c in self.traits.spirit_modifier_choices()}
        self.assertIn('army_attack_factor',choices);self.assertIn('army_core_defence_factor',choices)
        self.assertIn('FRA_example_cost',choices);self.assertNotIn('attack_skill',choices)
        self.assertEqual(choices['army_core_defence_factor'].name,'Core defense')
        self.assertEqual(self.traits.modifier_catalog()['army_core_defence_factor']['source'],'Mod modifier definition')
        self.assertEqual(self.traits.modifier_value('can_guarantee_other_ideologies','yes'),'yes')
        with self.assertRaises(ValueError):self.traits.modifier_value('army_attack_factor','yes')


class TraitTkTests(unittest.TestCase):
    def setUp(self):
        self.fixture = TraitTests(); self.fixture.setUp(); self.root = tk.Tk(); self.root.attributes('-alpha', 0)
        self.errors = []; self.root.report_callback_exception = lambda *args: self.errors.append(args)

    def tearDown(self):
        self.root.destroy(); self.fixture.tearDown(); self.assertEqual(self.errors, [])

    def test_editor_search_modifier_apply_undo_and_cancel(self):
        s = self.fixture.characters; t = self.fixture.traits
        dialog = TraitDialog(self.root, t); self.root.update()
        dialog.ident.set('lok_ui_new'); dialog.name.set('UI Trait')
        dialog.modifier_box.show('Division Attack'); self.assertIn('Division Attack (army_attack_factor)', dialog.modifier_box.listbox.get(0, 'end'))
        dialog.modifier_box.choose(); dialog.amount.set('0.2'); dialog.add_modifier(); self.root.update()
        self.assertIn('army_attack_factor = 0.2', dialog.raw.get('1.0', 'end-1c'))
        dialog.ok(); self.root.update()
        self.assertIn(('unit', 'lok_ui_new'), t.effective())
        s.docs.undo(); self.assertNotIn(('unit', 'lok_ui_new'), t.effective())
        self.assertFalse(s.docs.changed)
        dialog = TraitDialog(self.root, t); dialog.ident.set('lok_cancel'); dialog.name.set('Cancel'); dialog.cancel()
        self.assertFalse(s.docs.changed)

    def test_role_randomization_cancel_and_apply(self):
        s = self.fixture.characters
        s.edit_role('AAA_Zed', None, 'corps_commander', {'skill': '5'}, ['lok_custom'])
        s.docs.save()
        index = len(s.characters()['AAA_Zed'].roles) - 1
        dialog = RoleDialog(self.root, s, 'AAA_Zed', index); self.root.update()
        dialog.randomize_skills(); dialog.randomize_traits()
        self.assertEqual(sum(int(v.get()) for k, v in dialog.variables.items() if k != 'skill'), 16)
        self.assertIn('lok_custom', dialog.traits.get().split()); dialog.cancel()
        self.assertFalse(s.docs.changed)
        dialog = RoleDialog(self.root, s, 'AAA_Zed', index); dialog.randomize_skills(); dialog.randomize_traits(); dialog.ok()
        c = s.characters()['AAA_Zed']; role = c.roles[index]
        self.assertEqual(sum(int(atom(c.text, role.children, k)) for k in ('attack_skill', 'defense_skill', 'planning_skill', 'logistics_skill')), 16)


if __name__ == '__main__': unittest.main()
