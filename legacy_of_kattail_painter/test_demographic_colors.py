"""Native RGB operands, duplicate execution and ungrouped culture persistence."""
from decimal import Decimal,ROUND_DOWN
from pathlib import Path
import tkinter as tk
import unittest

from model import World,parse,child,value,walk
from character_model import CharacterStore
from demographics import MapCatalogStore,CATALOG_PATHS
import test_painter as fixtures


def evaluate_color(text,kind,part='bottom',cultures=(),species=0,minority=1000,initial=None):
    """Evaluate this project's native color arithmetic on a 0.001 fixed grid.

    This checks script execution paths, rather than merely reading literals.
    It is intentionally limited to operations actually used by these mapmodes.
    """
    mode=child(child(parse(text),'scripted_map_modes').children,f'LOK_{kind}_map_mode')
    color=child(child(mode.children,part).children,'color');variables=dict(initial or {})
    def number(raw):
        try:return Decimal(raw)
        except Exception:return variables.get(raw,Decimal(0))
    def condition(node,v=None):
        if node.key in {'limit','FROM','AND'}:return all(condition(c,v) for c in node.children)
        if node.key=='OR':return any(condition(c,v) for c in node.children)
        if node.key=='always':return value(text,node)=='yes'
        if node.key=='any_of':return any(condition(c,i) for i in cultures for c in node.children if c.key=='check_variable')
        if node.key=='check_variable':
            c=node.children[0];left=Decimal(v) if c.key=='v' else Decimal(species) if c.key=='species' else Decimal(minority) if c.key=='minority' else number(c.key)
            right=number(value(text,c));return left==right if c.op=='=' else left>right if c.op=='>' else left<right
        raise AssertionError('Unsupported test trigger '+node.key)
    operations={'set_temp_variable':lambda a,b:b,'add_to_temp_variable':lambda a,b:a+b,
                'subtract_from_temp_variable':lambda a,b:a-b,'multiply_temp_variable':lambda a,b:a*b,'divide_temp_variable':lambda a,b:a/b}
    def execute(nodes):
        for node in nodes:
            if node.key=='if':
                if condition(child(node.children,'limit')):execute([c for c in node.children if c.key!='limit'])
            elif node.key in operations:
                for c in node.children:
                    variables[c.key]=operations[node.key](variables.get(c.key,Decimal(0)),number(value(text,c))).quantize(Decimal('.001'),rounding=ROUND_DOWN)
            else:raise AssertionError('Unsupported test effect '+node.key)
    execute(color.children)
    return variables


class DemographicColorTests(unittest.TestCase):
    def setUp(self):
        fixtures.FixtureTests.setUp(self)
        def write(rel,text,bom=False):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig' if bom else 'utf-8')
        self.write=write
        branch='''if={limit={any_of={array=FROM.state_cultures value=v check_variable={v=4}}}
            add_to_temp_variable={num_cultures=1}
            add_to_temp_variable={culture_4_red=0.2} add_to_temp_variable={culture_4_green=0.4} add_to_temp_variable={culture_4_blue=0.6}
            divide_temp_variable={culture_4_red=num_cultures} divide_temp_variable={culture_4_green=num_cultures} divide_temp_variable={culture_4_blue=num_cultures}
            if={limit={check_variable={num_cultures>1}} set_temp_variable={factor=num_cultures} subtract_from_temp_variable={factor=1} divide_temp_variable={factor=num_cultures}
            multiply_temp_variable={red=factor} multiply_temp_variable={green=factor} multiply_temp_variable={blue=factor}}
            add_to_temp_variable={red=culture_4_red} add_to_temp_variable={green=culture_4_green} add_to_temp_variable={blue=culture_4_blue}}'''
        write(CATALOG_PATHS['culture_map'],'scripted_map_modes={LOK_culture_map_mode={top={type=none} bottom={color={set_temp_variable={num_cultures=0} '+branch+branch.replace('v=4','v=7').replace('culture_4_','culture_7_')+'}}}}')
        color=lambda field,i,r:f'if={{limit={{FROM={{check_variable={{{field}={i}}}}}}} set_temp_variable={{red={r}}} set_temp_variable={{green=0.4}} set_temp_variable={{blue=0.6}} set_temp_variable={{alpha=alpha_temp}}}}'
        write(CATALOG_PATHS['species_map'],'scripted_map_modes={LOK_species_map_mode={bottom={color={set_temp_variable={alpha_temp=1} '+color('species',1,.2)+'}} top={color={set_temp_variable={alpha_temp=.75} '+color('minority',1,.2)+color('minority',20,.3)+color('minority',20,.8)+'}}}}')
        write(CATALOG_PATHS['culture_loc'],'l_english:\n culture_group_1_name:0 "Group one"\n culture_4_name:0 "Culture four"\n culture_4_desc:0 "Authored"\n culture_4_full:0 "$culture_group_1_name$ $culture_4_desc$"\n culture_7_name:0 "Ungrouped seven"\n culture_7_full:0 "Authored independent description"\n',True)
        write(CATALOG_PATHS['species_loc'],'l_english:\n var_species_1:0 "Species one"\n var_species_20:0 "Species twenty"\n',True)
        write(CATALOG_PATHS['culture_triggers'],'culture_is_culture_group_1={OR={any_of={array=FROM.state_cultures value=v check_variable={v=4}}}}')
        functions=[f'GetCulture{i}{suffix}' for i in range(1,4) for suffix in ('','Desc')]+['GetCultureTemp']
        write(CATALOG_PATHS['culture_text'],'\n'.join('defined_text={name='+name+' text={localization_key=none}}' for name in functions))
        for key in ('culture_effects','species_triggers'):
            write(CATALOG_PATHS[key],'')
        self.world=World(self.root);self.c=CharacterStore(self.world);self.c.game_root=Path(self.tmp.name)/'game';self.c.game_root.mkdir()
        self.catalog=MapCatalogStore(self.world,self.c)

    tearDown=fixtures.FixtureTests.tearDown

    def test_culture_picker_updates_literal_colors_only_including_new_branch(self):
        path=CATALOG_PATHS['culture_map'];before=self.world.docs.text(path)
        self.catalog.set_map_color('culture',4,'#9dffff')
        text=self.world.docs.text(path)
        for _,n in walk(parse(text)):
            if n.key=='divide_temp_variable':
                for c in n.children:
                    if c.key.startswith('culture_4_'):self.assertEqual(value(text,c),'num_cultures')
        self.assertEqual(self.catalog.culture_colors()[4],(157,255,255))
        self.world.docs.undo();self.assertEqual(self.world.docs.text(path),before);self.world.docs.redo()
        self.catalog.set_map_color('culture',103,'#3944ca')
        text=self.world.docs.text(path)
        self.assertIn('culture_103_red=num_cultures',text)
        self.assertEqual(self.catalog.culture_colors()[103],(57,68,202))

    def test_all_matching_species_branches_change_and_save_exact_byte_colors(self):
        self.catalog.set_map_color('species',20,'#9dffff','top')
        text=self.catalog.text('species_map');mode=child(child(parse(text),'scripted_map_modes').children,'LOK_species_map_mode');top=child(child(mode.children,'top').children,'color')
        colors=[]
        for branch in top.children:
            if branch.key!='if' or 20 not in self.catalog.checked_ids(text,branch,'minority'):continue
            rgb={c.key:Decimal(value(text,c)) for n in branch.children if n.key=='set_temp_variable' for c in n.children if c.key in {'red','green','blue'}}
            self.assertEqual(rgb,{'red':Decimal('.616'),'green':Decimal('1'),'blue':Decimal('1')});colors.append(rgb)
        self.assertEqual(len(colors),2)
        self.catalog.set_map_color('species',61,'#9dffff','bottom')
        self.world.docs.save();w=World(self.root);c=CharacterStore(w);catalog=MapCatalogStore(w,c)
        self.assertEqual(catalog.species_colors()[0][61],(157,255,255));self.assertEqual(catalog.species_colors()[1][20],(157,255,255))
        self.assertEqual(w.species_colours[61],(157,255,255))

    def test_engine_precision_preserves_every_byte_value(self):
        # Three-decimal native fractions have enough resolution for all 256
        # byte components; six-decimal exports are unnecessary.
        for byte in range(256):
            self.catalog.set_map_color('species',1,(byte,byte,byte),'bottom')
            self.assertEqual(self.catalog.species_colors()[0][1],(byte,byte,byte))
        text=self.catalog.text('species_map')
        self.assertIn('red=1.000',text)

    def test_saved_culture_arithmetic_executes_single_and_mixed_colors(self):
        self.catalog.set_map_color('culture',4,'#ff0000');self.catalog.set_map_color('culture',7,'#0000ff')
        text=self.catalog.text('culture_map')
        one=evaluate_color(text,'culture',cultures=(4,));both=evaluate_color(text,'culture',cultures=(4,7))
        self.assertEqual(tuple(one[k] for k in ('red','green','blue')),(1,0,0))
        self.assertEqual(tuple(both[k] for k in ('red','green','blue')),(Decimal('.5'),0,Decimal('.5')))

    def test_ungrouped_cultures_create_edit_group_remove_and_roundtrip(self):
        self.assertIsNone(self.catalog.cultures()[7].group)
        self.catalog.edit_culture(7,'Ungrouped seven','','#123456','',None)
        self.assertEqual(self.catalog.localisations('culture_loc')['culture_7_full'],'Authored independent description')
        self.catalog.edit_culture(103,'New independent','','#3944ca','',None,True)
        self.assertIsNone(self.catalog.cultures()[103].group)
        self.assertNotIn('culture_group_None',self.catalog.text('startup'))
        self.assertNotIn('culture_group_None',self.catalog.text('culture_loc'))
        self.catalog.edit_culture(4,'Culture four','Authored','#336699','',None)
        self.assertIsNone(self.catalog.cultures()[4].group)
        self.assertNotIn(4,self.catalog.checked_ids(self.catalog.text('culture_triggers'),parse(self.catalog.text('culture_triggers'))[0],'v'))
        self.catalog.edit_culture(103,'New independent','','#3944ca','',1)
        self.assertEqual(self.catalog.cultures()[103].group,1)
        self.world.docs.undo();self.assertIsNone(self.catalog.cultures()[103].group);self.world.docs.redo()
        self.world.docs.save();w=World(self.root);c=CharacterStore(w);catalog=MapCatalogStore(w,c)
        self.assertIsNone(catalog.cultures()[4].group);self.assertEqual(catalog.cultures()[103].group,1)
        self.assertTrue((self.root/CATALOG_PATHS['culture_loc']).read_bytes().startswith(b'\xef\xbb\xbf'))

    def test_ungrouped_culture_dialog_can_apply_without_integer_error(self):
        from painter import MapDefinitionDialog
        root=tk.Tk();root.withdraw();root.attributes('-alpha',0);errors=[]
        root.report_callback_exception=lambda typ,val,tb:errors.append(str(val))
        try:
            d=MapDefinitionDialog(root,self.catalog,'Cultures');d.attributes('-alpha',0);root.deiconify();root.update()
            d.ident.set('103');d.name.set('Independent');d.group.set('');d.color.set('#3944ca');d.ok();root.update()
            self.assertFalse(d.winfo_exists());self.assertIsNone(self.catalog.cultures()[103].group)
            self.assertFalse(errors)
        finally:root.destroy()


if __name__=='__main__':unittest.main()
