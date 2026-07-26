#!/usr/bin/env python3
"""
fix_more_errors.py
Fixes MAP_ERRORs (missing air_base, rocket_site, anti_air_building),
navy spawn errors (land provinces),
air base spawn errors (state has no air base),
and bumps Anka state categories based on urban tiles and VPs.
"""

import os
import re

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
UNITS_DIR = os.path.join(MOD_ROOT, "history", "units")
BUILDINGS_FILE = os.path.join(MOD_ROOT, "map", "buildings.txt")
UNITSTACKS_FILE = os.path.join(MOD_ROOT, "map", "unitstacks.txt")
DEF_FILE = os.path.join(MOD_ROOT, "map", "definition.csv")

# 1. Map errors
MAP_ERROR_STATES = {96, 152, 176, 202, 207, 219, 324, 605, 611, 1040, 1050}

# 2. Navy port errors
NAVY_ERROR_PROVINCES = {3727, 12110, 3097, 7181, 4970, 5494, 17337, 4435}

# 3. Air base errors
AIR_BASE_ERROR_STATES = {74, 583, 25, 477, 588, 535, 84, 79, 544, 99, 519, 116, 488, 156, 119, 136, 133, 177, 204, 206, 168, 611, 174, 563, 71, 128, 1043, 76, 96, 166, 1041, 1050, 149, 203, 258, 276, 325, 722, 321}

# 4. Anka states
ANKA_STATES = set(range(1405, 1555)) | set(range(1570, 1576))

CATEGORY_ORDER = ["wasteland", "enclave", "tiny_island", "space", "pastoral", "small_island", "rural", "town", "large_town", "city", "large_city", "metropolis", "megalopolis"]

def get_category_level(cat):
    try:
        return CATEGORY_ORDER.index(cat)
    except ValueError:
        return 0

def read_file(path):
    with open(path, 'rb') as f:
        raw = f.read()
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    return (raw[3:].decode('utf-8', errors='replace') if has_bom else raw.decode('utf-8', errors='replace')), has_bom

def write_file(path, content, has_bom):
    with open(path, 'wb') as f:
        if has_bom:
            f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))

def main():
    print("Loading map data...")
    # Load unitstacks coordinates
    prov_coords = {}
    with open(UNITSTACKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 5:
                prov_id = int(parts[0])
                if prov_id not in prov_coords:
                    prov_coords[prov_id] = (parts[2], parts[3], parts[4])

    # Load terrain
    urban_provinces = set()
    with open(DEF_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split(';')
            if len(parts) >= 7:
                if parts[6].strip() == 'urban':
                    urban_provinces.add(int(parts[0]))

    # Parse states
    state_files = {}
    prov_to_state = {}
    state_to_owner = {}
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith('.txt'): continue
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            filepath = os.path.join(STATES_DIR, fname)
            state_files[sid] = filepath
            
            content, _ = read_file(filepath)
            
            # Find owner
            owner_m = re.search(r'\bowner\s*=\s*(\w+)', content)
            if owner_m:
                state_to_owner[sid] = owner_m.group(1)
            
            # Find provinces
            prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', content)
            if prov_m:
                for p in prov_m.group(1).split():
                    if p.isdigit():
                        prov_to_state[int(p)] = sid

    # Load all ports from buildings.txt
    print("Finding valid ports...")
    port_provinces = set()
    with open(BUILDINGS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.split(';')
            if len(parts) >= 7 and parts[1] == 'naval_base':
                # format: <state>;naval_base;x;y;z;rot;<prov>
                prov = int(parts[6].strip())
                port_provinces.add(prov)

    tag_to_ports = {}
    for prov in port_provinces:
        if prov in prov_to_state:
            sid = prov_to_state[prov]
            if sid in state_to_owner:
                tag = state_to_owner[sid]
                tag_to_ports.setdefault(tag, []).append(prov)

    # 1. Fix Navy errors
    print("Fixing Navy errors in history/units...")
    for fname in os.listdir(UNITS_DIR):
        if not fname.endswith('.txt'): continue
        path = os.path.join(UNITS_DIR, fname)
        content, has_bom = read_file(path)
        
        # Check if this file has any of our bad navy provinces
        changed = False
        for bad_prov in NAVY_ERROR_PROVINCES:
            # We look for base = X or location = X or something similar.
            # Easiest way: regex search for \b(base|location)\s*=\s*bad_prov\b
            pattern = rf'\b(base|location)\s*=\s*{bad_prov}\b'
            if re.search(pattern, content):
                # We need a replacement port. What tag is this file?
                # Filename format: TAG_1936_naval.txt
                tag_m = re.match(r'^([A-Z]{3})_', fname)
                tag = tag_m.group(1) if tag_m else None
                
                good_port = None
                if tag and tag in tag_to_ports and tag_to_ports[tag]:
                    good_port = tag_to_ports[tag][0]
                else:
                    # fallback: try to find ANY port they own, or just use a generic port.
                    print(f"  WARNING: No known port for tag {tag} in file {fname}. Keeping {bad_prov} but it's invalid.")
                
                if good_port:
                    print(f"  [{fname}] Replaced bad port {bad_prov} with {good_port} (tag {tag})")
                    content = re.sub(pattern, lambda m: f"{m.group(1)} = {good_port}", content)
                    changed = True
        
        if changed:
            write_file(path, content, has_bom)

    # 2. Fix State files: Air Base errors & Anka Category bumps
    print("Fixing State files...")
    for sid, filepath in state_files.items():
        content, has_bom = read_file(filepath)
        changed = False
        
        # Air base error
        if sid in AIR_BASE_ERROR_STATES:
            # Add air_base = 1 inside buildings = { if not present
            if not re.search(r'\bair_base\s*=\s*[1-9]', content):
                # Find buildings = {
                b_match = re.search(r'(\bbuildings\s*=\s*\{)', content)
                if b_match:
                    content = content[:b_match.end()] + "\n\t\t\tair_base = 1" + content[b_match.end():]
                    changed = True
                    print(f"  [{sid}] Added air_base = 1")
                else:
                    print(f"  [{sid}] WARNING: No buildings block found to add air_base")

        # Anka category bump
        if sid in ANKA_STATES:
            cat_m = re.search(r'\bstate_category\s*=\s*(\w+)', content)
            if cat_m:
                current_cat = cat_m.group(1)
                target_cat = current_cat
                
                # Check VPs
                has_vp = 'victory_points' in content
                if has_vp and get_category_level('town') > get_category_level(target_cat):
                    target_cat = 'town'
                
                # Check Urban
                prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', content)
                has_urban = False
                if prov_m:
                    for p in prov_m.group(1).split():
                        if p.isdigit() and int(p) in urban_provinces:
                            has_urban = True
                            break
                if has_urban and get_category_level('large_town') > get_category_level(target_cat):
                    target_cat = 'large_town'
                
                if target_cat != current_cat:
                    content = re.sub(r'\bstate_category\s*=\s*\w+', f'state_category = {target_cat}', content)
                    changed = True
                    print(f"  [{sid}] Bumped category: {current_cat} -> {target_cat} (VP:{has_vp}, Urban:{has_urban})")

        if changed:
            write_file(filepath, content, has_bom)

    # 3. Map errors (Missing buildings)
    print("Appending missing buildings to map/buildings.txt...")
    bcontent, bbom = read_file(BUILDINGS_FILE)
    b_lines = []
    appended_count = 0
    
    for sid in MAP_ERROR_STATES:
        # Get first province for coordinates
        if sid in state_files:
            s_content, _ = read_file(state_files[sid])
            prov_m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', s_content)
            if prov_m:
                provs = [int(p) for p in prov_m.group(1).split() if p.isdigit()]
                if provs:
                    prov = provs[0]
                    if prov in prov_coords:
                        x, y, z = prov_coords[prov]
                        b_lines.append(f"{sid};air_base;{x};{y};{z};0.00;0\r\n")
                        b_lines.append(f"{sid};anti_air_building;{x};{y};{z};0.00;0\r\n")
                        b_lines.append(f"{sid};rocket_site;{x};{y};{z};0.00;0\r\n")
                        appended_count += 3
                        print(f"  [{sid}] Added map buildings at province {prov} ({x},{y},{z})")
                    else:
                        print(f"  [{sid}] WARNING: Province {prov} not in unitstacks.txt")
                else:
                    print(f"  [{sid}] WARNING: No provinces found in state file")

    if b_lines:
        # Ensure buildings.txt ends with newline before appending
        if not bcontent.endswith('\n'):
            bcontent += '\r\n'
        bcontent += "".join(b_lines)
        write_file(BUILDINGS_FILE, bcontent, bbom)
        print(f"Appended {appended_count} lines to map/buildings.txt")

    print("Done!")

if __name__ == '__main__':
    main()
