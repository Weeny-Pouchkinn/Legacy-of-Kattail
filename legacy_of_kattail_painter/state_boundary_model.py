"""Atomic whole-province state boundaries, new states and conserved estimates."""
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal,ROUND_FLOOR
from pathlib import Path
import re

from character_model import atom,block,patch_field,quote
from demographics import Setup,set_local_draft
from geography_model import STATE_LOC
from model import State,parse,value
from state_positions import StatePositions

LAYER='State boundaries'
POPULATION_VP_WEIGHT=Decimal(10)
INDUSTRY_VP_WEIGHT=Decimal(2)
TERRAIN_DENSITY={key:Decimal(str(number)) for key,number in {
    'plains':1,'urban':4,'forest':.6,'hills':.65,'jungle':.4,
    'mountain':.2,'desert':.2,'marsh':.35,'frozen':.1,'volcanic':.1,
    'lakes':.02,'ocean':0,'unknown':.5}.items()}
DATE=re.compile(r'^\d{4}\.\d{1,2}\.\d{1,2}$')


@dataclass(frozen=True)
class Recalculate:
    population:bool=True
    resources:bool=True
    industry:bool=False


def number(raw,integer=False):
    try:result=Decimal(str(raw))
    except Exception as exc:raise ValueError('Recalculation requires numeric values: '+str(raw)) from exc
    if not result.is_finite() or result<0 or integer and result!=int(result):
        raise ValueError('Recalculation requires nonnegative '+('whole numbers' if integer else 'numbers')+': '+str(raw))
    return result


def apportioned(total,weights,quantum=Decimal(1)):
    """Largest remainders, stable state-ID ties, exact total and no negative shares."""
    total=number(total);weights={k:number(v) for k,v in weights.items()}
    if not weights:raise ValueError('No receiving states for recalculation')
    if not sum(weights.values()):weights={k:Decimal(1) for k in weights}
    units=total/quantum
    if units!=int(units):raise ValueError('Allocation quantum does not represent the source total')
    exact={k:units*v/sum(weights.values()) for k,v in weights.items()}
    shares={k:int(v.to_integral_value(rounding=ROUND_FLOOR)) for k,v in exact.items()}
    for key in sorted(exact,key=lambda k:(-(exact[k]-shares[k]),k))[:int(units)-sum(shares.values())]:shares[key]+=1
    return {k:Decimal(v)*quantum for k,v in shares.items()}


def scopes(text):
    history=block(block(parse(text),'state').children,'history')
    if history is None:raise ValueError('State has no history')
    return [(None,history)]+[(n.key,n) for n in history.children if n.children is not None and DATE.fullmatch(n.key)]


def root_field(text,key,raw):
    return patch_field(text,block(parse(text),'state'),key,raw)


def history_scope(text,date):
    history=block(block(parse(text),'state').children,'history')
    if date is None:return text,history
    node=block(history.children,date)
    if node is None:text=patch_field(text,history,date,'{ }');history=block(block(parse(text),'state').children,'history');node=block(history.children,date)
    return text,node


def append_raw(text,date,raw,building=False):
    text,parent=history_scope(text,date)
    if building:
        container=block(parent.children,'buildings')
        if container is None:
            text=patch_field(text,parent,'buildings','{ }');text,parent=history_scope(text,date);container=block(parent.children,'buildings')
        parent=container
    return text[:parent.end-1]+'\n'+raw+'\n'+text[parent.end-1:]


def transfer_payload(text,provinces):
    """Remove only province-addressed buildings/VP pairs, including dated history."""
    edits=[];payload=[]
    for date,parent in scopes(text):
        for node in parent.children:
            if node.key=='buildings' and node.children is not None:
                for province in node.children:
                    if province.key.isdigit() and int(province.key) in provinces:
                        edits.append((province.start,province.end,''));payload.append((date,True,text[province.start:province.end]))
            elif node.key=='victory_points' and node.children is not None:
                children=node.children
                if len(children)%2:raise ValueError('Malformed victory-point list in source state')
                kept=[];moved=[]
                for pid,amount in zip(children[::2],children[1::2]):
                    if not pid.key.isdigit():raise ValueError('Non-numeric province in victory points')
                    (moved if int(pid.key) in provinces else kept).append((pid.key,amount.key))
                if moved:
                    # Comments stay in place, and only the owned pair tokens are removed.
                    for pid,amount in zip(children[::2],children[1::2]):
                        if int(pid.key) in provinces:
                            edits.extend([(pid.start,pid.end,''),(amount.start,amount.end,'')])
                    payload.append((date,False,'victory_points = { '+' '.join(a+' '+b for a,b in moved)+' }'))
    for start,end,replacement in sorted(edits,reverse=True):text=text[:start]+replacement+text[end:]
    return text,payload


def state_data(text):
    root=block(parse(text),'state');history=block(root.children,'history')
    buildings={};vps={}
    for container in history.children:
        if container.key=='buildings' and container.children is not None:
            for n in container.children:
                if n.children is None:buildings[n.key]=value(text,n)
        if container.key=='victory_points' and container.children is not None:
            for pid,amount in zip(container.children[::2],container.children[1::2]):vps[int(pid.key)]=amount.key
    resources=block(root.children,'resources')
    return {'population':atom(text,root.children,'manpower','0'),
            'resources':{n.key:value(text,n) for n in resources.children or []} if resources else {},
            'buildings':buildings,'vps':vps}


class StateBoundaryStore:
    def __init__(self,world,geo,catalogs):
        self.world,self.geo,self.catalogs,self.docs=world,geo,catalogs,world.docs
        self.paths={state.path for state in world.states.values()}
        self.original_provinces=frozenset(world.province_states)
        self.positions=StatePositions(world,geo);self._revision=-1;self._state_files={};world.state_boundary_store=self

    def sync_world(self,force=False):
        if not force and self._revision==self.docs.revision:return
        paths=self.paths|{p for p in self.docs.originals if p.startswith('history/states/') and p.endswith('.txt')}
        states={};inverse={}
        for path in sorted(paths):
            text=self.docs.text(path)
            if not text.strip():continue
            cached=self._state_files.get(path)
            if cached is None or cached[0]!=text:
                _,nodes=self.docs.parsed(path);root=block(nodes,'state')
                if root is None:raise ValueError('Missing state block in '+path)
                sid=int(atom(text,root.children,'id'));history=block(root.children,'history');provinces=block(root.children,'provinces')
                members=[int(n.key) for n in provinces.children] if provinces else []
                state=State(sid,path,atom(text,root.children,'name'),atom(text,history.children,'owner') if history else '',members)
                cached=self._state_files[path]=(text,state)
            state=cached[1];sid=state.id;members=state.provinces
            if sid in states:raise ValueError('Duplicate state ID '+str(sid))
            if not members:raise ValueError(f'State {sid} must retain at least one province')
            for pid in members:
                if pid in inverse:raise ValueError(f'Province {pid} belongs to multiple states')
                # Native states also contain lake provinces; keep those memberships
                # intact even though the brush only transfers land provinces.
                if pid not in self.world.provinces:raise ValueError(f'Province {pid} is undefined')
                inverse[pid]=sid
            states[sid]=state
        if frozenset(inverse)!=self.original_provinces:raise ValueError('Every original state province must remain assigned exactly once')
        changed=inverse!=self.world.province_states or states.keys()!=self.world.states.keys()
        self.world.states=states;self.world.province_states=inverse
        self.world.region_states={rid:frozenset(inverse[p] for p in region['provinces'] if p in inverse) for rid,region in self.world.regions.items()}
        active={s.path for s in states.values()}
        self.world.files=sorted({p for p in self.world.files if not p.startswith('history/states/')}|active)
        if changed:
            self.world._state_nodes_cache.clear();self.world._boundary_cache.clear();self.world._boundary_size=None;self.world._map_palettes.clear()
            for key in ('_province_state_ids','_land_provinces'):
                if hasattr(self.world,key):delattr(self.world,key)
            self.geo._cache.pop('state_points',None)
        self._revision=self.docs.revision

    def terrain_weights(self):
        result=dict(TERRAIN_DENSITY)
        for key,(text,node) in self.geo.definitions('common/terrain','categories').items():
            if key in result:continue
            if atom(text,node.children,'is_water')=='yes' or atom(text,node.children,'naval_terrain')=='yes':result[key]=Decimal('.02')
            else:
                movement=max(Decimal(1),number(atom(text,node.children,'movement_cost','1')))
                result[key]=1/(movement*movement)
        for province in self.world.provinces.values():result.setdefault(province['terrain'],Decimal('.5'))
        return result

    def _membership(self,text,members):
        return root_field(text,'provinces','{ '+' '.join(map(str,sorted(members)))+' }')

    def _set_building(self,text,key,raw):
        text,parent=history_scope(text,None);containers=[n for n in parent.children if n.key=='buildings' and n.children is not None]
        edits=[(n.start,n.end) for container in containers for n in container.children if n.children is None and n.key==key]
        for a,b in sorted(edits,reverse=True):text=text[:a]+text[b:]
        if Decimal(raw):text=append_raw(text,None,key+' = '+raw,True)
        return text

    def _recalculate(self,before,options):
        g=self.positions.geometry();density=self.terrain_weights() if options.population else {};building_defs=self.geo.buildings()
        industry={key for key,row in building_defs.items() if row['shared'] and not row['province']}
        populations=defaultdict(Decimal);resources=defaultdict(lambda:defaultdict(Decimal));factories=defaultdict(lambda:defaultdict(Decimal))
        affected=set(before)
        for sid,(members,text) in before.items():
            if not members:continue
            data=state_data(text);mean_area=sum(int(g['sizes'][p]) for p in members)/Decimal(len(members))
            weights={kind:defaultdict(Decimal) for kind in ('population','resources','industry')}
            for pid in members:
                target=self.world.province_states[pid];affected.add(target)
                area=Decimal(int(g['sizes'][pid]));vp=number(data['vps'].get(pid,'0')) if options.population or options.industry else Decimal(0)
                if options.population:weights['population'][target]+=area*density[self.world.provinces[pid]['terrain']]+mean_area*POPULATION_VP_WEIGHT*vp
                weights['resources'][target]+=area
                weights['industry'][target]+=1+INDUSTRY_VP_WEIGHT*vp
            if options.population:
                for target,total in apportioned(number(data['population'],True),weights['population']).items():populations[target]+=total
            if options.resources:
                for kind,raw in data['resources'].items():
                    total=number(raw);quantum=Decimal(1) if total==int(total) else Decimal(1).scaleb(total.as_tuple().exponent)
                    for target,amount in apportioned(total,weights['resources'],quantum).items():resources[target][kind]+=amount
            if options.industry:
                for kind in industry:
                    total=number(data['buildings'].get(kind,'0'),True);shares=dict(weights['industry'])
                    if building_defs[kind]['coastal']:
                        shares={target:weight for target,weight in shares.items() if any(p in g['coasts'] for p in self.world.states[target].provinces)}
                    if not shares and not total:continue
                    for target,amount in apportioned(total,shares).items():factories[target][kind]+=amount
        for sid in affected:
            path=self.world.states[sid].path;text=self.docs.text(path)
            if options.population:text=root_field(text,'manpower',str(int(populations[sid])))
            if options.resources:
                values=resources[sid];text=root_field(text,'resources','{ '+' '.join(key+' = '+format(v,'f') for key,v in sorted(values.items()) if v)+' }')
            if options.industry:
                for kind in sorted(industry):text=self._set_building(text,kind,format(factories[sid][kind],'f'))
            self.docs.replace(path,text)
        return affected

    def move_provinces(self,provinces,target,options=Recalculate(),new_state=None):
        self.sync_world();provinces=set(map(int,provinces))
        if not new_state and target not in self.world.states:raise ValueError('Choose an existing target state')
        if any(self.world.provinces.get(p,{}).get('type')!='land' or p not in self.world.province_states for p in provinces):
            raise ValueError('Only assigned land provinces can move between states')
        provinces={p for p in provinces if self.world.province_states[p]!=target}
        if not provinces:return {'states':[],'provinces':0,'placements':0}
        donors={self.world.province_states[p] for p in provinces};affected=donors|{target}
        before={sid:(tuple(self.world.states[sid].provinces),self.docs.text(self.world.states[sid].path)) for sid in affected if sid in self.world.states}
        old_levels={sid:self.geo.state(sid)['buildings'] for sid in before}
        memberships={sid:set(members) for sid,(members,_) in before.items()}
        memberships.setdefault(target,set()).update(provinces)
        for sid in donors:
            memberships[sid]-=provinces
            if not any(self.world.provinces[p]['type']=='land' for p in memberships[sid]):
                raise ValueError(f'State {sid} would be empty of land; leave at least one land province')
        for sid,members in memberships.items():
            regions={self.world.province_regions.get(pid) for pid in members}
            if None in regions or len(regions)!=1:raise ValueError(f'State {sid} would cross strategic regions')
        try:
            with self.docs.grouped():
                if new_state:
                    path,text=new_state;self.docs.replace(path,text)
                    self.world.states[target]=State(target,path,'', '',[])
                target_path=self.world.states[target].path;target_text=self.docs.text(target_path)
                for sid in sorted(donors):
                    path=self.world.states[sid].path;text,payload=transfer_payload(self.docs.text(path),provinces)
                    self.docs.replace(path,self._membership(text,memberships[sid]))
                    for date,building,raw in payload:target_text=append_raw(target_text,date,raw,building)
                self.docs.replace(target_path,self._membership(target_text,memberships[target]))
                self.sync_world(force=True)
                affected=self._recalculate(before,options)|affected
                # A province capital is state-local; keep it on a retained province if present.
                for sid in affected:
                    path=self.world.states[sid].path;text=self.docs.text(path);root=block(parse(text),'state')
                    capital=atom(text,root.children,'capital')
                    if capital and (not capital.isdigit() or int(capital) not in self.world.states[sid].provinces):
                        land=[p for p in self.world.states[sid].provinces if self.world.provinces[p]['type']=='land']
                        point=max(land,key=lambda p:self.positions.geometry()['sizes'][p])
                        self.docs.replace(path,root_field(text,'capital',str(point)))
                self._validate_history(affected)
                self._validate_coastal_buildings(affected)
                placements=self.positions.regenerate(affected)
                for sid in affected:self.geo.validate_buildings(sid,self.geo.state(sid)['buildings'],old_levels.get(sid,{}))
            self.sync_world(force=True);self.world.demographics=Setup(self.world).load()
            return {'states':sorted(affected),'provinces':len(provinces),'placements':placements}
        except Exception:
            self.sync_world(force=True);self.world.demographics=Setup(self.world).load();raise

    def create_state(self,name,province,options=Recalculate()):
        if not name.strip():raise ValueError('Enter the new state name')
        self.sync_world()
        if province not in self.world.province_states:raise ValueError('Choose an assigned land province')
        source=self.world.province_states[province];data=self.world.demographics.get(source) or Setup(self.world).load()[source]
        text,nodes=self.world.state_nodes(source);history=block(nodes,'history')
        sid=max([*self.world.states,*[int(m[1]) for p in self.docs.originals if p.startswith('history/states/') for m in [re.match(r'(\d+)',Path(p).name)] if m]],default=0)+1
        # Do not reuse holes/session IDs or overwrite an existing human localisation key.
        records=self.catalogs.characters.loc_records()
        while 'STATE_'+str(sid) in records:sid+=1
        key='STATE_'+str(sid);path=f'history/states/{sid}-painter.txt'
        if self.docs.binary(path) is not None:raise ValueError('New state path already exists')
        rootparts=[text[n.start:n.end] for n in nodes if n.key not in {'id','name','provinces','manpower','resources','history','capital'}]
        politics=[text[n.start:n.end] for n in history.children if n.key in {'owner','controller','add_core_of','remove_core_of','add_claim_by','remove_claim_by'} and n.children is None]
        dated=[]
        for date,parent in scopes(text):
            if date is not None:
                parts=[text[n.start:n.end] for n in parent.children if n.key in {'owner','controller','add_core_of','remove_core_of','add_claim_by','remove_claim_by'} and n.children is None]
                if parts:dated.append(date+' = { '+' '.join(parts)+' }')
        # Infrastructure is an intensity; factory counts and other state buildings are not duplicated.
        old=state_data(text);infrastructure=old['buildings'].get('infrastructure')
        if infrastructure:politics.append('buildings = { infrastructure = '+infrastructure+' }')
        raw='state = {\n\tid = '+str(sid)+'\n\tname = '+quote(key)+'\n\tmanpower = 0\n\tprovinces = { }\n\tresources = { }\n'+'\n'.join(rootparts)+'\n\thistory = {\n'+'\n'.join(politics+dated)+'\n\t}\n}\n'
        try:
            with self.docs.grouped():
                result=self.move_provinces([province],sid,options,(path,raw))
                self.geo.set_loc(STATE_LOC,key,name.strip())
                set_local_draft(self.world,sid,list(data['culture']),data['species'],data['minority'])
                if hasattr(self.world,'imperium_store'):
                    ident=self.world.imperium_store.state_assignments().get(source,0)
                    if ident:self.world.imperium_store.paint_state(sid,ident)
                for relative in self.catalogs.characters.files('map/supplyareas','.txt'):
                    area_text=self.docs.text(relative);area=block(parse(area_text),'supply_area')
                    members=block(area.children,'states') if area else None
                    if members and str(source) in {n.key for n in members.children}:
                        self.docs.replace(relative,patch_field(area_text,area,'states','{ '+' '.join(n.key for n in members.children)+' '+str(sid)+' }'))
            self.sync_world(force=True);self.world.localisation=self.catalogs.characters.localisations()
            self.world.demographics=Setup(self.world).load();return sid,result
        except Exception:
            self.sync_world(force=True);self.world.demographics=Setup(self.world).load();raise

    def _validate_history(self,states):
        for sid in states:
            text,_=self.world.state_nodes(sid);members=set(self.world.states[sid].provinces)
            for _,parent in scopes(text):
                for node in parent.children:
                    if node.key=='buildings' and node.children is not None:
                        for n in node.children:
                            if n.children is not None and n.key.isdigit() and int(n.key) not in members:raise ValueError(f'State {sid} contains buildings for another state province')
                    elif node.key=='victory_points' and node.children is not None:
                        if len(node.children)%2:raise ValueError('Malformed victory points')
                        if any(int(n.key) not in members for n in node.children[::2]):raise ValueError(f'State {sid} contains VPs for another state province')

    def _validate_coastal_buildings(self,states):
        definitions=self.geo.buildings();coasts=self.positions.geometry()['coasts']
        for sid in states:
            if any(p in coasts for p in self.world.states[sid].provinces):continue
            data=state_data(self.docs.text(self.world.states[sid].path))
            for key,raw in data['buildings'].items():
                row=definitions.get(key,{})
                if row.get('coastal') and not row.get('province') and number(raw):
                    raise ValueError(f'State {sid} would have inland {key}; retain a coastal province or enable industry redistribution')

    def validate_save(self):
        self.sync_world()
        if self.world.regions:self.geo.validate_region_membership()
        changed=set()
        for sid,state in self.world.states.items():
            original=self.docs.snapshots.get(state.path)
            old=block(parse(self.docs._decode(original)),'state') if original else None
            members=block(old.children,'provinces') if old else None
            if members is None or {int(n.key) for n in members.children}!=set(state.provinces):changed.add(sid)
        if changed:
            self._validate_history(changed);self._validate_coastal_buildings(changed);self.positions.validate(changed)
