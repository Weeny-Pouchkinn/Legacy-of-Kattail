"""Stage native-style relief, graphical/gameplay agreement and tree coverage.

Requires NumPy, Pillow and SciPy. Uses the original masked-import audit and
backups, and never changes province geometry or pixels outside its selection.
"""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import (gaussian_filter, binary_dilation, binary_erosion,
                           distance_transform_edt)
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from import_masked_eu4_terrain import (ROOT, digest, image_array, patch_bmp,
                                      patch_colormap, raster, half_mask)
sys.path.insert(0,str(ROOT/'legacy_of_kattail_painter'))
from model import parse, child, scalar
from source_io import encode_source, write_changes


def smooth_weight(mask,width=48):
    x=np.clip(distance_transform_edt(mask)/width,0,1)
    return x*x*x*(10+x*(-15+6*x))


def poisson_offset(styled,base,mask):
    """Harmonic low-frequency correction with native heights as the boundary."""
    if mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any():
        raise ValueError('Poisson domain needs an unedited outer rim')
    ids=np.full(mask.shape,-1,np.int32);ids[mask]=np.arange(mask.sum());yy,xx=np.nonzero(mask)
    rows=[];cols=[];values=[];rhs=np.zeros(mask.sum());delta=base-styled
    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
        neighbor=ids[yy+dy,xx+dx];inside=neighbor>=0
        rows.extend(ids[yy[inside],xx[inside]]);cols.extend(neighbor[inside]);values.extend([-1]*int(inside.sum()))
        rhs[~inside]+=delta[yy[~inside]+dy,xx[~inside]+dx]
    rows.extend(range(mask.sum()));cols.extend(range(mask.sum()));values.extend([4]*int(mask.sum()))
    matrix=coo_matrix((values,(rows,cols)),shape=(mask.sum(),mask.sum())).tocsr()
    result=styled.copy();result[mask]+=spsolve(matrix,rhs)
    return result


def matched_height(original,source,mask,land,width=48):
    ring=binary_dilation(mask,iterations=45)&~binary_dilation(mask,iterations=5)&(original>=96)&(source>=96)&(original<180)
    smooth=gaussian_filter(source.astype(float),2)
    x=smooth[ring]-95;y=original[ring]-95
    if len(x)<50 or np.dot(x,x)==0:raise ValueError('Insufficient native relief samples')
    scale=float(np.clip(np.dot(x,y)/np.dot(x,x),.2,1))
    styled=95+scale*(smooth-95);domain=mask&binary_erosion(land)
    corrected=poisson_offset(styled,original,domain);weight=smooth_weight(domain,width)
    result=np.rint(original+weight*(corrected-original)).clip(0,255)
    result[domain]=np.maximum(result[domain],96);result[~domain]=original[~domain]
    return result.astype(np.uint8),scale,domain


def footprint_mask(mask,shape):
    """Only select lower-resolution cells wholly contained in the native mask."""
    h,w=shape;H,W=mask.shape
    y0=np.floor(np.arange(h)*H/h).astype(int);y1=np.ceil((np.arange(h)+1)*H/h).astype(int)
    x0=np.floor(np.arange(w)*W/w).astype(int);x1=np.ceil((np.arange(w)+1)*W/w).astype(int)
    integral=np.pad(mask.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
    count=integral[np.ix_(y1,x1)]-integral[np.ix_(y0,x1)]-integral[np.ix_(y1,x0)]+integral[np.ix_(y0,x0)]
    return count==(y1-y0)[:,None]*(x1-x0)[None,:]


def sample(array,shape):
    h,w=shape;H,W=array.shape[:2]
    ys=np.minimum(H-1,((np.arange(h)+.5)*H/h).astype(int));xs=np.minimum(W-1,((np.arange(w)+.5)*W/w).astype(int))
    return array[np.ix_(ys,xs)]


def native_graphics(root):
    types={};categories=set()
    for p in sorted((root/'common/terrain').glob('*.txt')):
        text=p.read_text(encoding='utf-8-sig');nodes=parse(text);cats=child(nodes,'categories')
        if cats:categories.update(n.key for n in cats.children)
        table=child(nodes,'terrain')
        for node in table.children if table else []:
            color=child(node.children,'color');kind=scalar(text,node.children,'type')
            for n in color.children if color else []:types[int(n.key)]=kind
    return types,categories


def graphical_province_types(ids,graphics,selection,definitions,mapping):
    rows=[]
    for pid in map(int,np.unique(ids[selection])):
        if definitions[pid][4]!='land':continue
        values,counts=np.unique(graphics[ids==pid],return_counts=True);votes=Counter()
        for index,count in zip(values,counts):
            if int(index) not in mapping:raise ValueError(f'Unmapped native graphical terrain index {index}')
            kind=mapping[int(index)]
            if kind not in {'ocean','lakes','water_space'}:votes[kind]+=int(count)
        if not votes:raise ValueError(f'Land province {pid} has no graphical land terrain')
        best=max(votes.values());tied=sorted(k for k,v in votes.items() if v==best)
        kind=definitions[pid][6] if definitions[pid][6] in tied else tied[0]
        rows.append({'province':pid,'old':definitions[pid][6],'terrain':kind,'votes':dict(votes)})
    return rows


def trees_with_native_density(old,source,graphics,selection):
    allowed=footprint_mask(selection,old.shape);native=sample(graphics,old.shape);prior=sample(source,old.shape)
    nearby=binary_dilation(allowed,iterations=90)&~allowed
    yy,xx=np.indices(old.shape,dtype=np.uint64)
    random=((xx*73856093)^(yy*19349663)^83492791)%1000003/1000003
    result=old.copy();result[allowed]=0;stats={}
    # These indices resolve to existing forest and beech-blend models in trees.gfx.
    for label,indices,model in [('forest',(1,4),5),('jungle',(21,22),28)]:
        woodland=np.isin(native,indices);reference=nearby&woodland
        if reference.sum()<20:reference=~allowed&woodland
        density=float(np.count_nonzero(old[reference])/max(1,reference.sum()))
        density=float(np.clip(density,.2,.99));area=allowed&woodland;seeds=area&(prior!=0)
        seed_rate=float(seeds.sum()/max(1,area.sum()));fill=float(np.clip((density-seed_rate)/max(1e-8,1-seed_rate),0,1))
        occupied=seeds|(area&~seeds&(random<fill));result[occupied]=model
        stats[label]={'cells':int(area.sum()),'before':int(np.count_nonzero(old[area])),
                      'after':int(occupied.sum()),'reference_density':density,'model':model}
    return result,allowed,stats


def run(root,eu4,original_audit,stage,apply=False):
    root=Path(root).resolve();eu4=Path(eu4).resolve();stage=Path(stage).resolve()
    report=Path(original_audit).resolve();old_audit=json.loads(report.read_text());backup=Path(old_audit['backup'])
    approved=None
    if apply:
        if not (stage/'audit.json').exists():raise ValueError('Inspect a staged dry run first')
        approved=json.loads((stage/'audit.json').read_text())
        if approved['applied']:raise ValueError('Stage is already applied')
    inputs={}
    def read(path):
        path=Path(path);data=path.read_bytes();inputs[str(path)]=digest(data);return data
    names=['map/heightmap.bmp','map/world_normal.bmp','map/terrain/colormap_rgb_cityemissivemask_a.dds','map/trees.bmp','map/definition.csv']
    before={n:read(root/n) for n in names};selection=image_array(read(report.parent/'selection.png'))==0
    if selection.ndim!=2:raise ValueError('Expected exact binary selection')
    ids,definitions=raster(read(root/'map/provinces.bmp'),before['map/definition.csv'])
    graphics=image_array(read(root/'map/terrain.bmp'));mapping,categories=native_graphics(root)
    land=np.zeros(int(ids.max())+1,bool)
    for pid,row in definitions.items():land[pid]=row[4]=='land'
    land=land[ids];source_ids,_=raster(read(eu4/'map/provinces.bmp'),read(eu4/'map/definition.csv'))
    nodes=parse(read(eu4/'map/default.map').decode('utf-8-sig'));water=set()
    for key in ('sea_starts','lakes'):
        node=child(nodes,key)
        if node:water.update(int(n.key) for n in node.children)
    compatible=selection&land&~np.isin(source_ids,list(water))
    y,x=np.nonzero(selection);box=(slice(max(0,int(y.min())-80),min(selection.shape[0],int(y.max())+81)),slice(max(0,int(x.min())-80),min(selection.shape[1],int(x.max())+81)))
    native_blob=read(backup/'map/heightmap.bmp')
    if digest(native_blob)!=old_audit['files']['map/heightmap.bmp']['before']:raise ValueError('Original native height backup changed')
    base=image_array(before['map/heightmap.bmp']).astype(float);base[compatible]=image_array(native_blob)[compatible]
    source_height=image_array(read(eu4/'map/heightmap.bmp')).astype(float)
    local,scale,domain=matched_height(base[box],source_height[box],compatible[box],land[box])
    height=base.astype(np.uint8);height[box]=local;height_mask=np.zeros_like(selection);height_mask[box]=domain
    changes={'map/heightmap.bmp':patch_bmp(before['map/heightmap.bmp'],height,height_mask)}
    # Match the existing native normal convention to the revised height derivatives.
    normal=image_array(before['map/world_normal.bmp']);shape=normal.shape[:2];small=half_mask(compatible)
    base_height=np.asarray(Image.fromarray(image_array(native_blob)).resize((shape[1],shape[0]),Image.Resampling.BILINEAR),float)
    final_height=np.asarray(Image.fromarray(height).resize((shape[1],shape[0]),Image.Resampling.BILINEAR),float)
    original_normal=image_array(read(backup/'map/world_normal.bmp')).astype(float)
    mask_small=sample(selection,shape);reference=binary_dilation(mask_small,iterations=30)&~binary_dilation(mask_small,iterations=3)&(base_height>=96)&(base_height<180)
    dy,dx=np.gradient(gaussian_filter(base_height,.7));matrix=np.c_[np.ones(reference.sum()),dx[reference],dy[reference]]
    ny,nx=np.gradient(gaussian_filter(final_height,.7));desired=np.zeros_like(original_normal);normal_fits=[]
    for channel in range(3):
        fit=np.linalg.lstsq(matrix,original_normal[:,:,channel][reference],rcond=None)[0];normal_fits.append(fit.tolist())
        desired[:,:,channel]=fit[0]+fit[1]*nx+fit[2]*ny
    weight=sample(smooth_weight(compatible,48),shape)
    normal_result=np.rint(original_normal*(1-weight[:,:,None])+desired*weight[:,:,None]).clip(0,255).astype(np.uint8)
    changes['map/world_normal.bmp']=patch_bmp(before['map/world_normal.bmp'],normal_result,small)
    # Native biome tones plus restrained EU4 fine texture, without baked bright relief.
    color=image_array(before['map/terrain/colormap_rgb_cityemissivemask_a.dds']);original_color=image_array(read(backup/'map/terrain/colormap_rgb_cityemissivemask_a.dds'))
    summer=image_array(read(eu4/'map/terrain/colormap_summer.dds'))[:,:,:3].astype(float)
    types=sample(graphics,shape);near=binary_dilation(mask_small,iterations=90)&~mask_small
    target=original_color[:,:,:3].astype(float).copy();detail=summer-gaussian_filter(summer,(3,3,0));biome_tones={}
    for index in map(int,np.unique(types[small])):
        reference=near&(types==index)
        if reference.sum()<10:reference=~mask_small&(types==index)
        if not reference.any():raise ValueError(f'No native colormap reference for graphic index {index}')
        tone=np.median(original_color[:,:,:3][reference],axis=0);biome_tones[index]=tone.tolist()
        area=small&(types==index);target[area]=tone+detail[area]*.2
    target=gaussian_filter(target,(.6,.6,0));rgb=np.rint(original_color[:,:,:3]*(1-weight[:,:,None])+target*weight[:,:,None]).clip(0,255).astype(np.uint8)
    changes['map/terrain/colormap_rgb_cityemissivemask_a.dds']=patch_colormap(before['map/terrain/colormap_rgb_cityemissivemask_a.dds'],rgb,small)
    trees=image_array(before['map/trees.bmp']);source_trees=image_array(read(eu4/'map/trees.bmp'))
    tree_result,tree_mask,tree_stats=trees_with_native_density(trees,source_trees,graphics,compatible)
    changes['map/trees.bmp']=patch_bmp(before['map/trees.bmp'],tree_result,tree_mask)
    # Every touched land province uses its complete, actually displayed terrain.
    rows=graphical_province_types(ids,graphics,selection,definitions,mapping);by_id={r['province']:r for r in rows}
    lines=before['map/definition.csv'].decode('utf-8-sig').splitlines(keepends=True)
    for i,line in enumerate(lines):
        fields=line.split(';')
        if len(fields)>=8 and fields[0].isdigit() and int(fields[0]) in by_id:
            kind=by_id[int(fields[0])]['terrain']
            if kind not in categories:raise ValueError('Undefined native terrain')
            fields[6]=kind;lines[i]=';'.join(fields)
    changes['map/definition.csv']=encode_source(''.join(lines),before['map/definition.csv'])
    protected={}
    for p in [root/'map/provinces.bmp',root/'map/terrain.bmp',root/'map/rivers.bmp',root/'map/railways.txt',root/'map/supply_nodes.txt',root/'map/adjacencies.csv',root/'map/buildings.txt']:
        protected[p.relative_to(root).as_posix()]=digest(p.read_bytes())
    for folder in ('history/states','map/strategicregions','map/supplyareas'):
        for p in (root/folder).glob('*.txt'):protected[p.relative_to(root).as_posix()]=digest(p.read_bytes())
    files={n:{'before':digest(before[n]),'after':digest(b),'bytes':len(b)} for n,b in changes.items() if b!=before[n]}
    if apply and (approved['files']!=files or approved['inputs']!=inputs):raise ValueError('Inputs changed since the inspected stage')
    stage.mkdir(parents=True,exist_ok=True)
    for name in files:
        p=stage/'files'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(changes[name])
    audit={'applied':False,'files':files,'inputs':inputs,'protected':protected,'height_scale':scale,'blend_width':48,
           'normal_fits':normal_fits,'biome_tones':biome_tones,'trees':tree_stats,'province_types':rows,
           'changed_provinces':sum(r['old']!=r['terrain'] for r in rows)}
    # Seam metrics use the same original gentle-gradient border sample.
    d=distance_transform_edt(height_mask[box]);base_grad=np.hypot(*np.gradient(base[box]));band=height_mask[box]&(d<12)&(base_grad<3)
    audit['boundary_slope_p95']={k:float(np.percentile(np.hypot(*np.gradient(z))[band],95)) for k,z in [('native',base[box]),('before',image_array(before['map/heightmap.bmp'])[box].astype(float)),('after',height[box].astype(float))]}
    preview=Image.new('RGB',(1200,940),'#181c24');draw=ImageDraw.Draw(preview)
    for col,(label,arr) in enumerate([('Native style',image_array(native_blob)),('Previous import',image_array(before['map/heightmap.bmp'])),('Matched and blended',height)]):
        draw.text((col*400+8,8),label,fill='white');preview.paste(Image.fromarray(arr[box]).convert('RGB').resize((400,420)),(col*400,30))
    color_box=tuple(v//2 for v in (box[1].start,box[0].start,box[1].stop,box[0].stop))
    for col,(label,arr) in enumerate([('Previous colors',color[:,:,:3]),('Native-style biome colors',image_array(changes['map/terrain/colormap_rgb_cityemissivemask_a.dds'])[:,:,:3])]):
        draw.text((col*600+8,470),label,fill='white');preview.paste(Image.fromarray(arr).crop(color_box).resize((600,420)),(col*600,495))
    preview.save(stage/'preview.png')
    if apply:
        for p,sha in inputs.items():
            if digest(Path(p).read_bytes())!=sha:raise ValueError('Input changed during refinement')
        audit['backup']=str(write_changes(root,{n:(before[n],changes[n]) for n in files},label='terrain_refinement'))
        audit['applied']=True
        for name,sha in protected.items():
            if digest((root/name).read_bytes())!=sha:raise AssertionError('Protected file changed')
    (stage/'audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ('applied','height_scale','boundary_slope_p95','trees','changed_provinces','files')},indent=2))
    return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--eu4',type=Path,required=True)
    p.add_argument('--original-audit',type=Path,default=ROOT/'modding_documentation/agent_memory/masked_eu4_terrain_import/audit.json')
    p.add_argument('--stage',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    run(a.root,a.eu4,a.original_audit,a.stage,a.apply)
