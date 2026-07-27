import os, re, random

random.seed(999)

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
states_dir = os.path.join(proj_dir, 'history', 'states')
units_dir = os.path.join(proj_dir, 'history', 'units')

tag_provs = {}
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
    tag_provs.setdefault(owner, set()).update(provs)

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

def get_border(tag_side, tag_other):
    provs_side = tag_provs.get(tag_side, set())
    provs_other = tag_provs.get(tag_other, set())
    border = []
    for p in provs_side:
        for n in adj.get(p, []):
            if n in provs_other:
                border.append(p)
                break
    return border

pool_kkn_1 = get_border('FOD', 'ACR')  # 90%
pool_kkn_2 = get_border('TEM', 'ENO')  # 10%

kkn_filepath = os.path.join(units_dir, 'KKN_1936.txt')

with open(kkn_filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    
divisions = re.findall(r'(\bdivision\s*=\s*\{.*?\})', content, re.DOTALL)
total_divs = len(divisions)
split_idx = round(total_divs * 0.9)

def repl(m, counter=[0]):
    c = counter[0]
    counter[0] += 1
    
    if c < split_idx:
        pool = pool_kkn_1
    else:
        pool = pool_kkn_2
        
    return re.sub(r'location\s*=\s*\d+', f'location = {random.choice(pool)}', m.group(1))

new_content = re.sub(r'(\bdivision\s*=\s*\{.*?\})', repl, content, flags=re.DOTALL)

with open(kkn_filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Repositioned KKN units: {split_idx} on ACR front, {total_divs - split_idx} on TEM/ENO front.")
