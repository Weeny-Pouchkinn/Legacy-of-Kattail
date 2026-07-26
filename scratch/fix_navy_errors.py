#!/usr/bin/env python3
import os, re

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
BUILDINGS_FILE = os.path.join(MOD_ROOT, "map", "buildings.txt")
UNITSTACKS_FILE = os.path.join(MOD_ROOT, "map", "unitstacks.txt")

PROV_TO_STATE = {
    4970: 1408, 3727: 1447, 5494: 1449, 3097: 1460,
    4435: 1481, 7181: 1502, 17337: 1565, 12110: 601
}

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
    # Load coords
    coords = {}
    with open(UNITSTACKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) >= 5:
                prov = int(parts[0])
                if prov not in coords:
                    coords[prov] = (parts[2], parts[3], parts[4])

    bcontent, bbom = read_file(BUILDINGS_FILE)
    if not bcontent.endswith('\n'):
        bcontent += '\r\n'

    b_lines = []

    for prov, sid in PROV_TO_STATE.items():
        # Find the state file
        fname = None
        for f in os.listdir(STATES_DIR):
            if f.startswith(f"{sid}-"):
                fname = f
                break
        
        if fname:
            path = os.path.join(STATES_DIR, fname)
            s_content, s_bom = read_file(path)
            
            # Add to buildings block
            if str(prov) + ' = {' not in s_content:
                b_match = re.search(r'(\bbuildings\s*=\s*\{)', s_content)
                if b_match:
                    insert = f"\n\t\t\t{prov} = {{\n\t\t\t\tnaval_base = 1\n\t\t\t}}"
                    s_content = s_content[:b_match.end()] + insert + s_content[b_match.end():]
                    write_file(path, s_content, s_bom)
                    print(f"Added naval_base = 1 for prov {prov} in state {sid}")
        
        if prov in coords:
            x, y, z = coords[prov]
            # Avoid duplicate if already exists
            if f"{sid};naval_base;" not in bcontent or str(prov) not in bcontent:
                b_lines.append(f"{sid};naval_base;{x};{y};{z};0.00;{prov}\r\n")
                b_lines.append(f"{sid};naval_base_spawn;{x};{y};{z};0.00;0\r\n")
                print(f"Added buildings.txt entries for port {prov}")
    
    if b_lines:
        bcontent += "".join(b_lines)
        write_file(BUILDINGS_FILE, bcontent, bbom)

if __name__ == '__main__':
    main()
