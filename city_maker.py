import os
import tkinter as tk
from tkinter import messagebox

# Function to locate the state file containing the Province ID
def find_state_file(province_id, folder):
    province_str = str(province_id)
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                inside_provinces_block = False
                provinces = []
                for line in file:
                    if 'provinces={' in line:
                        inside_provinces_block = True  # Start of provinces block
                    if inside_provinces_block:
                        provinces.extend(line.strip().replace('provinces={', '').replace('}', '').split())
                        if '}' in line:
                            inside_provinces_block = False  # End of provinces block
                            if province_str in provinces:
                                return filepath
    return None

# Function to modify the state file
def modify_state_file(filepath, province_id, vp_id, vp_value, fort_level, sea_fort_level, port_level, supply_hub_level):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # Locate "add_core_of" and add VP data
    for i, line in enumerate(content):
        if "add_core_of" in line:
            content.insert(i + 1, f"\t\tvictory_points = {{ {vp_id} {vp_value} }}\n")
            break

    # Locate "buildings = {}" block and add the building levels
    for i, line in enumerate(content):
        if "buildings =" in line:
            content.insert(i + 2, f"\t\t\t{vp_id} = {{ \n")
            content.insert(i + 3, f"\t\t\t\tsupply_node = {supply_hub_level}\n")
            content.insert(i + 4, f"\t\t\t\tnaval_base = {port_level}\n")
            content.insert(i + 5, f"\t\t\t\tbunker = {fort_level}\n")
            content.insert(i + 6, f"\t\t\t\tcoastal_bunker = {sea_fort_level}\n")
            content.insert(i + 7, f"\t\t\t}}\n")
            break

    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines(content)

# Function to modify the localisation file
def modify_localisation(province_id, vp_name, localisation_path):
    with open(localisation_path, 'a', encoding='utf-8') as loc_file:
        loc_file.write(f" VICTORY_POINTS_{province_id}:0 \"{vp_name}\"\n")

# Main function to handle GUI data and file processing
def confirm():
    province_id = int(province_entry.get())
    vp_name = vp_name_entry.get()
    vp_value = int(vp_value_entry.get())
    fort_level = int(fort_level_entry.get())
    sea_fort_level = int(sea_fort_level_entry.get())
    port_level = int(port_level_entry.get())
    supply_hub_level = int(supply_hub_level_entry.get())

    # Define file paths
    state_folder = 'history/states'
    localisation_path = 'localisation/english/victory_points_l_english.yml'

    # Find the state file and make changes
    state_file = find_state_file(province_id, state_folder)
    if state_file:
        modify_state_file(state_file, province_id, province_id, vp_value, fort_level, sea_fort_level, port_level, supply_hub_level)
        modify_localisation(province_id, vp_name, localisation_path)
        messagebox.showinfo("Success", "City data successfully updated!")
    else:
        messagebox.showerror("Error", "Province ID not found in state files.")

# Create the GUI
root = tk.Tk()
root.title("City Maker")

# Province ID Entry
tk.Label(root, text="Province ID").grid(row=0)
province_entry = tk.Entry(root)
province_entry.grid(row=0, column=1)

# VP Name Entry
tk.Label(root, text="VP Name").grid(row=1)
vp_name_entry = tk.Entry(root)
vp_name_entry.grid(row=1, column=1)

# VP Value Entry
tk.Label(root, text="VP Value").grid(row=2)
vp_value_entry = tk.Entry(root)
vp_value_entry.grid(row=2, column=1)

# Fort Level Entry
tk.Label(root, text="Fort Level (default 0)").grid(row=3)
fort_level_entry = tk.Entry(root)
fort_level_entry.insert(0, "0")
fort_level_entry.grid(row=3, column=1)

# Sea Fort Level Entry
tk.Label(root, text="Sea Fort Level (default 0)").grid(row=4)
sea_fort_level_entry = tk.Entry(root)
sea_fort_level_entry.insert(0, "0")
sea_fort_level_entry.grid(row=4, column=1)

# Port Level Entry
tk.Label(root, text="Port Level (default 0)").grid(row=5)
port_level_entry = tk.Entry(root)
port_level_entry.insert(0, "0")
port_level_entry.grid(row=5, column=1)

# Supply Hub Level Entry
tk.Label(root, text="Supply Hub Level (default 1)").grid(row=6)
supply_hub_level_entry = tk.Entry(root)
supply_hub_level_entry.insert(0, "1")
supply_hub_level_entry.grid(row=6, column=1)

# Confirm Button
confirm_button = tk.Button(root, text="Confirm", command=confirm)
confirm_button.grid(row=7, column=1)

root.mainloop()
