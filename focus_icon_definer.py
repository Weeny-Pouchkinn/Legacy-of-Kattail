import os

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
    interface_path = os.path.join("interface", "lok_national_focus_icons.gfx")
    loc_path = os.path.join("localisation", "english", f"{tag}_l_english.yml")

    processed_focuses = set()

    # Read the existing interface content
    with open(interface_path, 'r') as file:
        interface_content = file.read()

    for focus_id in focus_ids:
        if focus_id in processed_focuses:
            continue

        # Define the icon in interface
        if f"name = \"{focus_id}\"" not in interface_content:
            sprite_block = f"""
SpriteType = {{ 
    name = "{focus_id}"
    texturefile = "gfx/interface/goals/{tag}/{focus_id}.tga"
}}
SpriteType = {{ 
    name = "{focus_id}_shine"
    texturefile = "gfx/interface/goals/{tag}/{focus_id}.tga"
    effectFile = "gfx/FX/buttonstate.lua"
    animation = {{
        animationmaskfile = "gfx/interface/goals/{tag}/{focus_id}.tga"
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
        animationmaskfile = "gfx/interface/goals/{tag}/{focus_id}.tga"
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
}}
"""
            interface_content += sprite_block

        # Define the localization
        with open(loc_path, 'a') as file:
            file.write(f" {focus_id}:0 \"{focus_id}\"\n")
            file.write(f" {focus_id}_desc:0 \"Glorious Kayzoo!\"\n")

        processed_focuses.add(focus_id)

    # Write the updated interface content back to the file
    with open(interface_path, 'w') as file:
        file.write(interface_content)

if __name__ == "__main__":
    main()
