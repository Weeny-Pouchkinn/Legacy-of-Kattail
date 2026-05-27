import os
import re
from PIL import Image

mod_dir = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
dest_goals_dir = os.path.join(mod_dir, "gfx", "interface", "goals", "TAK")
gfx_file_path = os.path.join(mod_dir, "interface", "lok_national_focus_icons.gfx")

print("Initializing image format conversion (DDS -> TGA)...")

converted_count = 0
for file_name in os.listdir(dest_goals_dir):
    if file_name.endswith(".dds"):
        old_path = os.path.join(dest_goals_dir, file_name)
        new_name = file_name.replace(".dds", ".tga")
        new_path = os.path.join(dest_goals_dir, new_name)
        
        try:
            # Open DDS and save as TGA
            img = Image.open(old_path)
            img.save(new_path)
            # Delete original DDS
            os.remove(old_path)
            converted_count += 1
        except Exception as e:
            print(f"Error converting {file_name}: {e}")

print(f"Successfully converted {converted_count} files from DDS to TGA.")

# 2. Update references in interface/lok_national_focus_icons.gfx
# We only want to replace references inside our added definitions. But actually, all the TAK goals we added
# are defined with .dds. So replacing ".dds" with ".tga" in lok_national_focus_icons.gfx is safe, but wait!
# Are there any other .dds files referenced in lok_national_focus_icons.gfx?
# Let's check: "animationtexturefile = "gfx/interface/goals/shine_overlay.dds""
# Ah!!! "shine_overlay.dds" must stay as a DDS file because it's a shared vanilla asset!
# So we must NOT replace ".dds" globally if it refers to "shine_overlay.dds"!
# Instead, we should specifically replace the texturefiles that contain "goals/TAK/" and end in ".dds"!
# E.g. texturefile = "gfx/interface/goals/TAK/TAK_agricultural_programs.dds" -> .tga
# and animationmaskfile = "gfx/interface/goals/TAK/TAK_agricultural_programs.dds" -> .tga
# This is a very important detail! Let's be extremely precise:
with open(gfx_file_path, "r", encoding="utf-8") as f:
    gfx_content = f.read()

# Using regex to replace specifically our TAK files:
# goals/TAK/[something].dds -> goals/TAK/[something].tga
updated_gfx_content = re.sub(r'(goals/TAK/[a-zA-Z0-9_-]+)\.dds', r'\1.tga', gfx_content)

with open(gfx_file_path, "w", encoding="utf-8") as f:
    f.write(updated_gfx_content)

print("Updated lok_national_focus_icons.gfx GFX file references safely.")
