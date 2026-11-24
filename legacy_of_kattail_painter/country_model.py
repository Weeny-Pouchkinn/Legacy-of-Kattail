"""Native country history, names, flags and spirits; no editor metadata files."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import io
from pathlib import Path
import re

from PIL import Image, ImageColor, ImageDraw, ImageOps

from model import FLAG_SIZES, child, parse, value, scalar, walk, read_text
from character_model import atom, block, quote, LOC, unescape, inherited_sprites
from select_ui import Choice
from demographics import STARTUP

COUNTRY_LOC = 'localisation/english/countries_l_english.yml'
IDEA_LOC = 'localisation/english/LOK_ideas_l_english.yml'
IDEAS = 'common/ideas/lok_misc_ideas.txt'
IDEA_GFX = 'interface/lok_ideas.gfx'
EMBLEM_GFX = 'interface/lok_misc_icons.gfx'
TAGS = 'common/country_tags/00_countries.txt'
SPECIES_HISTORY_FLAG = 'lok_country_species_defined_in_history'
ATTRIBUTE_HISTORY_FLAG = 'lok_country_attribute_defined_in_history'
PATTERNS = ('Solid', 'Horizontal bicolor', 'Vertical bicolor', 'Horizontal tricolor',
            'Vertical tricolor', 'Horizontal 1:2:1', 'Vertical 1:2:1', 'Diagonal down',
            'Diagonal up', 'Quartered', 'Cross', 'Nordic cross', 'Saltire', 'Chevron',
            'Canton', 'Border', 'Central disk')


def copy_ideology_names(names,source,ideologies,undefined=False):
    values={k:(names[source][k] if names[source][k] is not None else names[''][k] if names[''][k] is not None else names['']['name']) for k in ('name','def')}
    for ideology in ideologies:
        for key in ('name','def'):
            if not undefined or names[ideology][key] is None:names[ideology][key]=values[key]


def definite_name(text,article=False):
    text=re.sub(r'^the\s+','',text.strip(),flags=re.I)
    return ('the ' if article and text else '')+text


def number(raw, low=None, high=None):
    try: n = Decimal(str(raw))
    except InvalidOperation: raise ValueError('Enter a numeric value') from None
    if not n.is_finite() or low is not None and n < low or high is not None and n > high:
        raise ValueError(f'Value must be between {low} and {high}' if low is not None and high is not None else 'Value must be finite')
    return format(n, 'f')


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


def render_flag(pattern, colors, mask=None, tint='#ffffff', size=(82, 52), scale=.75, offset=(.5, .5)):
    if pattern not in PATTERNS: raise ValueError('Choose a defined flag pattern')
    colors = [ImageColor.getrgb(c) for c in colors]
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
    if mask is not None:
        mask = mask.convert('L'); box = max(1, round(h * float(scale))); ratio = box/max(mask.size)
        mask = mask.resize((max(1, round(mask.width*ratio)), max(1, round(mask.height*ratio))), Image.Resampling.LANCZOS)
        out.paste(ImageColor.getrgb(tint), (round(w*offset[0]-mask.width/2), round(h*offset[1]-mask.height/2)), mask)
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


class CountryStore:
    def __init__(self, world, characters, catalogs, emblems=None):
        self.world, self.characters, self.catalogs, self.docs = world, characters, catalogs, world.docs
        self.emblems = emblems; self._cache = {}

    def cached(self, key, signature, build):
        cached = self._cache.get(key)
        if cached is None or cached[0] != signature: cached = self._cache[key] = (signature, build())
        return cached[1]

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
                       technologies, {k for k in ideas if k not in definitions or definitions[k][0] in {'country', 'hidden_ideas'}}, laws, self.names(tag))

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

    def apply(self, country, color, names, flags=None, create=False):
        tag = country.tag
        if not re.fullmatch(r'[A-Z][A-Z0-9]{2}', tag): raise ValueError('Use a three-character uppercase country tag, starting with a letter')
        if create == (tag in self.world.country_paths): raise ValueError('Choose a new unused tag' if create else 'Choose an existing country')
        if create and not (names.get('', {}).get('name') or '').strip(): raise ValueError('Enter the base country name')
        if not str(country.capital).isdigit() or int(country.capital) not in self.world.states: raise ValueError('Choose a defined capital state')
        if country.ruling not in self.ideologies(): raise ValueError('Choose a ruling ideology')
        pop = {i: number(v, 0, 100) for i, v in country.popularities.items()}
        if any(i not in self.ideologies() for i in pop): raise ValueError('Unknown ideology in popularities')
        if sum(Decimal(v) for v in pop.values()) != 100: raise ValueError('Party popularities must total exactly 100%')
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
        rgb = ImageColor.getrgb(color) if isinstance(color, str) else tuple(color)
        if len(rgb) != 3: raise ValueError('Choose an RGB map color')
        with self.docs.grouped():
            if create:
                if any(Path(p).name[:3]==tag and self.docs.text(p) for p in self.characters.files('history/countries','.txt')):
                    raise ValueError('An existing history source already uses this tag')
                for path in (f'common/countries/{tag}.txt', f'history/countries/{tag}.txt'):
                    if self.docs.binary(path) is not None: raise ValueError('A source already exists: '+path)
                text = self.docs.text(TAGS); self.docs.replace(TAGS, text.rstrip()+f'\n{tag} = "countries/{tag}.txt"\n')
                self.docs.replace(f'common/countries/{tag}.txt', 'graphical_culture = western_european_gfx\ngraphical_culture_2d = western_european_2d\n')
                country.path = f'history/countries/{tag}.txt'
            definition = self.world.country_paths.get(tag, f'common/countries/{tag}.txt')
            self.docs.replace(definition, field_text(self.docs.text(definition), 'color', 'rgb { '+' '.join(map(str,rgb))+' }'))
            # colors.txt is the authoritative override where an entry already exists.
            colors = 'common/countries/colors.txt'; text = self.docs.text(colors); node = child(parse(text), tag)
            if node and node.children:
                from character_model import patch_field
                self.docs.replace(colors, patch_field(text, node, 'color', 'rgb { '+' '.join(map(str,rgb))+' }'))
            text = self.docs.text(country.path)
            for key, raw in [('capital',str(country.capital)),('set_stability',format(stability,'f')),('set_war_support',format(war,'f'))]: text = field_text(text,key,raw)
            text = patch_root_block(text,'set_politics',{'ruling_party':country.ruling})
            raw = '{\n'+''.join(f'\t{i} = {pop.get(i,"0")}\n' for i in self.ideologies())+'}'
            if create or not existing or pop != existing.popularities: text = field_text(text,'set_popularities',raw)
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
            out=io.BytesIO(); image.convert('RGB').resize(dimensions,Image.Resampling.LANCZOS).save(out,format='TGA')
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

    def icon_catalog(self):
        mod=self.characters.sprites(); vanilla=inherited_sprites(str(self.characters.game_root))
        loc=self.characters.trait_store.names();signature=(id(mod),id(vanilla),id(loc))
        def build():
            out={}
            for source,entries in [('Vanilla',vanilla),('Mod',mod)]:
                for key,rows in entries.items():
                    if not key.startswith('GFX_idea_') or not rows:continue
                    row=rows[0]; short=key.removeprefix('GFX_idea_')
                    code='vanilla:'+key if source=='Vanilla' else key
                    out[code]={**row,'origin':source,'choice':Choice(code,loc.get(short,short.replace('_',' ').title()))}
            return out
        return self.cached('icons',signature,build)

    def icon_image(self, key, size=(40,40)):
        entry=self.icon_catalog()[key]; texture=entry['texture'];blob=self.docs.binary(texture)
        if blob is None and (self.characters.game_root/texture).is_file():blob=(self.characters.game_root/texture).read_bytes()
        if blob is None:return None
        token=(key,id(blob),size)
        def build():
            with Image.open(io.BytesIO(blob)) as opened:
                image=opened.convert('RGBA');frames=int(atom(entry['text'],entry['node'].children,'noOfFrames','1'))
                if frames>1:image=image.crop((0,0,image.width//frames,image.height))
                return ImageOps.contain(image,size,Image.Resampling.LANCZOS)
        return self.cached(('icon',key),token,build)

    def edit_spirit(self,key,name,description,icon,effects,create=False):
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
        effects={k:(v if previous.get(k)==v else number(v)) for k,v in effects.items()}
        if any(k not in known and previous.get(k)!=v for k,v in effects.items()):raise ValueError('Choose defined modifiers')
        if any(k in known and known[k]['categories'] and 'country' not in known[k]['categories'] and previous.get(k)!=v for k,v in effects.items()):
            raise ValueError('Choose country-scope modifiers for national spirits')
        if icon not in self.icon_catalog():raise ValueError('Choose a registered national spirit icon')
        old_icon=''
        if not create:
            _,_,source,node=ideas[key];old_icon='GFX_idea_'+atom(source,node.children,'picture',key)
            if old_icon not in self.icon_catalog():old_icon='vanilla:'+old_icon
        change_icon=create or icon!=old_icon
        with self.docs.grouped():
            if change_icon:
                entry=self.icon_catalog()[icon]; sprite='GFX_idea_'+key
                self.catalogs.put_sprite('interface/lok_ideas.gfx',sprite,entry['texture'])
                frames=atom(entry['text'],entry['node'].children,'noOfFrames','1')
                entry=self.characters.sprites()[sprite][0];text=self.docs.text(entry['path']);node=entry['node']
                if frames!='1' or atom(text,node.children,'noOfFrames'):
                    self.docs.replace(entry['path'],patch_field(text,node,'noOfFrames',frames))
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
            text=patch_field(text,node,'modifier',value(wrapped,parse(wrapped)[0]));self.docs.replace(path,text)
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
