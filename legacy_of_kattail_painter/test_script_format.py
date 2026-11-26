"""Changed-block formatting preserves Clausewitz tokens, comments and bytes."""
from pathlib import Path
import tempfile
import unittest

from model import Documents,parse,child
from character_model import patch_field
from script_format import format_changes,format_paths,index_nodes,tokens,script_path,Renderer


class ScriptFormatTests(unittest.TestCase):
    def test_spirit_blocks_match_native_tab_depth_and_preserve_compact_allowed(self):
        raw='ideas = {\n\tcountry = {\n\t\tMCF = { picture = MCF allowed = { always = no } modifier = {\n\tarmy_core_defence_factor = .1\n} research_bonus = {air_equipment=-.5} }\n}\n}'
        result=format_changes('common/ideas/test.txt','',raw)
        self.assertIn('\t\tMCF = {\n\t\t\tpicture = MCF\n\t\t\tallowed = { always = no }',result)
        self.assertIn('\t\t\t\tarmy_core_defence_factor = .1',result)
        self.assertIn('\t\t\tresearch_bonus = {\n\t\t\t\tair_equipment = -.5',result)
        self.assertEqual(tokens(raw),tokens(result));self.assertEqual(format_changes('common/ideas/test.txt','',result),result)

    def test_comments_strings_operators_duplicates_and_typed_colors_keep_exact_tokens(self):
        raw='''# leading
ideas={ country={ foo={ # header
 text="literal { # \\"quote\\" }" color=rgb { 10 20 30 }
 modifier={a=.1 a=-2 # trailing
 # own comment
 b>3} # close
 }}}'''
        result=format_changes('common/ideas/x.txt','',raw)
        self.assertEqual(tokens(raw),tokens(result));self.assertIn('color = rgb { 10 20 30 }',result)
        self.assertIn('a = -2 # trailing',result);self.assertIn('# own comment',result)

    def test_edit_formats_only_changed_definition_and_retains_other_bytes(self):
        before='ideas = {\n\tcountry = {\n\t\tuntouched={modifier={x=1}} # authored compact\n\t\tchanged = { modifier = { x = 1 } }\n\t}\n}\n'
        after=before.replace('x = 1','x = 2')
        result=format_changes('common/ideas/test.txt',before,after)
        self.assertIn('\t\tuntouched={modifier={x=1}} # authored compact',result)
        self.assertIn('\t\tchanged = {\n\t\t\tmodifier = {\n\t\t\t\tx = 2',result)
        self.assertEqual(tokens(after),tokens(result))

    def test_field_insertion_uses_nesting_even_with_inline_parent(self):
        text='ideas = {\n\tcountry = {\n\t\tX = { picture = x modifier = { a=1 } }\n\t}\n}'
        idea=child(child(child(parse(text),'ideas').children,'country').children,'X')
        result=patch_field(text,idea,'research_bonus','{\nindustry=.1\n}')
        self.assertIn('\n\t\t\tresearch_bonus',result)
        final=format_changes('common/ideas/test.txt',text,result)
        self.assertIn('\t\t\t\tindustry = .1',final)

    def test_long_lists_wrap_and_root_inline_statements_separate(self):
        raw='state={provinces={'+' '.join(str(i) for i in range(100))+'}}'
        result=format_changes('history/states/one.txt','',raw)
        self.assertEqual(tokens(raw),tokens(result));self.assertLess(len(result.splitlines()),15)
        result=format_changes('history/countries/AAA.txt','','capital=1 set_stability=.5 set_popularities={democratic=100}')
        self.assertIn('capital = 1\nset_stability = .5\nset_popularities = {',result)

    def test_save_formats_generated_text_and_staged_script_bytes_preserving_bom_and_crlf(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path='common/ideas/test.txt';p=root/path;p.parent.mkdir(parents=True)
            p.write_bytes(b'\xef\xbb\xbfideas = {\r\n\tcountry = { }\r\n}\r\n')
            docs=Documents(root);docs.replace(path,'ideas = {\r\n\tcountry = { X={modifier={a=.1}} }\r\n}\r\n')
            docs.stage_bytes('interface/test.gfx',b'spriteTypes={ spriteType={name="GFX_test" texturefile="gfx/test.tga"} }')
            docs.save();blob=p.read_bytes();self.assertTrue(blob.startswith(b'\xef\xbb\xbf'))
            self.assertNotIn(b'\n',blob.replace(b'\r\n',b''));self.assertIn(b'\t\tX = {',blob)
            self.assertEqual(tokens((root/'interface/test.gfx').read_text()),tokens('spriteTypes={ spriteType={name="GFX_test" texturefile="gfx/test.tga"} }'))

    def test_non_clausewitz_outputs_and_untouched_files_are_never_formatted(self):
        for path in ['map/railways.txt','map/supply_nodes.txt','map/buildings.txt','map/definition.csv','localisation/english/test.yml','file.json']:
            self.assertFalse(script_path(path));self.assertEqual(format_changes(path,'','1 2 3\n'),'1 2 3\n')
        raw='root={ a=1 }';self.assertEqual(format_changes('common/test.txt',raw,raw),raw)


if __name__=='__main__':unittest.main()
