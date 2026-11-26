"""Reusable historical Imperium elements stored entirely in native game files."""
from dataclasses import dataclass
from decimal import Decimal,ROUND_HALF_UP
import re

from model import parse,child,scalar,value,walk
from character_model import patch_field,LOC,quote,unescape

LAYER='Katzenartig Imperium'
CATALOG='Katzenartig Imperium Elements'
VARIABLE='lok_katzenartig_imperium_element'
MAPMODE='LOK_katzenartig_imperium_map_mode'
MAP_PATH='common/map_modes/LOK_katzenartig_imperium_map_mode.txt'
TEXT_PATH='common/scripted_localisation/LOK_katzenartig_imperium_scripted_loc.txt'
LOC_PATH='localisation/english/lok_katzenartig_imperium_l_english.yml'
FUNCTIONS=('GetKatzenartigImperiumTooltip','GetKatzenartigImperiumTooltipDelayed')
UNASSIGNED=(65,69,78)
MAX_ID=2147483  # Positive integer range of native 32-bit 1/1000 fixed point.


def loc_key(ident,suffix):return f'lok_ki_element_{ident}_{suffix}'


MAP_TEMPLATE='''scripted_map_modes = {
	LOK_katzenartig_imperium_map_mode = {
		top = { type = none }
		bottom = {
			type = state
			color = {
				set_temp_variable = { red = 0.255 }
				set_temp_variable = { green = 0.271 }
				set_temp_variable = { blue = 0.306 }
				set_temp_variable = { alpha = 1 }
			}
		}
		far_text = none
		near_text = state
		update_daily = no
	}
}
'''
TEXT_TEMPLATE=''.join('defined_text = {\n\tname = '+function+'\n\ttext = { localization_key = lok_ki_unassigned_'+suffix+' }\n}\n\n' for function,suffix in zip(FUNCTIONS,('tooltip','tooltip_delayed')))
LOC_TEMPLATE='''l_english:
 MAPMODE_LOK_KATZENARTIG_IMPERIUM_MAP_MODE:0 "Katzenartig Imperium"
 MAPMODE_LOK_KATZENARTIG_IMPERIUM_MAP_MODE_NAME:0 "Katzenartig Imperium"
 MAPMODE_LOK_KATZENARTIG_IMPERIUM_MAP_MODE_DESCRIPTION:0 "Shows the extent and organization of the Katzenartig Imperium at its peak."
 LOK_katzenartig_imperium_map_mode_tooltip:0 "[FROM.GetKatzenartigImperiumTooltip]"
 LOK_katzenartig_imperium_map_mode_tooltip_delayed:0 "[FROM.GetKatzenartigImperiumTooltipDelayed]"
 lok_ki_unassigned_tooltip:0 "[FROM.GetName]"
 lok_ki_unassigned_tooltip_delayed:0 ""
'''


@dataclass(frozen=True)
class ImperiumElement:
    key:int
    name:str
    color:tuple
    immediate:str
    delayed:str


class ImperiumStore:
    def __init__(self,world,characters,catalogs):
        self.world,self.characters,self.catalogs,self.docs=world,characters,catalogs,world.docs
        self._elements_revision=-1;self._elements={};self._assignment_signature=None;self._assignments={}
        world.imperium_store=self

    def bootstrap(self):
        for path,template in ((MAP_PATH,MAP_TEMPLATE),(TEXT_PATH,TEXT_TEMPLATE),(LOC_PATH,LOC_TEMPLATE)):
            if not self.docs.text(path).strip():self.docs.replace(path,template)

    def color_section(self):
        text,roots=self.docs.parsed(MAP_PATH);outer=child(roots,'scripted_map_modes')
        mode=child(outer.children,MAPMODE) if outer else None
        bottom=child(mode.children,'bottom') if mode else None
        section=child(bottom.children,'color') if bottom else None
        if section is None:raise ValueError('Missing native Katzenartig Imperium color block')
        return text,section

    @staticmethod
    def branch_ids(text,node):
        limit=child(node.children,'limit')
        return [int(value(text,n)) for _,n in walk([limit]) if n.key==VARIABLE and n.children is None and n.op=='=' and value(text,n).isdigit()] if limit else []

    def elements(self):
        if self._elements_revision==self.docs.revision:return self._elements
        out={};loc=self.characters.localisations()
        if self.docs.text(MAP_PATH).strip():
            text,section=self.color_section()
            for node in section.children:
                if node.key not in {'if','else_if'}:continue
                ids=self.branch_ids(text,node)
                if not ids:continue
                if len(ids)!=1 or ids[0] in out or not 1<=ids[0]<=MAX_ID:raise ValueError('Imperium element IDs must be unique positive native integers')
                channels={c.key:float(value(text,c)) for n in node.children if n.key=='set_temp_variable' for c in n.children or [] if c.key in {'red','green','blue'}}
                if set(channels)!={'red','green','blue'}:raise ValueError('Imperium elements require three literal color channels')
                ident=ids[0];color=self.world._fraction_rgb(channels)
                out[ident]=ImperiumElement(ident,loc.get(loc_key(ident,'name'),f'Element {ident}'),color,loc.get(loc_key(ident,'tooltip'),''),loc.get(loc_key(ident,'tooltip_delayed'),''))
        self._elements=out;self._elements_revision=self.docs.revision
        return out

    def _set_loc(self,key,text):
        owners=list(dict.fromkeys(r[0] for r in self.characters.loc_records().get(key,()))) or [LOC_PATH]
        for path in owners:
            source=self.docs.text(path);lines=source.splitlines(keepends=True)
            for index,line in enumerate(lines):
                match=LOC.match(line)
                if match and match[1]==key:
                    if unescape(match[3])==text:break
                    lines[index]=line[:match.start(3)]+quote(text)[1:-1]+line[match.end(3):];break
            else:
                newline='\r\n' if '\r\n' in source else '\n'
                if lines and not lines[-1].endswith(('\n','\r')):lines[-1]+=newline
                lines.append(' '+key+':0 '+quote(text)+newline)
            self.docs.replace(path,''.join(lines))

    def edit_element(self,ident,name,color,immediate,delayed,create=False):
        if isinstance(ident,bool) or not isinstance(ident,int) or not 1<=ident<=MAX_ID:raise ValueError(f'Element ID must be a whole number from 1 to {MAX_ID}')
        records=self.elements()
        if create and ident in records:raise ValueError('That Imperium element ID already exists')
        if not create and ident not in records:raise ValueError('Choose an existing Imperium element')
        if not name.strip():raise ValueError('Enter an element name')
        rgb=self.catalogs.rgb(color.strip() if isinstance(color,str) else color)
        if any(not isinstance(c,int) or isinstance(c,bool) for c in rgb):raise ValueError('Element RGB channels must be whole byte values')
        if create and any(loc_key(ident,s) in self.characters.loc_records() for s in ('name','tooltip','tooltip_delayed')):raise ValueError('That element ID already has localization; choose an unused ID')
        with self.docs.grouped():
            self.bootstrap();text,section=self.color_section()
            targets=[n for n in section.children if n.key in {'if','else_if'} and ident in self.branch_ids(text,n)]
            if targets:
                node=targets[0];edits=[]
                for operation in node.children:
                    if operation.key!='set_temp_variable':continue
                    for c in operation.children or []:
                        if c.key in {'red','green','blue'}:
                            component=rgb[('red','green','blue').index(c.key)]
                            edits.append((c.value_start,c.end,format((Decimal(component)/255).quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'f')))
                for start,end,new in sorted(edits,reverse=True):text=text[:start]+new+text[end:]
            else:
                raw='\n\t\t\t\tif = {\n\t\t\t\t\tlimit = { FROM = { check_variable = { '+VARIABLE+f' = {ident}'+' } } }\n'
                raw+=''.join('\t\t\t\t\tset_temp_variable = { '+key+' = '+format((Decimal(component)/255).quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'f')+' }\n' for key,component in zip(('red','green','blue'),rgb))
                raw+='\t\t\t\t}\n\t\t\t';text=text[:section.end-1]+raw+text[section.end-1:]
            self.docs.replace(MAP_PATH,text)
            self._set_loc(loc_key(ident,'name'),name.strip());self._set_loc(loc_key(ident,'tooltip'),immediate);self._set_loc(loc_key(ident,'tooltip_delayed'),delayed)
            for function,suffix in zip(FUNCTIONS,('tooltip','tooltip_delayed')):
                text,roots=self.docs.parsed(TEXT_PATH)
                nodes=[n for n in roots if n.key=='defined_text' and scalar(text,n.children,'name')==function]
                if len(nodes)!=1:raise ValueError('Missing or duplicate native Imperium tooltip function')
                node=nodes[0];cases=[n for n in node.children if n.key=='text' and any(c.key==VARIABLE and value(text,c)==str(ident) for _,c in walk([n]) if c.children is None)]
                if not cases:
                    fallback=next((n for n in node.children if n.key=='text' and child(n.children,'trigger') is None),None)
                    if fallback is None:raise ValueError('Imperium tooltip needs an unassigned fallback')
                    raw='\ttext = {\n\t\ttrigger = { check_variable = { '+VARIABLE+f' = {ident}'+' } }\n\t\tlocalization_key = '+loc_key(ident,suffix)+'\n\t}\n\t'
                    self.docs.replace(TEXT_PATH,text[:fallback.start]+raw+text[fallback.start:])

    @staticmethod
    def value_nodes(history,text):
        for operation in history.children:
            if operation.key!='set_variable' or operation.children is None:continue
            for n in operation.children:
                if n.key==VARIABLE and n.children is None:yield n
            var=next((n for n in operation.children if n.key=='var' and n.children is None),None)
            val=next((n for n in operation.children if n.key=='value' and n.children is None),None)
            if var and val and value(text,var)==VARIABLE:yield val

    def state_assignments(self):
        signature=tuple(self.docs.text(s.path) for s in self.world.states.values())
        if signature==self._assignment_signature:return self._assignments
        result={}
        for sid,state in self.world.states.items():
            text,nodes=self.world.state_nodes(sid)
            for history in (n for n in nodes if n.key=='history' and n.children is not None):
                for n in self.value_nodes(history,text):
                    raw=value(text,n)
                    if not raw.isdigit() or int(raw)>MAX_ID:raise ValueError(f'State {sid} has an invalid Imperium element ID')
                    result[sid]=int(raw)
        self._assignment_signature=signature;self._assignments=result
        return result

    def paint_state(self,sid,ident):
        if sid not in self.world.states:raise ValueError('Choose a state')
        if not isinstance(ident,int) or isinstance(ident,bool) or not 0<=ident<=MAX_ID:raise ValueError('Choose a whole-number Imperium element ID')
        if ident!=0 and ident not in self.elements():raise ValueError('Choose a defined Imperium element or No element')
        path=self.world.states[sid].path;text,roots=self.docs.parsed(path);state=child(roots,'state')
        histories=[n for n in state.children if n.key=='history' and n.children is not None]
        owned=[n for history in histories for n in self.value_nodes(history,text)]
        if owned:
            updated=text
            for n in reversed(owned):updated=updated[:n.value_start]+str(ident)+updated[n.end:]
        elif not ident:return False
        elif histories:
            h=histories[-1];updated=text[:h.end-1]+'\n\t\tset_variable = { '+VARIABLE+f' = {ident}'+' }\n\t'+text[h.end-1:]
        else:updated=patch_field(text,state,'history','{\n\t\tset_variable = { '+VARIABLE+f' = {ident}'+' }\n\t}')
        if updated==text:return False
        self.docs.replace(path,updated);return True

    def validate_save(self):
        elements=self.elements()
        for sid,ident in self.state_assignments().items():
            if ident and ident not in elements:raise ValueError(f'State {sid} references undefined Imperium element {ident}')
        if elements:
            loc=self.characters.localisations();text,roots=self.docs.parsed(TEXT_PATH)
            for function,suffix in zip(FUNCTIONS,('tooltip','tooltip_delayed')):
                functions=[n for n in roots if n.key=='defined_text' and scalar(text,n.children,'name')==function]
                if len(functions)!=1:raise ValueError('Missing or duplicate Imperium tooltip function')
                for ident in elements:
                    cases=[n for n in functions[0].children if n.key=='text' and any(c.key==VARIABLE and value(text,c)==str(ident) for _,c in walk([n]) if c.children is None)]
                    if len(cases)!=1 or scalar(text,cases[0].children,'localization_key')!=loc_key(ident,suffix):raise ValueError('Imperium tooltip branch does not match its element')
                    if loc_key(ident,suffix) not in loc or loc_key(ident,'name') not in loc:raise ValueError('Imperium element localization is missing')

    def hover_text(self,sid):
        element=self.elements().get(self.state_assignments().get(sid,0));loc=self.characters.localisations()
        key=self.world.states[sid].name;name=loc.get(key,key)
        def expand(text):
            for _ in range(4):
                updated=re.sub(r'\$([A-Za-z0-9_.]+)\$',lambda m:loc.get(m[1],m[0]),text)
                if updated==text:break
                text=updated
            text=re.sub(r'\[(?:FROM|THIS)\.GetName\]',lambda m:name,text,flags=re.I)
            return re.sub('[\u00a7\x15].','',text)
        return (expand(element.immediate),expand(element.delayed)) if element else (name,'')
