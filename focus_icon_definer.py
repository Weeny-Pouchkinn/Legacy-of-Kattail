import os
import re
import shutil


def insert_focus_section(content, block):
    line_ending = "\r\n" if "\r\n" in content else "\n"
    marker = re.search(r"(?mi)^[ \t]*# FOCUS ICONS[ \t]*\r?$", content)
    normalized_block = block.replace("\r\n", "\n").replace("\r", "\n").replace("\n", line_ending)
    if marker:
        next_section = re.search(r"(?mi)^[ \t]*# [A-Z][A-Z ]*[ \t]*\r?$", content[marker.end():])
        position = marker.end() + next_section.start() if next_section else content.rfind("}")
        return content[:position] + line_ending + normalized_block + line_ending + content[position:]
    position = content.rfind("}")
    return content[:position] + line_ending + "\t# FOCUS ICONS" + line_ending + normalized_block + line_ending + content[position:]


def focus_icon_block(focus_id, tag):
    texture = f"gfx/interface/goals/{tag}/{focus_id}.tga"
    return f'''\tSpriteType = {{
\t\tname = "{focus_id}"
\t\ttexturefile = "{texture}"
\t}}
\tSpriteType = {{
\t\tname = "{focus_id}_shine"
\t\ttexturefile = "{texture}"
\t\teffectFile = "gfx/FX/buttonstate.lua"
\t\tanimation = {{
\t\t\tanimationmaskfile = "{texture}"
\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"
\t\t\tanimationrotation = -90.0
\t\t\tanimationlooping = no
\t\t\tanimationtime = 0.75
\t\t\tanimationdelay = 0
\t\t\tanimationblendmode = "add"
\t\t\tanimationtype = "scrolling"
\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}
\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }}
\t\t}}
\t\tanimation = {{
\t\t\tanimationmaskfile = "{texture}"
\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"
\t\t\tanimationrotation = 90.0
\t\t\tanimationlooping = no
\t\t\tanimationtime = 0.75
\t\t\tanimationdelay = 0
\t\t\tanimationblendmode = "add"
\t\t\tanimationtype = "scrolling"
\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}
\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }}
\t\t}}
\t\tlegacy_lazy_load = no
\t}}
'''

def main():
    focus_tree = input("Enter the focus tree name: ")
    tag = input("Enter the tag: ")

    # Navigate to common/national_focus
    national_focus_path = os.path.join("common", "national_focus")
    focus_tree_file = None

    # Find the focus tree file
    for file_name in os.listdir(national_focus_path):
        file_path = os.path.join(national_focus_path, file_name)
        with open(file_path, 'r') as file:
            content = file.read()
            if f"id = {focus_tree}" in content:
                focus_tree_file = file_path
                break

    if not focus_tree_file:
        print(f"Focus tree {focus_tree} not found.")
        return

    # Read focus blocks
    with open(focus_tree_file, 'r') as file:
        content = file.read()

    focus_blocks = content.split("focus = {")[1:]
    focus_ids = [block.split("id = ")[1].split()[0] for block in focus_blocks]

    # Set up icons and localization
    goals_path = os.path.join("gfx", "interface", "goals", tag)
    template_path = os.path.join("gfx", "interface", "goals", "TEMPLATE.tga")
    interface_path = os.path.join("interface", f"lok_country_{tag}.gfx")
    loc_path = os.path.join("localisation", "english", f"{tag}_l_english.yml")

    processed_focuses = set()

    # Read the existing interface content
    with open(interface_path, 'r') as file:
        interface_content = file.read()

    # Read the existing localization content
    with open(loc_path, 'r') as file:
        loc_content = file.read()

    for focus_id in focus_ids:
        if focus_id in processed_focuses:
            continue

        icon_path = os.path.join(goals_path, f"{focus_id}.tga")
        if not os.path.exists(icon_path):
            shutil.copy(template_path, icon_path)

        # Define the icon in interface
        if f"name = \"{focus_id}\"" not in interface_content:
            interface_content = insert_focus_section(interface_content, focus_icon_block(focus_id, tag))

        # Define the localization
        if f" {focus_id}:0 \"{focus_id}\"" not in loc_content:
            with open(loc_path, 'a') as file:
                file.write(f" {focus_id}:0 \"{focus_id}\"\n")
                file.write(f" {focus_id}_desc:0 \"Glorious Kayzoo!\"\n\n")

        processed_focuses.add(focus_id)

    # Write the updated interface content back to the file
    with open(interface_path, 'w') as file:
        file.write(interface_content)

if __name__ == "__main__":
    main()
