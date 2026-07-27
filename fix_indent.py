import os, re

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
states_dir = os.path.join(proj_dir, 'history', 'states')

for filename in os.listdir(states_dir):
    if not filename.endswith('.txt'): continue
    filepath = os.path.join(states_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to match the poorly indented block
    pattern = r'\n\t\t([0-9]+)\s*=\s*\{\n\t\t\tsupply_node\s*=\s*1\n\t\t\}'
    replacement = r'\n\t\t\t\1 = {\n\t\t\t\tsupply_node = 1\n\t\t\t}'
    
    new_content, count = re.subn(pattern, replacement, content)
    
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed indent in {filename}")
