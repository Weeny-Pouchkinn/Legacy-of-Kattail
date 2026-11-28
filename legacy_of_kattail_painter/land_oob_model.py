"""Native land OOB templates, province deployments and explicit division names."""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re

from character_model import atom,block,patch_field,quote,unescape
from diplomacy_model import DiplomacyStore
from model import parse,value,read_text

LAYER='Land OOB'
SHORT_MARKER='LOK_PAINTER_SHORT_NAME'
SHORT=re.compile(r'(?m)^\s*#[ \t]*'+SHORT_MARKER+r'[ \t]*=[ \t]*("(?:\\.|[^"\\])*")[ \t]*\r?$')
DATE=re.compile(r'^\d{4}\.\d{1,2}\.\d{1,2}$')


def string(text):return unescape(text[1:-1]) if len(text)>=2 and text[0]==text[-1]=='"' else text


def native_string(text,nodes,key,default=''):
    found=[n for n in nodes if n.key==key and n.children is None]
    return string(value(text,found[-1])) if found else default


def ordinal(number):
    return str(number)+('th' if 10<=number%100<=20 else {1:'st',2:'nd',3:'rd'}.get(number%10,'th'))


def grid_text(raw,key,cells):
    parent=parse(raw)[0];container=block(parent.children,key)
    if container is None:return patch_field(raw,parent,key,'{ '+' '.join(k+f' = {{ x = {x} y = {y} }}' for k,x,y in cells)+' }')
    desired={(x,y):kind for kind,x,y in cells};edits=[];present=set()
    for n in container.children or []:
        point=(int(atom(raw,n.children,'x')),int(atom(raw,n.children,'y')));present.add(point)
        if point not in desired:edits.append((n.start,n.end,''))
        elif desired[point]!=n.key:edits.append((n.start,n.start+len(n.key),desired[point]))
    added='\n'.join(k+f' = {{ x = {x} y = {y} }}' for k,x,y in cells if (x,y) not in present)
    if added:edits.append((container.end-1,container.end-1,'\n'+added+'\n'))
    for a,b,text in sorted(edits,reverse=True):raw=raw[:a]+text+raw[b:]
    return raw


@dataclass(frozen=True)
class OobSource:
    path:str
    history:str
    start:int
    end:int
    raw:str
    context:tuple=()


@dataclass(frozen=True)
class LandTemplate:
    name:str
    short:str
    regiments:tuple
    support:tuple
    path:str
    raw:str
    start:int
    end:int


@dataclass(frozen=True)
class LandDivision:
    index:int
    province:int
    template:str
    name:str
    path:str
    raw:str
    start:int
    end:int


class LandOobStore:
    def __init__(self,world,characters,diplomacy=None):
        self.world,self.characters,self.docs=world,characters,world.docs
        self.diplomacy=diplomacy or DiplomacyStore(world,characters)
        self._refs_signature=None;self._refs_revision=None;self._refs={};self._files={};self._unit_signature=None;self._units={}
        self._counts_signature=None;self._counts={};world.land_oob_store=self

    def references(self):
        revision=(self.docs.revision,tuple(self.world.countries.items()))
        if revision==self._refs_revision:return self._refs
        signature=tuple((tag,path,self.docs.text(path)) for tag,path in sorted(self.world.countries.items()))
        if signature==self._refs_signature:self._refs_revision=revision;return self._refs
        refs={}
        for tag,history,text in signature:
            rows=[]
            def visit(nodes,context=()):
                for n in nodes:
                    if n.key in {'oob','set_oob','load_oob'} and n.children is None:
                        name=string(value(text,n));path='history/units/'+name+'.txt'
                        self.docs._path(path)
                        if '/' in name or '\\' in name:raise ValueError('Land OOB references must be filenames: '+tag)
                        rows.append(OobSource(path,history,n.start,n.end,text[n.start:n.end],context))
                    elif n.children is not None and (n.key in {'if','else','else_if','hidden_effect'} or DATE.fullmatch(n.key)):
                        visit([c for c in n.children if c.key!='limit'],context+(n.key,))
            visit(parse(text));refs[tag]=rows
        self._refs,self._refs_signature,self._refs_revision=refs,signature,revision;return refs

    def sources(self,tag):return list(self.references().get(tag,()))

    def source(self,tag,path=''):
        rows=self.sources(tag)
        if path:
            found=next((r for r in rows if r.path==path and not r.context),None) or next((r for r in rows if r.path==path),None)
            if found is None:raise ValueError('Select an OOB loaded by this country')
            return found
        base=[r for r in rows if not r.context and not r.raw.startswith('load_oob')]
        return base[-1] if base else next((r for r in rows if not r.context),None)

    def _file(self,path):
        text=self.docs.text(path);cached=self._files.get(path)
        if cached is not None and cached[0]==text:return cached
        templates={};divisions=[]
        for n in parse(text):
            if n.key=='division_template' and n.children is not None:
                name=native_string(text,n.children,'name');raw=text[n.start:n.end]
                if name in templates:raise ValueError('Duplicate division template '+name+' in '+path)
                marker=SHORT.search(raw);short=string(marker[1]) if marker else name
                def cells(key):
                    container=block(n.children,key)
                    return tuple((c.key,int(atom(text,c.children,'x')),int(atom(text,c.children,'y'))) for c in container.children or []) if container else ()
                templates[name]=LandTemplate(name,short,cells('regiments'),cells('support'),path,raw,n.start,n.end)
            elif n.key=='units' and n.children is not None:
                for d in n.children:
                    if d.key!='division' or d.children is None:continue
                    location=atom(text,d.children,'location','0')
                    if not location.isdigit():raise ValueError('Non-numeric division location in '+path)
                    divisions.append(LandDivision(len(divisions),int(location),native_string(text,d.children,'division_template'),
                        native_string(text,d.children,'name'),path,text[d.start:d.end],d.start,d.end))
        cached=self._files[path]=(text,templates,tuple(divisions));return cached

    def templates(self,tag,path=''):
        source=self.source(tag,path)
        return dict(self._file(source.path)[1]) if source else {}

    def divisions(self,tag,path=''):
        source=self.source(tag,path)
        return list(self._file(source.path)[2]) if source else []

    def counts(self,tag='',template='',global_view=False,path=''):
        if path and not any(r.path==path for r in self.sources(tag)):path=''
        signature=(self.docs.revision,tuple(self.world.countries),tag,template,global_view,path)
        if signature==self._counts_signature:return self._counts
        out=Counter()
        for country in self.world.countries if global_view else [tag]:
            for division in self.divisions(country,'' if global_view else path):
                if global_view or not template or template=='__all__' or division.template==template:out[division.province]+=1
        self._counts_signature,self._counts=signature,dict(out);return self._counts

    def _private(self,tag,path=''):
        if tag not in self.world.country_paths:raise ValueError('Select a registered country')
        history=self.world.countries.get(tag)
        if not history:raise ValueError('Apply country setup before creating its land OOB')
        source=self.source(tag,path)
        if source and sum(any(r.path==source.path for r in rows) for rows in self.references().values())==1:return source.path
        base=tag+'_painter_land';name=base;index=2
        while self.docs.binary('history/units/'+name+'.txt') is not None:name=base+'_'+str(index);index+=1
        target='history/units/'+name+'.txt'
        self.docs.replace(target,self.docs.text(source.path) if source else '')
        text=self.docs.text(history)
        if source:
            if text[source.start:source.end]!=source.raw:raise ValueError('OOB reference changed; refresh before editing')
            old=parse(source.raw)[0];raw=source.raw[:old.value_start]+quote(name)
            text=text[:source.start]+raw+text[source.end:]
        else:text=text.rstrip()+'\noob = '+quote(name)+'\n'
        self.docs.replace(history,text);return target

    def subunits(self):
        paths=[p for p in self.characters.files('common/units','.txt') if Path(p).parent.as_posix()=='common/units']
        signature=(str(self.characters.game_root),self.docs.text('descriptor.mod'),tuple((p,self.docs.text(p)) for p in paths))
        if signature==self._unit_signature:return self._units
        descriptor=self.docs.text('descriptor.mod');replaced=[value(descriptor,n).strip('"').rstrip('/') for n in parse(descriptor) if n.key=='replace_path']
        sources={} if any('common/units'==p or 'common/units'.startswith(p+'/') for p in replaced) else {p.relative_to(self.characters.game_root).as_posix():read_text(p) for p in sorted((self.characters.game_root/'common/units').glob('*.txt'))}
        sources.update({p:self.docs.text(p) for p in paths});out={}
        # Nested unit-name databases have their own grammar and are not subunits.
        for path,text in sorted(sources.items()):
            try:roots=parse(text)
            except ValueError as exc:raise ValueError(path+': '+str(exc)) from exc
            for root in roots:
                if root.key!='sub_units':continue
                for n in root.children or []:
                    if n.children is None:continue
                    group=atom(text,n.children,'group');category=block(n.children,'categories')
                    categories={c.key for c in category.children or []} if category else set()
                    icon=atom(text,n.children,'map_icon_category')
                    if 'category_army' in categories or group=='support' or icon in {'infantry','armored','other'}:
                        out[n.key]={'group':group,'support':group=='support'}
        self._units,self._unit_signature=out,signature;return out

    def dimensions(self):
        result={'MAX_DIVISION_BRIGADE_WIDTH':5,'MAX_DIVISION_BRIGADE_HEIGHT':5,'MAX_DIVISION_SUPPORT_WIDTH':1,'MAX_DIVISION_SUPPORT_HEIGHT':5}
        for folder in (self.characters.game_root/'common/defines',self.world.root/'common/defines'):
            for p in sorted(folder.glob('*.lua')):
                text='\n'.join(line.split('--',1)[0] for line in read_text(p).splitlines())
                for key,raw in re.findall(r'\b('+'|'.join(result)+r')\s*=\s*(\d+)',text):result[key]=int(raw)
        return (result['MAX_DIVISION_BRIGADE_WIDTH'],result['MAX_DIVISION_BRIGADE_HEIGHT'],result['MAX_DIVISION_SUPPORT_WIDTH'],result['MAX_DIVISION_SUPPORT_HEIGHT'])

    def _validate_cells(self,regiments,support,previous=None):
        if not regiments:raise ValueError('A land template needs at least one combat battalion')
        defs=self.subunits();cw,ch,sw,sh=self.dimensions()
        for cells,is_support,width,height in [(regiments,False,cw,ch),(support,True,sw,sh)]:
            seen=set();groups={}
            for key,x,y in cells:
                if not isinstance(x,int) or not isinstance(y,int) or not (0<=x<width and 0<=y<height):raise ValueError('Battalion coordinates are outside the division designer grid')
                if (x,y) in seen:raise ValueError('Two battalions occupy the same grid cell')
                seen.add((x,y))
                if key not in defs:
                    if previous and (key,x,y) in (previous.support if is_support else previous.regiments):continue
                    raise ValueError('Choose a defined land subunit: '+key)
                row=defs[key]
                if row['support']!=is_support:raise ValueError('Combat battalions and support companies use different sections')
                if is_support and sum(c[0]==key for c in cells)>1:raise ValueError('A support company type can only appear once')
                if not is_support:
                    if x in groups and groups[x]!=row['group']:raise ValueError('Each combat column must use one battalion group')
                    groups[x]=row['group']

    def edit_template(self,tag,name,short,regiments,support,old_name=None,path='',raw_override=None):
        if not name.strip() or not short.strip():raise ValueError('Enter the template name and shortened name')
        old=self.templates(tag,path).get(old_name) if old_name else None
        if old_name and old is None:raise ValueError('Choose an existing template')
        if name!=old_name and name in self.templates(tag,path):raise ValueError('This country already has a template with that name')
        self._validate_cells(regiments,support,old)
        with self.docs.grouped():
            target=self._private(tag,path);text,templates,divisions=self._file(target)
            current=templates.get(old_name) if old_name else None
            raw=current.raw if current else raw_override or 'division_template = { }'
            raw=patch_field(raw,parse(raw)[0],'name',quote(name))
            raw=grid_text(raw,'regiments',regiments);raw=grid_text(raw,'support',support)
            marker=SHORT.search(raw)
            comment='# '+SHORT_MARKER+' = '+quote(short)
            if marker:raw=raw[:marker.start()]+ '\n\t'+comment+raw[marker.end():]
            else:
                at=raw.index('{')+1;raw=raw[:at]+'\n\t'+comment+'\n'+raw[at:]
            if current:
                edits=[(current.start,current.end,raw)]
                if name!=old_name:
                    for division in divisions:
                        if division.template==old_name:
                            updated=patch_field(division.raw,parse(division.raw)[0],'division_template',quote(name));edits.append((division.start,division.end,updated))
                for a,b,replacement in sorted(edits,reverse=True):text=text[:a]+replacement+text[b:]
            else:
                at=next((n.start for n in parse(text) if n.key=='units'),len(text));text=text[:at]+raw+'\n'+text[at:]
            self.docs.replace(target,text)
        return name

    def copy_template(self,source_tag,name,target_tag,new_name=None,short=None,source_path='',target_path=''):
        template=self.templates(source_tag,source_path).get(name)
        if template is None:raise ValueError('Choose a source template')
        return self.edit_template(target_tag,new_name or name,short or template.short,template.regiments,template.support,path=target_path,raw_override=template.raw)

    def _generated(self,tag,template,province,number):
        sid=self.world.province_states[province];state=self.world.states[sid]
        label=self.characters.localisations().get(state.name,state.name)
        label=re.sub('[\x15§].','',label).replace('\n',' ')
        return f'{ordinal(number)} {label} {template.short}'

    def place(self,tag,template,province,amount=1,path=''):
        if not isinstance(amount,int) or isinstance(amount,bool) or not 1<=amount<=1000:raise ValueError('Choose 1 to 1000 divisions per click')
        if province not in self.world.province_states or self.world.provinces[province]['type']!='land':raise ValueError('Divisions must be placed in an assigned land province')
        selected=self.templates(tag,path).get(template)
        if selected is None:raise ValueError('Select a template to place')
        existing=[d for d in self.divisions(tag,path) if d.template==template]
        numbers=[int(m[1]) for d in existing for m in [re.match(r'^(\d+)(?:st|nd|rd|th|[. ])',d.name)] if m]
        number=max([len(existing),*numbers],default=0)+1
        names=[self._generated(tag,selected,province,n) for n in range(number,number+amount)]
        with self.docs.grouped():
            target=self._private(tag,path);text=self.docs.text(target);container=block(parse(text),'units')
            raw='\n'.join('division = { name = '+quote(name)+' location = '+str(province)+' division_template = '+quote(template)+' }' for name in names)
            if container:text=text[:container.end-1]+'\n'+raw+'\n'+text[container.end-1:]
            else:text=text.rstrip()+'\nunits = {\n'+raw+'\n}\n'
            self.docs.replace(target,text)
        return names

    def remove(self,tag,province,template='',amount=1,path=''):
        if not isinstance(amount,int) or isinstance(amount,bool) or not 1<=amount<=1000:raise ValueError('Choose 1 to 1000 divisions per click')
        matches=[d for d in self.divisions(tag,path) if d.province==province and (not template or template=='__all__' or d.template==template)]
        if not matches:return 0
        with self.docs.grouped():
            target=self._private(tag,path);text=self.docs.text(target)
            for d in reversed(matches[-amount:]):text=text[:d.start]+text[d.end:]
            self.docs.replace(target,text)
        return min(amount,len(matches))

    def delete_division(self,tag,index,path=''):
        divisions=self.divisions(tag,path)
        if not 0<=index<len(divisions):raise ValueError('Refresh the division list before deleting')
        row=divisions[index]
        with self.docs.grouped():
            target=self._private(tag,path);text=self.docs.text(target)
            self.docs.replace(target,text[:row.start]+text[row.end:])

    def rename(self,tag,index,name,path='',generated=False):
        divisions=self.divisions(tag,path)
        if not 0<=index<len(divisions):raise ValueError('Refresh the division list before editing')
        row=divisions[index]
        if generated:
            template=self.templates(tag,path).get(row.template)
            if template is None:raise ValueError('This division references an undefined template')
            if row.province not in self.world.province_states:raise ValueError('Division location is not in a state')
            number=1+sum(d.template==row.template for d in divisions[:index]);name=self._generated(tag,template,row.province,number)
        if not name.strip():raise ValueError('Enter a division name or use Generate name')
        with self.docs.grouped():
            target=self._private(tag,path);text=self.docs.text(target);raw=row.raw
            for node in reversed([n for n in parse(raw)[0].children if n.key=='division_name']):raw=raw[:node.start]+raw[node.end:]
            raw=patch_field(raw,parse(raw)[0],'name',quote(name));self.docs.replace(target,text[:row.start]+raw+text[row.end:])
        return name

    def validate_save(self):
        loaded={r.path for rows in self.references().values() for r in rows}
        for path in self.docs.changed:
            if not path.startswith('history/units/') or path not in loaded:continue
            text,templates,divisions=self._file(path)
            original=self.docs.snapshots.get(path);before=self.docs._decode(original) if original else ''
            old_locations={int(m[1]) for m in re.finditer(r'\blocation\s*=\s*(\d+)',before)}
            for d in divisions:
                if d.template not in templates:raise ValueError(f'{path}: undefined land template {d.template}')
                if d.province not in old_locations and (self.world.provinces.get(d.province,{}).get('type')!='land' or d.province not in self.world.province_states):raise ValueError(f'{path}: division placement must be assigned land')
