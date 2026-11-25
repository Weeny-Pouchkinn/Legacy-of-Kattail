"""Stage a masked EU4 terrain import; apply only an inspected, hash-guarded stage.

Province geometry, coastlines and all pixels outside the mask are protected.
Run without --apply first. The source mod is always read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'legacy_of_kattail_painter'))
from model import parse, child, scalar, read_text
from source_io import encode_source, write_changes


# Semantic conversion between the active native terrain tables, not RGB colors.
GRAPHICS = {0:0, 1:17, 2:11, 3:3, 4:0, 5:0, 6:20, 7:7, 8:17, 9:9,
            10:5, 11:5, 12:1, 13:1, 14:1, 15:15, 16:16, 17:15, 19:3,
            20:0, 21:5, 22:0, 23:17, 24:17, 35:0, 130:0, 254:21, 255:4}
TYPES = {'grasslands':'plains', 'farmlands':'plains', 'savannah':'plains',
         'steppe':'plains', 'drylands':'plains', 'coastline':'plains',
         'woods':'forest', 'forest':'forest', 'hills':'hills', 'highlands':'hills',
         'mountain':'mountain', 'impassable_mountains':'mountain', 'glacier':'mountain',
         'jungle':'jungle', 'marsh':'marsh', 'desert':'desert', 'coastal_desert':'desert',
         'urban':'urban', 'ocean':'ocean', 'inland_ocean':'ocean'}


def digest(blob):return hashlib.sha256(blob).hexdigest()


def image_array(blob):
    with Image.open(io.BytesIO(blob)) as im:return np.array(im)


def patch_bmp(blob, pixels, mask):
    """Patch only selected native BMP pixels; preserve every header/palette byte."""
    if blob[:2] != b'BM':raise ValueError('Expected a BMP')
    offset=struct.unpack_from('<I',blob,10)[0]
    width,height=struct.unpack_from('<ii',blob,18)
    bits=struct.unpack_from('<H',blob,28)[0];compression=struct.unpack_from('<I',blob,30)[0]
    if compression or bits not in {8,24}:raise ValueError('Require uncompressed 8/24-bit BMP')
    if mask.shape != (abs(height),width) or pixels.shape[:2] != mask.shape:raise ValueError('BMP/mask dimensions differ')
    stride=((width*bits+31)//32)*4;out=bytearray(blob)
    rows=np.ndarray((abs(height),stride),np.uint8,buffer=out,offset=offset)
    if height>0:rows=rows[::-1]
    if bits==8:rows[:,:width][mask]=pixels[mask]
    else:rows[:,:width*3].reshape(abs(height),width,3)[mask]=pixels[mask][:,::-1]
    result=bytes(out)
    expected=image_array(blob);expected[mask]=pixels[mask]
    if not np.array_equal(image_array(result),expected):raise AssertionError('BMP patch/readback mismatch')
    return result


def patch_colormap(blob, rgb, mask):
    """Patch RGB of the active uncompressed BGRA DDS, preserving city-light alpha."""
    if blob[:4]!=b'DDS ' or len(blob)<128:raise ValueError('Expected a DDS')
    height,width,pitch=struct.unpack_from('<III',blob,12)
    mipmaps=struct.unpack_from('<I',blob,28)[0]
    flags,fourcc,bits,red,green,blue,alpha=struct.unpack_from('<7I',blob,80)
    if fourcc or bits!=32 or (red,green,blue,alpha)!=(0xff0000,0xff00,0xff,0xff000000) or mipmaps not in {0,1}:
        raise ValueError('Require the native single-mip, uncompressed BGRA colormap')
    if mask.shape!=(height,width) or rgb.shape!=(height,width,3):raise ValueError('DDS/mask dimensions differ')
    if pitch!=width*4 or len(blob)!=128+pitch*height:raise ValueError('Unexpected DDS row layout')
    out=bytearray(blob);pixels=np.ndarray((height,width,4),np.uint8,buffer=out,offset=128)
    pixels[:,:,:3][mask]=rgb[mask][:,::-1]
    result=bytes(out);before=image_array(blob);after=image_array(result)
    if not np.array_equal(before[:,:,3],after[:,:,3]) or not np.array_equal(before[~mask],after[~mask]):
        raise AssertionError('Colormap alpha/exterior changed')
    if not np.array_equal(after[:,:,:3][mask],rgb[mask]):raise AssertionError('Colormap readback mismatch')
    return result


def erode(mask):
    out=np.zeros_like(mask)
    out[1:-1,1:-1]=mask[1:-1,1:-1]&mask[:-2,1:-1]&mask[2:,1:-1]&mask[1:-1,:-2]&mask[1:-1,2:]
    return out


def inward_blend(mask,width=4):
    if width<1:raise ValueError('Blend width must be positive')
    weight=np.zeros(mask.shape,np.float32);inner=mask.copy()
    for depth in range(1,width+1):
        weight[inner]=depth/width;inner=erode(inner)
    return weight


def half_mask(mask):
    h,w=mask.shape
    if h%2 or w%2:raise ValueError('Map dimensions must be even')
    return mask.reshape(h//2,2,w//2,2).all(axis=(1,3))


def half_weight(weight):
    h,w=weight.shape
    return weight.reshape(h//2,2,w//2,2).min(axis=(1,3))


def blend(old,new,weight):
    if old.shape!=new.shape:raise ValueError('Source/target image dimensions differ')
    if old.ndim==3:weight=weight[:,:,None]
    return np.rint(old.astype(np.float32)*(1-weight)+new.astype(np.float32)*weight).clip(0,255).astype(np.uint8)


def raster(provinces,definition):
    table={};lookup=np.zeros(1<<24,np.uint16);colors=set()
    for line in definition.decode('utf-8-sig').splitlines():
        fields=line.split(';')
        if not fields[0].isdigit():continue
        pid,r,g,b=map(int,fields[:4]);key=r<<16|g<<8|b
        if pid in table or key in colors or pid>65535:raise ValueError('Duplicate/unsupported province definition')
        colors.add(key);table[pid]=fields;lookup[key]=pid
    rgb=image_array(provinces).astype(np.uint32);packed=rgb[:,:,0]<<16|rgb[:,:,1]<<8|rgb[:,:,2]
    if not set(map(int,np.unique(packed))).issubset(colors):raise ValueError('Undefined province colors')
    return lookup[packed],table


def terrain_tables(text):
    roots=parse(text);indices={};overrides={}
    for node in child(roots,'terrain').children:
        color=child(node.children,'color');kind=scalar(text,node.children,'type')
        for n in color.children if color else []:indices[int(n.key)]=kind
    for node in child(roots,'categories').children:
        override=child(node.children,'terrain_override')
        for n in override.children if override else []:
            pid=int(n.key)
            if pid in overrides and overrides[pid]!=node.key:raise ValueError('Conflicting EU4 terrain overrides')
            overrides[pid]=node.key
    return indices,overrides


def province_types(source_ids,source_terrain,edited_ids,selected_mask,indices,overrides):
    result={}
    for pid in map(int,np.unique(source_ids[selected_mask])):
        kind=overrides.get(pid)
        if kind is None:
            values,counts=np.unique(source_terrain[source_ids==pid],return_counts=True)
            votes=Counter()
            for index,count in zip(values,counts):votes[indices[int(index)]]+=int(count)
            kind=max(sorted(votes),key=votes.get)
        if kind not in TYPES:raise ValueError(f'No approved terrain mapping for EU4 {kind}')
        result[pid]=TYPES[kind]
    counts=np.bincount(edited_ids.ravel());covered=np.bincount(edited_ids[selected_mask],minlength=len(counts))
    candidates=[pid for pid in np.flatnonzero(covered) if covered[pid]*2>=counts[pid]]
    rows=[]
    for pid in candidates:
        source,area=np.unique(source_ids[selected_mask&(edited_ids==pid)],return_counts=True);votes=Counter()
        for spid,count in zip(source,area):votes[result[int(spid)]]+=int(count)
        kind=max(sorted(votes),key=votes.get)
        if kind=='ocean':raise ValueError('Land import selected an EU4 ocean terrain')
        rows.append({'province':int(pid),'terrain':kind,'covered_pixels':int(covered[pid]),'province_pixels':int(counts[pid]),'votes':dict(votes)})
    return rows


def run(target,source,mask_path,stage,apply=False):
    target=Path(target).resolve();source=Path(source).resolve();stage=Path(stage).resolve()
    if source==target:raise ValueError('Source and target must differ')
    approved=None
    if apply:
        if not (stage/'audit.json').is_file():raise ValueError('Stage and inspect a dry run before --apply')
        approved=json.loads((stage/'audit.json').read_text(encoding='utf-8'))
        if approved.get('applied'):raise ValueError('This stage has already been applied')
    inputs={}
    def read(root,name):
        path=root/name;blob=path.read_bytes();inputs[str(path)]=digest(blob);return blob
    mask_blob=Path(mask_path).read_bytes();inputs[str(Path(mask_path).resolve())]=digest(mask_blob)
    with Image.open(io.BytesIO(mask_blob)) as im:mask=np.all(np.asarray(im.convert('RGB'))==0,axis=2)
    if not mask.any():raise ValueError('No exact black mask pixels')
    old={name:read(target,name) for name in ('map/terrain.bmp','map/heightmap.bmp','map/rivers.bmp','map/world_normal.bmp','map/terrain/colormap_rgb_cityemissivemask_a.dds','map/definition.csv')}
    hp,defs=raster(read(target,'map/provinces.bmp'),old['map/definition.csv'])
    ep,_=raster(read(source,'map/provinces.bmp'),read(source,'map/definition.csv'))
    if hp.shape!=ep.shape or hp.shape!=mask.shape:raise ValueError('Mask and province rasters must match without crop/scale')
    land=np.zeros(int(hp.max())+1,bool)
    for pid,row in defs.items():land[pid]=row[4]=='land'
    hl=land[hp];default=read(source,'map/default.map').decode('utf-8-sig');roots=parse(default);water=set()
    for key in ('sea_starts','lakes'):
        node=child(roots,key)
        if node:water.update(int(n.key) for n in node.children)
    el=~np.isin(ep,list(water));compatible=mask&hl&el
    if not compatible.any():raise ValueError('Mask contains no compatible land')
    st=image_array(read(source,'map/terrain.bmp'));ht=image_array(old['map/terrain.bmp'])
    unknown=set(map(int,np.unique(st[compatible])))-GRAPHICS.keys()
    if unknown:raise ValueError('Unmapped source graphic indices: '+str(unknown))
    # Verify the active source and target native semantic tables used by the mapping.
    source_text=read(source,'map/terrain.txt').decode('utf-8-sig');indices,overrides=terrain_tables(source_text)
    target_graphics={};target_categories=set()
    for path in sorted((target/'common/terrain').glob('*.txt')):
        text=read(target,path.relative_to(target).as_posix()).decode('utf-8-sig');nodes=parse(text)
        categories=child(nodes,'categories')
        if categories:target_categories.update(n.key for n in categories.children)
        table=child(nodes,'terrain')
        for n in table.children if table else []:
            colors=child(n.children,'color')
            for c in colors.children if colors else []:target_graphics[int(c.key)]=scalar(text,n.children,'type')
    converted=ht.copy()
    for index in map(int,np.unique(st[compatible])):
        dest=GRAPHICS[index]
        if dest not in target_graphics:raise ValueError(f'Undefined target graphical terrain {dest}')
        converted[compatible&(st==index)]=dest
    # Preserve the shoreline rim and the native land/water threshold (WATER_HEIGHT=9.5).
    height_mask=compatible&erode(hl);weight=inward_blend(height_mask)
    source_height=image_array(read(source,'map/heightmap.bmp'))
    desired_height=blend(image_array(old['map/heightmap.bmp']),np.maximum(source_height,96),weight)
    changes={'map/terrain.bmp':patch_bmp(old['map/terrain.bmp'],converted,compatible),
             'map/heightmap.bmp':patch_bmp(old['map/heightmap.bmp'],desired_height,height_mask)}
    small=half_mask(compatible);small_weight=half_weight(inward_blend(compatible))
    summer=image_array(read(source,'map/terrain/colormap_summer.dds'))[:,:,:3]
    colormap=image_array(old['map/terrain/colormap_rgb_cityemissivemask_a.dds'])
    color=blend(colormap[:,:,:3],summer,small_weight)
    changes['map/terrain/colormap_rgb_cityemissivemask_a.dds']=patch_colormap(old['map/terrain/colormap_rgb_cityemissivemask_a.dds'],color,small)
    normal=image_array(old['map/world_normal.bmp']);source_normal=image_array(read(source,'map/world_normal.bmp'))
    changes['map/world_normal.bmp']=patch_bmp(old['map/world_normal.bmp'],blend(normal,source_normal,small_weight),small)
    source_rivers=image_array(read(source,'map/rivers.bmp'));rivers=image_array(old['map/rivers.bmp'])
    with Image.open(io.BytesIO(old['map/rivers.bmp'])) as a,Image.open(source/'map/rivers.bmp') as b:
        if a.getpalette()!=b.getpalette():raise ValueError('River palettes differ; an explicit conversion is required')
    river_delta=int(np.count_nonzero((source_rivers!=rivers)&mask))
    if river_delta:raise ValueError('Rivers differ inside mask; stage explicit river topology handling before import')
    types=province_types(ep,st,hp,compatible,indices,overrides);by_id={r['province']:r for r in types}
    lines=old['map/definition.csv'].decode('utf-8-sig').splitlines(keepends=True)
    for i,line in enumerate(lines):
        fields=line.split(';')
        if not fields[0].isdigit() or int(fields[0]) not in by_id:continue
        row=by_id[int(fields[0])];row['old_terrain']=fields[6]
        if row['terrain'] not in target_categories:raise ValueError('Undefined target gameplay terrain')
        fields[6]=row['terrain'];lines[i]=';'.join(fields)
    changes['map/definition.csv']=encode_source(''.join(lines),old['map/definition.csv'])
    protected={}
    for name in ['map/provinces.bmp','map/adjacencies.csv','map/railways.txt','map/supply_nodes.txt','map/buildings.txt']:
        protected[name]=digest((target/name).read_bytes())
    for folder in ('history/states','map/strategicregions','map/supplyareas'):
        for p in (target/folder).glob('*.txt'):protected[p.relative_to(target).as_posix()]=digest(p.read_bytes())
    stage.mkdir(parents=True,exist_ok=True)
    manifest={}
    for name,new in changes.items():
        if new==old[name]:continue
        manifest[name]={'before':digest(old[name]),'after':digest(new),'bytes':len(new)}
    if apply and (manifest!=approved['files'] or inputs!=approved['inputs']):
        raise ValueError('Inputs/output changed since the inspected stage; repeat the dry run')
    for name in manifest:
        p=stage/'files'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(changes[name])
    y,x=np.nonzero(mask);bbox=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
    audit={'mask':str(Path(mask_path).resolve()),'mask_sha256':digest(mask_blob),'bbox':bbox,'black_pixels':int(mask.sum()),
           'compatible_land_pixels':int(compatible.sum()),'preserved_target_water_pixels':int((mask&~hl).sum()),
           'preserved_eu4_inland_water_on_hoi4_land':int((mask&hl&~el).sum()),'river_changed_pixels':river_delta,
           'province_types':types,'terrain_changes':dict(Counter(r['terrain'] for r in types if r['terrain']!=r['old_terrain'])),
           'files':manifest,'inputs':inputs,'protected':protected,'applied':False}
    # Compact native previews, using the exact staged arrays and mask outline.
    box=(max(0,bbox[0]-30),max(0,bbox[1]-30),min(mask.shape[1],bbox[2]+30),min(mask.shape[0],bbox[3]+30))
    tiles=[]
    for name in ('map/terrain.bmp','map/heightmap.bmp','map/terrain/colormap_rgb_cityemissivemask_a.dds'):
        for blob in (old[name],changes[name]):
            with Image.open(io.BytesIO(blob)) as im:
                scale=mask.shape[1]/im.width;crop=tuple(round(v/scale) for v in box)
                tiles.append(im.convert('RGB').crop(crop).resize((520,400),Image.Resampling.NEAREST))
    preview=Image.new('RGB',(1040,3*428),'#181c24');draw=ImageDraw.Draw(preview)
    for row,label in enumerate(('Graphical terrain','Heightmap','Colormap (RGB; native alpha retained)')):
        for col in range(2):
            draw.text((col*520+8,row*428+6),label+(' — BEFORE' if col==0 else ' — STAGED'),fill='white')
            preview.paste(tiles[row*2+col],(col*520,row*428+28))
    preview.save(stage/'preview.png')
    if apply:
        for path,sha in inputs.items():
            if digest(Path(path).read_bytes())!=sha:raise ValueError('Input changed during import: '+path)
        count={name:(old[name],changes[name]) for name in manifest}
        backup=write_changes(target,count,label='masked_eu4_terrain');audit['applied']=True;audit['backup']=str(backup)
        for name,sha in protected.items():
            if digest((target/name).read_bytes())!=sha:raise AssertionError('Protected source changed: '+name)
    (stage/'audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ('black_pixels','compatible_land_pixels','preserved_eu4_inland_water_on_hoi4_land','river_changed_pixels','terrain_changes','files','applied')},indent=2))
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,default=ROOT);parser.add_argument('--eu4',type=Path,required=True)
    parser.add_argument('--mask',type=Path,required=True);parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    run(args.target,args.eu4,args.mask,args.stage,args.apply)
