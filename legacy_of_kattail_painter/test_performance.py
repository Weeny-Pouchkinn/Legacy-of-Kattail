"""Prevent repeated expensive work while exercising real cache invalidation."""
from difflib import SequenceMatcher
import io
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

from character_model import inherited_sprites
from country_model import image_dimensions,asset_files
from country_ui import IconPicker
from select_ui import Choice,ChoiceIndex,normalized
import test_countries
import test_eaw_icons
import test_imperium
import test_state_boundaries


class PerformanceTests(unittest.TestCase):
    def fixture(self,kind):
        fixture=kind();fixture.setUp();self.addCleanup(fixture.doCleanups)
        if kind is test_imperium.ImperiumTests:self.addCleanup(fixture.tearDown)
        return fixture

    def test_state_refresh_parses_only_changed_sources_and_still_rejects_duplicate_membership(self):
        f=self.fixture(test_state_boundaries.BoundaryTests);f.store.sync_world(force=True)
        old=f.world.states[2];path=f.world.states[1].path
        f.world.docs.replace(path,f.world.docs.text(path).replace('manpower = 10001','manpower = 10002'))
        with patch.object(f.world.docs,'parsed',wraps=f.world.docs.parsed) as parsed:
            f.store.sync_world(force=True)
        self.assertEqual(parsed.call_count,1);self.assertIs(f.world.states[2],old)
        f.world.docs.undo();f.store.sync_world();self.assertEqual(f.data(1)['population'],'10001')
        f.world.docs.replace(path,f.world.docs.text(path).replace('provinces = { 1 2 3 }','provinces = { 1 2 3 4 }'))
        with self.assertRaisesRegex(ValueError,'multiple states'):f.store.sync_world()

    def test_imperium_cache_reuses_definitions_and_unchanged_states_but_follows_undo_and_loc(self):
        f=self.fixture(test_imperium.ImperiumTests);f.element();elements=f.store.elements();f.store.state_assignments()
        f.store.paint_state(1,1)
        with patch.object(f.store,'value_nodes',wraps=f.store.value_nodes) as values:
            self.assertEqual(f.store.state_assignments(),{1:1})
        self.assertEqual(values.call_count,1);self.assertIs(f.store.elements(),elements)
        f.world.docs.undo();self.assertEqual(f.store.state_assignments(),{})
        f.world.docs.redo();self.assertEqual(f.store.state_assignments(),{1:1})
        f.store._set_loc('lok_ki_element_1_name','New name');self.assertEqual(f.store.elements()[1].name,'New name')
        f.world.docs.undo();self.assertEqual(f.store.elements()[1].name,elements[1].name)

    def test_fast_texture_headers_agree_with_pillow_without_decoding_dds_or_tga(self):
        for suffix in ('.dds','.tga'):
            blob=io.BytesIO();Image.new('RGBA',(65,67),'red').save(blob,format='DDS' if suffix=='.dds' else 'TGA')
            with patch('country_model.Image.open',side_effect=AssertionError('Header inspection must not decode textures')):
                self.assertEqual(image_dimensions(io.BytesIO(blob.getvalue()),suffix),(65,67))
        blob=io.BytesIO();Image.new('RGB',(19,23),'blue').save(blob,format='PNG')
        self.assertEqual(image_dimensions(io.BytesIO(blob.getvalue()),'.png'),(19,23))

    def test_asset_walk_and_portrait_filter_keep_same_valid_assets(self):
        f=self.fixture(test_eaw_icons.EawIconTests)
        root=f.root/'legacy_of_kattail_painter/assets/eaw_ideas'
        self.assertEqual(set(asset_files(root)),set(f.paths.values()))
        catalog=f.store.spirit_icon_catalog();self.assertIn('eaw:EQS/royal_guard.dds',catalog)
        self.assertNotIn('eaw:minister_plain.dds',catalog)

    def test_native_preview_reuses_file_and_decode_then_mod_override_undo_invalidates(self):
        f=self.fixture(test_eaw_icons.EawIconTests);texture='gfx/interface/ideas/performance_test.dds'
        path=f.fixture.game/texture;path.parent.mkdir(parents=True,exist_ok=True);Image.new('RGBA',(60,68),'red').save(path)
        sprite=f.fixture.game/'interface/performance.gfx';sprite.parent.mkdir(parents=True,exist_ok=True)
        sprite.write_text('spriteTypes = { spriteType = { name = GFX_idea_performance texturefile = "'+texture+'" } }')
        key='vanilla:GFX_idea_performance';original=Path.read_bytes
        with patch.object(Path,'read_bytes',autospec=True,side_effect=original) as reads:
            first=f.store.icon_image(key);second=f.store.icon_image(key)
        self.assertIs(first,second);self.assertEqual(sum(c.args[0]==path for c in reads.call_args_list),1)
        blob=io.BytesIO();Image.new('RGBA',(60,68),'blue').save(blob,format='DDS');f.world.docs.stage_bytes(texture,blob.getvalue())
        self.assertEqual(f.store.icon_image(key).getpixel((0,0)),(0,0,255,255))
        f.world.docs.undo();self.assertEqual(f.store.icon_image(key).getpixel((0,0)),(255,0,0,255))
        for size in range(1,265):f.store.icon_image(key,(size,2))
        self.assertLessEqual(len(f.store._icon_previews),256)

    def test_native_sprite_prefix_catalog_matches_full_catalog(self):
        f=self.fixture(test_eaw_icons.EawIconTests)
        root=f.fixture.game/'interface';root.mkdir(parents=True,exist_ok=True)
        (root/'performance_filter.gfx').write_text('spriteTypes = { spriteType = { name = GFX_idea_filtered texturefile = "gfx/a.dds" } spriteType = { name = GFX_other texturefile = "gfx/b.dds" } }')
        full=inherited_sprites(str(f.fixture.game));filtered=inherited_sprites(str(f.fixture.game),'GFX_idea_')
        self.assertEqual(filtered,{k:v for k,v in full.items() if k.startswith('GFX_idea_')})

    def test_bonus_catalog_avoids_repeated_native_reads_and_follows_mod_override_and_undo(self):
        f=self.fixture(test_eaw_icons.EawIconTests);p=f.fixture.game/'common/technology_tags/performance.txt';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('technology_categories = { native_category }');self.assertIn('native_category',f.store.spirit_bonus_catalog()['research'])
        with patch('country_model.read_text',side_effect=AssertionError('Unchanged native files should not be reread')):
            f.store.bonus_choices('research');f.store.bonus_choices('equipment');f.store.bonus_choices('stats')
        f.world.docs.replace('common/technology_tags/performance.txt','technology_categories = { mod_category }')
        self.assertIn('mod_category',f.store.spirit_bonus_catalog()['research']);self.assertNotIn('native_category',f.store.spirit_bonus_catalog()['research'])
        f.world.docs.undo();self.assertIn('native_category',f.store.spirit_bonus_catalog()['research'])

    def test_fuzzy_pruning_matches_original_results_and_unicode_resolution(self):
        choices=[Choice('GFX_idea_'+str(i),name) for i,name in enumerate(['École nationale','Army command','Royal guard','Imperial factory','North coast','Catland alliance'])]
        index=ChoiceIndex(choices)
        for query in ['xx','royla','cst','imperil','noeth','army','ECOLE','alliance','commadn']:
            text=normalized(query).strip();words=text.split()
            expected=[c for c,name,code in index.search if all(w in name+' '+code for w in words)]
            if not expected:
                scored=[(max(SequenceMatcher(None,text,name).ratio(),SequenceMatcher(None,text,code).ratio()),c) for c,name,code in index.search if text[0] in name or text[0] in code]
                expected=[c for score,c in sorted(scored,key=lambda r:-r[0]) if score>=.45][:12]
                expected.sort(key=lambda c:(normalized(c.name),normalized(c.code)))
            self.assertEqual(index.matching(query),expected)
        self.assertEqual(index.resolve('Ecole nationale'),'GFX_idea_0')

    def test_icon_search_reuses_index_but_source_filters_rebuild_and_cancel_cleans_jobs(self):
        f=self.fixture(test_eaw_icons.EawIconTests);root=tk.Tk();root.attributes('-alpha',0);errors=[]
        root.report_callback_exception=lambda *exc:errors.append(exc)
        try:
            picker=IconPicker(root,f.store);root.update_idletasks();index=picker._search_index
            picker.query.set('royal');picker.refresh();self.assertIs(picker._search_index,index)
            self.assertIn('eaw:EQS/royal_guard.dds',picker.tree.get_children())
            picker.sources['EaW'].set(False);picker.filter_sources();self.assertIsNot(picker._search_index,index)
            self.assertNotIn('eaw:EQS/royal_guard.dds',picker.tree.get_children())
            picker.schedule_search();picker.cancel();root.update();self.assertFalse(errors)
        finally:root.destroy()


if __name__=='__main__':unittest.main()
