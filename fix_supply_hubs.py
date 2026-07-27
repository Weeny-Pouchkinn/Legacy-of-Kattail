import os, re

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
states_dir = os.path.join(proj_dir, 'history', 'states')

unplayable_tags = {'MUN', 'XEN', 'MRI', 'AAA', 'ZZZ', 'WWW', 'MON'}

def process_state(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    owner_m = re.search(r'owner\s*=\s*([A-Z]{3})', content)
    if not owner_m: return
    owner = owner_m.group(1)
    
    if owner in unplayable_tags: return
    
    vp_matches = re.findall(r'victory_points\s*=\s*\{\s*([0-9\.\s]+)\}', content)
    target_provs = []
    for vp_content in vp_matches:
        tokens = vp_content.split()
        for i in range(0, len(tokens)-1, 2):
            try:
                prov_id = tokens[i]
                val = float(tokens[i+1])
                if val >= 5:
                    target_provs.append(prov_id)
            except:
                pass
                
    if not target_provs: return
    
    changed = False
    
    # Check if buildings block exists
    if 'buildings = {' not in content and 'buildings={' not in content:
        # insert empty buildings block before state_category
        content = re.sub(r'(\t+)(state_category\s*=)', r'\1buildings = {\n\1}\n\1\2', content)
        changed = True

    for p in target_provs:
        # Check if province already has an entry
        # Typically looks like `\t\t1234 = {`
        p_pattern = r'(\n\s*' + p + r'\s*=\s*\{)(.*?)(\n\s*\})'
        p_match = re.search(p_pattern, content, re.DOTALL)
        if p_match:
            inner_content = p_match.group(2)
            if 'supply_node = 0' in inner_content:
                new_inner = inner_content.replace('supply_node = 0', 'supply_node = 1')
                content = content[:p_match.start(2)] + new_inner + content[p_match.end(2):]
                changed = True
            elif 'supply_node = 1' not in inner_content:
                # add supply_node = 1
                new_inner = inner_content + '\n\t\t\tsupply_node = 1'
                content = content[:p_match.start(2)] + new_inner + content[p_match.end(2):]
                changed = True
        else:
            # We need to insert it right after `buildings = {`
            insertion = f'\n\t\t{p} = {{\n\t\t\tsupply_node = 1\n\t\t}}'
            # find buildings = { with optional spaces
            content = re.sub(r'(buildings\s*=\s*\{)', r'\1' + insertion, content, count=1)
            changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed supply hubs in {os.path.basename(filepath)}")

for filename in os.listdir(states_dir):
    if filename.endswith('.txt'):
        process_state(os.path.join(states_dir, filename))
