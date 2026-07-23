import os, re, glob

MOD_ROOT = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
STATES_DIR = os.path.join(MOD_ROOT, 'history', 'states')
UNITS_DIR = os.path.join(MOD_ROOT, 'history', 'units')

lake_transfers = {96: 1486, 152: 1508, 176: 1531, 202: 1051, 207: 1051, 219: 1494, 324: 1432, 605: 1537, 611: 1506, 1040: 1550, 1050: 1527}
reindex_map = {1575: 96, 1574: 152, 1573: 176, 1572: 202, 1571: 207, 1570: 219, 1569: 324, 1568: 605, 1567: 611, 1566: 1040, 1565: 1050}
deleted_states = list(lake_transfers.keys())

# 1. Get provinces to transfer
provs_to_transfer = {} # { neighbor_sid: [provs] }
for sid in deleted_states:
    path = glob.glob(os.path.join(STATES_DIR, f'{sid}-*.txt'))
    if path:
        with open(path[0], 'r', encoding='utf-8', errors='ignore') as f:
            prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', f.read())
            if prov_m:
                provs = prov_m.group(1).split()
                neighbor = lake_transfers[sid]
                provs_to_transfer.setdefault(neighbor, []).extend(provs)

# 2. Add provinces to neighbor states
for neighbor_sid, provs in provs_to_transfer.items():
    path = glob.glob(os.path.join(STATES_DIR, f'{neighbor_sid}-*.txt'))
    if path:
        with open(path[0], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        def repl(m):
            return m.group(0)[:-1] + ' ' + ' '.join(provs) + ' }'
        content = re.sub(r'\bprovinces\s*=\s*\{([^}]*)\}', repl, content)
        with open(path[0], 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Transferred {provs} to {neighbor_sid}')

# 3. Delete lake states
for sid in deleted_states:
    path = glob.glob(os.path.join(STATES_DIR, f'{sid}-*.txt'))
    if path:
        os.remove(path[0])
        print(f'Deleted state {sid}')

# 4. Reindex states
for old_id, new_id in reindex_map.items():
    path = glob.glob(os.path.join(STATES_DIR, f'{old_id}-*.txt'))
    if path:
        old_path = path[0]
        fname = os.path.basename(old_path)
        new_fname = fname.replace(f'{old_id}-', f'{new_id}-', 1)
        new_path = os.path.join(STATES_DIR, new_fname)
        
        with open(old_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        content = re.sub(r'\bid\s*=\s*' + str(old_id) + r'\b', f'id = {new_id}', content)
        content = re.sub(r'\bname\s*=\s*\"STATE_' + str(old_id) + r'\"', f'name = \"STATE_{new_id}\"', content)
        
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # We don't remove if they are the same file name, but they are different.
        os.remove(old_path)
        print(f'Renamed state {old_id} to {new_id}')

# 5. Localization
loc_path = os.path.join(MOD_ROOT, 'localisation', 'english', 'anka_new_states_l_english.yml')
with open(loc_path, 'rb') as f:
    raw = f.read()
loc_content = raw.decode('utf-8', errors='replace')
bbom = raw[:3] == b'\xef\xbb\xbf'

for old_id, new_id in reindex_map.items():
    loc_content = re.sub(r'STATE_' + str(old_id) + r':', f'STATE_{new_id}:', loc_content)
with open(loc_path, 'wb') as f:
    if bbom: f.write(b'\xef\xbb\xbf')
    f.write(loc_content.encode('utf-8'))

# 6. LOK_on_actions.txt
on_actions = os.path.join(MOD_ROOT, 'common', 'on_actions', 'LOK_on_actions.txt')
with open(on_actions, 'rb') as f:
    raw = f.read()
oa_content = raw.decode('utf-8', errors='replace')
bbom = raw[:3] == b'\xef\xbb\xbf'
for old_id, new_id in reindex_map.items():
    oa_content = re.sub(r'value\s*=\s*' + str(old_id) + r'\s*\}', f'value = {new_id} }}', oa_content)
    oa_content = re.sub(r'^\s*' + str(old_id) + r'\s*=\s*\{', f'\t\t\t{new_id} = {{', oa_content, flags=re.MULTILINE)
with open(on_actions, 'wb') as f:
    if bbom: f.write(b'\xef\xbb\xbf')
    f.write(oa_content.encode('utf-8'))

# 7. map/buildings.txt
buildings = os.path.join(MOD_ROOT, 'map', 'buildings.txt')
with open(buildings, 'rb') as f:
    raw = f.read()
b_content = raw.decode('utf-8', errors='replace')
bbom = raw[:3] == b'\xef\xbb\xbf'

lines = b_content.split('\n')
new_lines = []
for line in lines:
    stripped = line.strip()
    if not stripped: continue
    parts = stripped.split(';')
    if parts[0].isdigit():
        sid = int(parts[0])
        if sid in deleted_states:
            continue # Delete old lake state entries
        if sid in reindex_map:
            parts[0] = str(reindex_map[sid])
            stripped = ';'.join(parts)
    new_lines.append(stripped)
b_content = '\r\n'.join(new_lines) + '\r\n'
with open(buildings, 'wb') as f:
    if bbom: f.write(b'\xef\xbb\xbf')
    f.write(b_content.encode('utf-8'))

# 8. history/units/
for fname in os.listdir(UNITS_DIR):
    if not fname.endswith('.txt'): continue
    path = os.path.join(UNITS_DIR, fname)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    modified = False
    for old_id in deleted_states:
        if f'base = {old_id}\n' in content or f'base = {old_id}\r' in content or f'base = {old_id}' in content:
            neighbor = lake_transfers[old_id]
            content = re.sub(r'\bbase\s*=\s*' + str(old_id) + r'\b', f'base = {neighbor}', content)
            modified = True
            
    for old_id, new_id in reindex_map.items():
        if f'base = {old_id}\n' in content or f'base = {old_id}\r' in content or f'base = {old_id}' in content:
            content = re.sub(r'\bbase\s*=\s*' + str(old_id) + r'\b', f'base = {new_id}', content)
            modified = True
            
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

print('Consolidation and Re-indexing Complete!')
