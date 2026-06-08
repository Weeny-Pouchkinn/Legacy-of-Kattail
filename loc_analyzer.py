import os
import re
import sys

def parse_yml_file(filepath):
    keys = {}
    try:
        with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' not in line:
                    continue
                parts = line.split(':', 1)
                key = parts[0].strip()
                if not re.match(r'^[a-zA-Z0-9_\-\.]+$', key):
                    continue
                val_part = parts[1].strip()
                match = re.match(r'^(\d*)\s*"(.*)"', val_part)
                if match:
                    val = match.group(2)
                    keys[key] = {
                        'val': val,
                        'file': filepath,
                        'line': line_num
                    }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return keys

def load_all_defined_keys(root_dir):
    defined_keys = {}
    loc_dir = os.path.join(root_dir, 'localisation')
    if not os.path.exists(loc_dir):
        return defined_keys
    for dirpath, _, filenames in os.walk(loc_dir):
        for f in filenames:
            if f.endswith('.yml'):
                fp = os.path.join(dirpath, f)
                file_keys = parse_yml_file(fp)
                for k, v in file_keys.items():
                    defined_keys[k] = v
    return defined_keys

def extract_keys_from_events(events_dir):
    referenced = {}
    if not os.path.exists(events_dir):
        return referenced
    
    patterns = [
        re.compile(r'\btitle\s*=\s*(?:"([^"]+)"|([a-zA-Z0-9_\-\.]+))'),
        re.compile(r'\bdesc\s*=\s*(?:"([^"]+)"|([a-zA-Z0-9_\-\.]+))'),
        re.compile(r'\bname\s*=\s*(?:"([^"]+)"|([a-zA-Z0-9_\-\.]+))'),
        re.compile(r'\btext\s*=\s*(?:"([^"]+)"|([a-zA-Z0-9_\-\.]+))')
    ]
    
    for dirpath, _, filenames in os.walk(events_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        for line_num, line in enumerate(file, 1):
                            comment_idx = line.find('#')
                            if comment_idx != -1:
                                line = line[:comment_idx]
                            for pattern in patterns:
                                for match in pattern.finditer(line):
                                    key = match.group(1) or match.group(2)
                                    if key and not key.isdigit():
                                        if key.lower() not in ['yes', 'no', 'root', 'from', 'prev', 'this']:
                                            if key not in referenced:
                                                referenced[key] = []
                                            referenced[key].append((fp, line_num, 'event'))
                except Exception as e:
                    print(f"Error reading event file {fp}: {e}")
    return referenced

def extract_focus_keys(focus_dir):
    expected = {}
    if not os.path.exists(focus_dir):
        return expected
    
    id_pattern = re.compile(r'\bid\s*=\s*([a-zA-Z0-9_\-\.]+)')
    
    for dirpath, _, filenames in os.walk(focus_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        for line_num, line in enumerate(file, 1):
                            comment_idx = line.find('#')
                            if comment_idx != -1:
                                line = line[:comment_idx]
                            match = id_pattern.search(line)
                            if match:
                                focus_id = match.group(1)
                                if focus_id and focus_id.lower() not in ['yes', 'no', 'root'] and not focus_id.endswith('_TREE') and not focus_id.endswith('_tree'):
                                    expected[focus_id] = (fp, line_num, 'focus_name')
                                    expected[focus_id + "_desc"] = (fp, line_num, 'focus_desc')
                except Exception as e:
                    print(f"Error reading focus file {fp}: {e}")
    return expected

def parse_decisions(decisions_dir):
    expected_keys = {}
    if not os.path.exists(decisions_dir):
        return expected_keys
        
    for dirpath, _, filenames in os.walk(decisions_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        content_no_comments = re.sub(r'#.*', '', content)
                        tokens = re.findall(r'([a-zA-Z0-9_\-\.]+)|([{}])|(=)', content_no_comments)
                        
                        depth = 0
                        last_identifier = None
                        current_category = None
                        
                        for token in tokens:
                            ident, brace, eq = token
                            if ident:
                                last_identifier = ident
                            elif brace == '{':
                                if depth == 0:
                                    if last_identifier:
                                        current_category = last_identifier
                                        expected_keys[current_category] = (fp, 0, 'category_name')
                                        expected_keys[current_category + "_desc"] = (fp, 0, 'category_desc')
                                elif depth == 1:
                                    if last_identifier and last_identifier not in ['visible', 'available', 'complete_effect', 'remove_effect', 'timeout_effect', 'ai_will_do', 'modifier', 'cost', 'custom_cost_trigger', 'custom_cost_text', 'days_remove', 'days_re_enable', 'fire_only_once', 'cancel_trigger']:
                                        decision_id = last_identifier
                                        expected_keys[decision_id] = (fp, 0, 'decision_name')
                                        expected_keys[decision_id + "_desc"] = (fp, 0, 'decision_desc')
                                depth += 1
                                last_identifier = None
                            elif brace == '}':
                                depth = max(0, depth - 1)
                                if depth == 0:
                                    current_category = None
                                last_identifier = None
                except Exception as e:
                    print(f"Error reading decision file {fp}: {e}")
    return expected_keys

def parse_ideas(ideas_dir):
    expected_keys = {}
    if not os.path.exists(ideas_dir):
        return expected_keys
        
    for dirpath, _, filenames in os.walk(ideas_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        content_no_comments = re.sub(r'#.*', '', content)
                        tokens = re.findall(r'([a-zA-Z0-9_\-\.]+)|([{}])|(=)', content_no_comments)
                        
                        depth = 0
                        last_identifier = None
                        
                        for token in tokens:
                            ident, brace, eq = token
                            if ident:
                                last_identifier = ident
                            elif brace == '{':
                                if depth == 2:
                                    if last_identifier and last_identifier not in ['allowed', 'cancel', 'modifier', 'targeted_modifier', 'picture', 'removal_cost', 'rule', 'traits', 'on_add', 'on_remove']:
                                        idea_id = last_identifier
                                        expected_keys[idea_id] = (fp, 0, 'idea_name')
                                        expected_keys[idea_id + "_desc"] = (fp, 0, 'idea_desc')
                                depth += 1
                                last_identifier = None
                            elif brace == '}':
                                depth = max(0, depth - 1)
                                last_identifier = None
                except Exception as e:
                    print(f"Error reading ideas file {fp}: {e}")
    return expected_keys

def parse_characters(characters_dir):
    expected_keys = {}
    if not os.path.exists(characters_dir):
        return expected_keys
        
    name_pattern = re.compile(r'\bname\s*=\s*(?:"([^"]+)"|([a-zA-Z0-9_\-\.]+))')
    
    for dirpath, _, filenames in os.walk(characters_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        for line_num, line in enumerate(file, 1):
                            comment_idx = line.find('#')
                            if comment_idx != -1:
                                line = line[:comment_idx]
                            match = name_pattern.search(line)
                            if match:
                                key = match.group(1) or match.group(2)
                                if key and not key.isdigit() and key.lower() not in ['yes', 'no', 'root']:
                                    expected_keys[key] = (fp, line_num, 'character_name')
                except Exception as e:
                    print(f"Error reading character file {fp}: {e}")
    return expected_keys

def parse_opinion_modifiers(opinion_dir):
    expected_keys = {}
    if not os.path.exists(opinion_dir):
        return expected_keys
        
    for dirpath, _, filenames in os.walk(opinion_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        content_no_comments = re.sub(r'#.*', '', content)
                        tokens = re.findall(r'([a-zA-Z0-9_\-\.]+)|([{}])|(=)', content_no_comments)
                        
                        depth = 0
                        last_identifier = None
                        
                        for token in tokens:
                            ident, brace, eq = token
                            if ident:
                                last_identifier = ident
                            elif brace == '{':
                                if depth == 1:
                                    if last_identifier and last_identifier not in ['opinion_modifiers']:
                                        modifier_id = last_identifier
                                        expected_keys[modifier_id] = (fp, 0, 'opinion_modifier')
                                depth += 1
                                last_identifier = None
                            elif brace == '}':
                                depth = max(0, depth - 1)
                                last_identifier = None
                except Exception as e:
                    print(f"Error reading opinion modifier file {fp}: {e}")
    return expected_keys

def parse_ideologies(ideologies_dir):
    expected_keys = {}
    if not os.path.exists(ideologies_dir):
        return expected_keys
        
    for dirpath, _, filenames in os.walk(ideologies_dir):
        for f in filenames:
            if f.endswith('.txt'):
                fp = os.path.join(dirpath, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        content_no_comments = re.sub(r'#.*', '', content)
                        tokens = re.findall(r'([a-zA-Z0-9_\-\.]+)|([{}])|(=)', content_no_comments)
                        
                        depth = 0
                        last_identifier = None
                        current_ideology = None
                        in_types = False
                        
                        for token in tokens:
                            ident, brace, eq = token
                            if ident:
                                last_identifier = ident
                            elif brace == '{':
                                if depth == 1:
                                    if last_identifier and last_identifier != 'ideologies':
                                        current_ideology = last_identifier
                                        expected_keys[current_ideology] = (fp, 0, 'ideology_name')
                                        expected_keys[current_ideology + "_desc"] = (fp, 0, 'ideology_desc')
                                        expected_keys[current_ideology + "_noun"] = (fp, 0, 'ideology_noun')
                                elif depth == 2:
                                    if last_identifier == 'types':
                                        in_types = True
                                elif depth == 3 and in_types:
                                    if last_identifier:
                                        sub_id = last_identifier
                                        expected_keys[sub_id] = (fp, 0, 'sub_ideology_name')
                                        expected_keys[sub_id + "_desc"] = (fp, 0, 'sub_ideology_desc')
                                        expected_keys[sub_id + "_noun"] = (fp, 0, 'sub_ideology_noun')
                                depth += 1
                                last_identifier = None
                            elif brace == '}':
                                depth = max(0, depth - 1)
                                if depth == 2:
                                    in_types = False
                                elif depth == 1:
                                    current_ideology = None
                                last_identifier = None
                except Exception as e:
                    print(f"Error reading ideology file {fp}: {e}")
    return expected_keys

def extract_all_script_tokens(root_dir):
    tokens = set()
    scan_dirs = ['common', 'events', 'history', 'interface', 'map', 'gfx']
    valid_exts = {'.txt', '.gui', '.gfx'}
    token_pattern = re.compile(r'[a-zA-Z0-9_\-\.]+')
    
    for folder in scan_dirs:
        folder_path = os.path.join(root_dir, folder)
        if not os.path.exists(folder_path):
            continue
        for dirpath, _, filenames in os.walk(folder_path):
            for f in filenames:
                _, ext = os.path.splitext(f)
                if ext.lower() in valid_exts:
                    fp = os.path.join(dirpath, f)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            content_no_comments = re.sub(r'#.*', '', content)
                            for match in token_pattern.finditer(content_no_comments):
                                tokens.add(match.group(0))
                    except Exception as e:
                        pass
    return tokens

def main():
    root_dir = '.'
    print("Loading defined localization keys...")
    defined_keys = load_all_defined_keys(root_dir)
    print(f"Loaded {len(defined_keys)} defined keys.")
    
    print("\nScanning event files...")
    event_keys = extract_keys_from_events(os.path.join(root_dir, 'events'))
    print(f"Found {len(event_keys)} referenced keys in events.")
    
    print("\nScanning focus tree files...")
    focus_keys = extract_focus_keys(os.path.join(root_dir, 'common', 'national_focus'))
    print(f"Expected {len(focus_keys)} keys from focuses.")
    
    print("\nScanning decision files...")
    decision_keys = parse_decisions(os.path.join(root_dir, 'common', 'decisions'))
    print(f"Expected {len(decision_keys)} keys from decisions.")
    
    print("\nScanning ideas files...")
    idea_keys = parse_ideas(os.path.join(root_dir, 'common', 'ideas'))
    print(f"Expected {len(idea_keys)} keys from ideas.")
    
    print("\nScanning character files...")
    character_keys = parse_characters(os.path.join(root_dir, 'common', 'characters'))
    print(f"Expected {len(character_keys)} keys from characters.")
    
    print("\nScanning opinion modifier files...")
    opinion_keys = parse_opinion_modifiers(os.path.join(root_dir, 'common', 'opinion_modifiers'))
    print(f"Expected {len(opinion_keys)} keys from opinion modifiers.")
    
    print("\nScanning ideology files...")
    ideology_keys = parse_ideologies(os.path.join(root_dir, 'common', 'ideologies'))
    print(f"Expected {len(ideology_keys)} keys from ideologies.")
    
    # Merge expected keys to check for missing
    all_expected = {}
    
    for k, v in event_keys.items():
        all_expected[k] = v[0]
        
    for k, v in focus_keys.items():
        all_expected[k] = v
        
    for k, v in decision_keys.items():
        all_expected[k] = v
        
    for k, v in idea_keys.items():
        all_expected[k] = v
        
    for k, v in character_keys.items():
        all_expected[k] = v
        
    for k, v in opinion_keys.items():
        all_expected[k] = v
        
    for k, v in ideology_keys.items():
        all_expected[k] = v
        
    # Check for missing keys
    missing_keys = {}
    for key, info in all_expected.items():
        if key not in defined_keys:
            if not re.match(r'^\d+$', key) and key.lower() not in ['yes', 'no', 'root', 'from', 'prev', 'this']:
                if not key.startswith('WARLORD_TAG_') and not key.startswith('MAPMODE_') and not key.startswith('COUNTRY_autonomy_') and not key.startswith('decision_cost_'):
                    missing_keys[key] = info
                
    print(f"\nFound {len(missing_keys)} missing localization keys.")
    
    # Check for unused keys
    print("\nExtracting all text tokens from mod scripts for unused check...")
    script_tokens = extract_all_script_tokens(root_dir)
    print(f"Extracted {len(script_tokens)} unique tokens from script files.")
    
    unused_keys = {}
    for key, info in defined_keys.items():
        is_used = key in script_tokens
        
        # Check implicit rules
        if not is_used:
            if key.endswith('_desc'):
                base = key[:-5]
                if base in focus_keys or base in decision_keys or base in idea_keys or base in ideology_keys:
                    is_used = True
            elif key.endswith('_name') or key.endswith('_noun'):
                base = key[:-5]
                if base in character_keys or base in ideology_keys:
                    is_used = True
                    
        # Check state/strategic region names which are loaded implicitly
        if not is_used:
            if re.match(r'^STATE_\d+$', key) or re.match(r'^STRATEGIC_REGION_\d+$', key) or re.match(r'^VICTORY_POINTS_\d+$', key):
                is_used = True
                
        # Check dynamic or standard game mechanics (like ideologies)
        if not is_used:
            if key.lower() in ['communism', 'fascism', 'democratic', 'neutrality', 'social_democracy', 'reformist_socialism', 'emergency_government', 'despotism', 'councilism', 'gestalt']:
                is_used = True
                
        # Check if key matches a character ID or character name
        if not is_used:
            if key in character_keys:
                is_used = True
                
        # Check country tags and common prefix conventions
        if not is_used:
            if len(key) == 3 and key.isupper():
                is_used = True
            elif len(key) > 3 and key[:4].isupper() and key[3] == '_':
                is_used = True
                
        # Check if key belongs to sub-ideologies
        if not is_used:
            if key in ideology_keys:
                is_used = True
                
        # Implicit prefix exclusions to prevent false positives
        if not is_used:
            if key.startswith('WARLORD_TAG_') or key.startswith('MAPMODE_') or key.startswith('COUNTRY_autonomy_') or key.startswith('autonomy_') or key.startswith('decision_cost_'):
                is_used = True
                
        if not is_used:
            unused_keys[key] = info
            
    print(f"Found {len(unused_keys)} potentially unused localization keys.")
    
    # Save the results to markdown files or text files so they can be easily reviewed
    with open('loc_analysis_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== MISSING LOCALIZATION KEYS ===\n")
        sorted_missing = sorted(missing_keys.items(), key=lambda x: (str(x[1][0]), x[0]))
        current_file = None
        for key, info in sorted_missing:
            fp, line_num, key_type = info[0], info[1], info[2]
            rel_path = os.path.relpath(fp, root_dir)
            if rel_path != current_file:
                f.write(f"\nIn file: {rel_path}\n")
                current_file = rel_path
            f.write(f"  Line {line_num}: '{key}' (type: {key_type})\n")
            
        f.write("\n\n=== UNUSED LOCALIZATION KEYS ===\n")
        sorted_unused = sorted(unused_keys.items(), key=lambda x: (x[1]['file'], x[0]))
        current_file = None
        for key, info in sorted_unused:
            fp = os.path.relpath(info['file'], root_dir)
            if fp != current_file:
                f.write(f"\nIn file: {fp}\n")
                current_file = fp
            f.write(f"  Line {info['line']}: '{key}' (value: \"{info['val']}\")\n")
            
    print("\nResults written to loc_analysis_results.txt")

if __name__ == '__main__':
    main()
