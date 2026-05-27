import re
import os
import shutil

# Paths
mod_dir = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
vanilla_interface_dir = os.path.join(mod_dir, "modding_documentation", "vanilla_folders", "vanilla_interface")
vanilla_goals_dir = os.path.join(mod_dir, "modding_documentation", "vanilla_folders", "vanilla_goals")
dest_goals_dir = os.path.join(mod_dir, "gfx", "interface", "goals", "TAK")
focus_tree_path = os.path.join(mod_dir, "common", "national_focus", "TAK.txt")
gfx_file_path = os.path.join(mod_dir, "interface", "lok_national_focus_icons.gfx")

print("Initializing focus icon copy and mapping tool...")

# Ensure destination directory exists
os.makedirs(dest_goals_dir, exist_ok=True)

# 1. Parse all .gfx files in vanilla_interface to map GFX names to texture filenames
gfx_map = {}
for file_name in os.listdir(vanilla_interface_dir):
    if file_name.endswith(".gfx"):
        path = os.path.join(vanilla_interface_dir, file_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                gfx_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="cp1252") as f:
                    gfx_content = f.read()
            except Exception as e:
                print(f"Skipping {file_name} due to read error: {e}")
                continue

        # Match SpriteType or spriteType blocks
        blocks = re.findall(r'[sS]priteType\s*=\s*\{([^}]+?)\}', gfx_content, re.DOTALL)
        for b in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', b)
            texture_match = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
            if name_match and texture_match:
                name = name_match.group(1).strip()
                texture_path = texture_match.group(1).strip()
                filename = os.path.basename(texture_path)
                # Map GFX key (e.g. GFX_focus_generic_farmland) to the actual .dds filename
                gfx_map[name] = filename

print(f"Successfully mapped {len(gfx_map)} GFX keys from vanilla GFX files.")

# 2. Parse common/national_focus/TAK.txt to find all focuses and their icons
with open(focus_tree_path, "r", encoding="utf-8") as f:
    focus_content = f.read()

# Using regex to find all focus blocks
# Standard focus blocks look like:
# focus = {
#     id = TAK_some_id
#     icon = some_icon
#     ...
# }
focus_matches = re.finditer(r'focus\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', focus_content)

updated_focus_content = focus_content
gfx_entries_to_add = []

focuses_to_process = []
for match in focus_matches:
    block = match.group(1)
    id_match = re.search(r'id\s*=\s*([a-zA-Z0-9_-]+)', block)
    icon_match = re.search(r'icon\s*=\s*([a-zA-Z0-9_-]+)', block)
    if id_match and icon_match:
        fid = id_match.group(1)
        icon = icon_match.group(1)
        focuses_to_process.append((fid, icon))

print(f"Parsed {len(focuses_to_process)} focus definitions from TAK.txt.")

# We will process each focus that reuses a vanilla icon
copied_count = 0
for fid, icon in focuses_to_process:
    if icon.startswith("GFX_"):
        # This uses a vanilla icon! Let's check if we have a mapped filename
        if icon in gfx_map:
            filename = gfx_map[icon]
        else:
            # Fallback guessing: try to guess filename
            # GFX_focus_generic_farmland -> focus_generic_farmland.dds
            # GFX_goal_generic_air_fighter -> goal_generic_air_fighter.dds
            guess = icon.replace("GFX_", "") + ".dds"
            filename = guess

        src_path = os.path.join(vanilla_goals_dir, filename)
        dest_filename = f"TAK_{fid}.dds"
        dest_path = os.path.join(dest_goals_dir, dest_filename)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dest_path)
            copied_count += 1
            # print(f"Copied {filename} -> {dest_filename}")

            # Define new GFX key: TAK_[fid]
            new_gfx_key = f"TAK_{fid}"
            
            # Replace in focus tree content
            # We replace "icon = [icon]" with "icon = TAK_[fid]" specifically inside the focus block
            # To be absolutely precise and safe, we can use regex to replace within the matched block
            pattern = r'(id\s*=\s*' + fid + r'\s+icon\s*=\s*)' + icon
            updated_focus_content = re.sub(pattern, r'\1' + new_gfx_key, updated_focus_content)

            # Generate GFX spriteType block
            gfx_block = f"""
	SpriteType = {{ 
		name = "{new_gfx_key}"
		texturefile = "gfx/interface/goals/TAK/{dest_filename}"
	}}
	SpriteType = {{ 
		name = "{new_gfx_key}_shine"
		texturefile = "gfx/interface/goals/TAK/{dest_filename}"
		effectFile = "gfx/FX/buttonstate.lua"
		animation = {{
			animationmaskfile = "gfx/interface/goals/TAK/{dest_filename}"
			animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
			animationrotation = -90.0
			animationlooping = no
			animationtime = 0.75
			animationdelay = 0
			animationblendmode = "add"
			animationtype = "scrolling"
			animationrotationoffset = {{ x = 0.0 y = 0.0 }}
			animationtexturescale = {{ x = 1.0 y = 1.0 }} 
		}}
		animation = {{
			animationmaskfile = "gfx/interface/goals/TAK/{dest_filename}"
			animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
			animationrotation = 90.0
			animationlooping = no
			animationtime = 0.75
			animationdelay = 0
			animationblendmode = "add"
			animationtype = "scrolling"
			animationrotationoffset = {{ x = 0.0 y = 0.0 }}
			animationtexturescale = {{ x = 1.0 y = 1.0 }} 
		}}
		legacy_lazy_load = no
	}}"""
            gfx_entries_to_add.append(gfx_block)
        else:
            print(f"WARNING: Source icon file {filename} not found for focus {fid} (icon GFX: {icon})")

print(f"Copied and processed {copied_count} vanilla focus icons.")

# 3. Add custom icons for the two new surveillance focuses
new_surveillance_icons = [
    ("TAK_tighten_surveillance", "focus_generic_national_security.dds"),
    ("TAK_le_roi_voit_tout", "goal_generic_radar.dds")
]

for fid, src_filename in new_surveillance_icons:
    src_path = os.path.join(vanilla_goals_dir, src_filename)
    dest_filename = f"{fid}.dds"
    dest_path = os.path.join(dest_goals_dir, dest_filename)

    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Successfully copied new focus icon: {src_filename} -> {dest_filename}")

        new_gfx_key = fid
        gfx_block = f"""
	SpriteType = {{ 
		name = "{new_gfx_key}"
		texturefile = "gfx/interface/goals/TAK/{dest_filename}"
	}}
	SpriteType = {{ 
		name = "{new_gfx_key}_shine"
		texturefile = "gfx/interface/goals/TAK/{dest_filename}"
		effectFile = "gfx/FX/buttonstate.lua"
		animation = {{
			animationmaskfile = "gfx/interface/goals/TAK/{dest_filename}"
			animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
			animationrotation = -90.0
			animationlooping = no
			animationtime = 0.75
			animationdelay = 0
			animationblendmode = "add"
			animationtype = "scrolling"
			animationrotationoffset = {{ x = 0.0 y = 0.0 }}
			animationtexturescale = {{ x = 1.0 y = 1.0 }} 
		}}
		animation = {{
			animationmaskfile = "gfx/interface/goals/TAK/{dest_filename}"
			animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
			animationrotation = 90.0
			animationlooping = no
			animationtime = 0.75
			animationdelay = 0
			animationblendmode = "add"
			animationtype = "scrolling"
			animationrotationoffset = {{ x = 0.0 y = 0.0 }}
			animationtexturescale = {{ x = 1.0 y = 1.0 }} 
		}}
		legacy_lazy_load = no
	}}"""
        gfx_entries_to_add.append(gfx_block)
    else:
        print(f"ERROR: Source icon file {src_filename} not found for new focus {fid}!")

# 4. Save updated focus tree file
with open(focus_tree_path, "w", encoding="utf-8") as f:
    f.write(updated_focus_content)
print("Updated TAK.txt focus tree icons successfully.")

# 5. Append GFX definitions to interface/lok_national_focus_icons.gfx
# We read the file, find the last closing brace '}', and insert our new entries before it.
with open(gfx_file_path, "r", encoding="utf-8") as f:
    gfx_file_content = f.read()

# Find the last closing brace '}'
# We can search backwards
last_brace_index = gfx_file_content.rfind("}")
if last_brace_index != -1:
    new_gfx_entries_str = "\n".join(gfx_entries_to_add) + "\n"
    updated_gfx_content = gfx_file_content[:last_brace_index] + new_gfx_entries_str + gfx_file_content[last_brace_index:]
    with open(gfx_file_path, "w", encoding="utf-8") as f:
        f.write(updated_gfx_content)
    print(f"Added {len(gfx_entries_to_add)} new GFX sprite definitions to lok_national_focus_icons.gfx.")
else:
    print("ERROR: Could not find closing brace in lok_national_focus_icons.gfx!")
