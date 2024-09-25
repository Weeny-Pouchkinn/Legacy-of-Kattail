import tkinter as tk
from tkinter import messagebox
import os

# Function to read provinces from the state file
def get_provinces_from_state(state_id):
    state_file_path = os.path.join("history", "states", f"{state_id}-")
    for filename in os.listdir("history/states"):
        if filename.startswith(f"{state_id}-"):
            state_file_path = os.path.join("history", "states", filename)
            break
    
    provinces = []
    with open(state_file_path, "r") as state_file:
        inside_provinces_block = False
        for line in state_file:
            line = line.strip()
            if "provinces={" in line:
                inside_provinces_block = True
            elif inside_provinces_block and "}" in line:
                inside_provinces_block = False
            elif inside_provinces_block:
                provinces += [int(p.strip()) for p in line.split() if p.strip().isdigit()]
    return provinces

# Function to get terrain and coastal data for a province
def get_province_data(province_id):
    with open("map/definition.csv", "r") as definition_file:
        for line in definition_file:
            parts = line.split(";")
            if int(parts[0]) == province_id:
                coastal = parts[5].strip().lower() == "true"
                terrain = parts[6].strip()
                return terrain, coastal
    return None, None

# Function to calculate the value of a state based on its provinces
def calculate_state_value(provinces, terrain_values):
    state_value = 0
    for province_id in provinces:
        terrain, coastal = get_province_data(province_id)
        if terrain in terrain_values:
            value = terrain_values[terrain]
            if coastal:
                value *= 1.25
            state_value += value
    return state_value

# Function to create the nation
def create_nation():
    # Retrieve values from input fields
    country_tag = country_tag_entry.get()
    state_ids_input = state_ids_entry.get()
    arms_factory = float(arms_factory_entry.get())
    industrial_complex = float(industrial_complex_entry.get())
    dockyard = float(dockyard_entry.get())
    manpower = float(manpower_entry.get())
    
    # Retrieve terrain values from input fields
    terrain_values = {
        "mountain": float(mountain_entry.get()),
        "plains": float(plains_entry.get()),
        "forest": float(forest_entry.get()),
        "desert": float(desert_entry.get()),
        "hills": float(hills_entry.get()),
        "jungles": float(jungles_entry.get()),
        "frozen": float(frozen_entry.get()),
        "volcanic": float(volcanic_entry.get()),
        "urban": float(urban_entry.get()),
        "marsh": float(marsh_entry.get())
    }
    
    # Process State IDs
    state_ids = [int(id.strip()) for id in state_ids_input.split(',') if id.strip().isdigit()]
    total_states = len(state_ids)
    
    # Validate input
    if total_states == 0:
        messagebox.showerror("Input Error", "Please enter valid State IDs.")
        return

    # Step 1: Calculate the total value of all states
    total_value = 0
    state_values = {}
    for state_id in state_ids:
        provinces = get_provinces_from_state(state_id)
        state_value = calculate_state_value(provinces, terrain_values)
        state_values[state_id] = state_value
        total_value += state_value

    # Create output text file
    output_file = "nations_output.txt"
    with open(output_file, "w") as file:
        for state_id in state_ids:
            state_value = state_values[state_id]
            
            # Step 2: Calculate the relative value for each state
            if total_value > 0:
                relative_value = state_value / total_value
            else:
                relative_value = 0
            
            # Step 3: Adjust factory and population values based on the relative value
            adjusted_military_factories = arms_factory * relative_value
            adjusted_civilian_factories = industrial_complex * relative_value
            adjusted_dockyards = dockyard * relative_value
            adjusted_population = manpower * relative_value

            # Write state info to the output file
            file.write(f"[{state_id}] has {adjusted_military_factories:.2f} Military Factories, "
                       f"{adjusted_civilian_factories:.2f} Civilian Factories, "
                       f"{adjusted_dockyards:.2f} Dockyards and {adjusted_population:.2f} Population.\n")
            file.write(f"Its relative value is {relative_value:.4f}\n")
            
            # Get provinces for the current state and print province data
            provinces = get_provinces_from_state(state_id)
            for province_id in provinces:
                terrain, coastal = get_province_data(province_id)
                if terrain and coastal is not None:
                    file.write(f"Province {province_id} has terrain {terrain} and coastal {coastal}\n")
                else:
                    file.write(f"Province {province_id} information not found.\n")
    
    messagebox.showinfo("Success", f"Nation created successfully! Output saved to {output_file}")

# Set up the GUI window
root = tk.Tk()
root.title("Hearts of Iron IV Nation Creator")

# Create and place input fields for nation stats
tk.Label(root, text="Country TAG:").grid(row=0, column=0)
country_tag_entry = tk.Entry(root)
country_tag_entry.grid(row=0, column=1)

tk.Label(root, text="Country State IDs:").grid(row=1, column=0)
state_ids_entry = tk.Entry(root)
state_ids_entry.grid(row=1, column=1)

tk.Label(root, text="Arms Factory:").grid(row=2, column=0)
arms_factory_entry = tk.Entry(root)
arms_factory_entry.grid(row=2, column=1)

tk.Label(root, text="Industrial Complex:").grid(row=3, column=0)
industrial_complex_entry = tk.Entry(root)
industrial_complex_entry.grid(row=3, column=1)

tk.Label(root, text="Dockyard:").grid(row=4, column=0)
dockyard_entry = tk.Entry(root)
dockyard_entry.grid(row=4, column=1)

tk.Label(root, text="Manpower:").grid(row=5, column=0)
manpower_entry = tk.Entry(root)
manpower_entry.grid(row=5, column=1)

# Create and place input fields for terrain values
terrain_defaults = {
    "mountain": 0.3,
    "plains": 1,
    "forest": 0.5,
    "desert": 0.2,
    "hills": 0.7,
    "jungles": 0.3,
    "frozen": 0.1,
    "volcanic": 0.05,
    "urban": 5,
    "marsh": 0.5
}

tk.Label(root, text="Terrain Values:").grid(row=6, column=0, columnspan=2)

tk.Label(root, text="Mountain:").grid(row=7, column=0)
mountain_entry = tk.Entry(root)
mountain_entry.insert(0, terrain_defaults["mountain"])
mountain_entry.grid(row=7, column=1)

tk.Label(root, text="Plains:").grid(row=8, column=0)
plains_entry = tk.Entry(root)
plains_entry.insert(0, terrain_defaults["plains"])
plains_entry.grid(row=8, column=1)

tk.Label(root, text="Forest:").grid(row=9, column=0)
forest_entry = tk.Entry(root)
forest_entry.insert(0, terrain_defaults["forest"])
forest_entry.grid(row=9, column=1)

tk.Label(root, text="Desert:").grid(row=10, column=0)
desert_entry = tk.Entry(root)
desert_entry.insert(0, terrain_defaults["desert"])
desert_entry.grid(row=10, column=1)

tk.Label(root, text="Hills:").grid(row=11, column=0)
hills_entry = tk.Entry(root)
hills_entry.insert(0, terrain_defaults["hills"])
hills_entry.grid(row=11, column=1)

tk.Label(root, text="Jungles:").grid(row=12, column=0)
jungles_entry = tk.Entry(root)
jungles_entry.insert(0, terrain_defaults["jungles"])
jungles_entry.grid(row=12, column=1)

tk.Label(root, text="Frozen:").grid(row=13, column=0)
frozen_entry = tk.Entry(root)
frozen_entry.insert(0, terrain_defaults["frozen"])
frozen_entry.grid(row=13, column=1)

tk.Label(root, text="Volcanic:").grid(row=14, column=0)
volcanic_entry = tk.Entry(root)
volcanic_entry.insert(0, terrain_defaults["volcanic"])
volcanic_entry.grid(row=14, column=1)

tk.Label(root, text="Urban:").grid(row=15, column=0)
urban_entry = tk.Entry(root)
urban_entry.insert(0, terrain_defaults["urban"])
urban_entry.grid(row=15, column=1)

tk.Label(root, text="Marsh:").grid(row=16, column=0)
marsh_entry = tk.Entry(root)
marsh_entry.insert(0, terrain_defaults["marsh"])
marsh_entry.grid(row=16, column=1)

# Create button to trigger nation creation
create_button = tk.Button(root, text="Create Nation", command=create_nation)
create_button.grid(row=17, column=0, columnspan=2)

# Start the GUI main loop
root.mainloop()
