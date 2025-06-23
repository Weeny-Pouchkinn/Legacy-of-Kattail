import tkinter as tk
from tkinter import filedialog, StringVar, IntVar
from PIL import Image
import os
import shutil

def ensure_file_exists(filepath, initial_content=''):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(initial_content)

def save_input():
    country_tag = tag_entry.get()
    code_name = code_name_entry.get()
    proper_name = proper_name_entry.get()
    
    # Prepare character data
    data = f"\t{country_tag}_{code_name} = {{\n"
    data += f"\t\tname = {country_tag}_{code_name}\n"
    if gender_var.get() == 'Female':
        data += "\t\tgender = female\n"
    data += f"\t\tportraits={{\n\t\t\tarmy={{\n\t\t\t\tlarge=\"GFX_portrait_{country_tag}_{code_name}\"\n\t\t\t\tsmall=\"GFX_portrait_{country_tag}_{code_name}_Small\"\n\t\t\t}}\n\t\t}}\n"

    if country_leader_var.get():
        data += "\t\tcountry_leader={\n"
        data += f"\t\t\texpire = \"1965.1.1\"\n\t\t\tideology = {country_leader_ideology_entry.get()}\n\t\t}}\n"

    if minister_var.get():
        data += "\t\tadvisor = {\n"
        data += f"\t\t\tslot = {minister_slot_var.get()}\n"
        data += f"\t\t\tidea_token = {country_tag}_{code_name}\n"
        if minister_category_var.get() != 'political_advisor' and minister_slot_var.get() not in ['political_advisor', 'air_chief', 'navy_chief', 'army_chief']:
            data += f"\t\t\tledger = {minister_category_var.get()}\n"
        data += f"\t\t\tcost = {minister_cost_entry.get()}\n"
        data += f"\t\t\tallowed = {{\n\t\t\t\toriginal_tag = {country_tag}\n\t\t\t}}\n"
        data += f"\t\t\ttraits = {{ {minister_traits_entry.get()} }}\n\t\t}}\n"

    if army_leader_var.get():
        skills = army_leader_skill_entry.get().split()
        data += f"\t\t{army_leader_role_var.get()} = {{\n"
        data += f"\t\t\ttraits = {{ {army_leader_traits_entry.get()} }}\n"
        data += f"\t\t\tskill = {army_leader_level_entry.get()}\n"
        data += f"\t\t\tattack_skill = {skills[0]}\n"
        data += f"\t\t\tdefense_skill = {skills[1]}\n"
        data += f"\t\t\tplanning_skill = {skills[2]}\n"
        data += f"\t\t\tlogistics_skill = {skills[3]}\n\t\t}}\n"

    data += "\t}\n"

    # Handle localization file
    loc_file = 'localisation/english/characters_l_english.yml'
    
    if not os.path.exists(loc_file):
        ensure_file_exists(loc_file, 'l_english:\n')
    
    with open(loc_file, 'r', encoding='utf-8') as f:
        lines = f.readlines() or ['l_english:\n']

    # Find existing tag section or prepare to create new one
    tag_header_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"#{country_tag}"):
            tag_header_index = i
            break

    if tag_header_index is None:
        # Remove trailing empty lines and add new section at end
        while lines and lines[-1].strip() == '':
            lines.pop()
        lines.extend(['\n', f" #{country_tag}\n"])
        tag_header_index = len(lines) - 1
    
    # Find where to insert the new name (before next tag or at end)
    next_tag_index = len(lines)
    for i in range(tag_header_index + 1, len(lines)):
        if lines[i].strip().startswith('#'):
            next_tag_index = i
            break
    
    lines.insert(next_tag_index, f" {country_tag}_{code_name}:0 \"{proper_name}\"\n")

    with open(loc_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # Handle portraits file
    gfx_file = 'interface/lok_leader_portraits.gfx'
    ensure_file_exists(gfx_file, 'spriteTypes = {\n}')

    with open(gfx_file, 'r') as f:
        lines = f.readlines()

    if not any("spriteTypes = {" in line for line in lines):
        lines = ["spriteTypes = {\n", "}"]

    # Find existing tag section or prepare to create new one
    tag_header_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"#{country_tag}"):
            tag_header_index = i
            break

    if tag_header_index is None:
        # Insert new section before closing brace with blank line
        lines.insert(-1, f"\n\t#{country_tag}\n")
        tag_header_index = len(lines) - 2

    new_entries = f"\tspriteType = {{ name = \"GFX_portrait_{country_tag}_{code_name}\" texturefile = \"gfx/leaders/{country_tag}/{country_tag}_{code_name}.tga\" }}\n"
    new_entries += f"\tspriteType = {{ name = \"GFX_portrait_{country_tag}_{code_name}_Small\" texturefile = \"gfx/interface/ministers/{country_tag}/{country_tag}_{code_name}.tga\" }}\n\n"
    
    # Insert after tag header
    lines.insert(tag_header_index + 1, new_entries)

    with open(gfx_file, 'w') as f:
        f.writelines(lines)

    # Handle character file - find existing or use default
    char_filename = None
    for f in os.listdir("common/characters"):
        if f.startswith(f"{country_tag} -"):
            char_filename = f
            break
    
    if char_filename is None:
        char_filename = f"{country_tag} - characters.txt"
    
    char_file = os.path.join("common/characters", char_filename)
    ensure_file_exists(char_file, "characters = {\n}")

    with open(char_file, 'r') as f:
        lines = f.readlines()

    if not lines:
        lines = ["characters = {\n", "}\n"]
    elif not any("characters = {" in line for line in lines):
        lines.insert(0, "characters = {\n")
        lines.append("}\n")

    # Insert character data before the closing brace
    closing_brace_index = next((i for i, line in reversed(list(enumerate(lines))) if "}" in line), len(lines))
    lines.insert(closing_brace_index, data)

    with open(char_file, 'w') as f:
        f.writelines(lines)

    # Write to the country history file
    directory = "history/countries/"
    for filename in os.listdir(directory):
        if filename.startswith(country_tag):
            with open(os.path.join(directory, filename), 'r') as f:
                lines = f.readlines()

            # Insert the new line at the second-to-last line
            lines.insert(0, f"\nrecruit_character = {country_tag}_{code_name}\n")

            with open(os.path.join(directory, filename), 'w') as f:
                f.writelines(lines)
            break

def upload_large_image():
    large_image_path = filedialog.askopenfilename()
    img = Image.open(large_image_path)
    img.save('large_image.tga')
    country_tag = tag_entry.get()
    code_name = code_name_entry.get()
    os.makedirs(f'gfx/leaders/{country_tag}', exist_ok=True)
    shutil.move('large_image.tga', f'gfx/leaders/{country_tag}/{country_tag}_{code_name}.tga')

    # Open the base image and border image
    base_image = Image.open(f'gfx/leaders/{country_tag}/{country_tag}_{code_name}.tga').convert('RGBA')
    border_image = Image.open('minister_border.png').convert('RGBA')

    # Resize the base image
    base_image = base_image.resize((35, 51))

    # Rotate the base image 5 degrees counter-clockwise and expand the output to fit the whole rotated image
    base_image = base_image.rotate(5, expand=True)

    # Create a new image with the desired size for the canvas
    canvas = Image.new('RGBA', (65, 67))

    # Calculate the position to center the base image on the canvas, shifted by 9 pixels to the left and 2 pixels up
    left = (canvas.width - base_image.width) // 2 - 7
    top = (canvas.height - base_image.height) // 2 - 2

    # Paste the base image onto the canvas using alpha_composite
    canvas.alpha_composite(base_image, (left, top))

    # Resize the border image to match the size of the canvas
    border_image = border_image.resize((canvas.width, canvas.height))

    # Paste the border image onto the canvas at the desired position, shifted by 9 pixels to the left and 2 pixels up
    canvas.alpha_composite(border_image, (7 - 7, 2 - 2))

    # Save the result
    ministers_dir = f'gfx/interface/ministers/{country_tag}'
    os.makedirs(ministers_dir, exist_ok=True)
    canvas.save(f'gfx/interface/ministers/{country_tag}/{country_tag}_{code_name}.tga')

def upload_small_image():
    small_image_path = filedialog.askopenfilename()
    img = Image.open(small_image_path)
    img.save('small_image.tga')
    country_tag = tag_entry.get()
    code_name = code_name_entry.get()
    ministers_dir = f'gfx/interface/ministers/{country_tag}'
    os.makedirs(ministers_dir, exist_ok=True)
    shutil.move('small_image.tga', f'{ministers_dir}/{country_tag}_{code_name}.tga')

def toggle_country_leader():
    if country_leader_var.get():
        country_leader_ideology_entry.config(state='normal')
    else:
        country_leader_ideology_entry.config(state='disabled')

def toggle_army_leader():
    if army_leader_var.get():
        army_leader_role_entry.config(state='normal')
        army_leader_level_entry.config(state='normal')
        army_leader_skill_entry.config(state='normal')
        army_leader_traits_entry.config(state='normal')
    else:
        army_leader_role_entry.config(state='disabled')
        army_leader_level_entry.config(state='disabled')
        army_leader_skill_entry.config(state='disabled')
        army_leader_traits_entry.config(state='disabled')

def toggle_minister():
    if minister_var.get():
        minister_slot_entry.config(state='normal')
        minister_traits_entry.config(state='normal')
        minister_cost_entry.config(state='normal')
        minister_category_entry.config(state='normal')
    else:
        minister_slot_entry.config(state='disabled')
        minister_traits_entry.config(state='disabled')
        minister_cost_entry.config(state='disabled')
        minister_category_entry.config(state='disabled')

root = tk.Tk()
root.geometry('250x750')

tag_label = tk.Label(root, text='Tag')
tag_label.pack()
tag_entry = tk.Entry(root)
tag_entry.pack()

code_name_label = tk.Label(root, text='Code Name')
code_name_label.pack()
code_name_entry = tk.Entry(root)
code_name_entry.pack()

proper_name_label = tk.Label(root, text='Proper Name')
proper_name_label.pack()
proper_name_entry = tk.Entry(root)
proper_name_entry.pack()

gender_label = tk.Label(root, text='Gender')
gender_label.pack()
gender_var = StringVar()
gender_entry = tk.OptionMenu(root, gender_var, 'Male', 'Female')
gender_entry.pack()

country_leader_var = IntVar()
country_leader_check = tk.Checkbutton(root, text='Country Leader', variable=country_leader_var, command=toggle_country_leader)
country_leader_check.pack()
country_leader_ideology_label = tk.Label(root, text='Country Leader Ideology')
country_leader_ideology_label.pack()
country_leader_ideology_entry = tk.Entry(root)
country_leader_ideology_entry.pack()
toggle_country_leader()  # Disable the input field by default

army_leader_var = IntVar()
army_leader_check = tk.Checkbutton(root, text='Army Leader', variable=army_leader_var, command=toggle_army_leader)
army_leader_check.pack()
army_leader_role_label = tk.Label(root, text='Army Leader Role')
army_leader_role_label.pack()
army_leader_role_var = StringVar()
army_leader_role_entry = tk.OptionMenu(root, army_leader_role_var, 'field_marshal', 'navy_leader', 'corps_commander')
army_leader_role_entry.pack()
army_leader_level_label = tk.Label(root, text='Army Leader Level')
army_leader_level_label.pack()
army_leader_level_entry = tk.Entry(root)
army_leader_level_entry.pack()
army_leader_skill_label = tk.Label(root, text='Army Leader Skill')
army_leader_skill_label.pack()
army_leader_skill_entry = tk.Entry(root)
army_leader_skill_entry.pack()
army_leader_traits_label = tk.Label(root, text='Army Leader Traits')
army_leader_traits_label.pack()
army_leader_traits_entry = tk.Entry(root)
army_leader_traits_entry.pack()
toggle_army_leader()  # Disable the input fields by default

minister_var = IntVar()
minister_check = tk.Checkbutton(root, text='Minister', variable=minister_var, command=toggle_minister)
minister_check.pack()
minister_slot_label = tk.Label(root, text='Minister Slot')
minister_slot_label.pack()
minister_slot_var = StringVar()
minister_slot_entry = tk.OptionMenu(root, minister_slot_var, 'high_command', 'navy_chief', 'army_chief', 'air_chief', 'political_advisor', 'theorist')
minister_slot_entry.pack()
minister_traits_label = tk.Label(root, text='Minister Traits')
minister_traits_label.pack()
minister_traits_entry = tk.Entry(root)
minister_traits_entry.pack()
minister_cost_label = tk.Label(root, text='Minister Cost')
minister_cost_label.pack()
minister_cost_entry = tk.Entry(root)
minister_cost_entry.pack()
minister_category_label = tk.Label(root, text='Minister Category')
minister_category_label.pack()
minister_category_var = StringVar()
minister_category_entry = tk.OptionMenu(root, minister_category_var, 'army', 'air', 'navy')
minister_category_entry.pack()
toggle_minister()  # Disable the input fields by default

large_image_button = tk.Button(root, text='Upload Large Image', command=upload_large_image)
large_image_button.pack()

small_image_button = tk.Button(root, text='Upload Small Image', command=upload_small_image)
small_image_button.pack()

save_button = tk.Button(root, text='Create Character', command=save_input)
save_button.pack()

root.mainloop()
