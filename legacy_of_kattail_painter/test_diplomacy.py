"""Native diplomacy discovery and draft editing in disposable mod/game fixtures."""
from dataclasses import replace
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

import numpy as np

import test_countries as fixtures
from model import World,Emblems,parse
from character_model import CharacterStore
from demographics import Setup,CATALOG_PATHS,STARTUP
from diplomacy_model import DiplomacyStore,Relation
from script_format import tokens


class DiplomacyTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.CountryTests();self.f.setUp();self.addCleanup(self.f.tearDown);self.root=self.f.root
        tags=self.root/'common/country_tags/tags.txt';tags.write_text(tags.read_text()+'\nCCC="countries/CCC.txt" DDD="countries/DDD.txt"')
        for tag in ('CCC','DDD'):
            self.write(f'common/countries/{tag}.txt','color=rgb { 20 30 40 }')
            self.write(f'history/countries/{tag}.txt','capital = 1\nset_politics = { ruling_party = neutrality }\nset_popularities = { neutrality = 100 }\n')
        self.path='history/countries/AAA - Native.txt';self.write(self.path,(self.root/self.path).read_text()+'''
create_faction = "Test faction"
add_to_faction = BBB
set_autonomy = { target = CCC autonomy_state = autonomy_custom freedom_level = .3 end_wars = no }
BBB = { give_guarantee = AAA }
every_country = {
    limit = { is_in_faction_with = AAA }
    declare_war_on = { target = DDD type = annex_everything custom = keep } # war note
}
if = { limit = { exists = yes CCC = { exists = yes } }
    declare_war_on = { target = CCC type = annex_everything } }
1940.1.1 = { give_military_access = DDD }
fixture_diplomacy_effect = yes
''')
        self.write('common/scripted_effects/test.txt','fixture_diplomacy_effect = { give_military_access = CCC }')
        self.write('common/autonomous_states/test.txt','autonomy_state = { id = autonomy_puppet } autonomy_state = { id = autonomy_custom }')
        self.write('common/wargoals/test.txt','wargoal_types = { annex_everything = { } puppet_wargoal = { } }')
        self.write('history/general/relations.txt','DDD = { diplomatic_relation = { country = BBB relation = non_aggression_pact active = yes } }')
        p=self.root/STARTUP;self.write(STARTUP,p.read_text(encoding='utf-8-sig').replace('preserve_startup = yes','preserve_startup = yes DDD = { give_market_access = CCC }'))
        self.world=World(self.root);self.world.demographics=Setup(self.world).load();self.c=CharacterStore(self.world);self.c.game_root=self.f.game
        self.s=DiplomacyStore(self.world,self.c)

    def write(self,path,text):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')

    def find(self,kind,actor,target='',group=None):
        return next(r for r in self.s.records() if (r.kind,r.actor,r.target)==(kind,actor,target) and (group is None or r.group==group))

    def test_detects_incoming_nested_custom_dated_conditional_startup_and_shared_effect(self):
        records=self.s.records()
        self.assertEqual(self.find('subject','AAA','CCC').detail,'autonomy_custom')
        self.assertIn('BBB =',self.world.docs.text(self.find('guarantee','BBB','AAA').path))
        self.assertTrue(self.find('war','AAA','CCC').conditional)
        self.assertEqual(self.find('military_access','AAA','DDD').context,('1940.1.1',))
        self.assertTrue(self.find('war','AAA','DDD').group);self.assertTrue(self.find('war','BBB','DDD').group)
        self.assertEqual(self.find('market_access','DDD','CCC').path,STARTUP)
        shared=self.find('military_access','AAA','CCC');self.assertFalse(shared.editable)
        self.assertIn('Shared scripted effect',shared.context[0]);self.assertFalse(self.world.docs.changed)
        # Ownership paint stages histories before the general UI index refresh.
        self.world.set_owner_draft(2,'DDD')
        self.assertFalse(any(r.group and r.actor=='BBB' for r in self.s.records()))

    def test_group_instance_remove_edit_preserves_other_members_conditions_comments_unknowns(self):
        old=(self.root/self.path).read_bytes();row=self.find('war','BBB','DDD',True)
        self.s.change(row)
        self.assertFalse(any(r.kind=='war' and r.actor=='BBB' and r.target=='DDD' for r in self.s.records()))
        self.assertEqual(self.find('war','AAA','DDD').detail,'annex_everything')
        text=self.world.docs.text(self.path);self.assertIn('# war note',text);self.assertIn('custom = keep',text)
        self.assertIn('is_in_faction_with = AAA',text);self.assertEqual((self.root/self.path).read_bytes(),old)
        self.world.docs.undo();row=self.find('war','BBB','DDD',True)
        self.s.change(row,replace(row,detail='puppet_wargoal'))
        self.assertEqual(self.find('war','BBB','DDD').detail,'puppet_wargoal')
        self.assertEqual(self.find('war','AAA','DDD').detail,'annex_everything')
        self.world.docs.save();fresh=World(self.root);s=DiplomacyStore(fresh,CharacterStore(fresh))
        self.assertEqual(next(r.detail for r in s.records() if r.kind=='war' and r.actor=='BBB' and r.target=='DDD'),'puppet_wargoal')

    def test_add_subject_before_politics_keep_wars_faction_order_undo_and_duplicate_checks(self):
        self.s.add(Relation('subject','BBB','DDD','autonomy_custom','.25'))
        text=self.world.docs.text(self.world.countries['DDD']);self.assertLess(text.index('set_autonomy'),text.index('set_politics'))
        self.assertIn('end_wars = no',text);self.assertIn('keep_subjects = yes',text)
        self.world.docs.undo();self.assertFalse(any(r.kind=='subject' and r.target=='DDD' for r in self.s.records()))
        self.s.add(Relation('faction','DDD',detail='User entered faction'));self.s.add(Relation('member','DDD','CCC'))
        text=self.world.docs.text(self.world.countries['DDD']);self.assertLess(text.index('create_faction'),text.index('add_to_faction'))
        with self.assertRaises(ValueError):self.s.add(Relation('member','DDD','BBB'))
        with self.assertRaises(ValueError):self.s.add(Relation('member','DDD','CCC'))
        with self.assertRaises(ValueError):self.s.change(self.find('faction','DDD'))

    def test_guarantee_edit_remove_nonaggression_cancel_and_stale_source(self):
        row=self.find('guarantee','BBB','AAA');self.s.change(row,replace(row,target='DDD'))
        self.assertEqual(self.find('guarantee','BBB','DDD').actor,'BBB')
        self.s.change(self.find('guarantee','BBB','DDD'));self.assertFalse(any(r.kind=='guarantee' for r in self.s.records()))
        self.s.add(Relation('non_aggression_pact','AAA','DDD',active=False))
        self.assertFalse(self.find('non_aggression_pact','AAA','DDD').active)
        row=self.find('subject','AAA','CCC');self.world.docs.replace(self.path,'# offset\n'+self.world.docs.text(self.path))
        with self.assertRaisesRegex(ValueError,'refresh'):self.s.change(row)

    def test_invalid_refs_cycles_same_faction_wars_unknown_goals_numeric_and_shared_no_writes(self):
        for row in [Relation('war','AAA','AAA','annex_everything'),Relation('war','AAA','ZZZ','annex_everything'),
                    Relation('war','AAA','BBB','annex_everything'),Relation('war','AAA','DDD','invalid_goal'),
                    Relation('subject','CCC','AAA','autonomy_puppet'),Relation('subject','BBB','DDD','missing_autonomy'),
                    Relation('subject','BBB','DDD','autonomy_puppet','NaN'),Relation('subject','BBB','DDD','autonomy_puppet','1.1')]:
            with self.subTest(row=row),self.assertRaises(ValueError):self.s.add(row)
            self.assertFalse(self.world.docs.changed)
        with self.assertRaises(ValueError):self.s.change(self.find('military_access','AAA','CCC'))
        self.assertFalse(self.world.docs.changed)

    def test_edit_custom_subject_preserves_extra_fields_and_guarded_war_scope(self):
        row=self.find('subject','AAA','CCC');self.s.change(row,replace(row,detail='autonomy_puppet',freedom='.6'))
        self.assertIn('end_wars = no',self.world.docs.text(self.path));self.assertEqual(self.find('subject','AAA','CCC').freedom,'.6')
        conditional=self.find('war','AAA','CCC');self.s.change(conditional,replace(conditional,detail='puppet_wargoal'))
        text=self.world.docs.text(self.path);self.assertRegex(text,r'CCC\s*=\s*\{\s*exists\s*=\s*yes\s*\}')
        self.assertTrue(self.find('war','AAA','CCC').conditional)

    def test_effective_catalog_replace_paths_and_invalid_literal_relation_can_be_removed(self):
        native=self.c.game_root/'common/autonomous_states/native.txt';native.parent.mkdir(parents=True,exist_ok=True);native.write_text('autonomy_state = { id = native_level }')
        self.assertIn('native_level',self.s.autonomies())
        self.world.docs.replace('descriptor.mod','replace_path = "common/autonomous_states"')
        self.assertNotIn('native_level',self.s.autonomies());self.assertIn('autonomy_custom',self.s.autonomies())
        self.world.docs.replace(self.path,self.world.docs.text(self.path)+'\nadd_to_faction = ZZZ\n')
        row=self.find('member','AAA','ZZZ');self.assertTrue(row.editable);self.s.change(row)
        self.assertNotIn('ZZZ',self.world.docs.text(self.path))

    def test_legacy_puppet_block_upgrades_safely_and_unchanged_escaped_faction_is_noop(self):
        old=self.find('subject','AAA','CCC')
        text=self.world.docs.text(self.path).replace(old.raw,'puppet = { target = CCC end_wars = no end_civil_wars = no }')
        self.world.docs.replace(self.path,text.replace('"Test faction"','"Test \\"quoted\\" faction"'))
        faction=self.find('faction','AAA');self.assertEqual(faction.detail,'Test "quoted" faction')
        before=dict(self.world.docs.drafts);self.s.change(faction,Relation('faction','AAA',detail=faction.detail));self.assertEqual(self.world.docs.drafts,before)
        puppet=self.find('subject','AAA','CCC');self.s.change(puppet,replace(puppet,detail='autonomy_custom',freedom='.4'))
        updated=self.find('subject','AAA','CCC');self.assertTrue(updated.raw.startswith('set_autonomy'))
        self.assertIn('end_civil_wars = no',updated.raw);self.assertEqual(updated.detail,'autonomy_custom')

    def test_real_country_tab_lists_incoming_and_group_wars_dialog_apply_cancel_outer_cancel(self):
        from painter import Painter
        from country_ui import CountryDialog
        from diplomacy_ui import RelationDialog
        for relative in set(CATALOG_PATHS.values()):
            p=self.root/relative
            if not p.exists():self.write(relative,'l_english:\n' if p.suffix=='.yml' else '')
        self.write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={}} top={color={}}}}')
        self.world.map_ids=np.tile(np.array([1]*40+[2]*40,dtype=np.int32),(40,1));self.world.map_ids[0,-1]=0
        root=tk.Tk();root.attributes('-alpha',0);errors=[];root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            with patch('character_model.default_paths',return_value={'game':self.f.game}),patch('diplomacy_ui.messagebox.showerror',side_effect=AssertionError('Unexpected diplomacy error')):
                app=Painter(root,self.world,Emblems());root.update();dialog=CountryDialog(root,app,'AAA');dialog.tabs.select(dialog.frames['diplomacy']);root.update()
                panel=dialog.diplomacy_panel;self.assertTrue(any(r.actor=='BBB' and r.kind=='guarantee' for r in panel.values.values()))
                relation=RelationDialog(dialog,app.diplomacy_store,'AAA',panel.choices());relation.kind.set('military_access');relation.configure_kind(True);relation.target.set('DDD');relation.ok()
                self.assertTrue(relation.result);panel.refresh();self.assertTrue(any(r.kind=='military_access' and r.target=='DDD' and not r.conditional for r in panel.values.values()))
                # Cancelling the parent rolls back its nested diplomacy edits too.
                dialog.cancel();self.assertFalse(self.world.docs.changed)
                self.assertFalse(errors);app.cancel_map_job();app.destroy()
        finally:root.update_idletasks();root.destroy()


if __name__=='__main__':unittest.main()
