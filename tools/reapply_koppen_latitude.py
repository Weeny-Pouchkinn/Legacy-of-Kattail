"""Reapply recognised main-planet Koppen classes with geographic seasons.

Dry run first; --apply requires an unchanged inspected audit and writes only the
changed native strategic-region weather blocks through the guarded backup writer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy_of_kattail_painter'))
from model import World
from character_model import CharacterStore
from demographics import MapCatalogStore
from geography_model import GeographyStore, LATITUDE_TRANSITION
from source_io import encode_source, write_changes


def sha(data):return hashlib.sha256(data).hexdigest()


def run(root,audit_path,apply=False):
    root=Path(root).resolve();audit_path=Path(audit_path).resolve()
    prior=json.loads(audit_path.read_text()) if audit_path.exists() else None
    if prior and prior['applied']:raise ValueError('This audit already records an applied run; choose a new audit path')
    if apply and not prior:raise ValueError('Run and inspect a dry run first')
    world=World(root);characters=CharacterStore(world);geo=GeographyStore(world,characters,MapCatalogStore(world,characters))
    paths=sorted(set(world.files)|{'map/provinces.bmp','map/definition.csv','map/heightmap.bmp','map/terrain.bmp','map/rivers.bmp','map/trees.bmp','map/world_normal.bmp','map/terrain/colormap_rgb_cityemissivemask_a.dds'})
    inputs={p:sha((root/p).read_bytes()) for p in paths}
    input_digest=sha(json.dumps(inputs,sort_keys=True).encode())
    presets=geo.preset_regions();rows=[];skipped=[]
    for rid,(code,old_hemi) in sorted(presets.items()):
        try:latitude=geo.region_latitude(rid)
        except ValueError as exc:
            skipped.append({'region':rid,'code':code,'reason':str(exc)});continue
        expected=geo.climate_at_region(rid,code)
        changed=geo.weather_signature(geo.region(rid)['weather'])!=geo.weather_signature(expected)
        if changed:geo.paint_climate(rid,code,account_latitude=True)
        rows.append({'region':rid,'code':code,'before_hemisphere':old_hemi,'hemisphere':'South' if latitude<0 else 'North',
                     'latitude':latitude,'temperature_smoothed':abs(latitude)<LATITUDE_TRANSITION,'changed':changed})
    changes={p:((root/p).read_bytes(),encode_source(text,(root/p).read_bytes())) for p,text in world.docs.drafts.items()}
    changes={p:pair for p,pair in changes.items() if pair[0]!=pair[1]}
    files={p:{'before':sha(a),'after':sha(b)} for p,(a,b) in changes.items()}
    if apply and (prior['input_digest']!=input_digest or prior['files']!=files or prior['regions']!=rows):raise ValueError('Sources changed after the dry run; inspect a new dry run')
    audit={'applied':False,'equator_y':geo.planet_frame().equator,'main_planet_top':geo.planet_frame().top,
           'main_planet_bottom':geo.planet_frame().bottom,'transition_degrees':LATITUDE_TRANSITION,
           'recognised_presets':len(presets),'regions':rows,'skipped_other_bodies':skipped,'files':files,'input_digest':input_digest}
    if apply:
        for p,s in inputs.items():
            if sha((root/p).read_bytes())!=s:raise ValueError('A source changed during preparation: '+p)
        audit['backup']=str(write_changes(root,changes,label='koppen_latitude')) if changes else None
        for p,s in inputs.items():
            expected=files[p]['after'] if p in files else s
            if sha((root/p).read_bytes())!=expected:raise AssertionError('Unexpected native source change: '+p)
        fresh=World(root);c=CharacterStore(fresh);g=GeographyStore(fresh,c,MapCatalogStore(fresh,c));recognised=g.preset_regions()
        for row in rows:
            rid=row['region'];assert recognised[rid]==(row['code'],row['hemisphere'])
            assert g.weather_signature(g.region(rid)['weather'])==g.weather_signature(g.climate_at_region(rid,row['code']))
        audit.update(applied=True,protected_sources_unchanged=len(inputs)-len(files),native_readback='all reapplied classes/hemispheres and exact weather signatures match')
    audit_path.parent.mkdir(parents=True,exist_ok=True);audit_path.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'applied':audit['applied'],'recognised':len(presets),'main_planet':len(rows),'changed_files':len(files),
                      'hemisphere_corrections':sum(r['before_hemisphere']!=r['hemisphere'] for r in rows),
                      'smoothed_regions':sum(r['temperature_smoothed'] for r in rows),'other_bodies_unchanged':len(skipped),
                      'equator_y':audit['equator_y']},indent=2))
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--audit',type=Path,default=ROOT/'modding_documentation/agent_memory/map_labels_latitude_export/reapplication.json')
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    run(args.root,args.audit,args.apply)
