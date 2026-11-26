"""Dry-run or repair malformed painter output proven by native Save backups.

Only whitespace is changed. Guarded writes preserve encoding/BOM/newlines and
make exact backups. Unresolved provenance or unsupported syntax is reported.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy_of_kattail_painter'))
from model import Documents,parse
from script_format import changed_paths,format_paths,index_nodes,script_path,tokens
from source_io import confined,encode_source,write_changes


def digest(blob):return hashlib.sha256(blob).hexdigest()


def structural(text):
    def node(n):
        return (n.key,n.op,tuple(node(c) for c in n.children)) if n.children is not None else (n.key,n.op,tokens(text[n.value_start:n.end]))
    return tuple(node(n) for n in parse(text))


def audit(root):
    root=Path(root).resolve();records=[];blobs={};current={};notes=[]
    manifests=sorted((root/'legacy_of_kattail_painter/backups').glob('save_*/manifest.json'))
    for manifest in manifests:
        for relative,entry in json.loads(manifest.read_text(encoding='utf-8')).items():
            if not script_path(relative):continue
            records.append((relative,entry,manifest.parent.name))
            backup=confined(manifest.parent,relative)
            if entry.get('before') and backup.is_file():
                blob=backup.read_bytes()
                if digest(blob)==entry['before']:blobs[entry['before']]=blob
            path=confined(root,relative)
            if relative not in current and path.is_file():
                current[relative]=path.read_bytes();blobs[digest(current[relative])]=current[relative]
    # A previous formatting repair is a byte witness for an old Save revision,
    # not additional authorization to reformat new/handwritten definitions.
    for manifest in (root/'legacy_of_kattail_painter/backups').glob('painter_script_formatting_*/manifest.json'):
        for relative,entry in json.loads(manifest.read_text(encoding='utf-8')).items():
            if not script_path(relative) or not entry.get('before'):continue
            path=confined(manifest.parent,relative)
            if path.is_file():
                blob=path.read_bytes()
                if digest(blob)==entry['before']:blobs[entry['before']]=blob
    owned=defaultdict(set);resolved=0;unresolved=Counter();parse_failures={}
    for relative,entry,label in records:
        before=blobs.get(entry.get('before')) if entry.get('before') else b''
        after=blobs.get(entry.get('after'))
        if before is None or after is None:unresolved[relative]+=1;continue
        try:paths=changed_paths(Documents._decode(before),Documents._decode(after))
        except ValueError as exc:parse_failures[relative]=str(exc);continue
        owned[relative].update(paths);resolved+=1
    changes={};files=[];missing_addresses=0
    for relative,paths in sorted(owned.items()):
        if relative not in current:continue
        before=current[relative];source=Documents._decode(before)
        try:
            indexed=index_nodes(source);missing_addresses+=len(paths-indexed.keys())
            updated=format_paths(source,paths,only_defective=True)
            if source==updated:continue
            after=encode_source(updated,before)
            # Independent of layout selection: order, operators, values, strings
            # and exact comment tokens must agree before any write is authorized.
            assert tokens(source)==tokens(Documents._decode(after)),relative
            assert structural(source)==structural(Documents._decode(after)),relative
        except ValueError as exc:
            notes.append({'path':relative,'reason':str(exc)});continue
        changes[relative]=(before,after)
        files.append({'path':relative,'before_sha256':digest(before),'after_sha256':digest(after),
                      'owned_paths_found':len(paths&indexed.keys()),'tokens':len(tokens(source)),
                      'bom_preserved':before.startswith(b'\xef\xbb\xbf')==after.startswith(b'\xef\xbb\xbf')})
    report={'save_manifests':len(manifests),'structured_save_records':len(records),
            'resolved_provenance_records':resolved,'provenance_files':len(owned),
            'unresolved_records':sum(unresolved.values()),'unresolved_files':sorted(unresolved),
            'old_addresses_no_longer_present':missing_addresses,'provenance_parse_failures':parse_failures,
            'skipped':notes,'changed_files':len(changes),'files':files,
            'checks':'Exact token stream including comments; ordered parsed structure; encoding/BOM; guarded source hashes'}
    return changes,report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--apply',action='store_true',help='Apply after exact token/structure checks, with guarded backups')
    parser.add_argument('--report',type=Path,help='JSON report path (default: agent_memory/painter_script_formatting/repair.json)')
    args=parser.parse_args();changes,report=audit(args.root)
    report['applied']=args.apply;report['backup']=None
    if args.apply:
        report['backup']=str(write_changes(args.root,changes,label='painter_script_formatting')) if changes else None
        for relative,(_,expected) in changes.items():assert confined(args.root,relative).read_bytes()==expected,relative
    destination=args.report or args.root/'modding_documentation/agent_memory/painter_script_formatting/repair.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ['save_manifests','structured_save_records','resolved_provenance_records','provenance_files','changed_files','applied','backup']},indent=2))
    print('Skipped current sources:',len(report['skipped']),'old parse failures:',len(report['provenance_parse_failures']))


if __name__=='__main__':main()
