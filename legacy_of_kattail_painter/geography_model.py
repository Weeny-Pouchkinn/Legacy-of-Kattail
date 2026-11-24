"""Native state, strategic-region/weather and province victory-point authoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
import math
import re

import numpy as np

from model import child, parse, scalar, value, walk, read_text
from character_model import atom, block, patch_field, quote, LOC, unescape, sort_name
from select_ui import Choice

STATE_LOC='localisation/english/state_names_l_english.yml'
REGION_LOC='localisation/english/strategic_region_names_l_english.yml'
VP_LOC='localisation/english/victory_points_l_english.yml'
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


def climate_preset(code,hemisphere='North'):
    """Köppen-inspired game profiles, not observational data or a classification algorithm."""
    if code not in CLIMATES or hemisphere not in {'North','South'}:raise ValueError('Choose a climate and hemisphere')
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


class GeographyStore:
    def __init__(self,world,characters,catalogs):
        self.world,self.characters,self.catalogs,self.docs=world,characters,catalogs,world.docs
        self._cache={};self._region_signature=None
        self._world_revision=-1
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
        def build():
            out={}
            for line in text.splitlines():
                words=line.split('#',1)[0].split()
                if len(words)>=2 and all(w.isdigit() for w in words[:2]):out[int(words[1])]=int(words[0])
            return out
        return self.cached('supply',text,build)

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

    def edit_state(self,sid,name,attributes,resources,buildings,owner=None,controller=None,cores=None,claims=None):
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
                if chosen is not None and chosen!=old[field_name]:text=patch_unique(text,block(block(parse(text),'state').children,'history'),field_name,chosen or None)
            for selected,previous,add,remove in [(cores,old['cores'],'add_core_of','remove_core_of'),(claims,old['claims'],'add_claim_by','remove_claim_by')]:
                if selected is None or set(selected)==previous:continue
                hist=block(block(parse(text),'state').children,'history')
                for n in reversed([n for n in hist.children if n.key in {add,remove}]):text=text[:n.start]+text[n.end:]
                hist=block(block(parse(text),'state').children,'history');at=hist.end-1
                text=text[:at]+''.join(f'\n\t\t{add} = {tag}' for tag in sorted(selected))+'\n'+text[at:]
            self.docs.replace(path,text)
            if name!=old['name']:self.set_loc(STATE_LOC,old['name_key'],name)
            changed_supply={pid:int(levels.get((pid,'supply_node'),'0')) for pid,kind in set(levels)|set(old['buildings']) if kind=='supply_node' and levels.get((pid,kind),'0')!=old['buildings'].get((pid,kind),'0')}
            if changed_supply:
                path='map/supply_nodes.txt';lines=self.docs.text(path).splitlines(keepends=True);out=[]
                for line in lines:
                    parts=line.split('#',1)[0].split()
                    if len(parts)>=2 and parts[1].isdigit() and int(parts[1]) in changed_supply:continue
                    out.append(line)
                text=''.join(out).rstrip()+'\n'+''.join(f'{v} {p}\n' for p,v in sorted(changed_supply.items()) if v)
                self.docs.replace(path,text)

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
        self._cache['points']=out;return out

    def sync_world(self):
        if self._world_revision==self.docs.revision:return
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
