"""Viewport rendering and session-only, camera-independent overlay configurations."""
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont
from geography_model import vp_color


@dataclass(frozen=True)
class MapConfig:
    layer:str
    building_key:str=''
    building_scope:str='State'
    resource_key:str=''
    province_borders:bool=False
    state_borders:bool=False
    region_borders:bool=False
    numbers:bool=True
    resource_highlight:int|None=None
    supply_hubs:bool=False
    names:bool|None=None
    country_tag:str=''
    state_preview:tuple=()
    state_target:int|None=None
    oob_template:str=''
    oob_global:bool=False
    oob_source:str=''

    @property
    def name_scope(self):
        if self.layer in {'States','State categories','Resources','Population','Katzenartig Imperium','Cores/Claims'} or self.layer=='Buildings' and self.building_scope=='State':return 'States'
        if self.layer in {'Strategic regions','Koppen presets'}:return 'Strategic regions'
        if self.layer=='VPs':return 'VPs'
        return None

    @property
    def show_names(self):
        return self.layer=='VPs' if self.names is None else self.names

    @property
    def label(self):
        if self.layer=='Land OOB':return 'Land OOB: '+('Global' if self.oob_global else self.country_tag+' / '+(self.oob_template or 'All templates'))
        if self.layer=='Cores/Claims':return 'Cores/Claims: '+self.country_tag
        if self.layer=='Buildings':return f'{self.building_scope} buildings: {self.building_key}'
        if self.layer=='Resources':return 'Resources: '+self.resource_key
        return self.layer


@lru_cache(maxsize=4)
def map_font(size=12):
    try:return ImageFont.truetype('segoeui.ttf',size)
    except OSError:return ImageFont.load_default()


class MapRenderer:
    def __init__(self,world,geography,characters,catalogs):
        self.world,self.geo,self.characters,self.catalogs=world,geography,characters,catalogs;self.icons=OrderedDict();self.labels=OrderedDict();self.label_bytes=0

    def text_tile(self,text,anchor):
        key=(text,anchor)
        if key not in self.labels:
            font=map_font();bbox=font.getbbox(text,anchor=anchor,stroke_width=1)
            tile=Image.new('RGBA',(max(1,bbox[2]-bbox[0]+2),max(1,bbox[3]-bbox[1]+2)))
            ImageDraw.Draw(tile).text((1-bbox[0],1-bbox[1]),text,font=font,fill='white',stroke_width=1,stroke_fill='#10141b',anchor=anchor)
            cost=tile.width*tile.height*4;offset=(bbox[0]-1,bbox[1]-1)
            if cost>16*1024*1024:return tile,offset
            self.labels[key]=(tile,offset,cost);self.label_bytes+=cost
            while len(self.labels)>4096 or self.label_bytes>16*1024*1024:
                _,(_,_,old)=self.labels.popitem(last=False);self.label_bytes-=old
        self.labels.move_to_end(key);return self.labels[key][:2]

    def annotations(self,config,zoom,box,numbers=True):
        """Map-space positions make snapshots follow the current zoom and camera."""
        rows=[];numbers=numbers and config.numbers
        def visible(x,y,margin=100):return box[0]-margin<=x<=box[2]+margin and box[1]-40<=y<=box[3]+40
        def text(point,label,source,dy=0,anchor='mm'):
            x,y=point;x*=zoom;y=y*zoom+dy
            if visible(x,y):rows.append(dict(kind='text',x=x,y=y,text=label,source=source,anchor=anchor))
        if config.layer=='Land OOB' and numbers:
            points=self.geo.province_points()
            for pid,count in self.world.land_oob_store.counts(config.country_tag,config.oob_template,config.oob_global,config.oob_source).items():
                if pid in points:text(points[pid],str(count),'land_oob')
        elif config.layer=='Railways' and numbers and zoom>=.45:
            points=self.geo.province_points()
            for pid,level in self.world.railway_store.levels().items():
                if pid in points:text(points[pid],str(level),'railway',dy=-10)
        elif config.layer=='Buildings' and numbers:
            counts=self.geo.building_counts(config.building_key,config.building_scope)
            points=self.geo.state_points() if config.building_scope=='State' else self.geo.province_points()
            for key,value in counts.items():
                if value>0 and key in points:text(points[key],str(value),'building',dy=-7 if config.building_scope=='State' else 0)
            if config.building_scope=='State':
                for sid,d in self.geo.slot_summary().items():
                    if d['used'] and sid in points:text(points[sid],f'{d["used"]}/{d["total"]}','capacity',dy=8)
        elif config.layer=='State categories' and numbers:
            points=self.geo.state_points()
            for sid,d in self.geo.slot_summary().items():
                if sid in points:text(points[sid],f'{d["used"]}/{d["total"]}','capacity')
        elif config.layer in {'Resources','Population'} and numbers:
            points=self.geo.state_points();counts=self.geo.population_counts() if config.layer=='Population' else self.geo.resource_counts(config.resource_key)
            for sid,value in counts.items():
                if value>0 and sid in points:text(points[sid],f'{int(value):,}' if config.layer=='Population' else format(Decimal(value).normalize(),'f'),'population' if config.layer=='Population' else 'resource')
        elif config.layer=='Koppen presets':
            points=self.geo.region_points()
            for rid,(code,hemisphere) in self.geo.preset_regions().items():
                if rid in points:text(points[rid],hemisphere[0],'hemisphere')
        elif config.layer=='VPs':
            points=self.geo.province_points();records=self.geo.victory_points();maximum=max((d['value'] for d in records.values()),default=1)
            for pid,d in records.items():
                if pid not in points:continue
                x,y=points[pid];x*=zoom;y*=zoom
                if not visible(x,y,160):continue
                rows.append(dict(kind='vp',x=x,y=y,color=vp_color(d['value'],maximum),radius=3 if zoom<.65 else 5))
                if zoom>=.65:
                    label=f'{d["name"]} ({d["value"]})' if config.show_names and numbers else d['name'] if config.show_names else str(d['value']) if numbers else ''
                    if label:text(points[pid],label,'vp',dy=-11,anchor='ms')
        elif config.layer=='Wonder':
            points=self.geo.state_points()
            for sid,ident in self.catalogs.wonder_sites().items():
                if not ident or sid not in points:continue
                x,y=points[sid];x*=zoom;y*=zoom
                if not visible(x,y):continue
                sprite=f'GFX_wonder_{ident}';key=(sprite,self.characters.image_token(sprite))
                if key not in self.icons:
                    self.icons[key]=self.characters.image(sprite,(44,30))
                    if len(self.icons)>64:self.icons.popitem(last=False)
                icon=self.icons[key]
                if icon is not None:rows.append(dict(kind='image',x=x,y=y,image=icon))
                elif numbers:text(points[sid],str(ident),'wonder')
        if config.show_names and config.name_scope in {'States','Strategic regions'}:
            states=config.name_scope=='States'
            points=self.geo.state_points() if states else self.geo.region_points()
            records=self.world.states if states else self.world.regions
            loc=self.characters.localisations()
            for ident,point in points.items():
                key=records[ident].name if states else records[ident]['name']
                text(point,loc.get(key,key),'state_name' if states else 'region_name',dy=-22 if states else -16)
        if config.supply_hubs:
            points=self.geo.province_points();sprite='GFX_supply_hub_icon_strip'
            key=(sprite,self.characters.image_token(sprite))
            if key not in self.icons:
                self.icons[key]=self.characters.image(sprite,(26,26))
                if len(self.icons)>64:self.icons.popitem(last=False)
            icon=self.icons[key]
            if icon is not None:
                for pid,level in self.geo.supply_nodes().items():
                    if level>0 and pid in points:
                        x,y=points[pid];x*=zoom;y*=zoom
                        if visible(x,y):rows.append(dict(kind='image',x=x,y=y,image=icon,source='supply_hub',province=pid))
        return rows

    def railway_lines(self,image,box,zoom):
        from railway_model import railway_color
        store=self.world.railway_store;points=self.geo.province_points();width=self.world.map_ids.shape[1]
        draw=ImageDraw.Draw(image);invalid=store.invalid_links()
        for (a,b),level in store.edges().items():
            if a not in points or b not in points:continue
            ax,ay=points[a];bx,by=points[b]
            if abs(bx-ax)>width/2:bx+=width if ax>bx else -width
            for shift in (-width,0,width):
                x1,y1=(ax+shift)*zoom,ay*zoom;x2,y2=(bx+shift)*zoom,by*zoom
                if max(x1,x2)<box[0]-4 or min(x1,x2)>box[2]+4 or max(y1,y2)<box[1]-4 or min(y1,y2)>box[3]+4:continue
                coords=(x1-box[0],y1-box[1],x2-box[0],y2-box[1])
                draw.line(coords,fill=(15,20,25),width=5)
                draw.line(coords,fill=(255,40,40) if (a,b) in invalid else railway_color(level,store.max_level()),width=3)

    def render(self,config,size,box,zoom,numbers=True):
        image=self.world.map_image(config.layer,size,box,building_key=config.building_key,building_scope=config.building_scope,resource_key=config.resource_key,resource_highlight=config.resource_highlight,country_tag=config.country_tag,state_preview=config.state_preview,state_target=config.state_target,oob_template=config.oob_template,oob_global=config.oob_global,oob_source=config.oob_source)
        image=self.world.boundary_overlay(image,config.province_borders,config.state_borders,config.region_borders,size,box)
        if config.layer=='Railways':self.railway_lines(image,box,zoom)
        draw=ImageDraw.Draw(image)
        for row in self.annotations(config,zoom,box,numbers):
            x,y=row['x']-box[0],row['y']-box[1]
            if row['kind']=='text':
                tile,offset=self.text_tile(row['text'],row['anchor']);image.paste(tile,(round(x+offset[0]),round(y+offset[1])),tile)
            elif row['kind']=='vp':
                r=row['radius'];draw.ellipse((x-r,y-r,x+r,y+r),fill=row['color'],outline='white')
            else:
                icon=row['image'].convert('RGBA');image.paste(icon,(round(x-icon.width/2),round(y-icon.height/2)),icon)
        return image

    def composite(self,config,overlay,opacity,size,box,zoom,numbers=True,*,equator=False):
        image=self.render(config,size,box,zoom,numbers)
        if overlay is not None and opacity>0:image=Image.blend(image,self.render(overlay,size,box,zoom,numbers),max(0,min(1,float(opacity))))
        if equator:
            y=round(self.geo.planet_frame().equator*zoom-box[1])
            if -2<=y<image.height+2:
                draw=ImageDraw.Draw(image)
                for start in range((-(box[0]%24))-24,image.width,24):
                    draw.line((start,y,start+14,y),fill='#171b21',width=5)
                    draw.line((start,y,start+14,y),fill='#ffdc60',width=2)
                tile,offset=self.text_tile('Equator','ls');image.paste(tile,(8-box[0]+offset[0],y-7+offset[1]),tile)
        return image
