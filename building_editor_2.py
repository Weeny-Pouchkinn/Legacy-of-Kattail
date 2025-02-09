import os
import random
from tkinter import *
from tkinter import ttk, messagebox

# Function to handle confirm button press
def add_buildings():
    building_type = building_type_var.get()
    country_tag = country_tag_entry.get().strip()
    num_building = num_building_entry.get().strip()
    odds_of_adding = odds_of_adding_entry.get().strip()

    # Validate input
    if not building_type or not country_tag or not num_building or not odds_of_adding:
        messagebox.showerror("Error", "All fields must be filled.")
        return

    try:
        num_building = int(num_building)
        odds_of_adding = float(odds_of_adding)
        if not (0 <= odds_of_adding <= 1):
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Invalid number of buildings or odds (should be between 0 and 1).")
        return

    # Get the selected state categories
    selected_categories = [cat for cat, var in category_vars.items() if var.get()]

    # If no categories are selected, show an error
    if not selected_categories:
        messagebox.showerror("Error", "At least one state category must be selected.")
        return

    # Log initial inputs for troubleshooting
    print(f"Building Type: {building_type}")
    print(f"Country Tag: {country_tag}")
    print(f"Num Buildings: {num_building}")
    print(f"Odds of Adding: {odds_of_adding}")
    print(f"Selected Categories: {selected_categories}")

    # Navigate and process files
    history_path = "history/states"
    if not os.path.exists(history_path):
        messagebox.showerror("Error", f"Directory '{history_path}' not found.")
        return

    state_processed = False
    for filename in os.listdir(history_path):
        filepath = os.path.join(history_path, filename)
        with open(filepath, 'r+', encoding='utf-8') as file:
            content = file.read()

            if f"owner = {country_tag}" in content:
                for category in selected_categories:
                    if f"state_category={category}" in content:
                        # Apply odds of adding
                        if random.random() <= odds_of_adding:
                            state_processed = True
                            print(f"Processing state: {filename} (Category: {category})")
                            # Add or modify buildings in the state file
                            process_state_file(filepath, building_type, num_building)
                        break

    if not state_processed:
        messagebox.showinfo("Result", "No states matched the criteria.")

def process_state_file(filepath, building_type, num_building):
    with open(filepath, 'r+', encoding='utf-8') as file:
        lines = file.readlines()
        file.seek(0)
        buildings_found = False
        building_added = False
        for i, line in enumerate(lines):
            # Look for the 'buildings = {' block
            if "buildings = {" in line:
                buildings_found = True
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith(f"{building_type} ="):
                        current_value = int(lines[j].strip().split('=')[1])
                        lines[j] = f"            {building_type} = {current_value + num_building}\n"
                        building_added = True
                        print(f"Updated {building_type} in {filepath}, adding {num_building}.")
                        break
                if not building_added:
                    # Add the building type if not already present
                    lines.insert(i + 1, f"\t\t\t{building_type} = {num_building}\n")
                    print(f"Added new entry for {building_type} = {num_building} in {filepath}.")
                break

        if not buildings_found:
            print(f"No 'buildings' block found in {filepath}.")
        
        file.writelines(lines)

# GUI setup
root = Tk()
root.title("Building Adder")

# Building type
building_type_var = StringVar()
building_type_label = Label(root, text="Type of building to add:")
building_type_label.grid(row=0, column=0)
building_type_options = sorted([
    'supertensiles_workshop', 'food_silo', 'hydroponics_farm', 'fusion_power_plant', 'anti_wmd', 
    'infrastructure', 'arms_factory', 'industrial_complex', 'air_base', 'dockyard', 'anti_air_building', 
    'synthetic_refinery', 'fuel_silo', 'radar_station', 'rocket_site', 'nuclear_reactor'
])
building_type_dropdown = ttk.Combobox(root, textvariable=building_type_var, values=building_type_options)
building_type_dropdown.grid(row=0, column=1)

# Country tag
country_tag_label = Label(root, text="Tag to add to:")
country_tag_label.grid(row=1, column=0)
country_tag_entry = Entry(root)
country_tag_entry.grid(row=1, column=1)

# Number of buildings
num_building_label = Label(root, text="Num of buildings to add:")
num_building_label.grid(row=2, column=0)
num_building_entry = Entry(root)
num_building_entry.grid(row=2, column=1)

# Odds of adding
odds_of_adding_label = Label(root, text="Odds of adding:")
odds_of_adding_label.grid(row=3, column=0)
odds_of_adding_entry = Entry(root)
odds_of_adding_entry.grid(row=3, column=1)

# State categories
category_vars = {}
categories_frame = LabelFrame(root, text="State categories to add to")
categories_frame.grid(row=4, columnspan=2, pady=10)

categories = [
    'wasteland', 'enclave', 'tiny_island', 'pastoral', 'small_island', 'rural', 
    'town', 'large_town', 'city', 'large_city', 'metropolis', 'megalopolis'
]

for idx, category in enumerate(categories):
    var = BooleanVar(value=True)
    category_vars[category] = var
    checkbox = Checkbutton(categories_frame, text=category, variable=var)
    checkbox.grid(row=idx//3, column=idx%3, sticky='w')

# Tick/untick all
def toggle_all():
    current_state = all(var.get() for var in category_vars.values())
    for var in category_vars.values():
        var.set(not current_state)

toggle_button = Button(root, text="Tick/Untick All", command=toggle_all)
toggle_button.grid(row=5, columnspan=2)

# Confirm button
confirm_button = Button(root, text="Confirm", command=add_buildings)
confirm_button.grid(row=6, columnspan=2)

root.mainloop()
