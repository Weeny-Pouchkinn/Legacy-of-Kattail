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

pool_eul = get_border('ACR', 'FOD')
pool_kkn_1 = get_border('FOD', 'ACR')
pool_kkn_2 = get_border('TEM', 'ENO')

print(f"EUL Pool (ACR side of ACR/FOD): {len(pool_eul)} provinces")
print(f"KKN Pool 1 (FOD side of ACR/FOD): {len(pool_kkn_1)} provinces")
print(f"KKN Pool 2 (TEM side of ENO/TEM): {len(pool_kkn_2)} provinces")

def replace_locations(filepath, pools):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    divisions = re.findall(r'(\bdivision\s*=\s*\{.*?\})', content, re.DOTALL)
    
    if len(pools) == 1:
        pool = pools[0]
        def repl(m):
            return re.sub(r'location\s*=\s*\d+', f'location = {random.choice(pool)}', m.group(1))
        
        new_content = re.sub(r'(\bdivision\s*=\s*\{.*?\})', repl, content, flags=re.DOTALL)
    else:
        # Alternating pools
        def repl(m, pool_idx=[0]):
            pool = pools[pool_idx[0] % len(pools)]
            pool_idx[0] += 1
            return re.sub(r'location\s*=\s*\d+', f'location = {random.choice(pool)}', m.group(1))
            
        new_content = re.sub(r'(\bdivision\s*=\s*\{.*?\})', repl, content, flags=re.DOTALL)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

replace_locations(os.path.join(units_dir, 'EUL_1936.txt'), [pool_eul])
replace_locations(os.path.join(units_dir, 'KKN_1936.txt'), [pool_kkn_1, pool_kkn_2])

print('Finished replacing locations.')
