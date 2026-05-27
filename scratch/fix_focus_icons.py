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

print("Initializing robust focus icon copy and mapping tool...")

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

        # Match SpriteType blocks
        blocks = re.findall(r'[sS]priteType\s*=\s*\{([^}]+?)\}', gfx_content, re.DOTALL)
        for b in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', b)
            texture_match = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
            if name_match and texture_match:
                name = name_match.group(1).strip()
                texture_path = texture_match.group(1).strip()
                filename = os.path.basename(texture_path)
                gfx_map[name] = filename

print(f"Successfully mapped {len(gfx_map)} GFX keys from vanilla GFX files.")

# 2. Parse common/national_focus/TAK.txt
with open(focus_tree_path, "r", encoding="utf-8") as f:
    focus_content = f.read()

# We split the focus tree by 'focus = {' to find all focus blocks
chunks = focus_content.split("focus = {")
print(f"Split focus tree into {len(chunks)} chunks.")

# We skip the first chunk (header of the file)
updated_chunks = [chunks[0]]
copied_count = 0
gfx_entries_to_add = []

for chunk in chunks[1:]:
    # In each chunk, find the first 'id' and 'icon'
    id_match = re.search(r'\bid\s*=\s*([a-zA-Z0-9_-]+)', chunk)
    icon_match = re.search(r'\bicon\s*=\s*([a-zA-Z0-9_-]+)', chunk)
    
    if id_match and icon_match:
        fid = id_match.group(1)
        icon = icon_match.group(1)
        
        if icon.startswith("GFX_"):
            # This is a vanilla icon! Let's check if we have a mapped filename
            if icon in gfx_map:
                filename = gfx_map[icon]
            else:
                filename = icon.replace("GFX_", "") + ".dds"
                
            src_path = os.path.join(vanilla_goals_dir, filename)
            dest_filename = f"TAK_{fid}.dds"
            dest_path = os.path.join(dest_goals_dir, dest_filename)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                copied_count += 1
                
                new_gfx_key = f"TAK_{fid}"
                # Replace the icon in this chunk
                # We replace specifically the first occurrence of the GFX key in the icon line
                chunk = re.sub(r'(\bicon\s*=\s*)' + icon, r'\1' + new_gfx_key, chunk, count=1)
                
                # Add GFX definition
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
                
    updated_chunks.append(chunk)

# Reassemble focus content
updated_focus_content = "focus = {".join(updated_chunks)

# Copy the two new surveillance focuses' icons as well
new_surveillance_icons = [
    ("TAK_tighten_surveillance", "focus_generic_national_security.dds"),
    ("TAK_le_roi_voit_tout", "goal_generic_radar.dds")
]

for fid, src_filename in new_surveillance_icons:
    src_path = os.path.join(vanilla_goals_dir, src_filename)
    dest_filename = f"{fid}.dds"
    dest_path = os.path.join(dest_goals_dir, dest_filename)
    
    # Check if we already added it in the previous quick run
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copied new surveillance icon: {src_filename} -> {dest_filename}")
        
        # We need to check if the GFX entry was already added or not, but it's safer to just let the script append it
        # as we can clean up any duplicates or we can just append it uniquely.
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
        # Only append if not already in the file
        with open(gfx_file_path, "r", encoding="utf-8") as f:
            gfx_file_content = f.read()
        if f'name = "{new_gfx_key}"' not in gfx_file_content:
            gfx_entries_to_add.append(gfx_block)
            print(f"Queueing GFX block for {fid}")
    else:
        print(f"ERROR: Source icon file {src_filename} not found for new focus {fid}!")

# Write updated focus tree
with open(focus_tree_path, "w", encoding="utf-8") as f:
    f.write(updated_focus_content)
print(f"Successfully updated TAK.txt. Copied {copied_count} focus icons.")

# Append to lok_national_focus_icons.gfx
with open(gfx_file_path, "r", encoding="utf-8") as f:
    gfx_file_content = f.read()

last_brace_index = gfx_file_content.rfind("}")
if last_brace_index != -1 and len(gfx_entries_to_add) > 0:
    new_gfx_entries_str = "\n".join(gfx_entries_to_add) + "\n"
    updated_gfx_content = gfx_file_content[:last_brace_index] + new_gfx_entries_str + gfx_file_content[last_brace_index:]
    with open(gfx_file_path, "w", encoding="utf-8") as f:
        f.write(updated_gfx_content)
    print(f"Added {len(gfx_entries_to_add)} new GFX sprite definitions to lok_national_focus_icons.gfx.")
else:
    print("Done! No new GFX entries needed or brace not found.")
