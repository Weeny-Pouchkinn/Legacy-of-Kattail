"""Native generic portrait groups, reserved species slots and shared art."""
from dataclasses import dataclass
import io
import json
import re

from PIL import Image, ImageOps

from model import parse, child, value
from character_model import quote, patch_field, LARGE_SIZE
from small_portrait import generate_small_portrait

PORTRAITS = 'portraits/LOK_portraits.txt'
GENERIC_GFX = 'interface/lok_generic_species_portraits.gfx'
UPLOAD_GFX = 'interface/lok_generic_portrait_groups_painter.gfx'
TEMPLATES = 'legacy_of_kattail_painter/generic_portrait_groups.json'
HEADER = re.compile(r'^###\s+([A-Za-z][A-Za-z0-9_]*)\s+#+[^\r\n]*', re.M)
GROUP = re.compile(r'(?:Species_\d+|[A-Za-z][A-Za-z0-9_]*_Species)\Z')
ROLES = ('army', 'navy', 'operative', 'scientist')
IDEOLOGIES = ('communism', 'democratic', 'fascism', 'neutrality', 'socialism',
              'social_democratic', 'social_liberal', 'social_conservative', 'authoritarian_democratic')
PLACEHOLDERS = {'civilian':6, 'military':6, 'navy':3, 'spy':3, 'scientist':4}


@dataclass(frozen=True)
class GenericPortraitGroup:
    key: str
    name: str
    tags: tuple
    body: str
    pools: dict


class GenericPortraitStore:
    def __init__(self, characters):
        self.characters, self.docs = characters, characters.docs
        self._revision = -1
        self._groups = {}

    def templates(self):
        text = self.docs.text(TEMPLATES)
        data = json.loads(text) if text.strip() else {}
        if not isinstance(data, dict) or any(not GROUP.fullmatch(k) or not isinstance(v, str) for k,v in data.items()):
            raise ValueError('Invalid generic portrait group templates')
        return data

    def remember(self, key, body):
        data = self.templates()
        if data.get(key) != body:
            data[key] = body
            self.docs.replace(TEMPLATES, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)+'\n')

    def sections(self):
        text, nodes = self.docs.parsed(PORTRAITS)
        headers = list(HEADER.finditer(text)); result = {}
        for index, header in enumerate(headers):
            key = header[1]
            if not GROUP.fullmatch(key): continue
            if key in result: raise ValueError('Duplicate generic portrait group section: '+key)
            end = headers[index+1].start() if index+1 < len(headers) else len(text)
            result[key] = (header.end(), end, [n for n in nodes if header.end() <= n.start < end])
        return text, result

    @staticmethod
    def prefix(key):
        return {'Amphibian_Species':'species_amphibian','Roqualian_Species':'species_roqualian'}.get(key,key.lower())

    @staticmethod
    def pools(body):
        roots = parse('group = '+body); result = {}
        def visit(nodes, path=()):
            for node in nodes:
                if node.children is None: continue
                current = path+(node.key,)
                if node.key in {'male','female'}:
                    result['/'.join(current)] = tuple(value('group = '+body, n).strip('"') for n in node.children if not n.op)
                else: visit(node.children, current)
        visit(roots[0].children)
        return result

    def default_body(self, key):
        # Fixed native layout: editing Species_0 must not mutate every vacant slot.
        prefix = 'GFX_portrait_'+self.prefix(key)+'_'
        def pool(kind, indices): return '{ '+' '.join(quote(prefix+kind+'_'+str(i)) for i in indices)+' }'
        def genders(kind, men, women): return '{ male = '+pool(kind,men)+' female = '+pool(kind,women)+' }'
        body = '{\n\tpolitical = {\n'
        for ideology in IDEOLOGIES:
            kind = 'military' if ideology in {'communism','fascism'} else 'civilian'
            body += '\t\t'+ideology+' = '+genders(kind,(1,2,3),(4,5,6))+'\n'
        body += '\t}\n'
        for role,kind,men,women in [('army','military',(1,2,3),(4,5,6)),('navy','military',(1,2),(3,)),('operative','spy',(1,),(2,3)),('scientist','scientist',(1,2),(3,4))]:
            body += '\t'+role+' = '+genders(kind,men,women)+'\n'
        return body+'}'

    def groups(self):
        if self._revision == self.docs.revision: return self._groups
        text, sections = self.sections(); templates = self.templates()
        # Reserved native sprites remain selectable even without a country block.
        reserved = {'Species_'+m[1] for m in re.finditer(r'GFX_portrait_species_(\d+)_', self.docs.text(GENERIC_GFX))}
        keys = list(dict.fromkeys([*sections, *sorted(reserved), *templates]))
        loc = self.characters.localisations(); result = {}
        for key in keys:
            nodes = sections.get(key, (0,0,[]))[2]
            body = value(text,nodes[0]) if nodes else templates.get(key) or self.default_body(key)
            ident = key.removeprefix('Species_')
            name = loc.get('var_species_'+ident, 'Unallocated') if ident.isdigit() else key.replace('_',' ')
            name = re.sub('[\u00a7\x15].','',name)
            result[key] = GenericPortraitGroup(key,name,tuple(n.key for n in nodes),body,self.pools(body))
        self._groups = result; self._revision = self.docs.revision
        return result

    def group_for_country(self, tag):
        return next((key for key,g in self.groups().items() if tag in g.tags), None)

    def ensure_species(self, ident):
        if isinstance(ident,bool) or not isinstance(ident,int) or ident < 0 or ident == 1000:
            raise ValueError('Choose a valid species ID')
        key = f'Species_{ident}'
        with self.docs.grouped():
            text, sections = self.sections()
            if key not in sections:
                self.docs.replace(PORTRAITS, text.rstrip()+'\n\n### '+key+' '+'#'*72+'\n')
            prefix = 'GFX_portrait_'+self.prefix(key)+'_'
            for kind,count in PLACEHOLDERS.items():
                for index in range(1,count+1):
                    for suffix,folder in (('', 'large_portraits'),('_small', 'small_portraits')):
                        target = prefix+kind+f'_{index}'+suffix
                        if target in self.characters.sprites(): continue
                        texture = f'gfx/leaders/{folder}/generic/placeholder/{kind}_{index}.tga'
                        if self.docs.binary(texture) is None: raise ValueError('Missing native placeholder texture: '+texture)
                        self.put_sprite(target,texture)
            body = self.groups()[key].body
            missing = [ref for refs in self.pools(body).values() for ref in refs if not self.characters.sprite_entries(ref)]
            if missing: raise ValueError('Missing generic placeholder sprite: '+missing[0])
        return key

    def put_sprite(self, name, texture):
        if self.characters.sprites().get(name):
            self.characters._put_sprite(name, texture, static=True)
            return
        text = self.docs.text(UPLOAD_GFX) or 'spriteTypes = {\n}\n'
        root = child(parse(text),'spriteTypes')
        if root is None: raise ValueError('Missing generic upload spriteTypes block')
        raw = '\tspriteType = { name = '+quote(name)+' texturefile = '+quote(texture)+' }\n'
        self.docs.replace(UPLOAD_GFX,text[:root.end-1]+raw+text[root.end-1:])

    def validate_body(self, body):
        pools = self.pools(body)
        if not pools or any(not refs for refs in pools.values()): raise ValueError('Each portrait pool needs at least one portrait')
        for refs in pools.values():
            for ref in refs:
                if not re.fullmatch(r'GFX_[A-Za-z0-9_]+',ref) or not self.characters.sprite_entries(ref):
                    raise ValueError('Choose an existing portrait sprite: '+ref)

    def set_pool(self, key, path, refs):
        parts = path.split('/')
        if not (len(parts)==2 and parts[0] in ROLES or len(parts)==3 and parts[0]=='political' and re.fullmatch(r'[a-z0-9_]+',parts[1])) or parts[-1] not in {'male','female'}:
            raise ValueError('Choose a role and gender pool')
        if not refs: raise ValueError('Keep at least one portrait in each role/gender pool')
        raw = '{ '+ ' '.join(quote(r) for r in refs)+' }'
        source = 'group = '+self.groups()[key].body
        def update(text, node, keys):
            if len(keys)==1: return patch_field(text,node,keys[0],raw)
            nested = child(node.children,keys[0])
            if nested: return update(text,nested,keys[1:])
            wrapped = raw
            for k in reversed(keys[1:]): wrapped = '{ '+k+' = '+wrapped+' }'
            return patch_field(text,node,keys[0],wrapped)
        source = update(source,parse(source)[0],parts)
        body = value(source,parse(source)[0]);self.validate_body(body)
        with self.docs.grouped():
            text, sections = self.sections()
            for node in reversed(sections.get(key,(0,0,[]))[2]):
                own = 'group = '+value(text,node)
                own = update(own,parse(own)[0],parts)
                text = text[:node.value_start]+value(own,parse(own)[0])+text[node.end:]
            self.docs.replace(PORTRAITS,text);self.remember(key,body)

    def assign_country(self, tag, key):
        if not re.fullmatch(r'[A-Z][A-Z0-9]{2}',tag): raise ValueError('Choose a valid country tag')
        if key and key not in self.groups(): raise ValueError('Choose a defined generic portrait group')
        old = self.group_for_country(tag)
        if old == key: return
        body = self.groups()[key].body if key else ''
        with self.docs.grouped():
            if old:
                self.remember(old,self.groups()[old].body)
            # Remove only this tag, including a previous pool in misc/katzen/no_portraits.
            for path in self.characters.files('portraits','.txt'):
                text, roots = self.docs.parsed(path)
                for node in reversed([n for n in roots if n.key==tag and n.children is not None]):
                    text = text[:node.start]+text[node.end:]
                self.docs.replace(path,text)
            if key:
                text, sections = self.sections()
                if key not in sections: raise ValueError('Missing native group section: '+key)
                # Insert just after its header, preserving the next section's comments.
                at = sections[key][0]
                self.docs.replace(PORTRAITS,text[:at]+'\n'+tag+' = '+body+'\n'+text[at:])
                self.remember(key,body)

    def upload(self, key, path, files, replace=None):
        if key not in self.groups(): raise ValueError('Choose an existing group')
        refs = list(self.groups()[key].pools.get(path,()))
        if replace is not None and replace not in refs: raise ValueError('Choose a portrait from this pool')
        if replace is not None and len(files)!=1: raise ValueError('Choose one replacement image')
        with self.docs.grouped():
            for file in files:
                if replace:
                    sprite = replace
                else:
                    stem = 'GFX_portrait_'+self.prefix(key)+'_'+path.replace('/','_')+'_'
                    index = 1
                    while self.characters.sprite_entries(stem+str(index)): index += 1
                    sprite = stem+str(index)
                if not re.fullmatch(r'GFX_[A-Za-z0-9_]+',sprite): raise ValueError('Invalid portrait sprite ID')
                with Image.open(file) as opened:
                    fitted = ImageOps.contain(opened.convert('RGBA'),LARGE_SIZE,Image.Resampling.LANCZOS)
                    large = Image.new('RGBA',LARGE_SIZE)
                    large.alpha_composite(fitted,((large.width-fitted.width)//2,(large.height-fitted.height)//2))
                small = generate_small_portrait(large)
                existing = next((s for s in self.characters.sprites() if s.casefold()==(sprite+'_small').casefold()),sprite+'_small')
                for name,image,kind in ((sprite,large,'large'),(existing,small,'small')):
                    destination = 'gfx/leaders/generic_groups/'+self.prefix(key)+'/'+kind+'/'+sprite.removeprefix('GFX_portrait_')+'.tga'
                    current = self.characters.sprites().get(name,[])
                    owned = {entry['texture'] for entry in current}
                    base = destination; index = 2
                    while self.docs.binary(destination) is not None and destination not in owned:
                        destination = base.removesuffix('.tga')+f'_{index}.tga';index += 1
                    data = io.BytesIO(); image.save(data,format='TGA')
                    self.docs.stage_bytes(destination,data.getvalue()); self.put_sprite(name,destination)
                if replace is None: refs.append(sprite)
            self.set_pool(key,path,refs)
        return tuple(refs)
