"""Dry-run or flatten saved EaW texture paths, active references and credit destinations."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy_of_kattail_painter'))
from country_model import EAW_TEXTURES,EAW_CREDITS,flat_eaw_destination
from model import Documents,TOKEN
from source_io import confined,encode_source,write_changes


def normalized(path):return str(PurePosixPath(path.replace('\\','/'))).casefold()


def rewrite_literals(text,mapping):
    def replacement(match):
        token=match[0]
        quoted=token.startswith('"') and token.endswith('"')
        path=token[1:-1] if quoted else token
        target=mapping.get(normalized(path))
        return ('"'+target+'"' if quoted else target) if target else token
    return TOKEN.sub(replacement,text)


def build(root):
    root=Path(root).resolve();base=confined(root,EAW_TEXTURES);reserved={};mapping={};assets=[]
    def read(path):
        if path in reserved:return reserved[path]
        file=confined(root,path)
        return file.read_bytes() if file.is_file() else None
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.tga','.dds'}:continue
        if path.parent==base:continue
        old=path.relative_to(root).as_posix();blob=confined(root,old).read_bytes()
        destination=flat_eaw_destination(path.name,blob,read);reserved[destination]=blob
        mapping[normalized(old)]=destination
        assets.append({'old':old,'new':destination,'sha256':hashlib.sha256(blob).hexdigest()})
    changes={}
    for path,blob in reserved.items():
        file=confined(root,path);original=file.read_bytes() if file.is_file() else None
        if original!=blob:changes[path]=(original,blob)
    references=[]
    for folder in ('common','history','events','interface','portraits','map','localisation'):
        for path in sorted((root/folder).rglob('*')):
            if not path.is_file() or path.suffix.lower() not in {'.txt','.gfx','.gui','.mod','.lua','.csv','.yml'}:continue
            original=path.read_bytes();text=Documents._decode(original)
            updated=rewrite_literals(text,mapping)
            # Refuse dangling nested EaW references even if their source file is missing.
            for match in TOKEN.finditer(updated):
                token=match[0].strip('"');normal=normalized(token);prefix=EAW_TEXTURES.casefold()+'/'
                if normal.startswith(prefix) and '/' in normal[len(prefix):]:
                    raise ValueError('Unresolved nested EaW reference in '+path.relative_to(root).as_posix()+': '+token)
            if updated==text:continue
            expected=tuple(rewrite_literals(m[0],mapping) for m in TOKEN.finditer(text))
            assert tuple(m[0] for m in TOKEN.finditer(updated))==expected,path
            relative=path.relative_to(root).as_posix();changes[relative]=(original,encode_source(updated,original))
            references.append(relative)
    credit=confined(root,EAW_CREDITS)
    if credit.is_file():
        original=credit.read_bytes();text=Documents._decode(original)
        def replace_credit(match):
            target=mapping.get(normalized(match[2]))
            return match[1]+target if target else match[0]
        updated=re.sub(r'^(Mod texture: )([^\r\n]+)',replace_credit,text,flags=re.M)
        if updated!=text:changes[EAW_CREDITS]=(original,encode_source(updated,original))
    # Reference updates and flat copies precede deletion of superseded textures.
    for asset in assets:changes[asset['old']]=(confined(root,asset['old']).read_bytes(),None)
    report={'textures':assets,'migrated_textures':len(assets),'script_files':references,
            'credits_updated':EAW_CREDITS in changes,'changed_files':len(changes),
            'checks':'Exact image bytes; only mapped path literals and credit Mod texture lines change; guarded backups/readback'}
    return changes,report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--report',type=Path,default=ROOT/'modding_documentation/agent_memory/eaw_flat_paths/repair.json')
    args=parser.parse_args();changes,report=build(args.root);report['applied']=args.apply;report['backup']=None
    if args.apply and changes:
        report['backup']=str(write_changes(args.root,changes,label='eaw_flat_paths'))
        for path,(_,expected) in changes.items():
            file=confined(args.root,path)
            assert file.read_bytes()==expected if expected is not None else not file.exists(),path
        base=confined(args.root,EAW_TEXTURES)
        for directory in sorted((p for p in base.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
            if not directory.resolve().is_relative_to(base.resolve()):continue
            try:directory.rmdir()  # Empty only; never recursively remove source directories.
            except OSError:pass
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
