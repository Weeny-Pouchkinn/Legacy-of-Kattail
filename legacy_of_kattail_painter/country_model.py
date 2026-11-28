"""Native country history, names, flags and spirits; no editor metadata files."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from functools import lru_cache
import io
import math
import os
import struct
from pathlib import Path
import re
import random

from PIL import Image, ImageColor, ImageDraw, ImageOps, ImageFilter

from model import FLAG_SIZES, child, parse, value, scalar, walk, read_text
from character_model import atom, block, quote, LOC, unescape, inherited_sprites, LARGE_SIZE, SMALL_SIZE
from select_ui import Choice
from demographics import STARTUP
from source_io import encode_source

COUNTRY_LOC = 'localisation/english/countries_l_english.yml'
IDEA_LOC = 'localisation/english/LOK_ideas_l_english.yml'
IDEAS = 'common/ideas/lok_misc_ideas.txt'
IDEA_GFX = 'interface/lok_ideas.gfx'
EAW_IDEAS = 'legacy_of_kattail_painter/assets/eaw_ideas'
EAW_TEXTURES = 'gfx/interface/ideas/eaw'
EAW_CREDITS = 'legacy_of_kattail_painter/credits/EaW Credits.txt'
CUSTOM_IDEAS = 'gfx/interface/ideas/custom'
SPIRIT_ICON_SIZE = (60,68)
EMBLEM_GFX = 'interface/lok_misc_icons.gfx'
TAGS = 'common/country_tags/00_countries.txt'
SPECIES_HISTORY_FLAG = 'lok_country_species_defined_in_history'
ATTRIBUTE_HISTORY_FLAG = 'lok_country_attribute_defined_in_history'


def asset_files(root):
    """Walk assets without resolving every file or following escaping links."""
    resolved=root.resolve();pending=[root]
    while pending:
        folder=pending.pop()
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    path=Path(entry.path)
                    if path.resolve().is_relative_to(resolved):pending.append(path)
                elif entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.lower() in {'.dds','.tga'}:
                    yield Path(entry.path)


def image_dimensions(source,suffix):
    """Inspect fixed DDS/TGA headers; use Pillow for other image formats."""
    with (open(source,'rb') if isinstance(source,(str,Path)) else source) as stream:
        header=stream.read(32)
        if header[:4]==b'DDS ' and len(header)>=20:
            height,width=struct.unpack_from('<II',header,12);return width,height
        if suffix.casefold()=='.tga' and len(header)>=18:
            return struct.unpack_from('<HH',header,12)
        stream.seek(0)
        with Image.open(stream) as image:return image.size


def flat_icon_destination(folder,asset,blob,read):
    """Readable runtime names; identical art shares a file, different art never overwrites it."""
    name=Path(asset).name;stem=Path(name).stem;suffix=Path(name).suffix;number=1
    while True:
        destination=folder+'/'+(name if number==1 else f'{stem}_{number}{suffix}')
        existing=read(destination)
        if existing is None or existing==blob:return destination
        number+=1


def flat_eaw_destination(asset,blob,read):
    return flat_icon_destination(EAW_TEXTURES,asset,blob,read)


def eaw_credit_sources(text):
    """Original paths survive flat runtime filenames in the existing human-readable credits."""
    result={}
    pattern=r'^EaW path: ([^\r\n]+)\r?\nUsed for: National spirit ([A-Za-z0-9_]+) [^\r\n]*\r?\nMod texture: ([^\r\n]+)\r?$'
    for match in re.finditer(pattern,text,re.M):
        source=match[1].replace('\\','/');texture=match[3].replace('\\','/').strip()
        prefix='gfx/interface/ideas/'
        if source.startswith(prefix):result[(texture.casefold(),match[2])]=source[len(prefix):]
    return result


PATTERNS = ('Solid', 'Horizontal bicolor', 'Vertical bicolor', 'Horizontal tricolor',
            'Vertical tricolor', 'Horizontal 1:2:1', 'Vertical 1:2:1', 'Diagonal down',
            'Diagonal up', 'Quartered', 'Cross', 'Nordic cross', 'Saltire', 'Chevron',
            'Canton', 'Border', 'Central disk',
            'Horizontal four-color', 'Vertical four-color', 'Horizontal five stripes', 'Vertical five stripes',
            'Horizontal seven stripes', 'Vertical seven stripes', 'Horizontal nine stripes', 'Vertical nine stripes',
            'Horizontal 1:1:2', 'Vertical 1:1:2', 'Diagonal tricolor down', 'Diagonal tricolor up',
            'Diagonal band down', 'Diagonal band up', 'Plain cross', 'Plain Nordic cross', 'Bordered saltire',
            'Chevron tricolor', 'Double chevron', 'Hoist triangle', 'Fly triangle',
            'Triangle with bicolor', 'Triangle with tricolor', 'Lozenge', 'Diagonal quarters',
            'Checkerboard', 'Small checkerboard', 'Stripes with canton', 'Union cross',
            'Sunburst', 'Pall', 'Serrated hoist', 'Rising diagonal stripes', 'Falling diagonal stripes',
            'Central ring', 'Double border', 'Nested diamonds', 'Horizontal gradient', 'Vertical gradient')


def copy_ideology_names(names,source,ideologies,undefined=False):
    values={k:(names[source][k] if names[source][k] is not None else names[''][k] if names[''][k] is not None else names['']['name']) for k in ('name','def')}
    for ideology in ideologies:
        for key in ('name','def'):
            if not undefined or names[ideology][key] is None:names[ideology][key]=values[key]


def definite_name(text,article=False):
    text=re.sub(r'^the\s+','',text.strip(),flags=re.I)
    return ('the ' if article and text else '')+text


def number(raw, low=None, high=None):
    low=Decimal(str(low)) if low is not None else None;high=Decimal(str(high)) if high is not None else None
    try: n = Decimal(str(raw))
    except InvalidOperation: raise ValueError('Enter a numeric value') from None
    if not n.is_finite() or low is not None and n < low or high is not None and n > high:
        raise ValueError(f'Value must be between {low} and {high}' if low is not None and high is not None else 'Value must be finite')
    return format(n, 'f')


def distribute_popularities(values, remaining=False, rng=None):
    """Fill unset percentages or rescale weights, with an exact total of 100."""
    raw={key:str(v).strip() or '0' for key,v in values.items()}
    if not raw:raise ValueError('No ideologies are defined')
    decimals={key:Decimal(number(v,0)) for key,v in raw.items()}
    # Native fixed-point values have three decimals; Python-only exact totals
    # with six-digit shares can still be rejected by set_popularities in game.
    if remaining:
        from decimal import ROUND_HALF_UP
        decimals={key:v.quantize(Decimal('.001'),rounding=ROUND_HALF_UP) for key,v in decimals.items()}
        raw={key:format(v,'f').rstrip('0').rstrip('.') if '.' in format(v,'f') else format(v,'f') for key,v in decimals.items()}
    amounts={key:Fraction(v) for key,v in decimals.items()}
    total=sum(amounts.values())
    if remaining:
        if total>100:raise ValueError('The total exceeds 100%. Use Normalize to 100 first.')
        weights={key:(rng or random).randint(1,1000000) for key,v in amounts.items() if not v and key!='gestalt'}
        budget=100-total
        if not weights:
            if budget:raise ValueError('No blank or zero ideologies remain. Clear a value or normalize to 100.')
            return raw
    else:
        weights=amounts if total else {key:1 for key in amounts if key!='gestalt'}
        if not weights:raise ValueError('Enter a manual Gestalt percentage or define a non-Gestalt ideology')
        budget=Fraction(100)
    # Largest remainders avoid float drift and retain fine authored percentages.
    precision=3
    scale=10**precision;units=int(budget*scale);weight_total=sum(weights.values())
    quotas={key:Fraction(w)*units/weight_total for key,w in weights.items()}
    allocated={key:q.numerator//q.denominator for key,q in quotas.items()}
    order=sorted(weights,key=lambda key:quotas[key]-allocated[key],reverse=True)
    for key in order[:units-sum(allocated.values())]:allocated[key]+=1
    for key,n in allocated.items():
        whole,part=divmod(n,scale)
        raw[key]=(str(whole)+'.'+str(part).zfill(precision)).rstrip('0').rstrip('.')
    return raw


def engine_popularities(values):
    clean={key:number(v,0,100) for key,v in values.items()}
    if sum(Decimal(v) for v in clean.values())!=100:raise ValueError('Party popularities must total exactly 100%')
    return distribute_popularities(clean)


def field_text(text, key, raw):
    """Change all unconditional repeated fields coherently, preserving other scopes."""
    nodes = [n for n in parse(text) if n.key == key]
    if not nodes: return text.rstrip() + '\n' + key + ' = ' + raw + '\n'
    last = nodes[-1]
    for n in reversed(nodes):
        text = text[:n.start] + (key + ' = ' + raw if n is last else '') + text[n.end:]
    return text


def patch_root_block(text, key, fields):
    from character_model import patch_field
    nodes = [n for n in parse(text) if n.key == key and n.children is not None]
    if not nodes: return text.rstrip() + '\n' + key + ' = {\n' + ''.join(f'\t{k} = {v}\n' for k, v in fields.items()) + '}\n'
    # Patch only named children, keeping elections, dates and unrelated options.
    node = nodes[-1]
    for k, v in fields.items():
        node = [n for n in parse(text) if n.key == key and n.children is not None][-1]
        text = patch_field(text, node, k, v)
    return text


def flag_rgb(raw):
    rgb=ImageColor.getrgb(str(raw).strip())
    if len(rgb)!=3:raise ValueError('Use an RGB color, for example #283c63')
    return rgb


@lru_cache(maxsize=64)
def _symbol_mask(data,source_size,canvas_size,scale,offset,stretch,angle):
    w,h=canvas_size;mask=Image.frombytes('L',source_size,data)
    ratio=h*scale/max(mask.size)
    mask=mask.resize((max(1,round(mask.width*ratio*stretch[0])),max(1,round(mask.height*ratio*stretch[1]))),Image.Resampling.LANCZOS)
    if angle:mask=mask.rotate(-angle,Image.Resampling.BICUBIC,expand=True)
    alpha=Image.new('L',(w,h));alpha.paste(mask,(round(w*offset[0]-mask.width/2),round(h*offset[1]-mask.height/2)))
    return alpha


@lru_cache(maxsize=64)
def _outline_mask(data,canvas_size,thickness):
    """Bounded in-memory dilation of the transformed silhouette, including holes."""
    w,h=canvas_size;alpha=Image.frombytes('L',canvas_size,data)
    radius=max(1,round(thickness*h/52))
    return alpha.filter(ImageFilter.MaxFilter(radius*2+1))


def symbol_alpha(symbol,size=(82,52)):
    mask=symbol.get('mask')
    if mask is None:return Image.new('L',size)
    mask=mask.convert('L');mask.thumbnail((256,256),Image.Resampling.LANCZOS)
    scale=float(number(symbol.get('scale',.65),.05,1.5))
    offset=tuple(float(number(symbol.get(k,.5),-.5,1.5)) for k in ('x','y'))
    stretch=tuple(float(number(symbol.get(k,1),.1,3)) for k in ('stretch_x','stretch_y'))
    angle=float(number(symbol.get('angle',0),-180,180))
    canvas=(max(1,round(size[0]*208/size[1])),208)
    alpha=_symbol_mask(mask.tobytes(),mask.size,canvas,scale,offset,stretch,angle)
    return alpha if alpha.size==size else alpha.resize(size,Image.Resampling.LANCZOS)


def render_flag(pattern, colors, mask=None, tint='#ffffff', size=(82, 52), scale=.75, offset=(.5, .5), outline_width=0, outline_color='#000000', symbols=None):
    if pattern not in PATTERNS: raise ValueError('Choose a defined flag pattern')
    colors = [flag_rgb(c) for c in colors]
    if not colors:raise ValueError('Choose at least one background color')
    tint=flag_rgb(tint);outline_color=flag_rgb(outline_color)
    outline_width=float(number(outline_width,0,8))
    colors += [colors[-1]] * max(0, 4-len(colors))
    width, height = size; factor = 4; w, h = width*factor, height*factor
    out = Image.new('RGB', (w, h), colors[0]); d = ImageDraw.Draw(out)
    if pattern in {'Horizontal bicolor', 'Vertical bicolor', 'Horizontal tricolor', 'Vertical tricolor', 'Horizontal 1:2:1', 'Vertical 1:2:1'}:
        vertical = pattern.startswith('Vertical'); length = w if vertical else h
        weights = [1, 1] if 'bicolor' in pattern else [1, 2, 1] if '1:2:1' in pattern else [1, 1, 1]
        at = 0
        for i, weight in enumerate(weights):
            end = round(length * sum(weights[:i+1])/sum(weights))
            d.rectangle((at, 0, end-1, h) if vertical else (0, at, w, end-1), fill=colors[i]); at = end
    elif pattern == 'Diagonal down': d.polygon([(0, 0), (w, h), (0, h)], fill=colors[1])
    elif pattern == 'Diagonal up': d.polygon([(0, h), (w, 0), (w, h)], fill=colors[1])
    elif pattern == 'Quartered':
        for i, box in enumerate([(0, 0, w//2, h//2), (w//2, 0, w, h//2), (0, h//2, w//2, h), (w//2, h//2, w, h)]): d.rectangle(box, fill=colors[i])
    elif pattern in {'Cross', 'Nordic cross'}:
        x = round(w*(.35 if pattern == 'Nordic cross' else .5)); band = max(1, h//5)
        d.rectangle((x-band//2, 0, x+band//2, h), fill=colors[1]); d.rectangle((0, h//2-band//2, w, h//2+band//2), fill=colors[1])
        narrow = max(1, band//2); d.rectangle((x-narrow//2, 0, x+narrow//2, h), fill=colors[2]); d.rectangle((0, h//2-narrow//2, w, h//2+narrow//2), fill=colors[2])
    elif pattern == 'Saltire':
        d.line((0, 0, w, h), fill=colors[1], width=h//5); d.line((0, h, w, 0), fill=colors[1], width=h//5)
    elif pattern == 'Chevron': d.polygon([(0, 0), (w*.48, h/2), (0, h)], fill=colors[1])
    elif pattern == 'Canton': d.rectangle((0, 0, w*.46, h*.52), fill=colors[1])
    elif pattern == 'Border':
        b = h//10; d.rectangle((b, b, w-b-1, h-b-1), fill=colors[1])
    elif pattern == 'Central disk':
        r = h*.35; d.ellipse((w/2-r, h/2-r, w/2+r, h/2+r), fill=colors[1])
    elif pattern.startswith(('Horizontal ','Vertical ')) and pattern.split(' ',1)[1] in {'four-color','five stripes','seven stripes','nine stripes','1:1:2'}:
        vertical=pattern.startswith('Vertical');kind=pattern.split(' ',1)[1];length=w if vertical else h
        if kind=='1:1:2':bands=[0,1,2];weights=[1,1,2]
        elif kind=='four-color':bands=list(range(4));weights=[1]*4
        else:
            count={'five stripes':5,'seven stripes':7,'nine stripes':9}[kind];bands=[i%2 for i in range(count)];weights=[1]*count
        at=0
        for i,index in enumerate(bands):
            end=round(length*sum(weights[:i+1])/sum(weights));d.rectangle((at,0,end-1,h) if vertical else (0,at,w,end-1),fill=colors[index]);at=end
    elif pattern.startswith('Diagonal tricolor'):
        for i in range(3):
            # Parallel diagonal strips, clipped by the flag canvas.
            lo=-w+i*2*w/3;hi=-w+(i+1)*2*w/3
            points=[(lo,0),(hi,0),(hi+w,h),(lo+w,h)]
            if pattern.endswith('up'):points=[(x,h-y) for x,y in points]
            d.polygon(points,fill=colors[i])
    elif pattern.startswith('Diagonal band'):
        coords=(0,0,w,h) if pattern.endswith('down') else (0,h,w,0)
        d.line(coords,fill=colors[1],width=max(1,h//3));d.line(coords,fill=colors[2],width=max(1,h//5))
    elif pattern in {'Plain cross','Plain Nordic cross'}:
        x=round(w*(.35 if 'Nordic' in pattern else .5));band=max(1,h//5)
        d.rectangle((x-band//2,0,x+band//2,h),fill=colors[1]);d.rectangle((0,h//2-band//2,w,h//2+band//2),fill=colors[1])
    elif pattern in {'Bordered saltire','Union cross'}:
        for color,width in [(colors[1],max(1,h//4)),(colors[2],max(1,h//9))]:
            d.line((0,0,w,h),fill=color,width=width);d.line((0,h,w,0),fill=color,width=width)
        if pattern=='Union cross':
            for color,band in [(colors[1],max(1,h//3)),(colors[3],max(1,h//6))]:
                d.rectangle((w//2-band//2,0,w//2+band//2,h),fill=color);d.rectangle((0,h//2-band//2,w,h//2+band//2),fill=color)
    elif pattern in {'Chevron tricolor','Double chevron'}:
        if pattern=='Chevron tricolor':d.rectangle((0,h//2,w,h),fill=colors[1]);d.polygon([(0,0),(w*.5,h/2),(0,h)],fill=colors[2])
        else:
            d.polygon([(0,0),(w*.6,h/2),(0,h)],fill=colors[1]);d.polygon([(0,0),(w*.35,h/2),(0,h)],fill=colors[2])
    elif pattern in {'Hoist triangle','Fly triangle','Triangle with bicolor','Triangle with tricolor'}:
        color=colors[1]
        if 'bicolor' in pattern:d.rectangle((0,h//2,w,h),fill=colors[1]);color=colors[2]
        elif 'tricolor' in pattern:
            d.rectangle((0,h//3,w,h*2//3),fill=colors[1]);d.rectangle((0,h*2//3,w,h),fill=colors[2]);color=colors[3]
        points=[(w,0),(w*.55,h/2),(w,h)] if pattern=='Fly triangle' else [(0,0),(w*.45,h/2),(0,h)]
        d.polygon(points,fill=color)
    elif pattern in {'Lozenge','Nested diamonds'}:
        for fraction,color in ([(.95,colors[1]),(.68,colors[2]),(.4,colors[3])] if pattern=='Nested diamonds' else [(.85,colors[1])]):
            d.polygon([(w/2,h*(1-fraction)/2),(w*(1+fraction)/2,h/2),(w/2,h*(1+fraction)/2),(w*(1-fraction)/2,h/2)],fill=color)
    elif pattern=='Diagonal quarters':
        for color,points in zip(colors,[[(0,0),(w,0),(w/2,h/2)],[(w,0),(w,h),(w/2,h/2)],[(w,h),(0,h),(w/2,h/2)],[(0,h),(0,0),(w/2,h/2)]]):d.polygon(points,fill=color)
    elif pattern in {'Checkerboard','Small checkerboard'}:
        cols,rows=(8,6) if pattern=='Small checkerboard' else (4,4)
        for y in range(rows):
            for x in range(cols):d.rectangle((round(x*w/cols),round(y*h/rows),round((x+1)*w/cols)-1,round((y+1)*h/rows)-1),fill=colors[(x+y)%2])
    elif pattern=='Stripes with canton':
        for i in range(7):d.rectangle((0,round(i*h/7),w,round((i+1)*h/7)-1),fill=colors[i%2])
        d.rectangle((0,0,w*.45,h*4/7),fill=colors[2])
    elif pattern=='Sunburst':
        for i in range(16):
            angles=[i*math.tau/16,(i+1)*math.tau/16]
            d.polygon([(w/2,h/2),*[(w/2+2*w*math.cos(a),h/2+2*w*math.sin(a)) for a in angles]],fill=colors[i%4])
    elif pattern=='Pall':
        d.polygon([(0,0),(w,0),(w,h/2),(w*.45,h/2)],fill=colors[1]);d.polygon([(0,h),(w,h),(w,h/2),(w*.45,h/2)],fill=colors[2])
        d.line((0,0,w*.45,h/2,w,h/2),fill=colors[3],width=max(1,h//7));d.line((0,h,w*.45,h/2),fill=colors[3],width=max(1,h//7))
    elif pattern=='Serrated hoist':
        points=[(0,0),(w*.28,0)]
        for i in range(10):points.append((w*(.4 if i%2 else .28),h*(i+1)/10))
        d.polygon([*points,(0,h)],fill=colors[1])
    elif pattern in {'Rising diagonal stripes','Falling diagonal stripes'}:
        for i in range(-7,8):
            lo=i*w/5;hi=(i+1)*w/5;points=[(lo,0),(hi,0),(hi+w,h),(lo+w,h)]
            if pattern.startswith('Rising'):points=[(x,h-y) for x,y in points]
            d.polygon(points,fill=colors[i%2])
    elif pattern=='Central ring':
        for radius,color in [(h*.36,colors[1]),(h*.25,colors[0])]:d.ellipse((w/2-radius,h/2-radius,w/2+radius,h/2+radius),fill=color)
    elif pattern=='Double border':
        for inset,color in [(h*.06,colors[1]),(h*.13,colors[2]),(h*.2,colors[3])]:d.rectangle((inset,inset,w-inset-1,h-inset-1),fill=color)
    elif pattern in {'Horizontal gradient','Vertical gradient'}:
        vertical=pattern.startswith('Vertical');length=h if vertical else w
        for i in range(length):
            t=i/max(1,length-1)*3;index=min(2,int(t));blend=t-index
            color=tuple(round(a+(b-a)*blend) for a,b in zip(colors[index],colors[index+1]))
            d.line((0,i,w,i) if vertical else (i,0,i,h),fill=color)
    if symbols is None:symbols=[dict(mask=mask,tint=tint,scale=scale,x=offset[0],y=offset[1],outline_width=outline_width,outline_color=outline_color)]
    if len(symbols)>8:raise ValueError('Use at most eight symbols')
    for symbol in symbols:
        if symbol.get('mask') is None:continue
        color=symbol.get('tint','#ffffff');color=flag_rgb(color) if isinstance(color,str) else color
        edge=float(number(symbol.get('outline_width',0),0,8));edge_color=symbol.get('outline_color','#000000');edge_color=flag_rgb(edge_color) if isinstance(edge_color,str) else edge_color
        alpha=symbol_alpha(symbol,(max(1,round(w*208/h)),208))
        if edge:
            outline=_outline_mask(alpha.tobytes(),alpha.size,edge)
            out.paste(edge_color,(0,0),outline.resize((w,h),Image.Resampling.LANCZOS))
        out.paste(color,(0,0),alpha.resize((w,h),Image.Resampling.LANCZOS))
    return out.resize(size, Image.Resampling.LANCZOS)


@dataclass
class Country:
    tag: str
    path: str
    name: str
    capital: str = ''
    stability: str = '50'
    war_support: str = '50'
    ruling: str = ''
    popularities: dict = field(default_factory=dict)
    technologies: dict = field(default_factory=dict)
    ideas: set = field(default_factory=set)
    laws: dict = field(default_factory=dict)
    names: dict = field(default_factory=dict)
    portrait_group: str | None = None


class CountrySourceExists(ValueError):
    def __init__(self,paths):
        self.paths=tuple(paths)
        super().__init__('Country sources already exist: '+', '.join(self.paths))


class CountryStore:
    def __init__(self, world, characters, catalogs, emblems=None):
        self.world, self.characters, self.catalogs, self.docs = world, characters, catalogs, world.docs
        self.emblems = emblems; self._cache = {};self._native_bonus_sources={};self._icon_previews=OrderedDict()

    def cached(self, key, signature, build):
        cached = self._cache.get(key)
        if cached is None or cached[0] != signature: cached = self._cache[key] = (signature, build())
        return cached[1]

    def summary(self,tag):
        signature=(tag,tuple(self.docs.text(s.path) for s in self.world.states.values()))
        def build():
            out={'states':0,'population':0,'factories':{'industrial_complex':0,'arms_factory':0,'dockyard':0},'resources':{}}
            if not re.fullmatch('[A-Z][A-Z0-9]{2}',tag):return out
            for sid in self.world.states:
                text,nodes=self.world.state_nodes(sid);history=block(nodes,'history')
                if history is None or atom(text,history.children,'owner')!=tag:continue
                out['states']+=1;out['population']+=Decimal(number(atom(text,nodes,'manpower','0'),0))
                resources=block(nodes,'resources')
                state_resources={}
                for n in resources.children if resources else []:
                    if n.children is None:state_resources[n.key]=Decimal(number(value(text,n),0))
                for key,amount in state_resources.items():out['resources'][key]=out['resources'].get(key,Decimal(0))+amount
                levels={}
                for container in history.children:
                    if container.key=='buildings' and container.children is not None:
                        for n in container.children:
                            if n.key in out['factories'] and n.children is None:levels[n.key]=int(Decimal(number(value(text,n),0)))
                for kind,amount in levels.items():out['factories'][kind]+=amount
            return out
        return self.cached(('summary',tag),signature,build)

    def ideologies(self):
        files = self.characters.files('common/ideologies', '.txt')
        signature = tuple(self.docs.text(p) for p in files)
        def build():
            out = {}
            for path in files:
                text, roots = self.docs.parsed(path); root = block(roots, 'ideologies')
                for n in root.children if root else []:
                    if n.children is None: continue
                    types = block(n.children, 'types'); color = block(n.children, 'color')
                    out[n.key] = {'types': tuple(c.key for c in types.children if c.children is not None) if types else (),
                                  'color': self.world._script_colour(text, color) if color else (128, 128, 128)}
            return out
        return self.cached('ideologies', signature, build)

    def names(self, tag):
        loc = self.characters.localisations()
        return {i: {'name': loc.get(tag + ('_'+i if i else '')), 'def': loc.get(tag + ('_'+i if i else '') + '_DEF')}
                for i in ('', *self.ideologies())}

    def set_loc(self, preferred, key, content):
        # Edit the existing owner(s) of a key; new strings join the native file.
        records = self.characters.loc_records().get(key, [])
        paths = list(dict.fromkeys(r[0] for r in records)) or [preferred]
        for path in paths:
            if content is None:
                text = self.docs.text(path); lines = text.splitlines(keepends=True)
                self.docs.replace(path, ''.join(line for line in lines if not ((m := LOC.match(line)) and m[1] == key)))
            else: self.catalogs.set_loc(path, key, content)

    def definitions(self, folder, container):
        files = self.characters.files(folder, '.txt'); signature = tuple(self.docs.text(p) for p in files)
        def build():
            out = {}
            for path in files:
                text, roots = self.docs.parsed(path)
                for root in roots:
                    if root.key != container or root.children is None: continue
                    if container == 'ideas':
                        for category in root.children:
                            if category.children is None: continue
                            for n in category.children:
                                if n.children is not None: out[n.key] = (category.key, path, text, n)
                    else:
                        for n in root.children:
                            if n.children is not None and not n.key.startswith('@'): out[n.key] = ('', path, text, n)
            return out
        return self.cached((folder, container), signature, build)

    def ideas(self): return self.definitions('common/ideas', 'ideas')
    def technologies(self): return self.definitions('common/technologies', 'technologies')

    def spirit_bonus_catalog(self):
        folders=('common/technology_tags','common/units/equipment')
        descriptor=self.docs.text('descriptor.mod')
        replaced=[value(descriptor,n).strip('"').rstrip('/') for n in parse(descriptor) if n.key=='replace_path']
        sources=[]
        for folder in folders:
            mods={p for p in self.characters.files(folder,'.txt') if self.docs.binary(p) is not None}
            if not any(folder==p or folder.startswith(p+'/') for p in replaced):
                native_key=(str(self.characters.game_root),folder)
                if native_key not in self._native_bonus_sources:
                    self._native_bonus_sources[native_key]=[(path.relative_to(self.characters.game_root).as_posix(),read_text(path))
                        for path in sorted((self.characters.game_root/folder).rglob('*.txt'))]
                sources.extend((relative,text) for relative,text in self._native_bonus_sources[native_key] if relative not in mods)
            sources.extend((p,self.docs.text(p)) for p in sorted(mods))
        def build():
            research=set();equipment=set();stats=set()
            metadata={'year','priority','visual_level','air_map_icon_frame','interface_overview_category_index',
                      'default_carrier_composition_weight','max_military_factories','railway_gun_attack_range_index_in_define'}
            for path,text in sources:
                for root in parse(text):
                    if root.key=='technology_categories':
                        research.update(n.key for n in root.children or [] if not n.op)
                    elif root.key=='equipments':
                        for item in root.children or []:
                            if item.children is None:continue
                            equipment.add(item.key)
                            for field in item.children:
                                if field.key=='type':equipment.update([value(text,field).strip('"')] if field.children is None else [n.key for n in field.children if not n.op])
                            for field in item.children:
                                if field.children is not None or field.key in metadata:continue
                                try:number(value(text,field))
                                except ValueError:continue
                                stats.add(field.key)
                    elif root.key=='equipment_modules':
                        for item in root.children or []:
                            for section in item.children or []:
                                if section.key not in {'add_stats','multiply_stats'}:continue
                                stats.update(n.key for n in section.children or [] if n.children is None)
            return {'research':research,'equipment':equipment,'stats':stats}
        return self.cached('spirit_bonus_catalog',tuple(sources),build)

    def bonus_choices(self,kind):
        names=self.characters.trait_store.names();keys=self.spirit_bonus_catalog()[kind]
        def label(key):
            candidates=[key]+['STAT_'+group+'_'+key.upper() for group in ('COMMON','ARMY','AIR','NAVY')]
            return next((names[c] for c in candidates if c in names),key.replace('_',' ').title())
        return tuple(Choice(key,label(key)) for key in sorted(keys))

    def spirit_bonuses(self,key):
        research={};equipment={}
        if key is None:return research,equipment
        _,_,text,node=self.ideas()[key]
        for section in node.children:
            if section.key=='research_bonus':
                research.update((n.key,value(text,n)) for n in section.children or [] if n.children is None)
            elif section.key=='equipment_bonus':
                for eq in section.children or []:
                    if eq.children is None:continue
                    fields={n.key:value(text,n) for n in eq.children if n.children is None}
                    if fields:equipment.setdefault(eq.key,{}).update(fields)
        return research,equipment

    def validate_spirit_bonuses(self,research,equipment,previous):
        if research is None and equipment is None:return None,None
        catalog=self.spirit_bonus_catalog();old_research,old_equipment=previous
        if research is not None:
            research=dict(research)
            for key,raw in research.items():
                if key not in catalog['research'] and key not in old_research:raise ValueError('Choose a defined research category')
                if raw!=old_research.get(key):research[key]=number(raw)
        if equipment is not None:
            equipment={key:dict(fields) for key,fields in equipment.items()}
            for key,fields in equipment.items():
                if key not in catalog['equipment'] and key not in old_equipment:raise ValueError('Choose a defined equipment type')
                old=old_equipment.get(key,{})
                for stat,raw in fields.items():
                    if raw==old.get(stat):continue
                    if stat=='instant':
                        if raw not in {'yes','no'}:raise ValueError('Instant must be yes or no')
                    else:
                        if stat not in catalog['stats'] and stat not in old:raise ValueError('Choose a defined equipment stat')
                        fields[stat]=number(raw)
        return research,equipment

    @staticmethod
    def patch_spirit_bonus(text,kind,before,after):
        """Patch only changed scalar leaves, including repeated native blocks."""
        from character_model import patch_field
        if after is None:return text
        flatten=lambda data:{(eq,stat):raw for eq,fields in data.items() for stat,raw in fields.items()} if kind=='equipment_bonus' else {(key,):raw for key,raw in data.items()}
        old,new=flatten(before),flatten(after)
        for path in sorted(old.keys()|new.keys()):
            if path in old and path in new and old[path]==new[path]:continue
            root=parse(text)[0];sections=[n for n in root.children if n.key==kind and n.children is not None]
            parents=sections if kind=='research_bonus' else [n for section in sections for n in section.children if n.key==path[0] and n.children is not None]
            leaves=[n for parent in parents for n in parent.children if n.key==path[-1] and n.children is None]
            if leaves:
                for n in reversed(leaves):
                    text=text[:n.value_start]+new[path]+text[n.end:] if path in new else text[:n.start]+text[n.end:]
            elif path in new:
                if parents:text=patch_field(text,parents[-1],path[-1],new[path])
                else:
                    raw='{\n\t\t\t\t'+path[-1]+' = '+new[path]+'\n\t\t\t}'
                    if kind=='equipment_bonus' and sections:text=patch_field(text,sections[-1],path[0],raw)
                    else:
                        if kind=='equipment_bonus':raw='{\n\t\t\t'+path[0]+' = '+raw+'\n\t\t}'
                        text=patch_field(text,root,kind,raw)
        return text

    def choices(self, kind):
        loc = self.characters.trait_store.names()
        if kind == 'technologies': keys = self.technologies()
        elif kind == 'spirits': keys = [k for k, r in self.ideas().items() if r[0] in {'country', 'hidden_ideas'}]
        else: keys = [k for k, r in self.ideas().items() if r[0] == kind]
        return tuple(Choice(k, re.sub('[\x15§].', '', loc.get(k, k))) for k in keys)

    @staticmethod
    def idea_values(text, node):
        return [c.key for c in node.children] if node.children is not None else [value(text, node).strip('"')]

    def history_ideas(self, text):
        out = set()
        for n in parse(text):
            if n.key == 'add_ideas': out.update(self.idea_values(text, n))
            elif n.key == 'remove_ideas': out.difference_update(self.idea_values(text, n))
        return out

    def startup_laws(self, tag, initial):
        text, effect = self.catalogs.startup(); out = set(initial)
        history = self.docs.text(self.world.countries.get(tag,f'history/countries/{tag}.txt'))
        flags = {value(history,n).strip('"') for n in parse(history) if n.key=='set_country_flag'}
        relevant = {k for k, r in self.ideas().items() if r[0] in {'species', 'specialty'}}
        triggers = {}
        for path in self.characters.files('common/scripted_triggers', '.txt'):
            t = self.docs.text(path)
            # Load only native tag classifiers used by country-species startup.
            if 'is_herzlands_warlord' not in t and 'is_roqualian' not in t: continue
            for n in parse(t): triggers[n.key] = (t, n.children)
        def limit(t, nodes, depth=0):
            if depth > 12: return False
            tests = []
            for n in nodes:
                v = value(t, n).strip('"')
                if n.key in {'OR', 'AND', 'NOT'}:
                    vals = [limit(t, [c], depth+1) for c in n.children]
                    ok = any(vals) if n.key == 'OR' else all(vals) if n.key == 'AND' else not any(vals)
                elif n.key in {'tag', 'original_tag'}: ok = v == tag
                elif n.key == 'has_idea': ok = v in out
                elif n.key == 'has_country_flag': ok = v in flags
                elif n.key == 'always': ok = v == 'yes'
                elif n.key in triggers:
                    tt, ns = triggers[n.key]; ok = limit(tt, ns, depth+1)
                    if v == 'no': ok = not ok
                else: ok = False
                tests.append(ok)
            return all(tests)
        def run(nodes):
            matched = False
            for n in nodes:
                if n.key in {'if', 'else_if', 'else'}:
                    if n.key == 'if': matched = False
                    condition = block(n.children, 'limit')
                    if not matched and (condition is None or limit(text, condition.children)):
                        run([c for c in n.children if c is not condition]); matched = True
                elif n.key in {tag, 'every_possible_country', 'every_country'} and n.children:
                    condition = block(n.children, 'limit')
                    if condition is None or limit(text, condition.children): run([c for c in n.children if c is not condition])
                elif n.key in {'add_ideas', 'remove_ideas'}:
                    for key in self.idea_values(text, n):
                        if key not in relevant: continue
                        if n.key == 'remove_ideas': out.discard(key)
                        else:
                            category = self.ideas()[key][0]
                            out.difference_update(k for k in list(out) if k in self.ideas() and self.ideas()[k][0] == category); out.add(key)
        run(effect.children)
        return {self.ideas()[k][0]: k for k in out if k in relevant}

    def read(self, tag):
        path = self.world.countries.get(tag, f'history/countries/{tag}.txt')
        text = self.docs.text(path); roots = parse(text); politics = [n for n in roots if n.key == 'set_politics' and n.children]
        popularity = [n for n in roots if n.key == 'set_popularities' and n.children]
        popularities = {i: '0' for i in self.ideologies()}
        if popularity: popularities.update({n.key: value(text, n) for n in popularity[-1].children if n.children is None})
        ruling = atom(text, politics[-1].children, 'ruling_party') if politics else next(iter(self.ideologies()), '')
        if not popularity and ruling: popularities[ruling] = '100'
        technologies = {n.key: value(text, n) for root in roots if root.key == 'set_technology' and root.children
                        for n in root.children if n.children is None and n.key != 'popup'}
        ideas = self.history_ideas(text); definitions = self.ideas()
        laws = {definitions[k][0]: k for k in ideas if k in definitions and definitions[k][0] not in {'country', 'hidden_ideas'}}
        laws.update(self.startup_laws(tag, ideas))
        laws.setdefault('mobilization_laws', 'volunteer_only'); laws.setdefault('economy', 'civilian_economy')
        laws.setdefault('specialty', 'specialty_nothing'); laws.setdefault('species', 'var_species_0')
        def pct(key): return format(Decimal(atom(text, roots, key, '.5'))*100, 'f')
        return Country(tag, path, self.characters.neutral_name(tag), atom(text, roots, 'capital'), pct('set_stability'), pct('set_war_support'), ruling, popularities,
                       technologies, {k for k in ideas if k not in definitions or definitions[k][0] in {'country', 'hidden_ideas'}}, laws, self.names(tag),
                       self.characters.generic_portraits.group_for_country(tag))

    def write_names(self, tag, names):
        for ideology, fields in names.items():
            if ideology and ideology not in self.ideologies(): raise ValueError('Choose a defined ideology')
            base = tag + ('_'+ideology if ideology else '')
            self.set_loc(COUNTRY_LOC, base, fields.get('name'))
            self.set_loc(COUNTRY_LOC, base+'_DEF', fields.get('def'))

    def rewrite_ideas(self, text, wanted, categories, extra=()):
        definitions = self.ideas(); edits = []
        for n in parse(text):
            if n.key not in {'add_ideas', 'remove_ideas'}: continue
            owned = [k for k in self.idea_values(text, n) if k in extra or k in definitions and definitions[k][0] in categories]
            if not owned: continue
            keep = [k for k in self.idea_values(text, n) if k not in owned]
            raw = n.key + ' = { ' + ' '.join(keep) + ' }' if keep else ''
            edits.append((n.start, n.end, raw))
        for a, b, raw in reversed(edits): text = text[:a] + raw + text[b:]
        return text.rstrip() + ('\nadd_ideas = { ' + ' '.join(sorted(wanted)) + ' }\n' if wanted else '\n')

    @staticmethod
    def rewrite_technologies(text,technologies):
        roots=[n for n in parse(text) if n.key=='set_technology' and n.children is not None]
        present={n.key for root in roots for n in root.children if n.children is None and n.key!='popup'}
        added={k:v for k,v in technologies.items() if k not in present}
        if not roots:
            return 'set_technology = {\n'+''.join(f'\t{k} = {v}\n' for k,v in sorted(technologies.items()))+'}\n'+text
        edits=[]
        for root in roots:
            raw=text[root.start:root.end]; changes=[]
            for n in root.children:
                if n.children is not None or n.key=='popup':continue
                if n.key not in technologies:changes.append((n.start-root.start,n.end-root.start,''))
                elif value(text,n)!=technologies[n.key]:changes.append((n.value_start-root.start,n.end-root.start,technologies[n.key]))
            for a,b,replacement in reversed(changes):raw=raw[:a]+replacement+raw[b:]
            if root is roots[0] and added:
                raw=raw[:-1]+'\n'+''.join(f'\t{k} = {v}\n' for k,v in sorted(added.items()))+'}'
            edits.append((root.start,root.end,raw))
        for a,b,raw in reversed(edits):text=text[:a]+raw+text[b:]
        return text

    def protect_history_species(self):
        """Keep native defaults for untouched countries; explicit history wins."""
        self.protect_history_laws('species',SPECIES_HISTORY_FLAG)

    def protect_history_laws(self,category,flag):
        allowed={k for k,r in self.ideas().items() if r[0]==category}
        text,effect=self.catalogs.startup();edits=[]
        def visit(nodes,guarded=False):
            for n in nodes:
                condition=block(n.children,'limit') if n.children is not None and n.key in {'if','else_if'} else None
                guard=guarded or condition is not None and flag in text[condition.start:condition.end]
                if n.key in {'add_ideas','remove_ideas'} and allowed.intersection(self.idea_values(text,n)) and not guarded:
                    keys=self.idea_values(text,n);species=[k for k in keys if k in allowed];other=[k for k in keys if k not in allowed]
                    raw=n.key+' = { '+' '.join(species)+' }'
                    preserve=n.key+' = { '+' '.join(other)+' }\n' if other else ''
                    edits.append((n.start,n.end,preserve+f'if = {{ limit = {{ NOT = {{ has_country_flag = {flag} }} }} {raw} }}'))
                elif category=='specialty' and n.key=='add_tech_bonus' and atom(text,n.children,'name') in allowed and not guarded:
                    raw=text[n.start:n.end];edits.append((n.start,n.end,f'if = {{ limit = {{ NOT = {{ has_country_flag = {flag} }} }} {raw} }}'))
                elif n.children is not None:visit(n.children,guard)
        visit(effect.children)
        for a,b,raw in sorted(edits,reverse=True):text=text[:a]+raw+text[b:]
        self.docs.replace(STARTUP,text)

    def startup_attribute(self,tag,key):
        self.protect_history_laws('specialty',ATTRIBUTE_HISTORY_FLAG)
        text,effect=self.catalogs.startup();templates={}
        for _,n in walk(effect.children):
            if n.key=='add_tech_bonus' and n.children:
                name=atom(text,n.children,'name')
                if name.startswith('specialty_'):templates[name]=text[n.start:n.end]
        edits=[]
        for root in effect.children:
            if root.key!=tag or not root.children:continue
            owned=[]
            for n in root.children:
                condition=block(n.children,'limit') if n.children and n.key=='if' else None
                if condition and ATTRIBUTE_HISTORY_FLAG in text[condition.start:condition.end] and 'NOT' not in text[condition.start:condition.end]:
                    if all(c.key in {'limit','add_tech_bonus'} for c in n.children):owned.append(n)
            if owned and len(owned)==len(root.children):edits.append((root.start,root.end,''))
            else:edits.extend((n.start,n.end,'') for n in owned)
        for a,b,raw in reversed(edits):text=text[:a]+raw+text[b:]
        self.docs.replace(STARTUP,text)
        if key in templates:
            text,effect=self.catalogs.startup()
            cohort=[n for n in effect.children if any(c.key in {'add_ideas','remove_ideas'} and any(v.startswith('specialty_') for v in self.idea_values(text,c)) for _,c in walk([n]))]
            if not cohort:raise ValueError('Missing native attribute startup cohort')
            at=cohort[-1].end;addition=f'\n\t\t\t{tag} = {{ if = {{ limit = {{ has_country_flag = {ATTRIBUTE_HISTORY_FLAG} has_idea = {key} }} '+templates[key]+' } }\n'
            self.docs.replace(STARTUP,text[:at]+addition+text[at:])

    def apply(self, country, color, names, flags=None, create=False, overwrite=False):
        tag = country.tag
        if not re.fullmatch(r'[A-Z][A-Z0-9]{2}', tag): raise ValueError('Use a three-character uppercase country tag, starting with a letter')
        if create == (tag in self.world.country_paths): raise ValueError('Choose a new unused tag' if create else 'Choose an existing country')
        if create and not (names.get('', {}).get('name') or '').strip(): raise ValueError('Enter the base country name')
        if not str(country.capital).isdigit() or int(country.capital) not in self.world.states: raise ValueError('Choose a defined capital state')
        if country.ruling not in self.ideologies(): raise ValueError('Choose a ruling ideology')
        pop = {i: number(v, 0, 100) for i, v in country.popularities.items()}
        if any(i not in self.ideologies() for i in pop): raise ValueError('Unknown ideology in popularities')
        pop=engine_popularities(pop)
        stability = Decimal(number(country.stability, 0, 100))/100; war = Decimal(number(country.war_support, 0, 100))/100
        tech = {k: number(v, 0, 100) for k, v in country.technologies.items()}
        existing = self.read(tag) if not create else None
        old_history=self.docs.text(country.path) if not create else ''
        species_defined=any(n.key=='set_country_flag' and value(old_history,n)==SPECIES_HISTORY_FLAG for n in parse(old_history))
        attribute_defined=any(n.key=='set_country_flag' and value(old_history,n)==ATTRIBUTE_HISTORY_FLAG for n in parse(old_history))
        if any(k not in self.technologies() and (not existing or k not in existing.technologies) for k in tech): raise ValueError('Choose defined technologies')
        definitions = self.ideas()
        laws=dict(country.laws)
        if create:
            for category,key in {'mobilization_laws':'volunteer_only','economy':'civilian_economy','specialty':'specialty_nothing','species':'var_species_0'}.items():laws.setdefault(category,key)
        for category, key in laws.items():
            if not key and category!='economy_laws':raise ValueError('Choose a defined '+category+' law')
            if key and (key not in definitions or definitions[key][0] != category): raise ValueError('Choose a defined '+category+' law')
        if any(k not in definitions and (not existing or k not in existing.ideas) for k in country.ideas): raise ValueError('Choose defined national spirits')
        rgb = flag_rgb(color) if isinstance(color, str) else tuple(color)
        if len(rgb) != 3: raise ValueError('Choose an RGB map color')
        history=f'history/countries/{tag}.txt';definition=f'common/countries/{tag}.txt'
        if create:
            histories=[p for p in self.characters.files('history/countries','.txt') if Path(p).name[:3]==tag and self.docs.binary(p) is not None]
            if len(histories)>1:raise ValueError('Multiple history files use this tag; choose one source before creating the country: '+', '.join(histories))
            if histories:history=histories[0]
            conflicts=[p for p in (definition,history) if self.docs.binary(p) is not None]
            if conflicts and not overwrite:raise CountrySourceExists(conflicts)
        with self.docs.grouped():
            if create:
                text = self.docs.text(TAGS); self.docs.replace(TAGS, text.rstrip()+f'\n{tag} = "countries/{tag}.txt"\n')
                if not self.docs.text(definition).strip():self.docs.replace(definition, 'graphical_culture = western_european_gfx\ngraphical_culture_2d = western_european_2d\n')
                country.path = history
            definition = self.world.country_paths.get(tag, f'common/countries/{tag}.txt')
            self.docs.replace(definition, field_text(self.docs.text(definition), 'color', 'rgb { '+' '.join(map(str,rgb))+' }'))
            # Keep existing UI-color fields in sync with the single country color.
            text=self.docs.text(definition)
            if any(n.key=='color_ui' for n in parse(text)):self.docs.replace(definition,field_text(text,'color_ui','rgb { '+' '.join(map(str,rgb))+' }'))
            # colors.txt is the authoritative override where an entry already exists.
            colors = 'common/countries/colors.txt'; text = self.docs.text(colors)
            if any(n.key==tag and n.children for n in parse(text)):
                from character_model import patch_field
                raw='rgb { '+' '.join(map(str,rgb))+' }'
                for node in reversed([n for n in parse(text) if n.key==tag and n.children]):
                    snippet=text[node.start:node.end]
                    for key in ('color','color_ui'):
                        root=parse(snippet)[0]
                        if key=='color' or any(n.key==key for n in root.children):
                            for n in reversed([n for n in root.children if n.key==key]):snippet=snippet[:n.value_start]+raw+snippet[n.end:]
                            if not any(n.key==key for n in root.children):snippet=patch_field(snippet,parse(snippet)[0],key,raw)
                    text=text[:node.start]+snippet+text[node.end:]
                self.docs.replace(colors,text)
            text = self.docs.text(country.path)
            for key, raw in [('capital',str(country.capital)),('set_stability',format(stability,'f')),('set_war_support',format(war,'f'))]: text = field_text(text,key,raw)
            text = patch_root_block(text,'set_politics',{'ruling_party':country.ruling})
            raw = '{\n'+''.join(f'\t{i} = {pop.get(i,"0")}\n' for i in self.ideologies())+'}'
            text = field_text(text,'set_popularities',raw)
            if create or tech != existing.technologies:
                text=self.rewrite_technologies(text,tech)
            if create or country.ideas != existing.ideas:
                text = self.rewrite_ideas(text,country.ideas,{'country','hidden_ideas'},existing.ideas if existing else ())
            for category,key in laws.items():
                if create or key != existing.laws.get(category,'') or category=='species' and not species_defined or category=='specialty' and not attribute_defined:
                    text = self.rewrite_ideas(text,{key} if key else set(),{category})
                    if category=='specialty':
                        if not any(n.key=='set_country_flag' and value(text,n)==ATTRIBUTE_HISTORY_FLAG for n in parse(text)):
                            text=text.rstrip()+f'\nset_country_flag = {ATTRIBUTE_HISTORY_FLAG}\n'
                        self.startup_attribute(tag,key)
                    elif category=='species':
                        if not any(n.key=='set_country_flag' and value(text,n)==SPECIES_HISTORY_FLAG for n in parse(text)):
                            text=text.rstrip()+f'\nset_country_flag = {SPECIES_HISTORY_FLAG}\n'
                        self.protect_history_species()
            self.docs.replace(country.path,text)
            if create and names[''].get('def') is None:names['']['def']=names['']['name']
            self.write_names(tag,names)
            if country.portrait_group is not None:
                self.characters.generic_portraits.assign_country(tag,country.portrait_group)
            for ideology, image in (flags or {}).items(): self.write_flag(tag,ideology,image)
            if create and '' not in (flags or {}): self.write_flag(tag,'',Image.new('RGB',(82,52),rgb))
            self.world.refresh_countries()
            self.characters._cache.pop('choices:countries',None)

    @staticmethod
    def flag_path(tag, ideology, size='large'):
        return 'gfx/flags/'+('' if size=='large' else size+'/')+tag+('_'+ideology if ideology else '')+'.tga'

    def flag(self, tag, ideology, fallback=True):
        blob = self.docs.binary(self.flag_path(tag,ideology))
        if blob is None and fallback: blob = self.docs.binary(self.flag_path(tag,''))
        if blob is None: return None
        with Image.open(io.BytesIO(blob)) as image: return image.convert('RGB')

    def write_flag(self, tag, ideology, image):
        if not re.fullmatch('[A-Z][A-Z0-9]{2}',tag) or ideology and ideology not in self.ideologies(): raise ValueError('Choose a native tag/ideology')
        for size, dimensions in FLAG_SIZES.items():
            out=io.BytesIO(); image.convert('RGB').resize(dimensions,Image.Resampling.LANCZOS).convert('RGBA').save(out,format='TGA')
            self.docs.stage_bytes(self.flag_path(tag,ideology,size),out.getvalue())

    def leaders(self, tag):
        types={t:g for g,info in self.ideologies().items() for t in info['types']}; out={g:[] for g in self.ideologies()}
        for c in self.characters.characters().values():
            if tag not in c.countries: continue
            for role in c.roles:
                if role.key=='country_leader':
                    ideology=atom(c.text,role.children,'ideology'); group=types.get(ideology)
                    if group: out[group].append((c.key,ideology))
        path=self.world.countries.get(tag,f'history/countries/{tag}.txt'); text=self.docs.text(path)
        for n in parse(text):
            if n.key!='promote_character':continue
            key=atom(text,n.children,'character') if n.children else value(text,n).strip('"')
            subtype=atom(text,n.children,'ideology') if n.children else ''
            for g,rows in out.items():
                for row in list(rows):
                    if row[0]==key and (not subtype or subtype==row[1]): rows.remove(row);rows.append(row)
        return out

    def set_leader(self, tag, key, subtype, name=None, description='', portrait=''):
        groups={t:g for g,d in self.ideologies().items() for t in d['types']}
        if subtype not in groups: raise ValueError('Choose a leader subideology')
        with self.docs.grouped():
            if name is not None:
                if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',key) or key in self.characters.characters(): raise ValueError('Choose a unique character ID')
                if not name.strip(): raise ValueError('Enter a leader name')
                if key in self.characters.localisations():raise ValueError('That character localisation key already exists')
                path=f'common/characters/{tag} - characters.txt';text=self.docs.text(path) or 'characters = {\n}\n';root=block(parse(text),'characters')
                if not root:raise ValueError('Character source needs a characters block')
                raw=f'\n\t{key} = {{ name = {key} country_leader = {{ ideology = {subtype} desc = {key}_desc expire = "2100.1.1" traits = {{ }} }} }}\n'
                self.docs.replace(path,text[:root.end-1]+raw+text[root.end-1:]);self.set_loc('localisation/english/characters_l_english.yml',key,name);self.set_loc('localisation/english/characters_l_english.yml',key+'_desc',description)
            person=self.characters.characters().get(key)
            if person is None:raise ValueError('Choose a character from the database')
            if not any(r.key=='country_leader' and atom(person.text,r.children,'ideology')==subtype for r in person.roles):
                self.characters.edit_role(key,None,'country_leader',{'ideology':subtype,'expire':'"2100.1.1"','desc':person.description_key},[])
            if portrait:
                from character_model import patch_field
                p=self.characters.portraits()[portrait];person=self.characters.characters()[key]
                portraits=block(person.node.children,'portraits');raw='{ large = '+quote(p.large)+(' small = '+quote(p.small) if p.small else '')+' }'
                if portraits:self.docs.replace(person.path,patch_field(person.text,portraits,'civilian',raw))
                else:self.characters._character_field(key,'portraits','{ civilian = '+raw+' }')
            path=self.world.countries.get(tag,f'history/countries/{tag}.txt');text=self.docs.text(path)
            if tag not in self.characters.recruitments().get(key,()):text=text.rstrip()+f'\nrecruit_character = {key}\n'
            # Explicit promotion avoids relying on recruitment order; other roles/recruitments remain.
            text += f'\npromote_character = {{ character = {key} ideology = {subtype} }}\n';self.docs.replace(path,text)

    def eaw_icon_catalog(self):
        def build():
            root=self.docs.root/EAW_IDEAS;out={}
            for path in sorted(asset_files(root)) if root.is_dir() else []:
                relative=path.relative_to(root).as_posix();code='eaw:'+relative
                out[code]={'texture':EAW_IDEAS+'/'+relative,'origin':'EaW','eaw_asset':relative,'frames':'1',
                           'choice':Choice(code,'EaW: '+str(Path(relative).with_suffix('')).replace('_',' '))}
            return out
        return self.cached('eaw_icons',str(self.docs.root),build)

    def icon_catalog(self):
        mod=self.characters.sprites(); vanilla=inherited_sprites(str(self.characters.game_root),'GFX_idea_')
        eaw=self.eaw_icon_catalog()
        credits=self.docs.text(EAW_CREDITS)
        loc=self.characters.trait_store.names();signature=(mod,vanilla,loc,eaw,credits)
        def build():
            out={};provenance=eaw_credit_sources(credits);library={}
            for row in eaw.values():library.setdefault(Path(row['eaw_asset']).name.casefold(),set()).add(row['eaw_asset'])
            for source,entries in [('Vanilla',vanilla),('Mod',mod)]:
                for key,rows in entries.items():
                    if not key.startswith('GFX_idea_') or not rows:continue
                    row=rows[0]; short=key.removeprefix('GFX_idea_')
                    code='vanilla:'+key if source=='Vanilla' else key
                    origin=source;extra={}
                    prefix=EAW_TEXTURES+'/'
                    texture=row['texture'].replace('\\','/')
                    if source=='Mod' and texture.startswith(prefix):
                        origin='EaW';relative=texture[len(prefix):]
                        original=provenance.get((texture.casefold(),short))
                        if original is None and '/' in relative:
                            first,rest=relative.split('/',1)
                            original=rest if re.fullmatch('[0-9a-fA-F]{16,64}',first) else relative
                        if original is None:
                            candidates={asset for (path,_),asset in provenance.items() if path==texture.casefold()} or library.get(Path(texture).name.casefold(),set())
                            if len(candidates)==1:original=next(iter(candidates))
                        extra['eaw_asset']=original
                    out[code]={**row,**extra,'origin':origin,'choice':Choice(code,loc.get(short,short.replace('_',' ').title()))}
            out.update(eaw)
            return out
        return self.cached('icons',signature,build)

    def icon_image(self, key, size=(40,40)):
        entry=self.icon_catalog()[key]; texture=entry['texture'];blob=self.docs.binary(texture)
        frames=int(entry['frames'] if 'frames' in entry else atom(entry['text'],entry['node'].children,'noOfFrames','1'))
        token=(key,texture,blob,size,str(self.characters.game_root),frames)
        if token in self._icon_previews:
            self._icon_previews.move_to_end(token);return self._icon_previews[token]
        def build():
            source=blob
            if source is None:
                try:source=(self.characters.game_root/texture).read_bytes()
                except FileNotFoundError:return None
            with Image.open(io.BytesIO(source)) as opened:
                image=opened.convert('RGBA')
                if frames>1:image=image.crop((0,0,image.width//frames,image.height))
                return ImageOps.contain(image,size,Image.Resampling.LANCZOS)
        result=build();self._icon_previews[token]=result
        while len(self._icon_previews)>256:self._icon_previews.popitem(last=False)
        return result

    def spirit_icon_catalog(self):
        # Portrait sprites also use GFX_idea_. Filter by the image, so aliases
        # cannot reintroduce minister art; retain the full registry for existing
        # assignments, previews and native validation.
        catalog=self.icon_catalog()
        def portrait_size(texture):
            def read_size():
                source=self.docs.root/texture
                if not source.is_file():source=self.characters.game_root/texture
                if texture in self.docs.drafts:source=io.BytesIO(self.docs.binary(texture) or b'')
                try:
                    return image_dimensions(source,Path(texture).suffix) in {SMALL_SIZE,LARGE_SIZE}
                except (OSError,ValueError):return False
            return self.cached(('spirit_portrait_size',texture),id(self.docs.drafts.get(texture)),read_size)
        def build():
            out={}
            for key,row in catalog.items():
                if row['texture'].replace('\\','/').startswith(CUSTOM_IDEAS+'/'):
                    out[key]=row;continue  # Deliberate user imports are selectable even when named portrait_*.
                parts=tuple(p for p in row['texture'].replace('\\','/').casefold().split('/') if p)
                if any(p in {'leaders','ministers','portraits','small_portraits','large_portraits'} for p in parts[:-1]):continue
                name=parts[-1] if parts else ''
                if name.startswith(('portrait_','idea_portrait_')) or re.match(r'^(?:idea_)?generic_political_advisor_',name):continue
                # Old vanilla ministers also live in ideas/ under plain names
                # (e.g. idea_hjalmar_schacht.dds). Check header dimensions only;
                # do not decode thousands of textures or alter source snapshots.
                texture=row['texture'].replace('\\','/')
                if portrait_size(texture):continue
                out[key]=row
            return out
        signature=(id(catalog),tuple((p,id(b)) for p,b in self.docs.drafts.items() if p.startswith('gfx/')))
        return self.cached('spirit_icons',signature,build)

    def import_spirit_icon(self,source):
        source=Path(source)
        library=(self.docs.root/EAW_IDEAS).resolve()
        if source.resolve().is_relative_to(library):
            key='eaw:'+source.resolve().relative_to(library).as_posix()
            if key not in self.spirit_icon_catalog():raise ValueError('Choose a national-spirit asset from the EaW library; restart to refresh newly added files')
            return key  # Known EaW art retains its attribution even through the file chooser.
        stem=re.sub('[^A-Za-z0-9_]+','_',source.stem).strip('_') or 'custom_icon'
        with Image.open(source) as opened:
            fitted=ImageOps.contain(opened.convert('RGBA'),SPIRIT_ICON_SIZE,Image.Resampling.LANCZOS)
            image=Image.new('RGBA',SPIRIT_ICON_SIZE)
            image.alpha_composite(fitted,((image.width-fitted.width)//2,(image.height-fitted.height)//2))
            output=io.BytesIO();image.save(output,format='DDS');blob=output.getvalue()
        destination=flat_icon_destination(CUSTOM_IDEAS,stem+'.dds',blob,self.docs.binary)
        base='GFX_idea_lok_custom_icon_'+Path(destination).stem;sprite=base;number=2
        registered=self.characters.sprites()
        while sprite in registered and any(row['texture']!=destination for row in registered[sprite]):
            sprite=base+'_'+str(number);number+=1
        with self.docs.grouped():
            self.docs.stage_bytes(destination,blob);self.catalogs.put_sprite(IDEA_GFX,sprite,destination)
        return sprite

    def import_spirit_texture(self,entry):
        if 'frames' not in entry:return entry['texture']
        blob=self.docs.binary(entry['texture'])
        if blob is None:raise ValueError('EaW source asset is missing: '+entry['texture'])
        with Image.open(io.BytesIO(blob)) as image:image.verify()
        destination=flat_eaw_destination(entry['eaw_asset'],blob,self.docs.binary)
        self.docs.stage_bytes(destination,blob)
        return destination

    def credit_spirit_icon(self,entry,key,name,texture):
        if entry['origin']!='EaW' or not entry.get('eaw_asset'):return
        asset=entry['eaw_asset'];source='gfx\\interface\\ideas\\'+asset.replace('/','\\')
        usage='National spirit '+key+' ('+' '.join(name.splitlines())+')'
        record='Asset: '+Path(asset).name+'\nEaW path: '+source+'\nUsed for: '+usage+'\nMod texture: '+texture+'\n'
        original=self.docs.binary(EAW_CREDITS) or b'';text=self.docs._decode(original)
        if record in text.replace('\r\n','\n'):return
        updated=text.rstrip()+'\n\n'+record if text.strip() else 'EaW Credits\n\n'+record
        self.docs.stage_bytes(EAW_CREDITS,encode_source(updated,original))

    def edit_spirit(self,key,name,description,icon,effects,create=False,research_bonuses=None,equipment_bonuses=None):
        from character_model import patch_field
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',key):raise ValueError('Use letters, digits and underscores for the spirit ID')
        ideas=self.ideas()
        if create and (key in ideas or key in self.characters.localisations()):raise ValueError('Spirit ID already exists')
        if create and 'GFX_idea_'+key in self.characters.sprites():raise ValueError('That spirit icon ID is already registered; choose another spirit ID')
        if not create and (key not in ideas or ideas[key][0] not in {'country','hidden_ideas'}):raise ValueError('Choose an existing national spirit')
        if not name.strip():raise ValueError('Enter a spirit name')
        previous={}
        if not create:
            _,_,source,node=ideas[key];modifier=block(node.children,'modifier')
            previous={n.key:value(source,n) for n in modifier.children if n.children is None} if modifier else {}
        known=self.characters.trait_store.modifier_catalog()
        effects={k:(v if previous.get(k)==v else self.characters.trait_store.modifier_value(k,v)) for k,v in effects.items()}
        if any(k not in known and previous.get(k)!=v for k,v in effects.items()):raise ValueError('Choose defined modifiers')
        if any(known.get(k,{}).get('trait_stat') and previous.get(k)!=v for k,v in effects.items()):
            raise ValueError('Trait skill bonuses belong on military traits')
        old_bonuses=self.spirit_bonuses(None if create else key)
        research_bonuses,equipment_bonuses=self.validate_spirit_bonuses(research_bonuses,equipment_bonuses,old_bonuses)
        if icon not in self.icon_catalog():raise ValueError('Choose a registered national spirit icon')
        old_icon=''
        if not create:
            _,_,source,node=ideas[key];old_icon='GFX_idea_'+atom(source,node.children,'picture',key)
            if old_icon not in self.icon_catalog():old_icon='vanilla:'+old_icon
        change_icon=create or icon!=old_icon
        selected=self.icon_catalog()[icon]
        if change_icon and selected['origin']=='EaW' and not selected.get('eaw_asset'):
            raise ValueError('Choose the original EaW library asset so its source can be credited')
        with self.docs.grouped():
            if change_icon:
                entry=selected; sprite='GFX_idea_'+key
                texture=self.import_spirit_texture(entry)
                self.catalogs.put_sprite('interface/lok_ideas.gfx',sprite,texture)
                frames=entry['frames'] if 'frames' in entry else atom(entry['text'],entry['node'].children,'noOfFrames','1')
                entry=self.characters.sprites()[sprite][0];text=self.docs.text(entry['path']);node=entry['node']
                if frames!='1' or atom(text,node.children,'noOfFrames'):
                    self.docs.replace(entry['path'],patch_field(text,node,'noOfFrames',frames))
            else:texture=selected['texture']
            self.credit_spirit_icon(selected,key,name,texture)
            path=IDEAS if create else ideas[key][1];text=self.docs.text(path);root=block(parse(text),'ideas')
            if root is None:raise ValueError('Existing native ideas file is missing its ideas block')
            if create:
                category=block(root.children,'country')
                if category is None:raise ValueError('Existing ideas file needs a country block')
                at=category.end-1;raw=f'\n\t\t{key} = {{ picture = {key} allowed = {{ always = no }} removal_cost = -1 modifier = {{ }} }}\n'
                text=text[:at]+raw+text[at:]
            node=next(n for _,n in walk(parse(text)) if n.key==key and n.children is not None)
            if change_icon:text=patch_field(text,node,'picture',key)
            node=next(n for _,n in walk(parse(text)) if n.key==key and n.children is not None)
            # Preserve nested effect/condition fields outside numeric modifier entries.
            modifier=block(node.children,'modifier');body=value(text,modifier) if modifier else '{ }'
            wrapped='modifier = '+body;mn=parse(wrapped)[0]
            for n in reversed([n for n in mn.children if n.children is None and n.key not in effects]):wrapped=wrapped[:n.start]+wrapped[n.end:]
            for k,v in effects.items():wrapped=patch_field(wrapped,parse(wrapped)[0],k,v)
            text=patch_field(text,node,'modifier',value(wrapped,parse(wrapped)[0]))
            node=next(n for _,n in walk(parse(text)) if n.key==key and n.children is not None)
            raw='spirit = '+value(text,node)
            raw=self.patch_spirit_bonus(raw,'research_bonus',old_bonuses[0],research_bonuses)
            raw=self.patch_spirit_bonus(raw,'equipment_bonus',old_bonuses[1],equipment_bonuses)
            text=text[:node.value_start]+value(raw,parse(raw)[0])+text[node.end:];self.docs.replace(path,text)
            self.set_loc(IDEA_LOC,key,name);self.set_loc(IDEA_LOC,key+'_desc',description)

    def import_emblem(self,path,mode='Alpha'):
        stem=re.sub('[^a-z0-9_]+','_',Path(path).stem.lower()).strip('_') or 'emblem'
        sprite='GFX_lok_flag_emblem_'+stem; existing=self.characters.sprites();i=2
        while sprite in existing:
            sprite='GFX_lok_flag_emblem_'+stem+'_'+str(i);i+=1
        destination='gfx/interface/flags/emblems/'+sprite.removeprefix('GFX_')+'.dds'
        if self.docs.binary(destination) is not None:raise ValueError('An emblem asset with this filename already exists')
        with Image.open(path) as opened:
            rgba=opened.convert('RGBA');rgba.thumbnail((1024,1024),Image.Resampling.LANCZOS)
            mask=rgba.getchannel('A') if mode=='Alpha' else rgba.convert('L')
            if mode=='Dark on light':mask=ImageOps.invert(mask)
            if not mask.getbbox():raise ValueError('Empty emblem mask')
            image=Image.new('RGBA',mask.size,'white');image.putalpha(mask);out=io.BytesIO();image.save(out,format='DDS')
        with self.docs.grouped():self.docs.stage_bytes(destination,out.getvalue());self.catalogs.put_sprite(EMBLEM_GFX,sprite,destination)
        return sprite

    def emblem_choices(self):
        rows=[Choice('', 'No emblem')]
        if self.emblems:rows += [Choice('mask:'+k,k) for k in self.emblems.sources]
        rows += [Choice(k,k.removeprefix('GFX_lok_flag_emblem_').replace('_',' ').title()) for k in self.characters.sprites() if k.startswith('GFX_lok_flag_emblem_')]
        # EU4 imported emblem art is reused directly; no EU4 loader/cache writes.
        from model import default_paths
        folder=default_paths()['painter']/'emblem_sources'
        if folder.is_dir():rows += [Choice('file:'+p.as_posix(),p.stem.replace('_',' ').title()) for p in folder.rglob('*') if p.suffix.lower() in {'.png','.dds','.tga'}]
        return rows

    def emblem_mask(self,key):
        if not key:return None
        if key.startswith('mask:'):return self.emblems.mask(key[5:])
        if key.startswith('file:'):
            with Image.open(key[5:]) as image:mask=image.convert('RGBA').getchannel('A')
        else:
            image=self.characters.image(key)
            if image is None:raise ValueError('Emblem image is unavailable')
            mask=image.getchannel('A')
        return mask.crop(mask.getbbox()) if mask.getbbox() else mask
