#!/usr/bin/env python3
"""
fix_anka_names.py  -- Pass 2
Fixes geographic names that came out as "X None Y" by re-reading owner from each state file
and generating a proper name. Also updates the localization file.
"""

import os
import re
import codecs

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
LOC_DIR = os.path.join(MOD_ROOT, "localisation", "english")
VP_LOC_FILE = os.path.join(LOC_DIR, "victory_points_l_english.yml")
ANKA_LOC_FILE = os.path.join(LOC_DIR, "anka_new_states_l_english.yml")

STATE_PATTERN_IDS = set(range(1405, 1555)) | set(range(1570, 1576))

OWNER_NAMES = {
    "PRL": "Parlesia", "AUR": "Aurelia", "ELO": "Eloria", "WPR": "Praw",
    "FRA": "Franchesse", "NKB": "Nokobia", "LMB": "Lambia", "OST": "Ostmark",
    "CAT": "Catalia", "KHA": "Kharna", "TEN": "Tenia", "LIO": "Lionheart",
    "CLE": "Cleria", "ROQ": "Roqueria", "MCF": "Macafia", "NEU": "Neumark",
    "POT": "Potland", "HYP": "Hyperia", "TAI": "Taikara", "PAW": "Pawland",
    "NMI": "Neminia", "ACR": "Amphibia", "FOD": "Fodaria", "TEM": "Temperia",
    "KKN": "Kronkia", "PER": "Perania", "NKR": "Nokrania",
    "PTQ": "Prateque", "VEL": "Velia", "UCE": "Uckenia",
    "HYP": "Hyperia", "TAK": "Takoria",
}

DIRECTIONS = [
    "North", "South", "East", "West", "Central",
    "Upper", "Lower", "Far North", "Far South", "Far East", "Far West", "Near"
]


def read_file_utf8bom(path):
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:3] == b'\xef\xbb\xbf':
        return raw[3:].decode('utf-8'), True
    return raw.decode('utf-8'), False


def load_vp_localization():
    vp_names = {}
    try:
        content, _ = read_file_utf8bom(VP_LOC_FILE)
        for line in content.splitlines():
            m = re.match(r'\s*VICTORY_POINTS_(\d+):0\s+"([^"]+)"', line)
            if m:
                vp_names[int(m.group(1))] = m.group(2)
    except Exception as e:
        print(f"Warning VP loc: {e}")
    return vp_names


def parse_quick(filepath):
    content, has_bom = read_file_utf8bom(filepath)
    sid = None
    owner = None
    vps = []
    m = re.search(r'\bid\s*=\s*(\d+)', content)
    if m: sid = int(m.group(1))
    m = re.search(r'\bowner\s*=\s*(\w+)', content)
    if m: owner = m.group(1)
    for m in re.finditer(r'\bvictory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', content):
        vps.append((int(m.group(1)), int(m.group(2))))
    return sid, owner, vps


def generate_geographic_name(sid, owner, used_directions):
    """Generate a unique directional name using owner's region."""
    region = OWNER_NAMES.get(owner, owner if owner else "Region")
    # Cycle through directions using sid to spread them out
    direction = DIRECTIONS[sid % len(DIRECTIONS)]
    num = (sid % 15) + 1
    base = f"{direction} {region}"
    # Make it unique by adding number if there's a collision
    name = f"{base} {num}"
    return name


def main():
    print("=== fix_anka_names.py (Pass 2) ===\n")
    
    vp_names = load_vp_localization()
    print(f"Loaded {len(vp_names)} VP names")
    
    # Read the current anka loc file
    current_loc_content, loc_bom = read_file_utf8bom(ANKA_LOC_FILE)
    current_entries = {}
    for line in current_loc_content.splitlines():
        m = re.match(r'\s*STATE_(\d+):0\s+"([^"]+)"', line)
        if m:
            current_entries[int(m.group(1))] = m.group(2)
    
    print(f"Current loc entries: {len(current_entries)}")
    
    # Collect all state files
    state_files = {}
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith('.txt'):
            continue
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            state_files[sid] = os.path.join(STATES_DIR, fname)
    
    # Re-generate names for all STATE_ pattern states
    new_entries = {}
    used_names = set()
    
    for sid in sorted(STATE_PATTERN_IDS):
        if sid not in state_files:
            continue
        
        parsed_sid, owner, vps = parse_quick(state_files[sid])
        
        # Find name from VPs first
        name = None
        if vps:
            sorted_vps = sorted(vps, key=lambda x: x[1], reverse=True)
            for prov_id, _ in sorted_vps:
                if prov_id in vp_names:
                    name = vp_names[prov_id]
                    break
        
        # If no VP name, generate geographic
        if name is None or name == "":
            name = generate_geographic_name(sid, owner, used_names)
        
        # Deduplicate names
        if name in used_names:
            # Add a suffix
            base_name = name
            idx = 2
            while name in used_names:
                name = f"{base_name} {idx}"
                idx += 1
        
        used_names.add(name)
        new_entries[sid] = name
        
        old = current_entries.get(sid, "<missing>")
        if old != name:
            print(f"  [{sid}] (owner={owner}) {old!r} -> {name!r}")
    
    # Write updated localization file
    lines = ['l_english:\n']
    for sid in sorted(new_entries.keys()):
        name = new_entries[sid]
        lines.append(f' STATE_{sid}:0 "{name}" #anka-generated state\n')
    
    loc_content = ''.join(lines)
    with open(ANKA_LOC_FILE, 'w', encoding='utf-8-sig') as f:
        f.write(loc_content)
    
    print(f"\nSaved {len(new_entries)} entries to {ANKA_LOC_FILE}")
    print("\nDone!")


if __name__ == '__main__':
    main()
