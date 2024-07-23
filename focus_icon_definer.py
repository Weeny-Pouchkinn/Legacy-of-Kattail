import os
import shutil

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
    interface_path = os.path.join("interface", "lok_national_focus_icons")
    loc_path = os.path.join("localisation", "english", f"{tag}_l_english.yml")

    for focus_id in focus_ids:
        icon_path = os.path.join(goals_path, f"{focus_id}.tga")
        if not os.path.exists(icon_path):
            shutil.copy(template_path, icon_path)

            # Define the icon in interface
            with open(interface_path, 'r') as file:
                interface_content = file.read()

            example_block = interface_content.split("#EXAMPLE")[1]
            new_block = example_block.replace("[FOCUS_ID]", focus_id).replace("[TAG]", tag)
            interface_content = interface_content.replace("#EXAMPLE", f"#EXAMPLE{new_block}")

            with open(interface_path, 'w') as file:
                file.write(interface_content)

            # Define the localization
            with open(loc_path, 'a') as file:
                file.write(f" {focus_id}:0 \"{focus_id}\"\n")
                file.write(f" {focus_id}_desc:0 \"Glorious Kayzoo!\"\n")

if __name__ == "__main__":
    main()
