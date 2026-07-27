import os, re, random, math

random.seed(999)

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
states_dir = os.path.join(proj_dir, 'history', 'states')
countries_dir = os.path.join(proj_dir, 'history', 'countries')
units_dir = os.path.join(proj_dir, 'history', 'units')

# 1. Parse States
tag_states = {}
tag_provs = {}
tag_vps = {}

for filename in os.listdir(states_dir):
    if not filename.endswith('.txt'): continue
    filepath = os.path.join(states_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    owner_m = re.search(r'owner\s*=\s*([A-Z]{3})', content)
    if not owner_m: continue
    owner = owner_m.group(1)
    
    prov_m = re.search(r'provinces\s*=\s*\{\s*([0-9\s]+)\}', content)
    if not prov_m: continue
    provs = [int(x) for x in prov_m.group(1).split()]
    
    tag_states[owner] = tag_states.get(owner, 0) + 1
    tag_provs.setdefault(owner, set()).update(provs)
    
    vps = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+\d+', content)
    tag_vps.setdefault(owner, []).extend([int(vp) for vp in vps])

# 2. Adjacencies
adj = {}
adj_path = os.path.join(proj_dir, 'modding_documentation', 'province_adjacencies.csv')
with open(adj_path, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(';')
        if len(parts) > 1:
            try:
                p = int(parts[0])
                neighbors = [int(x) for x in parts[1:] if x.strip()]
                adj[p] = neighbors
            except:
                pass

tag_borders = {}
for tag, provs in tag_provs.items():
    borders = {}
    for p in provs:
        for n in adj.get(p, []):
            n_owner = None
            for t2, p2 in tag_provs.items():
                if t2 != tag and n in p2:
                    n_owner = t2
                    break
            if n_owner:
                borders.setdefault(n_owner, []).append(p)
    tag_borders[tag] = borders

# 3. Adjectives
adjectives = {}
loc_dir = os.path.join(proj_dir, 'localisation', 'english')
for filename in os.listdir(loc_dir):
    if filename.endswith('.yml'):
        with open(os.path.join(loc_dir, filename), 'r', encoding='utf-8-sig') as f:
            for line in f:
                m = re.search(r'^ *([A-Z]{3})_ADJ:0\s*"([^"]+)"', line)
                if m:
                    adjectives[m.group(1)] = m.group(2)

# 4. Identify Targets
targets = []
for filename in os.listdir(countries_dir):
    if not filename.endswith('.txt'): continue
    tag = filename[:3]
    if tag == 'AAA': continue # Anarchy
    if tag_states.get(tag, 0) == 0: continue # not on map
    
    filepath = os.path.join(countries_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_oob = False
    is_ktz = False
    for m in re.finditer(r'\b(?:set_)?oob\s*=\s*"([^"]+)"', content):
        has_oob = True
        if m.group(1) == 'KTZ_1936':
            is_ktz = True
            break
            
    if not has_oob or is_ktz or tag in ['KKN', 'EUL']:
        targets.append((tag, filepath, content))

print(f'Found {len(targets)} target nations.')

with open(os.path.join(units_dir, 'FKS_1936.txt'), 'r', encoding='utf-8') as f:
    fks_content = f.read()
fks_templates = re.findall(r'(division_template\s*=\s*\{.*?\n\})', fks_content, re.DOTALL)

with open(os.path.join(units_dir, 'FOD_1936.txt'), 'r', encoding='utf-8') as f:
    fod_content = f.read()
fod_templates = re.findall(r'(division_template\s*=\s*\{.*?\n\})', fod_content, re.DOTALL)

for tag, filepath, content in targets:
    st_count = tag_states[tag]
    total_units = 3 * st_count if tag == 'KKN' else 2 * st_count
    
    if total_units == 0: continue
    
    reg_c = round(total_units * 0.5)
    gar_c = round(total_units * 0.3)
    mob_c = round(total_units * 0.1)
    arm_c = total_units - reg_c - gar_c - mob_c
    
    adj_name = adjectives.get(tag, tag)
    
    out_lines = ['##### Division Templates #####']
    if tag == 'KKN':
        for t in fod_templates: out_lines.append(t)
        reg_name = 'Katzen-Schweireinfanterie'
        gar_name = 'Garnison'
        mob_name = 'Katzen-Schweireinfanterie'
        arm_name = 'Katzen-Schweireinfanterie'
    else:
        for t in fks_templates:
            out_lines.append(t.replace('Katurneri', adj_name))
        reg_name = f'{adj_name} Regulars'
        gar_name = f'{adj_name} Garrison'
        mob_name = f'{adj_name} Mobile Troops'
        arm_name = f'{adj_name} Armored Force'
        
    out_lines.append('##### Units #####')
    out_lines.append('units = {')
    
    all_provs = list(tag_provs[tag])
    vps = tag_vps.get(tag, [])
    
    def get_loc(pool):
        if not pool: return random.choice(all_provs)
        return random.choice(pool)
        
    for i in range(reg_c):
        if tag == 'KKN':
            pool = tag_borders.get('KKN', {}).get('ENO', []) if i < reg_c/2 else tag_borders.get('KKN', {}).get('ACR', [])
        elif tag == 'EUL':
            pool = tag_borders.get('EUL', {}).get('FOD', [])
        else:
            pool = []
            for b in tag_borders.get(tag, {}).values(): pool.extend(b)
        
        loc = get_loc(pool)
        out_lines.append(f'\tdivision = {{ name = "{i+1}st {adj_name} Regulars" location = {loc} division_template = "{reg_name}" }}')
        
    for i in range(gar_c):
        loc = get_loc(vps)
        out_lines.append(f'\tdivision = {{ name = "{i+1}st {adj_name} Garrison" location = {loc} division_template = "{gar_name}" }}')
        
    for i in range(mob_c):
        loc = get_loc(all_provs)
        out_lines.append(f'\tdivision = {{ name = "{i+1}st {adj_name} Mobile" location = {loc} division_template = "{mob_name}" }}')
        
    for i in range(arm_c):
        loc = get_loc(all_provs)
        out_lines.append(f'\tdivision = "{i+1}st {adj_name} Armored" location = {loc} division_template = "{arm_name}" }}')
        
    out_lines.append('}')
    
    with open(os.path.join(units_dir, f'{tag}_1936.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
        
    if re.search(r'\b(?:set_)?oob\s*=\s*"[^"]+"', content):
        new_content = re.sub(r'\b(set_oob|oob)\s*=\s*"[^"]+"', f'\\1 = "{tag}_1936"', content)
    else:
        new_content = content + f'\nset_oob = "{tag}_1936"\n'
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

print('OOB creation complete.')
