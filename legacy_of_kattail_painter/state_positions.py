"""Deterministic native building placements for edited state membership."""
from collections import defaultdict
import math

import numpy as np
from PIL import Image

from character_model import atom,block
from source_io import encode_source

PLACEMENTS='map/buildings.txt'
HEIGHT_SCALE=.1


class StatePositions:
    def __init__(self,world,geo):
        self.world,self.geo,self.docs=world,geo,world.docs
        self._geometry=None

    def geometry(self):
        if self._geometry is not None:return self._geometry
        self.world.load_map();ids=self.world.map_ids;h,w=ids.shape
        sizes=np.bincount(ids.ravel(),minlength=max(self.world.provinces)+1)
        points=self.geo.province_points()
        sea=np.zeros(len(sizes),dtype=bool)
        for pid,p in self.world.provinces.items():sea[pid]=p['type']=='sea'
        coasts={};contacts=defaultdict(set);best={}
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            other=np.roll(ids,(-dy,-dx),(0,1));mask=(ids!=other)&~sea[ids]&sea[other]
            if dy==1:mask[-1,:]=False
            if dy==-1:mask[0,:]=False
            yy,xx=np.nonzero(mask)
            for y,x in zip(yy,xx):
                pid=int(ids[y,x])
                if self.world.provinces.get(pid,{}).get('type')!='land':continue
                sy=int(y+dy);sx=int((x+dx)%w);water=int(ids[sy,sx]);contacts[pid].add(water)
                cx,cy=points.get(pid,(x,y));distance=(x-cx)**2+(y-cy)**2
                if pid not in best or distance<best[pid]:
                    best[pid]=distance;coasts[pid]=(int(x),int(y),sx,sy,water)
        heightpath=self.world.root/'map/heightmap.bmp'
        if heightpath.is_file():
            with Image.open(heightpath) as image:
                height=np.asarray(image.convert('L').resize((w,h),Image.Resampling.BILINEAR))
        else:height=np.full((h,w),100,dtype=np.uint8)
        self._geometry={'ids':ids,'height':height,'sizes':sizes,'points':points,
                        'coasts':coasts,'contacts':contacts,'candidates':{}}
        return self._geometry

    def candidates(self,pid):
        g=self.geometry()
        if pid in g['candidates']:return g['candidates'][pid]
        ids=g['ids'];point=g['points'].get(pid)
        if point is None:raise ValueError(f'Province {pid} has no pixels for model placement')
        x,y=point;h,w=ids.shape;out=[(x,y)]
        # Spread small groups around an actual interior point, never outside its province.
        for radius in (4,8,16,24,40):
            for dx,dy in [(radius,0),(-radius,0),(0,radius),(0,-radius),
                          (radius,radius),(-radius,-radius),(radius,-radius),(-radius,radius)]:
                px=(x+dx)%w;py=y+dy
                if 0<=py<h and int(ids[py,px])==pid:out.append((px,py))
        g['candidates'][pid]=out
        return out

    def specs(self):
        result={};aliases={}
        for key,(text,node) in self.geo.definitions('common/buildings','buildings').items():
            spawn=atom(text,node.children,'spawn_point')
            if spawn:aliases[key]=spawn;continue
            count=atom(text,node.children,'show_on_map','0')
            if not count.isdigit() or not int(count):continue
            cap=block(node.children,'level_cap')
            result[key]={'count':int(count),'province':bool(cap and atom(text,cap.children,'province_max')),
                         'coast':atom(text,node.children,'only_costal')=='yes','manual':atom(text,node.children,'disable_auto_nudging')=='yes'}
        for key,(text,node) in self.geo.definitions('common/buildings','spawn_points').items():
            result[key]={'count':int(atom(text,node.children,'max','1')),
                         'province':atom(text,node.children,'type')=='province',
                         'coast':atom(text,node.children,'only_costal')=='yes',
                         'manual':atom(text,node.children,'disable_auto_nudging')=='yes'}
        # Native special entry: it sits in water and names the owning land province.
        result['floating_harbor']={'count':1,'province':True,'coast':True,'manual':False}
        # A valid airbase placement is required even when the state's building level is zero.
        result.setdefault('air_base',{'count':1,'province':False,'coast':False,'manual':False})
        return result,aliases

    def point_province(self,fields):
        g=self.geometry();h,w=g['ids'].shape
        try:x=float(fields[2]);z=float(fields[4])
        except (ValueError,IndexError):return None
        if not (0<=x<w and 0<=z<h):return None
        return int(g['ids'][h-1-int(z),int(x)])

    def row(self,sid,kind,point,rotation=0,link=0,water=False):
        x,y=point;g=self.geometry();h,_=g['ids'].shape
        height=9.5 if water else float(g['height'][y,x])*HEIGHT_SCALE
        # Exact pixels agree under both the editor's floor and the map validator's
        # nearest-pixel sampling, including one-pixel shorelines.
        return f'{sid};{kind};{x:.2f};{height:.2f};{h-1-y:.2f};{rotation:.2f};{link}'

    def regenerate(self,affected):
        affected=set(affected);g=self.geometry();specs,aliases=self.specs()
        original=self.docs.binary(PLACEMENTS) or b'';text=self.docs._decode(original)
        self._vps=self.geo.victory_points()
        newline='\r\n' if '\r\n' in text else '\n'
        keep=[];available=defaultdict(list);manual=[]
        for line in text.splitlines(keepends=True):
            body=line.split('#',1)[0].strip();fields=body.split(';')
            if len(fields)!=7 or not fields[0].isdigit():
                keep.append(line);continue
            sid=int(fields[0]);kind=aliases.get(fields[1],fields[1]);pid=self.point_province(fields)
            owner=self.world.province_states.get(pid)
            if fields[1]=='floating_harbor':
                try:owner=self.world.province_states.get(int(fields[6]))
                except ValueError:owner=None
            if sid not in affected:
                keep.append(line);continue
            if '#' in line:keep.append('#'+line.split('#',1)[1])
            spec=specs.get(kind)
            if spec is None or spec['manual']:
                if owner is None:raise ValueError(f'Manual {fields[1]} placement in state {sid} cannot be assigned safely')
                if owner not in affected:raise ValueError(f'Manual {fields[1]} placement lies outside the edited states')
                fields[0]=str(owner);manual.append(';'.join(fields))
            elif not spec['province'] and owner==sid and not spec['coast'] and self.world.provinces.get(pid,{}).get('type')=='land':
                fields[1]=kind;available[(sid,kind)].append(';'.join(fields))
            # Provincial and coastal rows are rebuilt for their precise current provinces.
        generated=[]
        for sid in sorted(affected):
            provinces=[p for p in self.world.states[sid].provinces if self.world.provinces[p]['type']=='land']
            ordered=sorted(provinces,key=lambda p:(-self._vp(p),-int(g['sizes'][p]),p))
            candidates=[point for p in ordered for point in self.candidates(p)]
            used=set()
            for kind,spec in sorted(specs.items()):
                if spec['manual']:continue
                if spec['province']:
                    for pid in sorted(provinces):
                        coast=g['coasts'].get(pid)
                        if spec['coast'] and coast is None:continue
                        for index in range(spec['count']):
                            if coast and spec['coast']:
                                x,y,sx,sy,water=coast;dx=sx-x
                                if abs(dx)>g['ids'].shape[1]//2:dx=-1 if dx>0 else 1
                                rotation=math.atan2(dx,-(sy-y))
                                if kind=='floating_harbor':row=self.row(sid,kind,(sx,sy),rotation,pid,True)
                                else:row=self.row(sid,kind,(x,y),rotation,water if kind in {'naval_base','naval_base_spawn'} else 0)
                            else:
                                points=self.candidates(pid)
                                point=next((p for p in points if p not in used),points[index%len(points)])
                                used.add(point);row=self.row(sid,kind,point)
                            generated.append(row)
                else:
                    options=candidates
                    if spec['coast']:
                        options=[(g['coasts'][p][0],g['coasts'][p][1]) for p in ordered if p in g['coasts']]
                    if not options:continue
                    existing=available.get((sid,kind),[])
                    for index in range(spec['count']):
                        if index<len(existing):generated.append(existing[index]);continue
                        point=next((p for p in options if p not in used),options[index%len(options)])
                        used.add(point);generated.append(self.row(sid,kind,point))
        result=''.join(keep)
        if result and not result.endswith(('\n','\r')):result+=newline
        result+=newline.join(manual+generated)+(newline if manual or generated else '')
        self.docs.stage_bytes(PLACEMENTS,encode_source(result,original))
        self.validate(affected)
        return len(manual)+len(generated)

    def _vp(self,pid):
        return self._vps.get(pid,{}).get('value',0)

    def validate(self,affected):
        g=self.geometry();specs,_=self.specs();counts=defaultdict(int)
        for line in self.docs.text(PLACEMENTS).splitlines():
            fields=line.split('#',1)[0].strip().split(';')
            if len(fields)!=7 or not fields[0].isdigit() or int(fields[0]) not in affected:continue
            sid=int(fields[0]);kind=fields[1];pid=self.point_province(fields)
            if kind=='floating_harbor':
                land=int(fields[6])
                if self.world.province_states.get(land)!=sid or pid not in g['contacts'].get(land,set()):
                    raise ValueError(f'Invalid floating-harbor placement in state {sid}')
                pid=land
            elif self.world.province_states.get(pid)!=sid:
                raise ValueError(f'{kind} placement lies outside state {sid}')
            elif kind in specs and not specs[kind]['manual'] and self.world.provinces[pid]['type']!='land':
                raise ValueError(f'{kind} placement in state {sid} must be on land')
            if kind in {'naval_base','naval_base_spawn'} and int(fields[6]) not in g['contacts'].get(pid,set()):
                raise ValueError(f'{kind} in province {pid} has no adjacent ocean access')
            counts[(sid,kind,pid if specs.get(kind,{}).get('province') else None)]+=1
        for sid in affected:
            for kind,spec in specs.items():
                if spec['manual']:continue
                if spec['province']:
                    targets=[p for p in self.world.states[sid].provinces if self.world.provinces[p]['type']=='land' and (not spec['coast'] or p in g['coasts'])]
                else:targets=[None] if not spec['coast'] or any(p in g['coasts'] for p in self.world.states[sid].provinces) else []
                for pid in targets:
                    if counts[(sid,kind,pid)]<spec['count']:raise ValueError(f'State {sid} lacks a valid {kind} placement')
