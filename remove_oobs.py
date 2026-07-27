import os, re

proj_dir = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail'
countries_dir = os.path.join(proj_dir, 'history', 'countries')
units_dir = os.path.join(proj_dir, 'history', 'units')

tags_to_remove = ['MUN', 'XEN', 'MRI', 'AAA', 'ZZZ', 'WWW', 'MON']

# 1. Clean history/countries
for filename in os.listdir(countries_dir):
    if not filename.endswith('.txt'): continue
    tag = filename[:3]
    if tag in tags_to_remove:
        filepath = os.path.join(countries_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(r'(?:set_)?oob\s*=\s*"[^"]+"\n?', '', content)
        new_content = re.sub(r'set_air_oob\s*=\s*"[^"]+"\n?', '', new_content)
        new_content = re.sub(r'set_naval_oob\s*=\s*"[^"]+"\n?', '', new_content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Cleaned country file: {filename}')

# 2. Delete units files
for tag in tags_to_remove:
    for suffix in ['_1936.txt', '_1936_air.txt', '_1936_naval.txt']:
        filepath = os.path.join(units_dir, f'{tag}{suffix}')
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f'Deleted unit file: {tag}{suffix}')

print('Removal complete.')
