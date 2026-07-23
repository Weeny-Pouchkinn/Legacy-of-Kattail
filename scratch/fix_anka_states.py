#!/usr/bin/env python3
"""
fix_anka_states.py
Fixes all anka-generated STATE_ pattern states (1405-1554, 1570-1575) and
zero-population states from the error log in Legacy of Kattail mod.

Also fixes:
 - Province building errors (orphaned province references)
 - Invalid dockyard errors
 - Map port errors (buildings.txt)
"""

import os
import re
import random
import codecs

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
LOC_DIR = os.path.join(MOD_ROOT, "localisation", "english")
VP_LOC_FILE = os.path.join(LOC_DIR, "victory_points_l_english.yml")
STATE_LOC_FILE = os.path.join(LOC_DIR, "state_names_l_english.yml")
ANKA_LOC_FILE = os.path.join(LOC_DIR, "anka_new_states_l_english.yml")
BUILDINGS_FILE = os.path.join(MOD_ROOT, "map", "buildings.txt")

# Category -> local_building_slots
CATEGORY_SLOTS = {
    "wasteland": 0, "enclave": 0, "tiny_island": 0, "space": 0,
    "pastoral": 1, "small_island": 1,
    "rural": 2,
    "town": 4,
    "large_town": 5,
    "city": 6,
    "large_city": 8,
    "metropolis": 10,
    "megalopolis": 12,
}

# Category -> (pop_min, pop_max) for random assignment
CATEGORY_POP = {
    "pastoral":    (100_000,   500_000),
    "small_island":(50_000,    300_000),
    "rural":       (300_000,   1_000_000),
    "town":        (500_000,   3_000_000),
    "large_town":  (1_000_000, 4_000_000),
    "city":        (2_000_000, 6_000_000),
    "large_city":  (4_000_000, 8_000_000),
    "metropolis":  (6_000_000, 12_000_000),
    "megalopolis": (10_000_000,16_000_000),
}

# Ordered list of categories for slot-fitting
CATEGORY_ORDER = ["pastoral","rural","town","large_town","city","large_city","metropolis","megalopolis"]

# Province building errors: state_id -> list of province IDs to remove
PROVINCE_BUILDING_ERRORS = {
    37:   [10655],
    87:   [3689],
    96:   [7040],
    176:  [2703, 8389],
    202:  [15998],
    207:  [16303],
    219:  [16338],
    260:  [16788],
    324:  [10299],
    364:  [6245],
    605:  [15292, 11115, 7713, 15119, 15049, 15007],
    611:  [16179, 9146, 447, 287, 16300, 16228, 8852, 1376, 1759, 9155, 1906, 11281],
    725:  [17337],
    821:  [6949],
    1050: [2590, 15531],
}

# States with invalid dockyards (landlocked) - state_id
INVALID_DOCKYARD_STATES = {25, 74, 177, 488, 1037, 1046, 1419, 1425, 1466, 1483, 1499, 1536, 1544}

# Named zero-pop states from error log (these already have localization, just need population)
NAMED_ZERO_POP_STATES = {
    71, 76, 93, 105, 120, 123, 124, 128, 149, 166, 203, 256, 258, 269, 276, 281,
    297, 303, 314, 321, 325, 722, 724, 734, 740, 741, 844,
    1036, 1037, 1038, 1039, 1041, 1042, 1043, 1044, 1046, 1047, 1048, 1049,
    1052, 1053, 1054, 1055, 1313,
    1555, 1556, 1562, 1563, 1567, 1568,
}

# STATE_ pattern states that need full processing
STATE_PATTERN_IDS = set(range(1405, 1555)) | set(range(1570, 1576))

# These STATE_ states have VP entries that give them population already > 0 (from subagent report)
# We still need to add names, adjust categories, and apply ±15% randomization
# States that were reported with manpower=0 in STATE_ range:
STATE_ZERO_POP = {
    1421, 1422, 1424, 1425, 1426, 1431, 1432, 1433, 1434, 1448,
    *range(1470, 1497), 1500, 1501, *range(1508, 1537), *range(1539, 1552),
    1570, 1571, 1572, 1573, 1574
}

random.seed(42)  # reproducible


def read_file_utf8bom(path):
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:3] == b'\xef\xbb\xbf':
        return raw[3:].decode('utf-8'), True
    return raw.decode('utf-8'), False


def write_file_utf8bom(path, content, has_bom):
    with open(path, 'wb') as f:
        if has_bom:
            f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))


def load_vp_localization():
    """Load province_id -> city_name from victory_points_l_english.yml"""
    vp_names = {}
    try:
        content, _ = read_file_utf8bom(VP_LOC_FILE)
        for line in content.splitlines():
            m = re.match(r'\s*VICTORY_POINTS_(\d+):0\s+"([^"]+)"', line)
            if m:
                vp_names[int(m.group(1))] = m.group(2)
    except Exception as e:
        print(f"Warning: could not load VP localization: {e}")
    return vp_names


def load_state_localization():
    """Load state_id -> name from state_names_l_english.yml"""
    state_names = {}
    try:
        content, _ = read_file_utf8bom(STATE_LOC_FILE)
        for line in content.splitlines():
            m = re.match(r'\s*STATE_(\d+):\d+\s+"([^"]+)"', line)
            if m:
                state_names[int(m.group(1))] = m.group(2)
    except Exception as e:
        print(f"Warning: could not load state localization: {e}")
    return state_names


def parse_state_file(filepath):
    """Parse a state file and return a dict of key properties."""
    content, has_bom = read_file_utf8bom(filepath)
    result = {
        'content': content,
        'has_bom': has_bom,
        'id': None,
        'name': None,
        'manpower': None,
        'state_category': None,
        'provinces': [],
        'vps': [],  # list of (province_id, vp_value)
        'buildings_used': 0,  # slots used by factory buildings
        'has_dockyard': False,
    }
    
    # Parse ID
    m = re.search(r'\bid\s*=\s*(\d+)', content)
    if m:
        result['id'] = int(m.group(1))
    
    # Parse name
    m = re.search(r'\bname\s*=\s*"([^"]+)"', content)
    if m:
        result['name'] = m.group(1)
    
    # Parse manpower
    m = re.search(r'\bmanpower\s*=\s*(\d+)', content)
    if m:
        result['manpower'] = int(m.group(1))
    
    # Parse state_category
    m = re.search(r'\bstate_category\s*=\s*(\w+)', content)
    if m:
        result['state_category'] = m.group(1)
    
    # Parse provinces
    m = re.search(r'\bprovinces\s*=\s*\{([^}]*)\}', content, re.DOTALL)
    if m:
        result['provinces'] = [int(x) for x in m.group(1).split() if x.isdigit()]
    
    # Parse VPs
    for m in re.finditer(r'\bvictory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', content):
        result['vps'].append((int(m.group(1)), int(m.group(2))))
    
    # Count building slots used
    slots = 0
    slots += len(re.findall(r'\bindustrial_complex\s*=\s*(\d+)', content)) and \
             sum(int(x) for x in re.findall(r'\bindustrial_complex\s*=\s*(\d+)', content))
    slots += sum(int(x) for x in re.findall(r'\barms_factory\s*=\s*(\d+)', content))
    # Dockyard
    dockyard_match = re.findall(r'\bdockyard\s*=\s*(\d+)', content)
    if dockyard_match:
        result['has_dockyard'] = True
        slots += sum(int(x) for x in dockyard_match)
    result['buildings_used'] = slots
    
    return result


def determine_best_category(buildings_used, current_category):
    """
    Pick the best category so there are 1-2 free building slots.
    Target: slots = buildings_used + 1 or buildings_used + 2
    """
    if buildings_used == 0:
        # If no buildings, keep current or use pastoral/rural
        if current_category in CATEGORY_SLOTS:
            return current_category
        return "rural"
    
    target_slots_low = buildings_used + 1
    target_slots_high = buildings_used + 2
    
    best = None
    for cat in CATEGORY_ORDER:
        slots = CATEGORY_SLOTS[cat]
        if target_slots_low <= slots <= target_slots_high:
            best = cat
            break
        # If we overshoot but it's the closest, still pick it
        if slots >= target_slots_low:
            best = cat
            break
    
    if best is None:
        # Clamp to megalopolis if buildings_used is very high
        best = "megalopolis"
    
    return best


def assign_population(state_category):
    """Assign a base population from category range."""
    if state_category not in CATEGORY_POP:
        return random.randint(100_000, 500_000)
    lo, hi = CATEGORY_POP[state_category]
    return random.randint(lo, hi)


def randomize_population(manpower, pct=0.15):
    """Apply ±15% randomization to manpower."""
    factor = 1.0 + random.uniform(-pct, pct)
    return max(1000, int(manpower * factor))


def generate_geographic_name(state_id, provinces, vps, owner):
    """
    Generate a geographic/directional name for states without VP localization.
    Uses owner + a direction/number combo.
    """
    directions = ["North", "South", "East", "West", "Central", "Upper", "Lower", "Far North", "Far South", "Far East", "Far West"]
    direction = directions[state_id % len(directions)]
    # Try to make a name from owner
    owner_names = {
        "PRL": "Parlesia", "AUR": "Aurelia", "ELO": "Eloria", "WPR": "West Praw",
        "FRA": "Francia", "NKB": "Nokobia", "LMB": "Lambia", "OST": "Ostmark",
        "CAT": "Catalia", "KHA": "Kharna", "TEN": "Tenia", "LIO": "Lionheart",
        "CLE": "Cleria", "ROQ": "Roqueria", "MCF": "Macafia", "NEU": "Neumark",
        "POT": "Potland", "HYP": "Hyperia", "TAI": "Taikara", "PAW": "Pawland",
        "NMI": "Neminia", "ACR": "Amphibia", "FOD": "Fodaria", "TEM": "Temperia",
        "KKN": "Krönia", "PER": "Perania", "NKR": "Nokrania", "HYP": "Hyperia",
        "PTQ": "Prateque", "VEL": "Velia", "UCE": "Uckenia",
    }
    region = owner_names.get(owner, owner)
    num = (state_id % 12) + 1
    return f"{direction} {region} {num}"


def get_state_name(state_info, vp_names):
    """
    Determine the name for a STATE_ pattern state.
    Priority: highest VP province name from vp_names.
    Fallback: generate geographic name.
    """
    if state_info['vps']:
        # Sort by VP value descending, pick highest
        sorted_vps = sorted(state_info['vps'], key=lambda x: x[1], reverse=True)
        for prov_id, _ in sorted_vps:
            if prov_id in vp_names:
                return vp_names[prov_id]
    
    # No VP or no name found - generate geographic name
    return generate_geographic_name(
        state_info['id'],
        state_info['provinces'],
        state_info['vps'],
        None  # will look up owner separately
    )


def process_state_file(filepath, state_info, new_name, new_category, new_manpower,
                       is_new_state, remove_dockyard, remove_provinces):
    """Apply all changes to a state file content and return new content."""
    content = state_info['content']
    
    # 1. Add #anka-generated state comment as first line (only for STATE_ pattern states)
    if is_new_state:
        if not content.startswith('#anka-generated state'):
            content = '#anka-generated state\n' + content
    
    # 2. Update state name
    if new_name:
        content = re.sub(r'(\bname\s*=\s*")[^"]*(")', f'\\g<1>{new_name}\\2', content)
    
    # 3. Update state_category
    if new_category:
        content = re.sub(r'\bstate_category\s*=\s*\w+', f'state_category = {new_category}', content)
    
    # 4. Update manpower
    if new_manpower is not None:
        if re.search(r'\bmanpower\s*=\s*\d+', content):
            content = re.sub(r'\bmanpower\s*=\s*\d+', f'manpower = {new_manpower}', content)
        else:
            # Insert manpower after 'state_category = ...' line or after 'name = ...'
            content = re.sub(
                r'(\bstate_category\s*=\s*\w+)',
                f'\\1\n\tmanpower = {new_manpower}',
                content
            )
    
    # 5. Remove invalid dockyard
    if remove_dockyard:
        content = re.sub(r'\n?\t*dockyard\s*=\s*\d+\n?', '\n', content)
        content = re.sub(r'\n{3,}', '\n\n', content)  # clean up extra blank lines
    
    # 6. Remove province building blocks for orphaned provinces
    for prov_id in remove_provinces:
        # Match province building block like: 10655 = { supply_node = 1 bunker = 3 naval_base = 2 }
        pattern = rf'\n?\t*{prov_id}\s*=\s*\{{[^}}]*\}}\n?'
        content = re.sub(pattern, '\n', content)
    
    # Clean up any double newlines inside buildings blocks
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content


def fix_buildings_txt():
    """
    Fix map/buildings.txt:
    - Remove floating_harbor line for province 21029 (landlocked, invalid sea zone)
    - Check provinces 10565 and 21035 (coastal, no port in nudger)
    """
    print("\n=== Fixing map/buildings.txt ===")
    
    with open(BUILDINGS_FILE, 'rb') as f:
        raw = f.read()
    
    # Detect line endings
    has_crlf = b'\r\n' in raw
    
    content = raw.decode('utf-8', errors='replace')
    lines = content.splitlines(keepends=True)
    
    new_lines = []
    removed = []
    added = []
    
    # Track state-province relationship for 10565 and 21035 port fix
    # Province 10565 is in state 82, province 21035 is in state 736
    # The floating_harbor entries exist but we need to check if they're actually there
    
    has_10565_harbor = False
    has_21035_harbor = False
    state82_harbor_ref = None  # line index for state 82's harbor section
    state736_harbor_ref = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Remove floating_harbor for province 21029 (landlocked with invalid sea zone)
        if re.match(r'736;floating_harbor;[^;]+;[^;]+;[^;]+;[^;]+;21029\r?\n?', stripped + '\n'):
            print(f"  REMOVE line {i+1}: {stripped} (province 21029 is landlocked)")
            removed.append(i+1)
            continue
        
        # Track floating_harbor for 10565 
        if re.match(r'82;floating_harbor;[^;]+;[^;]+;[^;]+;[^;]+;10565', stripped):
            has_10565_harbor = True
        
        # Track floating_harbor for 21035
        if re.match(r'736;floating_harbor;[^;]+;[^;]+;[^;]+;[^;]+;21035', stripped):
            has_21035_harbor = True
        
        new_lines.append(line)
    
    result_content = ''.join(new_lines)
    
    # For provinces 10565 and 21035 that are coastal with "no port building in nudger":
    # The floating_harbor entries EXIST (we confirmed above), so the issue is the 
    # game can't find the nudger entry. This is likely because these floating_harbor
    # entries are present but the game complains anyway (could be a sea zone issue).
    # The safe fix: the floating_harbor IS the nudger port. If they exist, the error
    # might be cosmetic. We'll log what we found.
    print(f"  Province 10565 has floating_harbor: {has_10565_harbor}")
    print(f"  Province 21035 has floating_harbor: {has_21035_harbor}")
    
    if not has_10565_harbor:
        print("  WARNING: Province 10565 has no floating_harbor - adding placeholder port")
        # Add a port entry for state 82, province 10565
        # Use coordinates from unitstacks.txt approximate position
        port_line = "82;floating_harbor;1239.15;9.50;1211.10;-2.98;10565\r\n"
        # Insert after state 82's last floating_harbor
        # Find last 82;floating_harbor line
        for i in range(len(new_lines) - 1, -1, -1):
            if new_lines[i].startswith('82;floating_harbor;'):
                new_lines.insert(i + 1, port_line)
                added.append(f"state82 port province 10565")
                break
        result_content = ''.join(new_lines)
    
    if not has_21035_harbor:
        print("  WARNING: Province 21035 has no floating_harbor - adding placeholder port")
        port_line = "736;floating_harbor;1282.64;9.50;692.21;-1.25;21035\r\n"
        for i in range(len(new_lines) - 1, -1, -1):
            if new_lines[i].startswith('736;floating_harbor;'):
                new_lines.insert(i + 1, port_line)
                added.append(f"state736 port province 21035")
                break
        result_content = ''.join(new_lines)
    
    with open(BUILDINGS_FILE, 'wb') as f:
        f.write(result_content.encode('utf-8'))
    
    print(f"  Removed {len(removed)} lines, added {len(added)} lines")
    print(f"  Saved: {BUILDINGS_FILE}")


def main():
    random.seed(42)
    print("=== fix_anka_states.py ===\n")
    
    # Load VP localization
    vp_names = load_vp_localization()
    print(f"Loaded {len(vp_names)} VP names")
    
    # Load existing state localization
    state_names_existing = load_state_localization()
    print(f"Loaded {len(state_names_existing)} existing state names")
    
    # Collect all state files
    state_files = {}
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith('.txt'):
            continue
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            state_files[sid] = os.path.join(STATES_DIR, fname)
    
    print(f"Found {len(state_files)} state files\n")
    
    # Collect new localization entries
    new_loc_entries = {}  # state_id -> name
    
    # Track stats
    stats = {
        'new_states_processed': 0,
        'zero_pop_fixed': 0,
        'dockyard_removed': 0,
        'province_building_removed': 0,
    }
    
    # Process all states
    for sid in sorted(state_files.keys()):
        filepath = state_files[sid]
        
        # Determine what needs to change
        is_new_state = sid in STATE_PATTERN_IDS
        is_named_zero_pop = sid in NAMED_ZERO_POP_STATES
        remove_provinces = PROVINCE_BUILDING_ERRORS.get(sid, [])
        remove_dockyard = sid in INVALID_DOCKYARD_STATES
        
        if not (is_new_state or is_named_zero_pop or remove_provinces or remove_dockyard):
            continue
        
        try:
            state_info = parse_state_file(filepath)
        except Exception as e:
            print(f"  ERROR parsing {filepath}: {e}")
            continue
        
        new_name = None
        new_category = None
        new_manpower = None
        
        if is_new_state:
            stats['new_states_processed'] += 1
            
            # Determine name
            state_name = get_state_name(state_info, vp_names)
            # If no VP name found, generate geographic name with owner
            if state_name is None or state_name == "":
                state_name = generate_geographic_name(
                    sid, state_info['provinces'], state_info['vps'],
                    None
                )
            
            new_name = f"STATE_{sid}"  # keep as internal key, name goes in loc
            new_loc_entries[sid] = state_name
            
            # Determine building count WITHOUT dockyard if we're removing it
            buildings_used = state_info['buildings_used']
            if remove_dockyard and state_info['has_dockyard']:
                # Subtract dockyard count from buildings_used
                dockyard_counts = re.findall(r'\bdockyard\s*=\s*(\d+)', state_info['content'])
                for dc in dockyard_counts:
                    buildings_used -= int(dc)
            
            # Determine category
            new_category = determine_best_category(buildings_used, state_info['state_category'])
            
            # Determine population
            current_pop = state_info['manpower'] if state_info['manpower'] is not None else 0
            if current_pop == 0 or sid in STATE_ZERO_POP:
                base_pop = assign_population(new_category)
                new_manpower = randomize_population(base_pop)
                stats['zero_pop_fixed'] += 1
            else:
                # Randomize existing population ±15%
                new_manpower = randomize_population(current_pop)
            
            cat_display = f"{state_info['state_category']} -> {new_category}" if new_category != state_info['state_category'] else new_category
            print(f"  [{sid}] {state_name} | owner={None} | cat: {cat_display} | pop: {current_pop} -> {new_manpower:,} | bldg slots used: {buildings_used}")
        
        elif is_named_zero_pop:
            stats['zero_pop_fixed'] += 1
            current_pop = state_info['manpower'] if state_info['manpower'] is not None else 0
            if current_pop == 0:
                base_pop = assign_population(state_info['state_category'])
                new_manpower = randomize_population(base_pop)
            else:
                new_manpower = randomize_population(current_pop)
            print(f"  [{sid}] (named zero-pop) {state_info['name']} | cat: {state_info['state_category']} | pop: {current_pop} -> {new_manpower:,}")
        
        if remove_dockyard:
            stats['dockyard_removed'] += 1
            print(f"  [{sid}] Removing invalid dockyard")
        
        if remove_provinces:
            stats['province_building_removed'] += len(remove_provinces)
            print(f"  [{sid}] Removing province building refs: {remove_provinces}")
        
        # Apply changes
        new_content = process_state_file(
            filepath, state_info,
            new_name=new_name if is_new_state else None,
            new_category=new_category,
            new_manpower=new_manpower,
            is_new_state=is_new_state,
            remove_dockyard=remove_dockyard,
            remove_provinces=remove_provinces,
        )
        
        write_file_utf8bom(filepath, new_content, state_info['has_bom'])
    
    # Write new localization file
    print(f"\n=== Writing localization for {len(new_loc_entries)} new states ===")
    loc_lines = ['\ufeffl_english:\n']  # BOM + header
    for sid in sorted(new_loc_entries.keys()):
        name = new_loc_entries[sid]
        loc_lines.append(f' STATE_{sid}:0 "{name}" #anka-generated state\n')
    
    loc_content = ''.join(loc_lines)
    with open(ANKA_LOC_FILE, 'w', encoding='utf-8-sig') as f:
        f.write(loc_content)
    print(f"Saved: {ANKA_LOC_FILE}")
    
    # Fix map/buildings.txt
    fix_buildings_txt()
    
    # Print stats
    print("\n=== Summary ===")
    print(f"  New STATE_ states processed: {stats['new_states_processed']}")
    print(f"  Zero-population states fixed: {stats['zero_pop_fixed']}")
    print(f"  States with dockyard removed: {stats['dockyard_removed']}")
    print(f"  Province building refs removed: {stats['province_building_removed']}")
    print("\nDone!")


if __name__ == '__main__':
    main()
