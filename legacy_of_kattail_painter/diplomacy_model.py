"""Source-aware starting diplomacy; declarations are not a simulated game VM."""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from pathlib import Path
import re

from character_model import atom,block,patch_field,quote,unescape
from model import parse,value,read_text
from script_format import format_changes

KINDS={'faction':'Faction leader','member':'Faction member','subject':'Subject / puppet',
       'war':'War','guarantee':'Guarantee','military_access':'Military access',
       'non_aggression_pact':'Non-aggression pact','market_access':'Market access'}
EFFECTS={'create_faction':'faction','add_to_faction':'member','set_autonomy':'subject',
         'puppet':'subject','declare_war_on':'war','give_guarantee':'guarantee',
         'give_military_access':'military_access','give_market_access':'market_access'}
OTHER={'remove_from_faction','dismantle_faction','set_faction_leader','set_faction_name','white_peace'}
DATE=re.compile(r'^\d{4}\.\d{1,2}\.\d{1,2}$')


@dataclass(frozen=True)
class Relation:
    kind:str
    actor:str
    target:str=''
    detail:str=''
    freedom:str=''
    active:bool=True
    path:str=''
    start:int=0
    end:int=0
    raw:str=''
    context:tuple=()
    group:bool=False
    editable:bool=True
    conditional:bool=False
    line:int=0

    @property
    def description(self):return KINDS.get(self.kind,self.kind.replace('_',' ').title())


class DiplomacyStore:
    def __init__(self,world,characters):
        self.world,self.characters,self.docs=world,characters,world.docs
        self._signature=None;self._records=[]

    def definitions(self,folder):
        """Effective native definitions, honoring replace_path and same-file overrides."""
        descriptor=self.docs.text('descriptor.mod')
        replaced=[value(descriptor,n).strip('"').rstrip('/') for n in parse(descriptor) if n.key=='replace_path']
        native={} if any(folder==p or folder.startswith(p+'/') for p in replaced) else {
            p.relative_to(self.characters.game_root).as_posix():read_text(p)
            for p in sorted((self.characters.game_root/folder).rglob('*.txt'))}
        native.update({p:self.docs.text(p) for p in self.characters.files(folder,'.txt')})
        return [(path,text,parse(text)) for path,text in sorted(native.items()) if text.strip()]

    def autonomies(self):
        return {atom(text,n.children,'id') for _,text,nodes in self.definitions('common/autonomous_states')
                for n in nodes if n.key=='autonomy_state' and atom(text,n.children,'id')}

    def wargoals(self):
        return {n.key for _,text,nodes in self.definitions('common/wargoals') for root in nodes
                for n in (root.children if root.key=='wargoal_types' else [root]) if n.children is not None}

    def faction_map(self,records=None):
        records=self.records() if records is None else records
        factions={r.actor:{r.actor} for r in records if r.kind=='faction' and not r.conditional}
        for _ in range(len(factions)+len(records)+1):
            changed=False
            for r in records:
                if r.kind!='member' or r.conditional or not r.active:continue
                for leader,members in factions.items():
                    if r.actor in members and r.target not in members:members.add(r.target);changed=True
            if not changed:break
        return factions

    def _resolve(self,token,actor,root,previous):
        return {'THIS':actor,'ROOT':root,'PREV':previous}.get(token,token)

    def _match(self,text,nodes,actor,root,previous,factions):
        results=[];existing=self._existing
        for n in nodes or []:
            raw=value(text,n).strip('"');key=n.key
            if key in {'AND','NOT','OR'} and n.children is not None:
                pieces=[self._match(text,[c],actor,root,previous,factions) for c in n.children]
                result=(False if False in pieces else None if None in pieces else True) if key!='OR' else (True if True in pieces else None if None in pieces else False)
                results.append(not result if key=='NOT' and result is not None else result)
            elif key=='tag':results.append(actor==self._resolve(raw,actor,root,previous))
            elif key=='always':results.append(raw=='yes')
            elif key=='exists':results.append((actor in existing)==(raw=='yes'))
            elif key=='is_in_faction_with':
                target=self._resolve(raw,actor,root,previous)
                results.append(any(actor in members and target in members for members in factions.values()))
            else:results.append(None)
        return False if False in results else None if None in results else True

    def records(self):
        signature=(self.docs.revision,tuple(self.world.country_paths))
        if signature==self._signature:return list(self._records)
        self._existing={self.world.state_relations(sid)['owner'] for sid in self.world.states}
        sources=[]
        for path in self.characters.files('history/countries','.txt'):
            actor=Path(path).name[:3]
            if actor in self.world.country_paths:sources.append((path,self.docs.text(path),actor,None))
        sources.extend((p,self.docs.text(p),'',None) for p in self.characters.files('history/general','.txt'))
        for path in self.characters.files('common/on_actions','.txt'):
            text=self.docs.text(path)
            for root in parse(text):
                for startup in root.children or []:
                    if startup.key=='on_startup':
                        for effect in startup.children or []:
                            if effect.key=='effect':sources.append((path,text,'',effect.children))
        scripted={}
        for path in self.characters.files('common/scripted_effects','.txt'):
            text=self.docs.text(path)
            for n in parse(text):
                if n.children is not None:scripted[n.key]=(path,text,n.children)

        def scan(expand,factions):
            out=[]
            def visit(path,text,nodes,actor,root,previous='',context=(),group=False,conditional=False,shared=False,stack=()):
                for n in nodes:
                    if n.key in EFFECTS or n.key=='diplomatic_relation' or n.key in OTHER:
                        kind=EFFECTS.get(n.key,n.key);target='';detail='';freedom='';active=True
                        if n.key=='diplomatic_relation':kind=atom(text,n.children,'relation');target=atom(text,n.children,'country');active=atom(text,n.children,'active','yes')!='no'
                        elif kind=='faction':detail=unescape(value(text,n).strip('"'))
                        elif kind=='subject':
                            target=atom(text,n.children,'target') if n.children is not None else value(text,n)
                            detail=atom(text,n.children,'autonomy_state','autonomy_puppet') if n.children is not None else 'autonomy_puppet'
                            freedom=atom(text,n.children,'freedom_level') if n.children is not None else ''
                        elif kind=='war':target=atom(text,n.children,'target');detail=atom(text,n.children,'type')
                        else:target=value(text,n) if n.children is None else atom(text,n.children,'tag')
                        target=self._resolve(target.strip('"'),actor,root,previous)
                        editable=not shared and actor in self.world.country_paths and (kind=='faction' or bool(re.fullmatch('[A-Z][A-Z0-9]{2}',target)))
                        out.append(Relation(kind,actor or '(dynamic country)',target,detail,freedom,active,path,n.start,n.end,text[n.start:n.end],context,group,editable and kind in KINDS,conditional,text.count('\n',0,n.start)+1))
                        continue
                    if n.key in self.world.country_paths and n.children is not None:
                        visit(path,text,n.children,n.key,root,actor,context,group,conditional,shared,stack)
                    elif n.key in {'THIS','ROOT','PREV'} and n.children is not None:
                        current=self._resolve(n.key,actor,root,previous)
                        visit(path,text,n.children,current,root,actor,context,group,conditional,shared,stack)
                    elif n.key in {'every_country','every_possible_country'} and n.children is not None:
                        if not expand:continue
                        limit=block(n.children,'limit');members=[c for c in n.children if c.key!='limit']
                        for tag in sorted(self.world.country_paths):
                            if n.key=='every_country' and tag not in self._existing:continue
                            result=self._match(text,limit.children if limit else [],tag,root,actor,factions)
                            if result is False:continue
                            label=n.key+(' limit '+re.sub(r'\s+',' ',text[limit.value_start:limit.end]) if limit else '')
                            visit(path,text,members,tag,root,actor,context+(label,),True,conditional or result is None,shared or result is None,stack)
                    elif n.key in {'hidden_effect','effect','if','else','else_if'} or DATE.fullmatch(n.key):
                        if n.children is None:continue
                        condition=n.key in {'if','else','else_if'} or bool(DATE.fullmatch(n.key))
                        limit=block(n.children,'limit');label=n.key+(' '+re.sub(r'\s+',' ',text[limit.value_start:limit.end]) if limit else '')
                        if group and n.key=='if' and limit is not None:
                            result=self._match(text,limit.children,actor,root,previous,factions)
                            if result is False:continue
                            if result is True:condition=False
                        visit(path,text,[c for c in n.children if c.key!='limit'],actor,root,previous,context+((label,) if condition else ()),group,conditional or condition,shared,stack)
                    elif n.key in scripted and n.key not in stack:
                        p,t,children=scripted[n.key]
                        visit(p,t,children,actor,root,previous,context+('Shared scripted effect '+n.key,),group,conditional,True,stack+(n.key,))
            for path,text,actor,nodes in sources:visit(path,text,parse(text) if nodes is None else nodes,actor,actor)
            return out
        preliminary=scan(False,{})
        self._records=scan(True,self.faction_map(preliminary));self._signature=signature
        return list(self._records)

    def _validate(self,new,old=None):
        if new.kind not in KINDS:raise ValueError('Choose a supported diplomatic relation')
        if new.actor not in self.world.country_paths:raise ValueError('Choose a registered source country')
        if new.kind!='faction' and (new.target not in self.world.country_paths or new.actor==new.target):raise ValueError('Choose a different registered target country')
        if old and new.actor!=old.actor:raise ValueError('The source country of an existing relation cannot change; remove it and add a new relation')
        if new.kind=='faction' and not new.detail.strip():raise ValueError('Enter the faction name or localisation key')
        if new.kind=='subject':
            if new.detail not in self.autonomies() and (not old or new.detail!=old.detail):raise ValueError('Choose a defined autonomy level')
            if new.freedom:
                try:amount=Decimal(new.freedom)
                except InvalidOperation:raise ValueError('Freedom level must be between 0 and 1') from None
                if not amount.is_finite() or not 0<=amount<=1:raise ValueError('Freedom level must be between 0 and 1')
        if new.kind=='war' and new.detail not in self.wargoals() and (not old or new.detail!=old.detail):raise ValueError('Choose a defined war goal')
        others=[r for r in self.records() if not old or (r.path,r.start,r.actor)!=(old.path,old.start,old.actor)]
        if old and old.conditional:return
        definite=[r for r in others if not r.conditional]
        for r in definite:
            same=(r.kind,r.actor,r.target)==(new.kind,new.actor,new.target)
            mutual=new.kind in {'war','non_aggression_pact','market_access'} and r.kind==new.kind and (r.actor,r.target)==(new.target,new.actor)
            if same or mutual:raise ValueError('This relation already exists; edit its existing row')
        factions=self.faction_map(definite)
        if new.kind=='member':
            own=next((k for k,v in factions.items() if new.actor in v),None)
            if own is None:raise ValueError('Create a faction for the source country first')
            current=next((k for k,v in factions.items() if new.target in v),None)
            if current and current!=own:raise ValueError('Remove the target country from its existing faction first')
        if new.kind=='faction' and any(new.actor in v for v in factions.values()):raise ValueError('This country already belongs to a faction')
        if new.kind=='subject':
            parents={r.target:r.actor for r in definite if r.kind=='subject' and r.active}
            if new.target in parents:raise ValueError('This country already has an overlord; edit the existing subject row')
            current=new.actor;seen={new.target}
            while current in parents:
                if current in seen:raise ValueError('Subjects cannot form a circular overlord chain')
                seen.add(current);current=parents[current]
            if current in seen:raise ValueError('Subjects cannot form a circular overlord chain')
        if new.kind=='war' and any(new.actor in v and new.target in v for v in factions.values()):raise ValueError('Countries in the same faction cannot start at war')
        if new.kind=='war':
            parents={r.target:r.actor for r in definite if r.kind=='subject' and r.active}
            for child,enemy in [(new.actor,new.target),(new.target,new.actor)]:
                seen=set()
                while child in parents and child not in seen:
                    seen.add(child);child=parents[child]
                    if child==enemy:raise ValueError('An overlord and its subject cannot start at war')

    def _raw(self,new,old=None):
        if old and old.kind==new.kind:
            raw=old.raw;node=parse(raw)[0]
            if new.kind=='faction':return raw[:node.value_start]+quote(new.detail)+raw[node.end:]
            if new.kind in {'subject','war'} and node.children is not None:
                if node.key=='puppet':raw='set_autonomy'+raw[len(node.key):]
                fields={'target':new.target}
                fields.update({'autonomy_state':new.detail,'freedom_level':new.freedom or None} if new.kind=='subject' else {'type':new.detail})
                for key,content in fields.items():raw=patch_field(raw,parse(raw)[0],key,content)
                return raw
            if node.key=='diplomatic_relation':
                for key,content in {'country':new.target,'relation':new.kind,'active':'yes' if new.active else 'no'}.items():raw=patch_field(raw,parse(raw)[0],key,content)
                return raw
        if new.kind=='faction':return 'create_faction = '+quote(new.detail)
        if new.kind=='member':return 'add_to_faction = '+new.target
        if new.kind=='subject':return 'set_autonomy = { target = '+new.target+' autonomy_state = '+new.detail+(' freedom_level = '+new.freedom if new.freedom else '')+' end_wars = no end_civil_wars = no keep_subjects = yes }'
        if new.kind=='war':return 'declare_war_on = { target = '+new.target+' type = '+new.detail+' }'
        if new.active and new.kind in {'guarantee','military_access','market_access'}:
            return {'guarantee':'give_guarantee','military_access':'give_military_access','market_access':'give_market_access'}[new.kind]+' = '+new.target
        return 'diplomatic_relation = { country = '+new.target+' relation = '+new.kind+' active = '+('yes' if new.active else 'no')+' }'

    def add(self,new):
        self._validate(new)
        path=self.world.countries.get(new.target if new.kind=='subject' else new.actor)
        if not path:raise ValueError('Apply country setup before editing diplomacy')
        raw=self._raw(new)
        if new.kind=='subject':raw=new.actor+' = { '+raw+' }'
        text=self.docs.text(path)
        updated=(raw+'\n'+text) if new.kind in {'subject','faction'} else text.rstrip()+'\n'+raw+'\n'
        with self.docs.grouped():self.docs.replace(path,format_changes(path,text,updated))

    def change(self,old,new=None):
        if not old.editable:raise ValueError('This dynamic/shared declaration requires editing its source script')
        text=self.docs.text(old.path)
        if text[old.start:old.end]!=old.raw:raise ValueError('Diplomacy source changed; refresh the list before editing')
        if new and all(getattr(new,key)==getattr(old,key) for key in ('kind','actor','target','detail','freedom','active')):return
        if new:self._validate(new,old)
        raw=self._raw(new,old) if new else ''
        if old.group:
            # Keep the original group filter, ROOT/PREV and all other members.
            # Only this selected country's instance changes.
            raw=('if = { limit = { NOT = { tag = '+old.actor+' } } '+old.raw+' }'+
                 ('\nif = { limit = { tag = '+old.actor+' } '+raw+' }' if raw else ''))
        if old.kind=='faction' and new is None:
            records=self.records();faction=self.faction_map(records).get(old.actor,{old.actor})
            members=[r for r in records if r.kind=='member' and not r.conditional and r.actor in faction]
            if members:raise ValueError('Remove the faction memberships before deleting its leader declaration')
        updated=text[:old.start]+raw+text[old.end:]
        with self.docs.grouped():self.docs.replace(old.path,format_changes(old.path,text,updated))
