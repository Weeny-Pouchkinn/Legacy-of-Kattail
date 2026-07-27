import os, re

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
states_dir = os.path.join(proj_dir, 'history', 'states')

unplayable_tags = {'MUN', 'XEN', 'MRI', 'AAA', 'ZZZ', 'WWW', 'MON'} # MON is interflusionian

def process_state(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get owner
    owner_m = re.search(r'owner\s*=\s*([A-Z]{3})', content)
    if not owner_m: return
    owner = owner_m.group(1)
    
    if owner in unplayable_tags: return
    
    # Find all VPs
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
    
    # Find the buildings block
    b_match = re.search(r'(\bbuildings\s*=\s*\{)(.*?^\t\})', content, re.DOTALL | re.MULTILINE)
    if not b_match:
        # no buildings block, we need to add it before state_category
        # this is rare, but just in case
        b_block_new = "\n\tbuildings = {\n"
        for p in target_provs:
            b_block_new += f"\t\t{p} = {{\n\t\t\tsupply_node = 1\n\t\t}}\n"
        b_block_new += "\t}\n"
        content = re.sub(r'(state_category\s*=)', b_block_new + r'\1', content)
        changed = True
    else:
        # edit existing buildings block
        b_block_original = b_match.group(2)
        b_block = b_block_original
        for p in target_provs:
            # check if province is in buildings block
            p_match = re.search(rf'^\s*{p}\s*=\s*{{(.*?^\s*}})', b_block, re.DOTALL | re.MULTILINE)
            if p_match:
                # check if supply_node is in it
                if re.search(r'supply_node\s*=\s*0', p_match.group(1)):
                    # change 0 to 1
                    new_p_block = re.sub(r'supply_node\s*=\s*0', 'supply_node = 1', p_match.group(0))
                    b_block = b_block.replace(p_match.group(0), new_p_block, 1)
                    changed = True
                elif not re.search(r'supply_node\s*=\s*1', p_match.group(1)):
                    # add it
                    new_p_block = p_match.group(0).replace('{', '{\n\t\t\tsupply_node = 1', 1)
                    b_block = b_block.replace(p_match.group(0), new_p_block, 1)
                    changed = True
            else:
                # add province to buildings block
                insertion = f"\n\t\t{p} = {{\n\t\t\tsupply_node = 1\n\t\t}}"
                # inject before the last closing brace of buildings block
                b_block = b_block[:-1] + insertion + "\n\t}"
                changed = True
                
        if b_block != b_block_original:
            content = content.replace(b_match.group(2), b_block)
            changed = True
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added supply hubs to state {os.path.basename(filepath)}")

for filename in os.listdir(states_dir):
    if filename.endswith('.txt'):
        process_state(os.path.join(states_dir, filename))

print("Supply hubs script finished.")
