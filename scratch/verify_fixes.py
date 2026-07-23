import os, re

STATES_DIR = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\history\states"

PROVINCE_ERRORS = {
    37: [10655], 87: [3689], 96: [7040],
    176: [2703, 8389], 202: [15998], 207: [16303], 219: [16338],
    260: [16788], 324: [10299], 364: [6245],
    605: [15292, 11115, 7713, 15119, 15049, 15007],
    611: [16179, 9146, 447, 287, 16300, 16228, 8852, 1376, 1759, 9155, 1906, 11281],
    725: [17337], 821: [6949], 1050: [2590, 15531],
}

still_has_errors = {}
for fname in os.listdir(STATES_DIR):
    if not fname.endswith('.txt'):
        continue
    m = re.match(r'^(\d+)-', fname)
    if not m:
        continue
    sid = int(m.group(1))
    if sid not in PROVINCE_ERRORS:
        continue
    with open(os.path.join(STATES_DIR, fname), 'rb') as f:
        raw = f.read()
    content = raw.decode('utf-8', errors='replace')
    remaining = []
    for prov_id in PROVINCE_ERRORS[sid]:
        if re.search(str(prov_id) + r'\s*=\s*\{', content):
            remaining.append(prov_id)
    if remaining:
        still_has_errors[sid] = remaining

if still_has_errors:
    print('STILL HAS PROVINCE BUILD ERRORS:', still_has_errors)
else:
    print('All province building errors cleared!')

LOC_FILE = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\localisation\english\anka_new_states_l_english.yml"
with open(LOC_FILE, 'r', encoding='utf-8-sig') as f:
    loc_content = f.read()

entries = re.findall(r'STATE_(\d+):0', loc_content)
print('Localization entries:', len(entries), '(expected 156)')

none_count = loc_content.count(' None ')
print('None-containing names count:', none_count)

BUILD_FILE = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\map\buildings.txt"
with open(BUILD_FILE, 'rb') as f:
    bcontent = f.read().decode('utf-8', errors='replace')
if re.search(r'floating_harbor[^;]*;[^;]*;[^;]*;[^;]*;[^;]*;21029', bcontent):
    print('Province 21029 floating_harbor STILL PRESENT - ERROR')
else:
    print('Province 21029 floating_harbor correctly removed!')

print('All checks done.')
