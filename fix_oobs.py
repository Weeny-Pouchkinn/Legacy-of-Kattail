import os, re
history_path = r'c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\history\countries'
for filename in os.listdir(history_path):
    if not filename.endswith('.txt'): continue
    filepath = os.path.join(history_path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tag = filename[:3]
    changed = False
    
    if 'set_air_oob = "' + tag + '_1936"' in content:
        content = content.replace('set_air_oob = "' + tag + '_1936"', 'set_air_oob = "' + tag + '_1936_air"')
        changed = True
    
    if 'set_naval_oob = "' + tag + '_1936"' in content:
        content = content.replace('set_naval_oob = "' + tag + '_1936"', 'set_naval_oob = "' + tag + '_1936_naval"')
        changed = True
        
    if tag in ['XEN', 'MUN', 'ZZZ', 'WWW', 'AAA']:
        # remove any oob = ...
        new_content = re.sub(r'(?:set_)?oob\s*=\s*"[^"]+"\n?', '', content)
        # Also remove set_air_oob and set_naval_oob if any, but since the user just said remove OOBs, I'll remove all of them
        new_content = re.sub(r'set_air_oob\s*=\s*"[^"]+"\n?', '', new_content)
        new_content = re.sub(r'set_naval_oob\s*=\s*"[^"]+"\n?', '', new_content)
        if new_content != content:
            content = new_content
            changed = True
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed {filename}')
