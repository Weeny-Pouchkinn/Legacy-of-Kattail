"""Native state, strategic-region/weather and province victory-point authoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, DecimalException
from decimal import ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
import math
import re
import random

import numpy as np
from PIL import ImageColor

from model import child, parse, scalar, value, walk, read_text
from character_model import atom, block, patch_field, quote, LOC, unescape, sort_name
from select_ui import Choice

STATE_LOC='localisation/english/state_names_l_english.yml'
REGION_LOC='localisation/english/strategic_region_names_l_english.yml'
VP_LOC='localisation/english/victory_points_l_english.yml'
CATEGORY_LOC='localisation/english/lok_misc_l_english.yml'
RESOURCE_COLORS={'steel':(135,206,250),'aluminium':(255,255,255),'aluminum':(255,255,255),'tungsten':(128,128,128),'food':(245,210,45),'fissiles':(55,185,80),'rubber':(205,205,205),'oil':(65,65,65),'supertensiles':(30,60,155),'chromium':(115,140,165)}
# Beck et al. legend, also published in Hylke Beck's KoppenGeiger.m class table.
KOPPEN_COLORS=dict(zip(('Af','Am','Aw','BWh','BWk','BSh','BSk','Csa','Csb','Csc','Cwa','Cwb','Cwc','Cfa','Cfb','Cfc','Dsa','Dsb','Dsc','Dsd','Dwa','Dwb','Dwc','Dwd','Dfa','Dfb','Dfc','Dfd','ET','EF'),
    ((0,0,255),(0,120,255),(70,170,250),(255,0,0),(255,150,150),(245,165,0),(255,220,100),(255,255,0),(200,200,0),(150,150,0),(150,255,150),(100,200,100),(50,150,50),(200,255,80),(100,255,80),(50,200,0),(255,0,255),(200,0,200),(150,50,150),(150,100,150),(170,175,255),(90,120,220),(75,80,180),(50,0,135),(0,255,255),(55,200,255),(0,125,125),(0,70,95),(178,178,178),(102,102,102))))
MONTH_DAYS=(31,28,31,30,31,30,31,31,30,31,30,31)
WEATHER_FIELDS=('no_phenomenon','rain_light','rain_heavy','snow','blizzard','arctic_water','mud','sandstorm','min_snow_level')
KOPPEN_SOURCE='https://doi.org/10.1038/s41597-023-02549-6'  # Classification reference; weights below are editor approximations.
CLIMATES={'Af':'Tropical rainforest','Am':'Tropical monsoon','Aw':'Tropical savanna (dry winter)',
          'BWh':'Hot desert','BWk':'Cold desert','BSh':'Hot steppe','BSk':'Cold steppe',
          'Csa':'Hot-summer Mediterranean','Csb':'Warm-summer Mediterranean','Csc':'Cool-summer Mediterranean',
          'Cwa':'Dry-winter humid subtropical','Cwb':'Dry-winter subtropical highland','Cwc':'Dry-winter cool highland',
          'Cfa':'Humid subtropical','Cfb':'Oceanic','Cfc':'Subpolar oceanic',
          **{'D'+season+heat:dry+' '+temp for season,dry in [('s','Dry-summer'),('w','Dry-winter'),('f','Year-round precipitation')]
             for heat,temp in [('a','hot-summer continental'),('b','warm-summer continental'),('c','subarctic'),('d','extreme-winter subarctic')]},
          'ET':'Tundra','EF':'Ice cap'}


def numeric(raw,minimum=None,integer=False):
    try:n=Decimal(str(raw))
    except InvalidOperation:raise ValueError('Enter a numeric value') from None
    if not n.is_finite() or minimum is not None and n<minimum:raise ValueError('Enter a finite value'+(f' of at least {minimum}' if minimum is not None else ''))
    if integer and n!=n.to_integral_value():raise ValueError('Enter a whole number')
    return str(int(n)) if integer else format(n,'f')


def arithmetic_operand(amount,precision=0,rng=None):
    """Uniform integer operand inside the inclusive +/- percentage interval."""
    base=Decimal(numeric(amount,0,True));percent=Decimal(numeric(precision,0))
    if not percent:return int(base)
    try:
        spread=base*percent/100
        low=int(max(Decimal(0),base-spread).to_integral_value(rounding=ROUND_CEILING))
        high=int((base+spread).to_integral_value(rounding=ROUND_FLOOR))
        return (rng or random).randint(low,high)
    except DecimalException:raise ValueError('Amount or precision range is too large') from None


def arithmetic_amount(old,amount,operation='Set',reverse=False,integer=False):
    value=Decimal(numeric(amount,0));old=Decimal(numeric(old,0))
    try:
        if operation=='Set':new=value
        elif operation=='Add':new=max(Decimal(0),old-value if reverse else old+value)
        elif operation=='Multiply':
            if reverse and not value:raise ValueError('Cannot divide by zero; amount unchanged')
            new=old/value if reverse else old*value
        else:raise ValueError('Choose Add or Multiply')
        return new.quantize(Decimal(1) if integer else Decimal('.000001'),rounding=ROUND_HALF_UP)
    except DecimalException:raise ValueError('Amount is too large or too precise') from None


def patch_unique(text,parent,key,raw):
    """Target a direct field, preserving other scopes and unowned text."""
    nodes=[n for n in parent.children if n.key==key]
    if not nodes:return patch_field(text,parent,key,raw) if raw is not None else text
    for n in reversed(nodes):
        replacement=key+' = '+raw if n is nodes[-1] and raw is not None else ''
        text=text[:n.start]+replacement+text[n.end:]
    return text


def calendar_date(raw):
    m=re.fullmatch(r'(\d+)\.(\d+)',str(raw))
    if not m:raise ValueError('Weather dates use zero-based day.month, for example 0.0')
    day,month=map(int,m.groups())
    if not 0<=month<12 or not 0<=day<MONTH_DAYS[month]:raise ValueError('Weather day/month is outside the game calendar')
    return day,month


@dataclass
class WeatherPeriod:
    start:str
    end:str
    low:str
    high:str
    weights:dict=field(default_factory=dict)
    raw:str=''

    def validate(self):
        calendar_date(self.start);calendar_date(self.end)
        if Decimal(numeric(self.low))>Decimal(numeric(self.high)):raise ValueError('Minimum temperature must not exceed maximum temperature')
        for raw in self.weights.values():numeric(raw,0)
        return self

    def script(self):
        self.validate();text=self.raw or 'period = { }'
        fields={'between':'{ '+self.start+' '+self.end+' }','temperature':'{ '+numeric(self.low)+' '+numeric(self.high)+' }',**{k:numeric(v,0) for k,v in self.weights.items()}}
        for k,v in fields.items():text=patch_unique(text,parse(text)[0],k,v)
        return text


def weather_periods(text,node):
    out=[]
    for n in node.children if node else []:
        if n.key!='period' or n.children is None:continue
        between=block(n.children,'between');temp=block(n.children,'temperature')
        if between is None or temp is None or len(between.children)!=2 or len(temp.children)!=2:raise ValueError('Malformed native weather period')
        out.append(WeatherPeriod(*(c.key for c in between.children),*(c.key for c in temp.children),
                                 {c.key:value(text,c) for c in n.children if c.children is None},text[n.start:n.end]))
    return out


LATITUDE_TRANSITION=10.0  # Editor approximation; preserve preset contrast beyond this latitude.


@dataclass(frozen=True)
class PlanetFrame:
    top:float
    bottom:float

    @property
    def equator(self):return (self.top+self.bottom)/2

    @classmethod
    def main_world(cls,width,height):
        # The original 2:1 planet is bottom-aligned; the solar chart was added
        # above it. EU4 JUBLIO_SYSTEM_README.md:3-6 records 4096x2048 -> 4096x3072.
        if width<=0 or height<width/2:raise ValueError('Map cannot contain the bottom-aligned 2:1 main planet')
        return cls(height-width/2,height)

    def latitude(self,y):
        if not self.top<=y<=self.bottom:raise ValueError('Position is outside the main planet')
        return 180*(self.equator-y)/(self.bottom-self.top)


def climate_preset(code,hemisphere='North',latitude=None):
    """Köppen-inspired game profiles, not observational data or a classification algorithm."""
    if code not in CLIMATES or hemisphere not in {'North','South'}:raise ValueError('Choose a climate and hemisphere')
    if latitude is not None:
        latitude=float(numeric(latitude))
        if not -90<=latitude<=90:raise ValueError('Latitude must be between -90 and 90 degrees')
        hemisphere='North' if latitude>=0 else 'South'
    if code=='Af':cold,hot=26,28
    elif code=='Am':cold,hot=24,29
    elif code=='Aw':cold,hot=22,30
    elif code in {'BWh','BSh'}:cold,hot=(16,38) if code=='BWh' else (14,34)
    elif code in {'BWk','BSk'}:cold,hot=(-6,27) if code=='BWk' else (-8,26)
    elif code.startswith('C'):cold,hot={'a':(8,27),'b':(6,20),'c':(2,13)}[code[-1]]
    elif code.startswith('D'):cold,hot={'a':(-15,25),'b':(-18,20),'c':(-25,16),'d':(-45,15)}[code[-1]]
    elif code=='ET':cold,hot=-26,6
    else:cold,hot=-50,-10
    out=[]
    for month in range(12):
        season=(month+(6 if hemisphere=='South' else 0))%12
        summer=(1-math.cos(2*math.pi*season/12))/2
        mean=cold+(hot-cold)*summer
        if code.startswith('C') and code.endswith('c'):mean=[2,2,4,6,8,10,13,12,9,6,4,2][season]
        if latitude is not None and abs(latitude)<LATITUDE_TRANSITION:
            t=abs(latitude)/LATITUDE_TRANSITION;strength=t*t*(3-2*t)
            opposite=(season+6)%12
            other=[2,2,4,6,8,10,13,12,9,6,4,2][opposite] if code.startswith('C') and code.endswith('c') else cold+(hot-cold)*(1-math.cos(2*math.pi*opposite/12))/2
            # Suppress only the north/south annual component, retaining the
            # annual mean and any semiannual structure. Rainfall is class-led.
            mean=(mean+other)/2+strength*(mean-other)/2
        wet=.3
        if code=='Af':wet=.65
        elif code=='Am':wet=.12+.68*summer
        elif code=='Aw':wet=.04+.5*summer
        elif code.startswith('BW'):wet=.025
        elif code.startswith('BS'):wet=.13
        elif code[0] in 'CD' and code[1]=='s':wet=.05+.4*(1-summer)
        elif code[0] in 'CD' and code[1]=='w':wet=.025+.5*summer
        elif code.startswith('E'):wet=.15
        frozen=max(0,min(1,(3-mean)/15));snow=wet*frozen;rain=wet-snow
        weights={'no_phenomenon':max(.15,1-wet),'rain_light':rain*.75,'rain_heavy':rain*.25,
                 'snow':snow*.85,'blizzard':snow*.15,'arctic_water':frozen*.8 if code.startswith('E') else frozen*.35,
                 'mud':rain*.7,'sandstorm':.18 if code.startswith('BW') else .07 if code.startswith('BS') else 0,
                 'min_snow_level':.1*frozen}
        out.append(WeatherPeriod(f'0.{month}',f'{MONTH_DAYS[month]-1}.{month}',f'{mean-6:.1f}',f'{mean+6:.1f}',{k:f'{v:.3f}' for k,v in weights.items()}))
    return out


def vp_color(amount,maximum):
    if not amount:return (60,65,73)
    t=max(0,min(1,float(amount)/max(1,float(maximum))))
    return tuple(round(a+(b-a)*t) for a,b in zip((55,125,225),(250,65,40)))


def building_color(amount,maximum):
    if not amount:return (55,60,68)
    t=max(0,min(1,float(amount)/max(1,float(maximum))))
    return tuple(round(a+(b-a)*t) for a,b in zip((190,225,255),(25,80,205)))


class GeographyStore:
    def __init__(self,world,characters,catalogs):
        self.world,self.characters,self.catalogs,self.docs=world,characters,catalogs,world.docs
        self._cache={};self._region_signature=None
        self._world_revision=-1;self._terrain_signature=None
        world.geography_store=self

    def cached(self,key,signature,build):
        old=self._cache.get(key)
        if old is None or old[0]!=signature:old=self._cache[key]=(signature,build())
        return old[1]

    def definitions(self,folder,container):
        files=self.characters.files(folder,'.txt');signature=tuple(self.docs.text(p) for p in files)
        def build():
            out={}
            for path in files:
                text,roots=self.docs.parsed(path)
                for root in roots:
                    if root.key==container and root.children:
                        for n in root.children:
                            if n.children is not None:out[n.key]=(text,n)
            return out
        return self.cached((folder,container),signature,build)

    def choices(self,kind):
        loc=self.characters.trait_store.names()
        if kind=='categories':data=self.definitions('common/state_category','state_categories')
        elif kind=='resources':data=self.definitions('common/resources','resources')
        elif kind=='terrain':data={k:r for k,r in self.definitions('common/terrain','categories').items() if atom(r[0],r[1].children,'naval_terrain')=='yes'}
        else:data=self.buildings()
        return [Choice(k,loc.get('PRODUCTION_MATERIALS_'+k.upper(),loc.get(k,k.replace('_',' ').title()))) for k in data]

    def terrain_catalog(self):
        names=self.characters.trait_store.names();out={}
        for key,(text,node) in self.definitions('common/terrain','categories').items():
            color=block(node.children,'color')
            out[key]={'name':names.get(key,key.replace('_',' ').title()),
                      'color':self.world._script_colour(text,color) if color else (128,128,128),
                      'water':atom(text,node.children,'is_water')=='yes' or atom(text,node.children,'naval_terrain')=='yes'}
        return out

    def province_terrain(self):
        text=self.docs.text('map/definition.csv')
        def build():
            out={}
            for line in text.splitlines():
                fields=line.split(';')
                if len(fields)>=8 and fields[0].isdigit():
                    pid=int(fields[0])
                    if pid in out:raise ValueError('Duplicate province definition')
                    out[pid]=fields[6]
            return out
        return self.cached('province_terrain',text,build)

    def sync_terrain(self):
        text=self.docs.text('map/definition.csv')
        if text is self._terrain_signature:return
        for pid,kind in self.province_terrain().items():
            if pid in self.world.provinces:self.world.provinces[pid]['terrain']=kind
        self.world._map_palettes.pop('Terrain',None);self._terrain_signature=text

    def set_province_terrain(self,pid,kind):
        if pid not in self.world.province_states or self.world.provinces[pid]['type']!='land':raise ValueError('Choose a land province; naval terrain is edited in strategic regions')
        catalog=self.terrain_catalog()
        if kind not in catalog or catalog[kind]['water']:raise ValueError('Choose a defined land terrain')
        path='map/definition.csv';text=self.docs.text(path);lines=text.splitlines(keepends=True);found=[]
        for i,line in enumerate(lines):
            fields=line.split(';')
            if len(fields)>=8 and fields[0].isdigit() and int(fields[0])==pid:found.append((i,fields))
        if len(found)!=1:raise ValueError('Province must have exactly one definition')
        i,fields=found[0]
        if fields[6]==kind:return False
        fields[6]=kind;lines[i]=';'.join(fields);self.docs.replace(path,''.join(lines));self.sync_terrain()
        return True

    def buildings(self):
        definitions=self.definitions('common/buildings','buildings');out={}
        for key,(text,n) in definitions.items():
            cap=block(n.children,'level_cap');caps={c.key:value(text,c) for c in cap.children if c.children is None} if cap else {}
            out[key]={'province':'province_max' in caps,'shared':caps.get('shares_slots')=='yes','coastal':atom(text,n.children,'only_costal')=='yes',
                      'state_max':int(caps['state_max']) if caps.get('state_max','').isdigit() else None,
                      'province_max':int(caps['province_max']) if caps.get('province_max','').isdigit() else None,
                      'group':caps.get('group_by',''),'exclusive':caps.get('exclusive_with',''),
                      'spawn':atom(text,n.children,'spawn_point',key),'network':key=='rail_way','supply':key=='supply_node'}
        return out

    def categories(self):
        files=self.characters.files('common/state_category','.txt');signature=tuple(self.docs.text(p) for p in files)
        def build():
            names=self.characters.trait_store.names();out={}
            for path in files:
                text,roots=self.docs.parsed(path)
                for root in roots:
                    if root.key!='state_categories' or root.children is None:continue
                    for n in root.children:
                        if n.children is None:continue
                        if n.key in out:raise ValueError('Duplicate state category: '+n.key)
                        color=block(n.children,'color');extra=text[n.value_start+1:n.end-1]
                        for owned in reversed([c for c in n.children if c.key in {'color','local_building_slots'}]):
                            a,b=owned.start-n.value_start-1,owned.end-n.value_start-1;extra=extra[:a]+extra[b:]
                        out[n.key]={'key':n.key,'path':path,'name':names.get(n.key,n.key.replace('_',' ').title()),'slots':int(numeric(atom(text,n.children,'local_building_slots','0'),0,True)),
                                    'color':self.world._script_colour(text,color) if color else (128,128,128),'extra':extra,
                                    'factor':numeric(atom(text,n.children,'local_building_slots_factor','0'))}
            return out
        # Localization may change without a definition change.
        return self.cached('categories',(signature,id(self.characters.trait_store.names())),build)

    def edit_category(self,key,name,slots,color,path=None,extra=None,create=False):
        if not re.fullmatch('[a-z][a-z0-9_]*',key):raise ValueError('Use a lowercase category ID with underscores')
        existing=self.categories()
        if create==(key in existing):raise ValueError('Choose an unused category ID' if create else 'Choose an existing category')
        if not name.strip():raise ValueError('Enter a category name')
        if create and key in self.characters.localisations() and self.characters.localisations()[key]!=name:raise ValueError('This localization key is already used; choose a unique category ID')
        slots=numeric(slots,0,True);rgb=ImageColor.getrgb(color.strip())
        if len(rgb)!=3:raise ValueError('Choose an RGB category color')
        path=path if create else existing[key]['path']
        if path not in self.characters.files('common/state_category','.txt'):raise ValueError('Choose an existing native category file')
        if extra is not None and any(n.key in {'color','local_building_slots'} for n in parse(extra)):raise ValueError('Set color and slots in their dedicated fields')
        with self.docs.grouped():
            text,roots=self.docs.parsed(path);root=block(roots,'state_categories')
            if root is None:raise ValueError('Missing state_categories container')
            if create:
                text=patch_field(text,root,key,'{ }')
            root=block(parse(text),'state_categories');node=block(root.children,key)
            if extra is not None and (create or extra!=existing[key]['extra']):
                raw=key+' = {\n'+extra+'\n}'
                text=text[:node.start]+raw+text[node.end:]
            for field,raw in [('local_building_slots',slots),('color','{ '+' '.join(map(str,rgb))+' }')]:
                node=block(block(parse(text),'state_categories').children,key);text=patch_unique(text,node,field,raw)
            self.docs.replace(path,text)
            if create or name!=existing[key]['name']:self.set_loc(CATEGORY_LOC,key,name)

    def set_category(self,sid,key):
        if key not in self.categories():raise ValueError('Choose a defined state category')
        path=self.world.states[sid].path;text=self.docs.text(path)
        self.docs.replace(path,patch_unique(text,block(parse(text),'state'),'state_category',key))

    def max_shared_slots(self):
        def build():
            maximum=25
            for folder in [self.characters.game_root/'common/defines',self.world.root/'common/defines']:
                for path in sorted(folder.glob('*.lua')):
                    source='\n'.join(line.split('--',1)[0] for line in read_text(path).splitlines())
                    for m in re.finditer(r'\bMAX_SHARED_SLOTS\s*=\s*(\d+)\s*(?:[,;]|$)',source,re.M):maximum=int(m[1])
            return maximum
        return self.cached('max_slots',str(self.characters.game_root),build)

    def slot_summary(self):
        categories=self.categories();defs=self.buildings();shared={k for k,d in defs.items() if d['shared'] and not d['province']}
        signature=(tuple(self.docs.text(s.path) for s in self.world.states.values()),tuple((k,d['slots'],d['factor']) for k,d in categories.items()),tuple(sorted(shared)),self.max_shared_slots())
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);history=block(nodes,'history');key=atom(text,nodes,'state_category');cat=categories.get(key,{'slots':0,'factor':'0'});levels={}
                for container in history.children if history else []:
                    if container.key=='buildings' and container.children is not None:
                        for n in container.children:
                            if n.key in shared and n.children is None:levels[n.key]=int(numeric(value(text,n),0,True))
                extra=sum(Decimal(numeric(value(text,n))) for n in history.children if n.key=='add_extra_state_shared_building_slots' and n.children is None) if history else Decimal(0)
                factor=Decimal(numeric(atom(text,nodes,'buildings_max_level_factor','1'),0))
                capacity=max(0,min(self.max_shared_slots(),int(Decimal(cat['slots'])*factor*(1+Decimal(cat['factor']))+extra)))
                used=sum(levels.values());out[sid]={'category':key,'used':used,'total':capacity,'status':'over' if used>capacity else 'full' if used==capacity else 'free'}
            return out
        return self.cached('slots',signature,build)

    def resource_counts(self,kind):
        signature=tuple(self.docs.text(s.path) for s in self.world.states.values())
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);resources=block(nodes,'resources')
                if resources:
                    raw=atom(text,resources.children,kind,'0');amount=Decimal(numeric(raw,0))
                    if amount:out[sid]=amount
            return out
        return self.cached(('resource',kind),signature,build)

    def resource_type_counts(self):
        signature=tuple(self.docs.text(s.path) for s in self.world.states.values())
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);resources=block(nodes,'resources');types={}
                for n in resources.children if resources else []:
                    if n.children is None:types[n.key]=Decimal(numeric(value(text,n),0))
                out[sid]=sum(v>0 for v in types.values())
            return out
        return self.cached('resource_types',signature,build)

    def change_resource(self,sid,kind,amount,operation='Set',reverse=False):
        if kind not in self.definitions('common/resources','resources'):raise ValueError('Choose a defined resource')
        new=arithmetic_amount(self.resource_counts(kind).get(sid,0),amount,operation,reverse,integer=operation!='Set')
        raw=format(new.normalize(),'f');path=self.world.states[sid].path;text=self.docs.text(path);root=block(parse(text),'state');resources=block(root.children,'resources')
        if not resources and not new:return raw
        if resources is None:text=patch_field(text,root,'resources','{ }')
        resources=block(block(parse(text),'state').children,'resources');text=patch_unique(text,resources,kind,raw if new else None)
        self.docs.replace(path,text);return raw

    def population_counts(self):
        signature=tuple(self.docs.text(s.path) for s in self.world.states.values())
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);amount=int(numeric(atom(text,nodes,'manpower','0'),0,True))
                if amount:out[sid]=amount
            return out
        return self.cached('population',signature,build)

    def change_population(self,sid,amount,operation='Set',reverse=False):
        if operation=='Set':numeric(amount,0,True)
        new=arithmetic_amount(self.population_counts().get(sid,0),amount,operation,reverse,True);raw=format(new,'f')
        path=self.world.states[sid].path;text=self.docs.text(path)
        self.docs.replace(path,patch_unique(text,block(parse(text),'state'),'manpower',raw));return raw

    def building_choices(self,scope):
        definitions=self.buildings()
        return [c for c in self.choices('buildings') if definitions[c.code]['province']==(scope=='Province') and not definitions[c.code]['network']]

    def building_counts(self,kind,scope='State'):
        paths=[s.path for s in self.world.states.values()]
        signature=tuple(self.docs.text(p) for p in paths)
        if scope=='Province' and kind=='supply_node':return {p:v for p,v in self.supply_nodes().items() if v>0}
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);history=block(nodes,'history')
                for container in history.children if history else []:
                    if container.key!='buildings' or container.children is None:continue
                    scopes=[(sid,container)] if scope=='State' else [(int(n.key),n) for n in container.children if n.key.isdigit() and n.children is not None]
                    for ident,node in scopes:
                        for n in node.children:
                            if n.key==kind and n.children is None:out[ident]=int(numeric(value(text,n),0,True))
            return {ident:level for ident,level in out.items() if level>0}
        return self.cached(('building_counts',kind,scope),signature,build)

    def change_building(self,ident,kind,scope,delta):
        delta=int(numeric(delta,integer=True))
        return self.change_building_amount(ident,kind,scope,abs(delta),'Add',delta<0)

    def change_building_amount(self,ident,kind,scope,amount,operation='Add',reverse=False):
        definitions=self.buildings()
        if scope not in {'State','Province'} or kind not in definitions or definitions[kind]['province']!=(scope=='Province') or definitions[kind]['network']:raise ValueError('Choose a building for this scope')
        sid=ident if scope=='State' else self.world.province_states.get(ident)
        if sid not in self.world.states:raise ValueError('Choose a province belonging to a state')
        old=self.state(sid);key=(None if scope=='State' else ident,kind);level=int(numeric(old['buildings'].get(key,'0'),0,True))
        new=int(arithmetic_amount(level,numeric(amount,0,True),operation,reverse,True))
        if new==level:return new
        levels=dict(old['buildings'])
        if new:levels[key]=str(new)
        else:levels.pop(key,None)
        self.edit_state(sid,old['name'],{},old['resources'],levels)
        return new

    def assign_state(self,sid,rid):
        if all(self.world.province_regions.get(p)==rid for p in self.world.states[sid].provinces):return False
        region=self.region(rid);self.edit_region(rid,region['name'],region['terrain'],region['weather'],{sid:rid});return True

    def set_loc(self,preferred,key,name):
        owners=list(dict.fromkeys(r[0] for r in self.characters.loc_records().get(key,()))) or [preferred]
        for path in owners:self.catalogs.set_loc(path,key,name)

    def state(self,sid):
        text,nodes=self.world.state_nodes(sid);history=block(nodes,'history')
        root={n.key:value(text,n) for n in nodes if n.children is None and n.key not in {'id','name'}}
        resources=block(nodes,'resources');res={n.key:value(text,n) for n in resources.children if n.children is None} if resources else {}
        buildings={}
        for container in history.children if history else []:
            if container.key!='buildings' or container.children is None:continue
            for n in container.children:
                if n.children is None:buildings[(None,n.key)]=value(text,n)
                elif n.key.isdigit():
                    for c in n.children:
                        if c.children is None:buildings[(int(n.key),c.key)]=value(text,c)
        for pid,level in self.supply_nodes().items():
            if pid in self.world.states[sid].provinces:buildings[(pid,'supply_node')]=str(level)
        def memberships(add,remove):
            out=set()
            for n in history.children if history else []:
                if n.key==add:out.add(value(text,n))
                elif n.key==remove:out.discard(value(text,n))
            return out
        key=atom(text,nodes,'name',f'STATE_{sid}')
        return {'id':sid,'name_key':key,'name':self.characters.localisations().get(key,key),'attributes':root,'resources':res,'buildings':buildings,
                'owner':atom(text,history.children,'owner') if history else '', 'controller':atom(text,history.children,'controller') if history else '',
                'cores':memberships('add_core_of','remove_core_of'),'claims':memberships('add_claim_by','remove_claim_by')}

    def supply_nodes(self):
        text=self.docs.text('map/supply_nodes.txt')
        signature=(text,*(self.docs.text(s.path) for s in self.world.states.values()))
        def build():
            out={}
            # Both native sources occur in this mod. Do not infer hubs from VPs.
            for sid,state in self.world.states.items():
                source,nodes=self.world.state_nodes(sid);history=block(nodes,'history')
                for container in history.children if history else []:
                    if container.key!='buildings' or container.children is None:continue
                    for province in container.children:
                        if not province.key.isdigit() or province.children is None:continue
                        pid=int(province.key)
                        if pid not in state.provinces:continue
                        for n in province.children:
                            if n.key=='supply_node' and n.children is None:out[pid]=int(numeric(value(source,n),0,True))
            for line in text.splitlines():
                words=line.split('#',1)[0].split()
                if len(words)>=2 and all(w.isdigit() for w in words[:2]):
                    pid,level=int(words[1]),int(words[0]);out[pid]=max(out.get(pid,0),level)
            return {pid:level for pid,level in out.items() if level>0}
        return self.cached('supply',signature,build)

    def validate_buildings(self,sid,levels,old):
        defs=self.buildings();provinces=set(self.world.states[sid].provinces);clean={}
        changed={k for k in set(levels)|set(old) if levels.get(k,'0')!=old.get(k,'0')}
        for key,raw in levels.items():
            pid,kind=key;level=int(numeric(raw,0,True));clean[key]=str(level)
            if key not in changed:continue
            if kind not in defs:raise ValueError('Choose a defined building')
            d=defs[kind]
            if d['network']:raise ValueError('Railways are routes; their topology is not edited by state building levels')
            if d['province']!=(pid is not None):raise ValueError('Choose a province for province buildings, or State for state buildings')
            if pid is not None and (pid not in provinces or self.world.provinces[pid]['type']!='land'):raise ValueError('Province building must belong to this state on land')
            cap=d['province_max'] if d['province'] else d['state_max']
            if cap is not None and level>cap:raise ValueError(f'{kind} has a native maximum of {cap}')
            coastal=[p for p in ([pid] if pid is not None else provinces) if self.world.provinces[p]['coastal']=='true']
            if level and d['coastal'] and not coastal:raise ValueError(kind+' requires a coastal province/state')
            if level and ('facility' in kind or kind.startswith('dam')):
                positions=self.docs.text('map/buildings.txt')
                if not any(line.startswith(str(sid)+';'+d['spawn']+';') for line in positions.splitlines()):raise ValueError('This building needs an existing '+d['spawn']+' map placement in the state')
        changed_kinds={k for _,k in changed if k in defs}
        for kind in changed_kinds:
            d=defs[kind]
            if d['province'] and d['state_max'] is not None:
                total=sum(int(v) for (_,k),v in clean.items() if k==kind)
                if total>d['state_max']:raise ValueError(f'{kind} is limited to {d["state_max"]} per state')
            if d['group']:
                grouped=[k for k,r in defs.items() if r['group']==d['group']]
                caps=[r['state_max'] for k,r in defs.items() if k in grouped and r['state_max'] is not None]
                if caps and sum(int(v) for (_,k),v in clean.items() if k in grouped)>min(caps):raise ValueError('Building group '+d['group']+' exceeds its state maximum')
            if d['exclusive'] and any(int(v)>0 and k==kind for (_,k),v in clean.items()) and any(int(v)>0 and k==d['exclusive'] for (_,k),v in clean.items()):raise ValueError(kind+' is mutually exclusive with '+d['exclusive'])
            if any(r['exclusive']==kind and any(int(v)>0 and k==other for (_,k),v in clean.items()) for other,r in defs.items()) and any(int(v)>0 and k==kind for (_,k),v in clean.items()):raise ValueError('Mutually exclusive state buildings are both present')
        return clean

    def edit_state(self,sid,name,attributes,resources,buildings,owner=None,controller=None,cores=None,claims=None,transfer_cores=True):
        old=self.state(sid);path=self.world.states[sid].path
        if not name.strip():raise ValueError('Enter a state name')
        allowed=set(old['attributes'])|{'manpower','state_category','buildings_max_level_factor','local_supplies','impassable'}
        if set(attributes)-allowed:raise ValueError('State IDs, provinces and structural fields cannot be edited here')
        attributes=dict(attributes)
        for key,raw in attributes.items():
            if raw is None:continue
            if key=='state_category':
                if raw not in self.definitions('common/state_category','state_categories'):raise ValueError('Choose a state category')
            elif key=='impassable':
                if raw not in {'yes','no'}:raise ValueError('Impassable must be yes or no')
            else:attributes[key]=numeric(raw,0,key=='manpower')
        resource_defs=self.definitions('common/resources','resources')
        resources={k:numeric(v,0) for k,v in resources.items()}
        if any(k not in resource_defs and k not in old['resources'] for k in resources):raise ValueError('Choose a defined resource')
        levels=self.validate_buildings(sid,buildings,old['buildings'])
        for tag in [owner,controller,*(cores or ()),*(claims or ())]:
            if tag and tag not in self.world.country_paths:raise ValueError('Choose a registered country tag')
        with self.docs.grouped():
            text=self.docs.text(path)
            for k,v in attributes.items():
                if v==old['attributes'].get(k):continue
                text=patch_unique(text,block(parse(text),'state'),k,v)
            if resources!=old['resources']:
                root=block(parse(text),'state');container=block(root.children,'resources')
                if container is None:text=patch_unique(text,root,'resources','{ }')
                for k in set(old['resources'])|set(resources):
                    root=block(parse(text),'state');container=block(root.children,'resources')
                    text=patch_unique(text,container,k,resources.get(k))
            regular={k:v for k,v in levels.items() if k[1]!='supply_node'};previous={k:v for k,v in old['buildings'].items() if k[1]!='supply_node'}
            if regular!=previous:
                root=block(parse(text),'state');hist=block(root.children,'history')
                if hist is None:raise ValueError('State has no history block')
                containers=[n for n in hist.children if n.key=='buildings' and n.children is not None]
                if not containers:text=patch_unique(text,hist,'buildings','{ }')
                for (pid,kind) in set(regular)|set(previous):
                    if regular.get((pid,kind))==previous.get((pid,kind)):continue
                    root=block(parse(text),'state');hist=block(root.children,'history');containers=[n for n in hist.children if n.key=='buildings' and n.children is not None]
                    # Remove owned repeated levels first, retaining other buildings and dates.
                    edits=[]
                    for container in containers:
                        scopes=[container] if pid is None else [n for n in container.children if n.key==str(pid) and n.children is not None]
                        for scope in scopes:
                            for n in scope.children:
                                if n.key==kind:edits.append((n.start,n.end))
                    for a,b in sorted(edits,reverse=True):text=text[:a]+text[b:]
                    if int(regular.get((pid,kind),'0')):
                        root=block(parse(text),'state');hist=block(root.children,'history');container=[n for n in hist.children if n.key=='buildings' and n.children is not None][-1]
                        if pid is not None:
                            target=next((n for n in container.children if n.key==str(pid) and n.children is not None),None)
                            if target is None:
                                text=patch_field(text,container,str(pid),'{ }');root=block(parse(text),'state');hist=block(root.children,'history');container=[n for n in hist.children if n.key=='buildings' and n.children is not None][-1];target=block(container.children,str(pid))
                        else:target=container
                        text=patch_field(text,target,kind,regular[(pid,kind)])
            for field_name,chosen in [('owner',owner),('controller',controller)]:
                if field_name=='owner' and chosen:continue
                if chosen is not None and chosen!=old[field_name]:text=patch_unique(text,block(block(parse(text),'state').children,'history'),field_name,chosen or None)
            for selected,previous,add,remove in [(cores,old['cores'],'add_core_of','remove_core_of'),(claims,old['claims'],'add_claim_by','remove_claim_by')]:
                if selected is None or set(selected)==previous:continue
                hist=block(block(parse(text),'state').children,'history')
                for n in reversed([n for n in hist.children if n.key in {add,remove}]):text=text[:n.start]+text[n.end:]
                hist=block(block(parse(text),'state').children,'history');at=hist.end-1
                text=text[:at]+''.join(f'\n\t\t{add} = {tag}' for tag in sorted(selected))+'\n'+text[at:]
            changed_supply={pid:int(levels.get((pid,'supply_node'),'0')) for pid,kind in set(levels)|set(old['buildings']) if kind=='supply_node' and levels.get((pid,kind),'0')!=old['buildings'].get((pid,kind),'0')}
            if changed_supply:
                # Update existing history definitions as well as explicit map rows.
                # Otherwise removing a history-only hub would resurrect it on reload.
                history=block(block(parse(text),'state').children,'history');edits=[];history_pids=set()
                for container in history.children if history else []:
                    if container.key!='buildings' or container.children is None:continue
                    for province in container.children:
                        if not province.key.isdigit() or province.children is None:continue
                        pid=int(province.key)
                        for n in province.children:
                            if n.key=='supply_node' and n.children is None and pid in changed_supply:
                                history_pids.add(pid);edits.append((n.value_start,n.end,str(changed_supply[pid])))
                for a,b,new in sorted(edits,reverse=True):text=text[:a]+new+text[b:]
                supply_path='map/supply_nodes.txt';supply=self.docs.text(supply_path);out=[];map_pids=set()
                newline='\r\n' if '\r\n' in supply else '\n'
                for line in supply.splitlines(keepends=True):
                    row=re.match(r'^(\s*)(\d+)([ \t]+)(\d+)(.*?)(\r?\n)?$',line)
                    if row and int(row[4]) in changed_supply:
                        pid=int(row[4]);map_pids.add(pid);level=changed_supply[pid]
                        if level:line=line[:row.start(2)]+str(level)+line[row.end(2):]
                        elif '#' in line:line=row[1]+line[line.index('#'):]
                        else:continue
                    out.append(line)
                supply=''.join(out)
                additions=''.join(f'{level} {pid}'+newline for pid,level in sorted(changed_supply.items()) if level and pid not in history_pids|map_pids)
                if additions:supply+=('' if not supply or supply.endswith(('\n','\r')) else newline)+additions
                self.docs.replace(supply_path,supply)
            self.docs.replace(path,text)
            if owner and owner!=old['owner']:self.world.set_owner_draft(sid,owner,transfer_cores)
            if name!=old['name']:self.set_loc(STATE_LOC,old['name_key'],name)

    def region(self,rid):
        data=self.world.regions[rid];path=data['path'];text,roots=self.docs.parsed(path);node=block(roots,'strategic_region')
        key=atom(text,node.children,'name',f'STRATEGICREGION_{rid}')
        return {'id':rid,'path':path,'name_key':key,'name':self.characters.localisations().get(key,key),
                'terrain':atom(text,node.children,'naval_terrain'),'weather':weather_periods(text,block(node.children,'weather')),
                'states':set(self.world.region_states[rid]),'sea':not any(self.world.provinces[p]['type']=='land' for p in data['provinces'])}

    def validate_region_membership(self,memberships=None):
        memberships=memberships or {rid:set(r['provinces']) for rid,r in self.world.regions.items()}
        inverse={}
        for rid,provinces in memberships.items():
            if not provinces:raise ValueError(f'Strategic region {rid} would be empty')
            for p in provinces:
                if p not in self.world.provinces:raise ValueError('Undefined province in strategic region')
                if p in inverse:raise ValueError(f'Province {p} would belong to multiple strategic regions')
                inverse[p]=rid
        for sid,state in self.world.states.items():
            regions={inverse.get(p) for p in state.provinces}
            if None in regions or len(regions)!=1:raise ValueError(f'State {sid} must be wholly inside exactly one strategic region')
        return memberships

    def edit_region(self,rid,name,terrain,periods,transfers=None):
        old=self.region(rid)
        if not name.strip():raise ValueError('Enter a region name')
        for period in periods:period.validate()
        if terrain and terrain not in {c.code for c in self.choices('terrain')}:raise ValueError('Choose a defined naval terrain')
        memberships={r:set(data['provinces']) for r,data in self.world.regions.items()}
        for sid,destination in (transfers or {}).items():
            if sid not in self.world.states or destination not in memberships:raise ValueError('Choose defined states and destination regions')
            provinces=set(self.world.states[sid].provinces)
            for members in memberships.values():members.difference_update(provinces)
            memberships[destination].update(provinces)
        self.validate_region_membership(memberships)
        with self.docs.grouped():
            for region,members in memberships.items():
                if members==set(self.world.regions[region]['provinces']):continue
                path=self.world.regions[region]['path'];text,roots=self.docs.parsed(path);node=block(roots,'strategic_region')
                raw='{\n'+''.join('\t\t'+' '.join(map(str,sorted(members)[i:i+20]))+'\n' for i in range(0,len(members),20))+'\t}'
                self.docs.replace(path,patch_unique(text,node,'provinces',raw))
            path=old['path'];text,roots=self.docs.parsed(path);node=block(roots,'strategic_region')
            if terrain!=old['terrain']:text=patch_unique(text,node,'naval_terrain',terrain or None)
            node=block(parse(text),'strategic_region');weather=block(node.children,'weather')
            old_scripts=[p.script() for p in old['weather']];scripts=[p.script() for p in periods]
            if scripts!=old_scripts:
                # Preserve non-period weather fields and each period's unknown fields/comments.
                if weather:
                    raw=text[weather.start:weather.end];wn=parse(raw)[0]
                    for n in reversed([n for n in wn.children if n.key=='period']):raw=raw[:n.start]+raw[n.end:]
                    at=parse(raw)[0].end-1;raw=raw[:at]+'\n'+'\n'.join(scripts)+'\n'+raw[at:]
                    text=text[:weather.start]+raw+text[weather.end:]
                else:text=patch_unique(text,node,'weather','{\n'+'\n'.join(scripts)+'\n}')
            self.docs.replace(path,text)
            if name!=old['name']:self.set_loc(REGION_LOC,old['name_key'],name)
        self.sync_world()

    def planet_frame(self):
        self.world.load_map();height,width=self.world.map_ids.shape
        return PlanetFrame.main_world(width,height)

    def region_latitude(self,rid):
        if rid not in self.world.regions:raise ValueError('Choose a defined strategic region')
        frame=self.planet_frame();ids=self.world.map_ids
        if frame.top!=int(frame.top):raise ValueError('Main planet extent must align with map pixels')
        if 'latitude_areas' not in self._cache:
            count=np.bincount(ids.ravel());planet=ids[int(frame.top):int(frame.bottom)]
            inside=np.bincount(planet.ravel(),minlength=len(count))
            ys=np.broadcast_to(np.arange(int(frame.top),int(frame.bottom))[:,None]+.5,planet.shape)
            sy=np.bincount(planet.ravel(),weights=ys.ravel(),minlength=len(count))
            self._cache['latitude_areas']=(count,inside,sy)
        count,inside,sy=self._cache['latitude_areas'];provinces=sorted(self.world.regions[rid]['provinces'])
        if not provinces or any(p>=len(count) or count[p]!=inside[p] for p in provinces):raise ValueError('Region extends outside the main planet; edit this body’s weather directly')
        land=[p for p in provinces if self.world.provinces[p]['type']=='land'];sample=land or provinces
        area=sum(inside[p] for p in sample)
        if not area:raise ValueError('Region has no mapped area on the main planet')
        return float(frame.latitude(sum(sy[p] for p in sample)/area))

    def climate_at_region(self,rid,code,account_latitude=True):
        latitude=self.region_latitude(rid)
        return climate_preset(code,'South' if latitude<0 else 'North',latitude if account_latitude else None)

    def paint_climate(self,rid,code,hemisphere='North',account_latitude=False):
        """Replace only a region’s weather with one complete native preset."""
        if rid not in self.world.regions:raise ValueError('Choose a defined strategic region')
        periods=climate_preset(code,hemisphere,self.region_latitude(rid) if account_latitude else None)
        path=self.world.regions[rid]['path'];text,roots=self.docs.parsed(path);node=block(roots,'strategic_region')
        newline='\r\n' if '\r\n' in text else '\n';lines=['{']
        for period in periods:
            period.validate()
            lines.extend(['\t\tperiod = {',f'\t\t\tbetween = {{ {period.start} {period.end} }}',f'\t\t\ttemperature = {{ {period.low} {period.high} }}'])
            lines.extend(f'\t\t\t{k} = {numeric(period.weights[k],0)}' for k in WEATHER_FIELDS)
            lines.append('\t\t}')
        lines.append('\t}')
        updated=patch_unique(text,node,'weather',newline.join(lines))
        if updated==text:return False
        self.docs.replace(path,updated)
        return True

    def vanilla_regions(self):
        def build():
            out={}
            for path in sorted((self.characters.game_root/'map/strategicregions').glob('*.txt')):
                text=read_text(path);root=block(parse(text),'strategic_region')
                if root is not None:out[int(atom(text,root.children,'id'))]=(path,text,root)
            return out
        return self.cached('vanilla_regions',str(self.characters.game_root),build)

    def import_weather(self,rid,flip=False):
        path,text,node=self.vanilla_regions()[rid];periods=weather_periods(text,block(node.children,'weather'))
        if flip:
            for p in periods:
                a,m=calendar_date(p.start);b,n=calendar_date(p.end);last=b==MONTH_DAYS[n]-1;m=(m+6)%12;n=(n+6)%12
                p.start=f'{min(a,MONTH_DAYS[m]-1)}.{m}';p.end=f'{MONTH_DAYS[n]-1 if last else min(b,MONTH_DAYS[n]-1)}.{n}'
        return periods,atom(text,node.children,'naval_terrain')

    @staticmethod
    def weather_signature(periods):
        rows=[]
        for p in periods:
            rows.append((calendar_date(p.start),calendar_date(p.end),Decimal(numeric(p.low)),Decimal(numeric(p.high)),tuple(sorted((k,Decimal(numeric(v,0))) for k,v in p.weights.items()))))
        return tuple(sorted(rows,key=lambda r:(r[0][1],r[0][0])))

    def preset_regions(self):
        signature=tuple((rid,tuple(sorted(r['provinces'])),self.docs.text(r['path'])) for rid,r in self.world.regions.items())
        def build():
            if 'climate_lookup' not in self._cache:
                self._cache['climate_lookup']={self.weather_signature(climate_preset(code,hemi)):(code,hemi) for code in CLIMATES for hemi in ('North','South')}
            out={}
            for rid,data in self.world.regions.items():
                try:
                    text,roots=self.docs.parsed(data['path']);weather=block(block(roots,'strategic_region').children,'weather')
                    if weather is None or any(n.key!='period' for n in weather.children):continue
                    if any(n.key not in {'between','temperature',*WEATHER_FIELDS} or n.children is not None and n.key not in {'between','temperature'} for p in weather.children for n in p.children or []):continue
                    periods=weather_periods(text,weather);actual=self.weather_signature(periods)
                    match=self._cache['climate_lookup'].get(actual)
                    if not match and len(periods)==12:
                        latitude=self.region_latitude(rid)
                        if abs(latitude)<LATITUDE_TRANSITION:
                            key=('latitude_climates',latitude)
                            if key not in self._cache:self._cache[key]={self.weather_signature(climate_preset(code,latitude=latitude)):(code,'North' if latitude>=0 else 'South') for code in CLIMATES}
                            match=self._cache[key].get(actual)
                    if match:out[rid]=match
                except (ValueError,OSError):continue
            return out
        return self.cached('preset_regions',signature,build)

    def victory_points(self):
        signature=tuple(self.docs.text(s.path) for s in self.world.states.values())
        def build():
            out={}
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);history=block(nodes,'history')
                for n in history.children if history else []:
                    if n.key!='victory_points' or n.children is None:continue
                    if len(n.children)%2:raise ValueError(f'State {sid} has malformed victory_points')
                    for p,v in zip(n.children[::2],n.children[1::2]):
                        pid=int(p.key);amount=int(numeric(v.key,0,True))
                        if amount:out[pid]={'province':pid,'state':sid,'value':amount}
            return out
        records=self.cached('vps',signature,build);loc=self.characters.localisations()
        return {p:{**d,'name':loc.get(f'VICTORY_POINTS_{p}',f'Province {p}')} for p,d in records.items()}

    def organise_vp_localisation(self):
        records={k:r for k,r in self.characters.loc_records().items() if re.fullmatch(r'VICTORY_POINTS_\d+',k)}
        for key,rows in records.items():
            if len({unescape(r[2]) for r in rows})>1:raise ValueError('Conflicting authored VP names: '+key)
        lines=[]
        for key,rows in records.items():
            preferred=next((r for r in rows if r[0]==VP_LOC),rows[-1]);lines.append((sort_name(re.sub('[§\x15].','',unescape(preferred[2]))),int(key.rsplit('_',1)[1]),preferred[1]))
        for path in {r[0] for rows in records.values() for r in rows}|{VP_LOC}:
            text=self.docs.text(path);remaining=[]
            for line in text.splitlines(keepends=True):
                m=LOC.match(line)
                if m and re.fullmatch(r'VICTORY_POINTS_\d+',m[1]):continue
                if path==VP_LOC and re.match(r'\s*#\s*(Country|State)\s*:',line):continue
                remaining.append(line)
            if path==VP_LOC:
                prelude=''.join(remaining).rstrip();text=prelude+'\n\n'+'\n'.join(line for _,_,line in sorted(lines))+'\n'
            else:text=''.join(remaining)
            self.docs.replace(path,text)

    def set_vp(self,pid,name,amount=None):
        if pid not in self.world.province_states or self.world.provinces[pid]['type']!='land':raise ValueError('Choose a land province belonging to a state')
        if amount is not None:
            amount=numeric(amount,1,True)
            if not name.strip():raise ValueError('Enter a victory-point name')
        sid=self.world.province_states[pid];path=self.world.states[sid].path;text,nodes=self.world.state_nodes(sid);hist=block(nodes,'history')
        if hist is None:raise ValueError('State has no history block')
        edits=[]
        for n in hist.children:
            if n.key!='victory_points' or n.children is None:continue
            if len(n.children)%2:raise ValueError('Malformed existing VP block')
            pairs=[(a.key,b.key) for a,b in zip(n.children[::2],n.children[1::2])]
            if not any(int(a)==pid for a,b in pairs):continue
            keep=[(a,b) for a,b in pairs if int(a)!=pid]
            raw='victory_points = { '+' '.join(a+' '+b for a,b in keep)+' }' if keep else ''
            edits.append((n.start,n.end,raw))
        for a,b,raw in reversed(edits):text=text[:a]+raw+text[b:]
        if amount is not None:
            hist=block(block(parse(text),'state').children,'history');at=hist.end-1
            text=text[:at]+f'\n\t\tvictory_points = {{ {pid} {amount} }}\n'+text[at:]
        with self.docs.grouped():
            self.docs.replace(path,text)
            if amount is not None:
                self.set_loc(VP_LOC,f'VICTORY_POINTS_{pid}',name);self.organise_vp_localisation()

    def province_points(self):
        if 'points' in self._cache:return self._cache['points']
        self.world.load_map();full=self.world.map_ids;sample=full[::2,::2];ids=sample.ravel();yy,xx=np.indices(sample.shape)
        count=np.bincount(ids);sx=np.bincount(ids,weights=xx.ravel()*2);sy=np.bincount(ids,weights=yy.ravel()*2)
        order=np.argsort(ids,kind='stable');offset=np.concatenate(([0],np.cumsum(count)));out={}
        for pid in self.world.provinces:
            if pid>=len(count) or not count[pid]:continue
            x,y=round(sx[pid]/count[pid]),round(sy[pid]/count[pid]);x=min(full.shape[1]-1,x);y=min(full.shape[0]-1,y)
            if int(full[y,x])!=pid:
                indices=order[offset[pid]:offset[pid+1]];px=indices%sample.shape[1]*2;py=indices//sample.shape[1]*2
                nearest=np.argmin((px-x)**2+(py-y)**2);x,y=int(px[nearest]),int(py[nearest])
            out[pid]=(x,y)
        missing=set(self.world.provinces)-out.keys()
        if missing:
            ys,xs=np.nonzero(np.isin(full,list(missing)))
            for y,x in zip(ys,xs):out.setdefault(int(full[y,x]),(int(x),int(y)))
        self._cache['province_sizes']={p:int(count[p]) if p<len(count) else 0 for p in out}
        self._cache['points']=out;return out

    def state_points(self):
        if 'state_points' not in self._cache:
            points=self.province_points();sizes=self._cache['province_sizes'];out={}
            for sid,state in self.world.states.items():
                candidates=[p for p in state.provinces if p in points]
                if candidates:out[sid]=points[max(candidates,key=lambda p:sizes.get(p,0))]
            self._cache['state_points']=out
        return self._cache['state_points']

    def region_points(self):
        signature=tuple((rid,r['provinces']) for rid,r in self.world.regions.items())
        def build():
            points=self.province_points();sizes=self._cache['province_sizes'];out={}
            for rid,r in self.world.regions.items():
                candidates=[p for p in r['provinces'] if p in points]
                if candidates:out[rid]=points[max(candidates,key=lambda p:sizes.get(p,0))]
            return out
        return self.cached('region_points',signature,build)

    def sync_world(self):
        if self._world_revision==self.docs.revision:return
        if hasattr(self.world,'state_boundary_store'):self.world.state_boundary_store.sync_world()
        self.sync_terrain()
        paths=self.characters.files('map/strategicregions','.txt');signature=tuple(self.docs.text(p) for p in paths)
        if self._region_signature!=signature:
            self.world._load_strategic_regions();self.world._boundary_cache.clear();self.world._boundary_size=None;self._region_signature=signature
        for sid,s in self.world.states.items():
            text,nodes=self.world.state_nodes(sid)
            if {int(n.key) for n in block(nodes,'provinces').children}!=set(s.provinces):raise ValueError('State reshaping is not enabled')
            s.name=atom(text,nodes,'name',s.name);hist=block(nodes,'history');s.owner=atom(text,hist.children,'owner') if hist else ''
        self._world_revision=self.docs.revision

    def validate_save(self):
        self.sync_world()
        if self.world.regions:self.validate_region_membership()
        if hasattr(self.world,'state_boundary_store'):self.world.state_boundary_store.validate_save()
