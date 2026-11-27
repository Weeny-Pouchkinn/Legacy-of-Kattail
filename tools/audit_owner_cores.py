"""Dry-run or apply missing owner cores, preserving SIL's four Katown exceptions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy_of_kattail_painter'))
from model import World,child,parse,scalar,value
from script_format import tokens
from source_io import write_changes

# Verified native SIL demilitarized states with KTW cores, not a generic DMZ rule.
KATOWN_EXCEPTIONS={34:'SIL',36:'SIL',44:'SIL',45:'SIL'}


def without_owner_core(text,owner):
    history=child(child(parse(text),'state').children,'history')
    for node in reversed(history.children):
        if node.children is None and node.key in {'add_core_of','remove_core_of'} and value(text,node).strip('"')==owner:
            text=text[:node.start]+text[node.end:]
    return tokens(text)


def build(root):
    world=World(root);rows=[];owned=0;excluded=[]
    for sid,tag in KATOWN_EXCEPTIONS.items():
        relations=world.state_relations(sid);text,nodes=world.state_nodes(sid);history=child(nodes,'history')
        if relations['owner']!=tag or scalar(text,history.children,'set_demilitarized_zone')!='yes' or 'KTW' not in relations['cores']:
            raise ValueError(f'Katown exception {sid} no longer matches its verified SIL/DMZ/KTW setup')
        path=world.states[sid].path
        excluded.append({'id':sid,'path':path,'owner':tag,'cores':sorted(relations['cores']),
                         'sha256':hashlib.sha256((Path(root)/path).read_bytes()).hexdigest()})
    before_relations={}
    for sid,state in sorted(world.states.items()):
        relations=world.state_relations(sid);tag=relations['owner']
        if not tag:continue
        owned+=1
        if sid in KATOWN_EXCEPTIONS or tag in relations['cores']:continue
        before_relations[sid]=relations
        world.set_relation_draft(sid,tag,'core',True)
        rows.append({'state':sid,'name':world.label(state.name),'owner':tag,'path':state.path})
    world.docs.format_script_drafts();changes={}
    for row in rows:
        path=row['path'];sid=row['state'];tag=row['owner']
        before=world.docs.snapshots[path];after=world.docs.binary(path)
        old=world.docs._decode(before);new=world.docs.text(path);relations=world.state_relations(sid)
        assert without_owner_core(old,tag)==without_owner_core(new,tag),path
        assert relations['owner']==tag and relations['claims']==before_relations[sid]['claims'],path
        assert relations['cores']==before_relations[sid]['cores']|{tag},path
        row.update(before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest())
        changes[path]=(before,after)
    return changes,{'owned_states':owned,'changed_states':len(rows),'files':rows,'exceptions':excluded,
                    'checks':'All non-owner-core tokens/comments/order identical; owner and claims unchanged; exactly the owner added to cores; guarded hashes/backup'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--report',type=Path,default=ROOT/'modding_documentation/agent_memory/core_audit/repair.json')
    args=parser.parse_args();changes,report=build(args.root);report['applied']=args.apply;report['backup']=None
    if args.apply and changes:
        report['backup']=str(write_changes(args.root,changes,label='owner_core_audit'))
        for path,(_,expected) in changes.items():assert (args.root/path).read_bytes()==expected,path
    for row in report['exceptions']:
        assert hashlib.sha256((args.root/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ['owned_states','changed_states','applied','backup']},indent=2))


if __name__=='__main__':main()
