
import os
import re
import json

sub_to_parent = {"anarchism": "communism", "councilism": "communism", "ultravisionary_socialism": "communism", "left_socialism": "communism", "communism_military_authority": "communism", "socio_kaiserism_military_authority": "communism", "reformist_socialism": "socialism", "syndicalism": "socialism", "kraksism": "socialism", "social_democracy": "social_democratic", "liberalism": "social_liberal", "centrism": "social_liberal", "market_democracy": "democratic", "techno_democracy": "democratic", "conservatism": "social_conservative", "census_democracy": "social_conservative", "reformed_kaiserism": "authoritarian_democratic", "corporatocracy": "authoritarian_democratic", "oligarchic_democracy": "authoritarian_democratic", "emergency_government": "authoritarian_democratic", "reformed_kaiserism_military_authority": "authoritarian_democratic", "technocracy": "authoritarian_democratic", "lorissian_kaiserism": "neutrality", "neutrality_military_authority": "neutrality", "magocracy": "neutrality", "despotism": "neutrality", "absolutism": "neutrality", "benevolent_absolutism": "neutrality", "anarchy": "neutrality", "technoautocracy": "neutrality", "kleptocracy": "neutrality", "stratocracy": "neutrality", "nationalism": "fascism", "ultranationalism": "fascism", "totalitarianism": "fascism", "kaiserism": "fascism", "fascism_military_authority": "fascism", "kaiserism_military_authority": "fascism"}

groups = [
    ["communism", "socialism", "social_democratic"],
    ["social_liberal", "democratic", "social_conservative"],
    ["authoritarian_democratic", "neutrality"],
    ["fascism"]
]

defaults = {
    "communism": "councilism",
    "socialism": "reformist_socialism",
    "social_democratic": "social_democracy",
    "social_liberal": "liberalism",
    "democratic": "market_democracy",
    "social_conservative": "conservatism",
    "authoritarian_democratic": "oligarchic_democracy",
    "neutrality": "despotism",
    "fascism": "nationalism"
}

char_to_file = {}
char_to_sub = {}
char_dir = 'common/characters'
for filename in os.listdir(char_dir):
    if not filename.endswith('.txt'): continue
    with open(os.path.join(char_dir, filename), 'r', encoding='utf-8') as f:
        content = f.read()
        top_match = re.search(r'characters\s*=\s*\{(.*)\}', content, re.DOTALL)
        if not top_match: continue
        chars_block = top_match.group(1)
        pos = 0
        while pos < len(chars_block):
            match = re.search(r'(\w+)\s*=\s*\{', chars_block[pos:])
            if not match: break
            char_id = match.group(1)
            start = pos + match.end()
            brace_count = 1
            cur = start
            while brace_count > 0 and cur < len(chars_block):
                if chars_block[cur] == '{': brace_count += 1
                elif chars_block[cur] == '}': brace_count -= 1
                cur += 1
            char_content = chars_block[start:cur]
            char_to_file[char_id] = filename
            leader_blocks = re.findall(r'country_leader\s*=\s*\{(.*?)\}', char_content, re.DOTALL)
            ideologies = []
            for lb in leader_blocks:
                ideol_match = re.search(r'ideology\s*=\s*(\w+)', lb)
                if ideol_match:
                    ideologies.append(ideol_match.group(1))
            char_to_sub[char_id] = ideologies
            pos = cur

excluded_tags = ["TAK", "FRA", "KUS", "AUR", "TAI", "PAW"]

roles_to_add = {}

history_dir = 'history/countries'
for filename in os.listdir(history_dir):
    if not filename.endswith('.txt'): continue
    tag = filename[:3]
    if tag in excluded_tags: continue
    with open(os.path.join(history_dir, filename), 'r', encoding='utf-8') as f:
        content = f.read()
    recruited = re.findall(r'recruit_character\s*=\s*(\w+)', content)
    if not recruited: continue
    ideology_leaders = {p: [] for p in defaults.keys()}
    for char_id in recruited:
        if char_id in char_to_sub:
            for s in char_to_sub[char_id]:
                parent = sub_to_parent.get(s)
                if parent: ideology_leaders[parent].append(char_id)
    for group in groups:
        existing = [p for p in group if ideology_leaders[p]]
        missing = [p for p in group if not ideology_leaders[p]]
        if existing and missing:
            leader_char = None
            for char_id in recruited:
                if char_id in char_to_sub:
                    if any(sub_to_parent.get(s) in existing for s in char_to_sub[char_id]):
                        leader_char = char_id
                        break
            if leader_char:
                if leader_char not in roles_to_add: roles_to_add[leader_char] = set()
                for m in missing:
                    roles_to_add[leader_char].add(defaults[m])
                    ideology_leaders[m].append(leader_char)

for char_id, subs in roles_to_add.items():
    filename = char_to_file[char_id]
    filepath = os.path.join(char_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    char_pattern = rf'({char_id}\s*=\s*\{{)'
    match = re.search(char_pattern, content)
    if not match: continue
    pos = match.end()
    brace_count = 1
    while brace_count > 0 and pos < len(content):
        if content[pos] == '{': brace_count += 1
        elif content[pos] == '}': brace_count -= 1
        pos += 1
    char_block_content = content[match.start():pos]
    existing_subs = char_to_sub[char_id]
    new_roles_content = ""
    for s in subs:
        if s not in existing_subs:
            new_roles_content += f"\t\tcountry_leader={{\n\t\t\texpire = \"1965.1.1\"\n\t\t\tideology = {s}\n\t\t}}\n"
    if new_roles_content:
        # Find last brace to insert before
        last_brace_idx = char_block_content.rfind('}')
        new_char_block = char_block_content[:last_brace_idx] + new_roles_content + char_block_content[last_brace_idx:]
        content = content[:match.start()] + new_char_block + content[pos:]
        with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(content)
        print(f'Added roles to {char_id} in {filename}')
