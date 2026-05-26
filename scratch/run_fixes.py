import os
import codecs
import re

workspace = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"

def edit_file_content(path, edit_fn):
    with open(path, 'rb') as f:
        raw = f.read(3)
    encoding = 'utf-8-sig' if raw == codecs.BOM_UTF8 else 'utf-8'

    with codecs.open(path, 'r', encoding=encoding) as f:
        content = f.read()
    
    lines = content.splitlines(keepends=True)
    header = lines[0] if lines else ""
    
    has_rn = '\r\n' in content
    content_norm = content.replace('\r\n', '\n')
    
    new_content_norm = edit_fn(content_norm)
    
    new_lines = new_content_norm.splitlines(keepends=True)
    if new_lines and lines:
        orig_first_line = lines[0].replace('\r\n', '\n').replace('\r', '\n')
        new_first_line = new_lines[0].replace('\r\n', '\n').replace('\r', '\n')
        if orig_first_line != new_first_line:
            new_lines[0] = lines[0].replace('\r\n', '\n')
            new_content_norm = "".join(new_lines)
            
    if has_rn:
        new_content = new_content_norm.replace('\n', '\r\n')
    else:
        new_content = new_content_norm
        
    with codecs.open(path, 'w', encoding=encoding) as f:
        f.write(new_content)
    print(f"Successfully edited {os.path.basename(path)}")

# 1. Edit lok_culture_l_english.yml (using correct 1-space target)
def edit_lok_culture(content):
    # Ensure any previous un-localized block is cleared first
    if 'culture_96_name' in content:
        print("Culture 96 already localized")
        return content

    target = ' remove_culture_group_1_tt:0'
    insertion = (
        ' #AI-Generated Placeholder, change later!\n'
        ' culture_95_name:0 "§3Far Katzen§!" #AI-Generated Placeholder, change later!\n'
        ' culture_95_desc:0 "" #AI-Generated Placeholder, change later!\n'
        ' culture_95_full:0 "$culture_95_name$ is not part of any $culture_group$.$culture_95_desc$" #AI-Generated Placeholder, change later!\n\n'
        ' #AI-Generated Placeholder, change later!\n'
        ' culture_group_15_name:0 "§YGalletian Group§!" #AI-Generated Placeholder, change later!\n'
        ' culture_group_15_desc:0 "\\n§LCultures of Galletian descent or influence.§!" #AI-Generated Placeholder, change later!\n'
        ' remove_culture_group_15_tt:0 "All cultures of the §YGalletian Group§! culture group are §Oremoved§! from the state\'s cultural makeup." #AI-Generated Placeholder, change later!\n\n'
        ' #AI-Generated Placeholder, change later!\n'
        ' culture_96_name:0 "§OBarzintonite§!" #AI-Generated Placeholder, change later!\n'
        ' culture_96_desc:0 "" #AI-Generated Placeholder, change later!\n'
        ' culture_96_full:0 "$culture_96_name$ is part of the $culture_group_15_name$ $culture_group$.$culture_96_desc$" #AI-Generated Placeholder, change later!\n\n'
        ' #AI-Generated Placeholder, change later!\n'
        ' culture_97_name:0 "§YExtremadoughrian§!" #AI-Generated Placeholder, change later!\n'
        ' culture_97_desc:0 "" #AI-Generated Placeholder, change later!\n'
        ' culture_97_full:0 "$culture_97_name$ is part of the $culture_group_15_name$ $culture_group$.$culture_97_desc$" #AI-Generated Placeholder, change later!\n\n'
    )
    return content.replace(target, insertion + target)

edit_file_content(
    f"{workspace}\\localisation\\english\\lok_culture_l_english.yml",
    edit_lok_culture
)

# 2. SMI and FKS namelists in katzen_names.txt
def edit_katzen_names(content):
    if 'SMI = {' in content:
        print("SMI/FKS already in katzen_names.txt")
        return content

    # Find the KTZ block
    ktz_start = content.find("KTZ = {")
    if ktz_start == -1:
        raise Exception("Could not find KTZ block in katzen_names.txt")
    brackets = 0
    ktz_end = -1
    for idx in range(ktz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                ktz_end = idx
                break
    if ktz_end == -1:
        raise Exception("Could not find KTZ closing bracket in katzen_names.txt")

    ktz_block = content[ktz_start:ktz_end+1]
    
    smi_block = "\n\n" + ktz_block.replace("KTZ = {", "SMI = {")
    fks_block = "\n\n" + ktz_block.replace("KTZ = {", "FKS = {")
    
    return content.strip() + smi_block + fks_block

edit_file_content(
    f"{workspace}\\common\\names\\katzen_names.txt",
    edit_katzen_names
)

# 3. Copy GAL lists for BAZ in misc_names.txt
def edit_misc_names(content):
    # Find GAL block
    gal_start = content.find("GAL = {")
    if gal_start == -1:
        raise Exception("Could not find GAL in misc_names.txt")
    brackets = 0
    gal_end = -1
    for idx in range(gal_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                gal_end = idx
                break
    if gal_end == -1:
        raise Exception("Could not find GAL closing bracket in misc_names.txt")

    gal_block = content[gal_start:gal_end+1]
    baz_block = gal_block.replace("GAL = {", "BAZ = {")

    # Replace BAZ block
    baz_start = content.find("BAZ = {")
    if baz_start == -1:
        raise Exception("Could not find BAZ in misc_names.txt")
    brackets = 0
    baz_end = -1
    for idx in range(baz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                baz_end = idx
                break
    if baz_end == -1:
        raise Exception("Could not find BAZ closing bracket in misc_names.txt")

    return content[:baz_start] + baz_block + content[baz_end+1:]

edit_file_content(
    f"{workspace}\\common\\names\\misc_names.txt",
    edit_misc_names
)

# 4. Make BAZ Galletian species (ID 25)
# 4a. Update LOK_on_actions.txt
def edit_on_actions_species(content):
    # BAZ startup country species idea: change from 3 (Roqualian) to 25 (Galletian)
    content = content.replace(
        "BAZ = { remove_ideas = var_species_0 add_ideas = var_species_3 }",
        "BAZ = { remove_ideas = var_species_0 add_ideas = var_species_25 }"
    )
    # BAZ state species: change from 3 (Roqualian) to 25 (Galletian)
    content = content.replace(
        "BAZ = { every_owned_state = { set_variable = { species = 3 } } }",
        "BAZ = { every_owned_state = { set_variable = { species = 25 } } }"
    )

    # 4b. Add Katzen minorities to 1203 and 1183
    if 'Katzen minorities' not in content:
        target_minorities = "# Zuspri minorities"
        idx = content.find(target_minorities)
        if idx == -1:
            raise Exception("Could not find Zuspri minorities in on_actions")
        
        katzen_minorities_code = (
            "# Katzen minorities\n"
            "\t\t\t1203 = { set_variable = { minority = 1 } }\n"
            "\t\t\t1183 = { set_variable = { minority = 1 } }\n\n\t\t\t"
        )
        content = content[:idx] + katzen_minorities_code + content[idx:]

    return content

edit_file_content(
    f"{workspace}\\common\\on_actions\\LOK_on_actions.txt",
    edit_on_actions_species
)

# 5. Set BAZ fallback generic portraits
# 5a. Add BAZ block to no_portraits.txt
def edit_no_portraits(content):
    if 'BAZ = {' in content:
        print("BAZ already in no_portraits.txt")
        return content

    gal_start = content.find("GAL = {")
    if gal_start == -1:
        raise Exception("Could not find GAL in no_portraits.txt")
    brackets = 0
    gal_end = -1
    for idx in range(gal_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                gal_end = idx
                break
    if gal_end == -1:
        raise Exception("Could not find GAL closing bracket in no_portraits.txt")

    gal_block = content[gal_start:gal_end+1]
    baz_block = "\n\n" + gal_block.replace("GAL = {", "BAZ = {")
    
    return content.strip() + baz_block

edit_file_content(
    f"{workspace}\\portraits\\no_portraits.txt",
    edit_no_portraits
)

# 5b. Remove BAZ from misc_portraits.txt
def edit_misc_portraits(content):
    baz_start = content.find("BAZ = {")
    if baz_start == -1:
        print("BAZ block already removed from misc_portraits.txt")
        return content
    brackets = 0
    baz_end = -1
    for idx in range(baz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                baz_end = idx
                break
    if baz_end == -1:
        raise Exception("Could not find BAZ closing bracket in misc_portraits.txt")

    return content[:baz_start] + content[baz_end+1:]

edit_file_content(
    f"{workspace}\\portraits\\misc_portraits.txt",
    edit_misc_portraits
)

# 5c. Set Albert Gouraud's portrait to democratic fallback
def edit_baz_character(content):
    return content.replace(
        'large = "GFX_portrait_roqualian_generic_civilian_1_male"',
        'large = "GFX_no_portrait_democratic"'
    )

edit_file_content(
    f"{workspace}\\common\\characters\\BAZ - characters.txt",
    edit_baz_character
)

# 5d. Replace BAZ generic advisors with GAL generic advisors in generic_advisors.txt
def edit_generic_advisors(content):
    gal_start = content.find("GAL = {")
    if gal_start == -1:
        raise Exception("Could not find GAL in generic_advisors.txt")
    brackets = 0
    gal_end = -1
    for idx in range(gal_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                gal_end = idx
                break
    if gal_end == -1:
        raise Exception("Could not find GAL closing bracket in generic_advisors.txt")

    gal_block = content[gal_start:gal_end+1]
    baz_block = gal_block.replace("GAL = {", "BAZ = {").replace("GAL_gen_", "BAZ_gen_")

    baz_start = content.find("BAZ = {")
    if baz_start == -1:
        raise Exception("Could not find BAZ in generic_advisors.txt")
    brackets = 0
    baz_end = -1
    for idx in range(baz_start, len(content)):
        char = content[idx]
        if char == '{':
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0:
                baz_end = idx
                break
    if baz_end == -1:
        raise Exception("Could not find BAZ closing bracket in generic_advisors.txt")

    return content[:baz_start] + baz_block + content[baz_end+1:]

edit_file_content(
    f"{workspace}\\history\\general\\generic_advisors.txt",
    edit_generic_advisors
)

# 6. Relocate Capitals
# SMI Capital -> 1187 (San-Sebakestian)
edit_file_content(
    f"{workspace}\\history\\countries\\SMI - Smileycatia.txt",
    lambda content: content.replace("capital = 1186", "capital = 1187")
)

# FKS Capital -> 1192 (Crumbrid)
edit_file_content(
    f"{workspace}\\history\\countries\\FKS - Far Katzen State.txt",
    lambda content: content.replace("capital = 300", "capital = 1192")
)

print("ALL FIXES AND ADJUSTMENTS SUCCESSFUL!")
