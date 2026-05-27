import os

mod_dir = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail"
dest_goals_dir = os.path.join(mod_dir, "gfx", "interface", "goals", "TAK")
focus_tree_path = os.path.join(mod_dir, "common", "national_focus", "TAK.txt")
gfx_file_path = os.path.join(mod_dir, "interface", "lok_national_focus_icons.gfx")

print("Initializing prefix cleanup (TAK_TAK_ -> TAK_)...")

# 1. Rename files in gfx/interface/goals/TAK/
renamed_files = 0
for file_name in os.listdir(dest_goals_dir):
    if file_name.startswith("TAK_TAK_"):
        new_name = file_name.replace("TAK_TAK_", "TAK_")
        old_path = os.path.join(dest_goals_dir, file_name)
        new_path = os.path.join(dest_goals_dir, new_name)
        
        # If the destination already exists, delete it first
        if os.path.exists(new_path):
            os.remove(new_path)
            
        os.rename(old_path, new_path)
        renamed_files += 1

print(f"Renamed {renamed_files} focus icon files.")

# 2. Replace references in common/national_focus/TAK.txt
with open(focus_tree_path, "r", encoding="utf-8") as f:
    focus_content = f.read()

# Replace all occurrences of TAK_TAK_ with TAK_
updated_focus_content = focus_content.replace("TAK_TAK_", "TAK_")

with open(focus_tree_path, "w", encoding="utf-8") as f:
    f.write(updated_focus_content)
print("Updated TAK.txt references.")

# 3. Replace references in interface/lok_national_focus_icons.gfx
with open(gfx_file_path, "r", encoding="utf-8") as f:
    gfx_content = f.read()

updated_gfx_content = gfx_content.replace("TAK_TAK_", "TAK_")

with open(gfx_file_path, "w", encoding="utf-8") as f:
    f.write(updated_gfx_content)
print("Updated lok_national_focus_icons.gfx GFX key references.")

print("Cleanup complete!")
