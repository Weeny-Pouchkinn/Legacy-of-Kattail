#!/usr/bin/env python3
import os
import re
import subprocess

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
ON_ACTIONS_FILE = os.path.join(MOD_ROOT, "common", "on_actions", "LOK_on_actions.txt")
COMMIT_BEFORE = "61b8af8d^"

ANKA_STATES = set(range(1405, 1555)) | set(range(1570, 1576))

def get_old_states():
    # Get tree of old states
    result = subprocess.run(["git", "ls-tree", "-r", COMMIT_BEFORE, "history/states/"], cwd=MOD_ROOT, capture_output=True, text=True)
    
    prov_to_old_state = {}
    
    for line in result.stdout.strip().split('\n'):
        if not line: continue
        parts = line.split('\t')
        meta = parts[0].split()
        if len(meta) < 3: continue
        obj_hash = meta[2]
        filepath = parts[1]
        
        fname = os.path.basename(filepath)
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            # Read content from git
            content_res = subprocess.run(["git", "cat-file", "-p", obj_hash], cwd=MOD_ROOT, capture_output=True, text=True, errors="ignore")
            content = content_res.stdout
            prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', content)
            if prov_m:
                for p in prov_m.group(1).split():
                    if p.isdigit():
                        prov_to_old_state[int(p)] = sid
    return prov_to_old_state

def get_new_states_origins(prov_to_old_state):
    new_state_to_old = {}
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith('.txt'): continue
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            if sid in ANKA_STATES:
                path = os.path.join(STATES_DIR, fname)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', content)
                if prov_m:
                    provs = [int(p) for p in prov_m.group(1).split() if p.isdigit()]
                    # Find old state from the first province
                    for p in provs:
                        if p in prov_to_old_state:
                            new_state_to_old[sid] = prov_to_old_state[p]
                            break
    return new_state_to_old

def main():
    print("Reading old states from commit...")
    prov_to_old_state = get_old_states()
    print(f"Found {len(prov_to_old_state)} provinces in old states.")
    
    print("Mapping new states to old states...")
    new_state_to_old = get_new_states_origins(prov_to_old_state)
    print(f"Mapped {len(new_state_to_old)} new states to their old origins.")
    
    with open(ON_ACTIONS_FILE, 'rb') as f:
        raw = f.read()
    content = raw.decode('utf-8', errors='replace')
    bbom = raw[:3] == b'\xef\xbb\xbf'
    
    # Parse culture arrays from on_actions
    # Format: add_to_array = { array = global.culture_group_1_array value = 1 }
    old_state_to_culture = {}
    
    # We only care about culture_group_..._array
    for match in re.finditer(r'add_to_array\s*=\s*\{\s*array\s*=\s*(global\.culture_group_\d+_array)\s*value\s*=\s*(\d+)\s*\}', content):
        array_name = match.group(1)
        state_id = int(match.group(2))
        old_state_to_culture[state_id] = array_name
        
    print(f"Found {len(old_state_to_culture)} states in culture arrays.")
    
    # Map new state to array
    new_state_to_culture = {}
    for n_sid, o_sid in new_state_to_old.items():
        if o_sid in old_state_to_culture:
            new_state_to_culture[n_sid] = old_state_to_culture[o_sid]
        else:
            print(f"WARNING: Old state {o_sid} (for new {n_sid}) is not in any culture array!")
            
    # Now we insert the new lines into LOK_on_actions.txt
    # Let's insert them at the end of the culture arrays block. 
    # Or even better, group them by array and insert right after the last entry of each array.
    
    # Group additions by array
    array_additions = {}
    for n_sid, arr in new_state_to_culture.items():
        array_additions.setdefault(arr, []).append(n_sid)
        
    for arr, sids in array_additions.items():
        # Find the last occurrence of this array
        matches = list(re.finditer(r'add_to_array\s*=\s*\{\s*array\s*=\s*' + re.escape(arr) + r'\s*value\s*=\s*\d+\s*\}', content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            
            # build insertion string
            insertion = ""
            for sid in sorted(sids):
                insertion += f"\n\t\t\tadd_to_array = {{ array = {arr} value = {sid} }}"
                
            content = content[:insert_pos] + insertion + content[insert_pos:]
            print(f"Added {len(sids)} states to {arr}")

    with open(ON_ACTIONS_FILE, 'wb') as f:
        if bbom: f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))
    
    print("Done!")

if __name__ == '__main__':
    main()
