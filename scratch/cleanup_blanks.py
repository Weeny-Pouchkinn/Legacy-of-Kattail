#!/usr/bin/env python3
"""
cleanup_blanks.py - Remove excessive blank lines from state files that were modified.
Also fixes the 'Far West Fodaria 2 2' deduplication issue and WAC unknown owner.
"""

import os
import re

MOD_ROOT = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
STATES_DIR = os.path.join(MOD_ROOT, "history", "states")
LOC_DIR = os.path.join(MOD_ROOT, "localisation", "english")
ANKA_LOC_FILE = os.path.join(LOC_DIR, "anka_new_states_l_english.yml")

# States that had province buildings removed - clean up blank lines
STATES_TO_CLEAN = {37, 87, 96, 176, 202, 207, 219, 260, 324, 364, 605, 611, 725, 821, 1050}

# Also clean all STATE_ pattern states (they may have blank lines from dockyard removal)
STATE_PATTERN_IDS = set(range(1405, 1555)) | set(range(1570, 1576))
STATES_TO_CLEAN |= STATE_PATTERN_IDS

# States with dockyard removed
DOCKYARD_STATES = {25, 74, 177, 488, 1037, 1046, 1419, 1425, 1466, 1483, 1499, 1536, 1544}
STATES_TO_CLEAN |= DOCKYARD_STATES


def read_file(path):
    with open(path, 'rb') as f:
        raw = f.read()
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    if has_bom:
        return raw[3:].decode('utf-8'), True
    return raw.decode('utf-8'), False


def write_file(path, content, has_bom):
    with open(path, 'wb') as f:
        if has_bom:
            f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))


def clean_blank_lines(content):
    """
    Replace 3+ consecutive blank lines (possibly with whitespace) with max 1 blank line.
    Also clean up blank lines immediately inside { } blocks.
    """
    # Replace runs of 3+ newlines with 2 newlines
    content = re.sub(r'\n(\s*\n){2,}', '\n\n', content)
    # Remove blank lines right after opening {
    content = re.sub(r'(\{)\n\n', '\\1\n', content)
    # Remove blank lines right before closing }
    content = re.sub(r'\n\n(\s*\})', '\n\\1', content)
    return content


def main():
    print("=== cleanup_blanks.py ===\n")
    
    # Find all state files
    state_files = {}
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith('.txt'):
            continue
        m = re.match(r'^(\d+)-', fname)
        if m:
            sid = int(m.group(1))
            state_files[sid] = os.path.join(STATES_DIR, fname)
    
    cleaned = 0
    for sid in sorted(STATES_TO_CLEAN):
        if sid not in state_files:
            continue
        filepath = state_files[sid]
        content, has_bom = read_file(filepath)
        new_content = clean_blank_lines(content)
        if new_content != content:
            write_file(filepath, new_content, has_bom)
            cleaned += 1
    
    print(f"Cleaned blank lines in {cleaned} state files")
    
    # Fix the loc file: correct "Far West Fodaria 2 2" -> "South Fodaria 15"
    # and WAC -> "Far Praw" (WAC is presumably a West Praw variant)
    print("\nFixing problematic loc entries...")
    
    with open(ANKA_LOC_FILE, 'r', encoding='utf-8-sig') as f:
        loc_content = f.read()
    
    # Fix duplicated number suffix
    loc_content = loc_content.replace('"Far West Fodaria 2 2"', '"West Fodaria 16"')
    
    # Fix WAC entries (unknown owner tag)
    loc_content = loc_content.replace('"Far East WAC 13"', '"Far East Praw 13"')
    loc_content = loc_content.replace('"Far West WAC 14"', '"Far West Praw 14"')
    loc_content = loc_content.replace('"Near WAC 15"', '"Near Praw 15"')
    
    with open(ANKA_LOC_FILE, 'w', encoding='utf-8-sig') as f:
        f.write(loc_content)
    
    print("Fixed WAC and duplicate entries in loc file")
    print("\nDone!")


if __name__ == '__main__':
    main()
