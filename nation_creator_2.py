import tkinter as tk
from tkinter import messagebox
import os
import random

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
def calculate_state_value(provinces, terrain_values, seafaringness, hotspots, coldspots, capitals):
    state_value = 0
    has_coastal_province = False
    urban_provinces = []  # List to store urban province IDs
    for province_id in provinces:
        terrain, coastal = get_province_data(province_id)
        if terrain in terrain_values:
            value = terrain_values[terrain]
            if coastal:
                value *= seafaringness  # Use the seafaringness multiplier
                has_coastal_province = True
            state_value += value

            # Track urban provinces
            if terrain == "urban":
                urban_provinces.append(province_id)

    return state_value, has_coastal_province, urban_provinces


# Function to round values
def round_value(value):
    return int(value) + (1 if random.random() >= 0.5 else 0)

def round_value_2(value):
    return round(value, 0)

# Function to round manpower up to the nearest ten thousand
def round_manpower(manpower):
    return (manpower // 10000 + (1 if manpower % 10000 > 0 else 0)) * 10000

def get_state_category(military_factories, civilian_factories, dockyards):
    total_factories = military_factories + civilian_factories + dockyards
    if total_factories == 1 or total_factories == 2:
        return "town"
    elif total_factories == 3:
        return "town"
    elif total_factories == 4:
        return "large_town"
    elif total_factories == 5:
        return "city"
    elif total_factories == 6:
        return "large_city"
    elif total_factories == 7:
        return "large_city"
    elif total_factories == 8 or total_factories == 9:
        return "metropolis"
    elif total_factories > 9:
        return "megalopolis"

def get_infrastructure(military_factories, civilian_factories, dockyards):
    total_factories = military_factories + civilian_factories + dockyards
    if total_factories == 0:
        return random.randint(1, 2)
    elif total_factories == 1 or total_factories == 2:
        return random.randint(2, 3)
    elif total_factories == 3 or total_factories == 4 or total_factories == 5:
        return random.randint(3, 4)
    elif total_factories == 6 or total_factories == 7:
        return random.randint(4, 5)
    elif total_factories > 7:
        return 5

# Function to create the victory point buildings block
def create_victory_point_building(province_id, militarization, is_coastal):
    building_block = (
        f"\t\t\t{province_id} = {{\n"
        f"\t\t\t\tsupply_node = 1\n"
        f"\t\t\t\tbunker = {militarization}\n"
    )
    if is_coastal:
        building_block += (
            f"\t\t\t\tcoastal_bunker = {militarization}\n"
            f"\t\t\t\tnaval_base = 2\n"
        )
    building_block += "\t\t\t}\n"
    return building_block


# Function to update the localisation file for victory points
def update_localisation(province_ids):
    loc_file_path = os.path.join("localisation", "english", "victory_points_l_english.yml")
    
    # Open the localisation file in append mode to add new VPs at the end
    with open(loc_file_path, "a") as loc_file:
        for province_id in province_ids:
            loc_file.write(f" VICTORY_POINTS_{province_id}:0 \"{province_id}\"\n")


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

    # Get seafaringness, militarization, and nuclear coverage
    seafaringness = float(seafaringness_entry.get())
    militarization = float(militarization_entry.get())
    nuclear_coverage = float(nuclear_coverage_entry.get())

    # Hotspots, Coldspots, and Capital processing
    hotspots_input = hotspots_entry.get()
    coldspots_input = coldspots_entry.get()
    capitals_input = capitals_entry.get()

    hotspots_factor = float(hotspot_factor_entry.get())
    coldspots_factor = float(coldspot_factor_entry.get())
    capitals_factor = float(capital_factor_entry.get())

    # Retrieve resource values
    total_oil = float(total_oil_entry.get()) if total_oil_entry.get() else 0
    oil_states_input = oil_states_entry.get()
    oil_states = [int(id.strip()) for id in oil_states_input.split(' ') if id.strip().isdigit()]
    
    total_steel = float(total_steel_entry.get()) if total_steel_entry.get() else 0
    steel_states_input = steel_states_entry.get()
    steel_states = [int(id.strip()) for id in steel_states_input.split(' ') if id.strip().isdigit()]

    total_tungsten = float(total_tungsten_entry.get()) if total_tungsten_entry.get() else 0
    tungsten_states_input = tungsten_states_entry.get()
    tungsten_states = [int(id.strip()) for id in tungsten_states_input.split(' ') if id.strip().isdigit()]

    total_aluminium = float(total_aluminium_entry.get()) if total_aluminium_entry.get() else 0
    aluminium_states_input = aluminium_states_entry.get()
    aluminium_states = [int(id.strip()) for id in aluminium_states_input.split(' ') if id.strip().isdigit()]

    total_food = float(total_food_entry.get()) if total_food_entry.get() else 0
    food_states_input = food_states_entry.get()
    food_states = [int(id.strip()) for id in food_states_input.split(' ') if id.strip().isdigit()]

    total_chromium = float(total_chromium_entry.get()) if total_chromium_entry.get() else 0
    chromium_states_input = chromium_states_entry.get()
    chromium_states = [int(id.strip()) for id in chromium_states_input.split(' ') if id.strip().isdigit()]

    total_fissiles = float(total_fissiles_entry.get()) if total_fissiles_entry.get() else 0
    fissiles_states_input = fissiles_states_entry.get()
    fissiles_states = [int(id.strip()) for id in fissiles_states_input.split(' ') if id.strip().isdigit()]

    total_rubber = float(total_rubber_entry.get()) if total_rubber_entry.get() else 0
    rubber_states_input = rubber_states_entry.get()
    rubber_states = [int(id.strip()) for id in rubber_states_input.split(' ') if id.strip().isdigit()]

    total_supertensiles = float(total_supertensiles_entry.get()) if total_supertensiles_entry.get() else 0
    supertensiles_states_input = supertensiles_states_entry.get()
    supertensiles_states = [int(id.strip()) for id in supertensiles_states_input.split(' ') if id.strip().isdigit()]

    resource_distribution = {}  # Store the distributed resources per state

    def distribute_resource(resource_amount, resource_states):
        if len(resource_states) == 0:
            return {}
        resource_per_state = resource_amount / len(resource_states)
        resource_allocation = {state_id: resource_per_state for state_id in resource_states}
        return resource_allocation

    oil_distribution = distribute_resource(total_oil, oil_states)
    steel_distribution = distribute_resource(total_steel, steel_states)
    tungsten_distribution = distribute_resource(total_tungsten, tungsten_states)
    aluminium_distribution = distribute_resource(total_aluminium, aluminium_states)
    chromium_distribution = distribute_resource(total_chromium, chromium_states)
    rubber_distribution = distribute_resource(total_rubber, rubber_states)
    fissiles_distribution = distribute_resource(total_fissiles, fissiles_states)
    food_distribution = distribute_resource(total_food, food_states)
    supertensiles_distribution = distribute_resource(total_supertensiles, supertensiles_states)

    # Process State IDs
    state_ids = [int(id.strip()) for id in state_ids_input.split(' ') if id.strip().isdigit()]
    hotspots = {int(id.strip()): hotspots_factor for id in hotspots_input.split(' ') if id.strip().isdigit()}
    coldspots = {int(id.strip()): coldspots_factor for id in coldspots_input.split(' ') if id.strip().isdigit()}
    capitals = {int(id.strip()): capitals_factor for id in capitals_input.split(' ') if id.strip().isdigit()}

    total_states = len(state_ids)
    
    # Validate input
    if total_states == 0:
        messagebox.showerror("Input Error", "Please enter valid State IDs.")
        return

    # Step 1: Calculate the total value of all states
    total_value = 0
    state_values = {}
    state_urban_provinces = {}  # To store urban provinces per state
    state_has_coastal_province = {}  # To store coastal info per state (if needed)
    for state_id in state_ids:
        provinces = get_provinces_from_state(state_id)
        state_value, has_coastal_province, urban_provinces = calculate_state_value(provinces, terrain_values, seafaringness, hotspots, coldspots, capitals)

        # Adjust state value based on hotspots, coldspots, and capitals
        if state_id in hotspots:
            state_value *= hotspots[state_id]
        elif state_id in coldspots:
            state_value *= coldspots[state_id]
        elif state_id in capitals:
            state_value *= capitals[state_id]

        # Store state value and urban provinces per state
        state_values[state_id] = state_value
        state_urban_provinces[state_id] = urban_provinces  # Store urban provinces
        state_has_coastal_province[state_id] = has_coastal_province  # Store coastal info

        total_value += state_value

    # Create output text file
    output_file = "nations_output.txt"
    with open(output_file, "w") as file:
        for state_id in state_ids:
            state_value = state_values[state_id]
            urban_provinces = state_urban_provinces[state_id]  # Retrieve urban provinces for this state
            has_coastal_province = state_has_coastal_province[state_id]  # Retrieve coastal info if needed

            # Step 2: Calculate the relative value for each state
            relative_value = state_value / total_value if total_value > 0 else 0
            
            # Step 3: Adjust factory and population values based on the relative value
            adjusted_military_factories = round_value(arms_factory * relative_value)
            adjusted_civilian_factories = round_value(industrial_complex * relative_value)
            adjusted_population = round_manpower(manpower * relative_value)
            anti_air_building_value = max(0, militarization - 1)

            # Check if the state has any coastal provinces to determine dockyards
            has_coastal_province = any(get_province_data(province_id)[1] for province_id in get_provinces_from_state(state_id))
            adjusted_dockyards = round_value(dockyard * relative_value) if has_coastal_province else 0

            # Define the dictionary with victory point values
            victory_point_value_map = {
                "rural": 1,
                "town": 3,
                "large_town": 5,       # Differentiated from 'town'
                "city": 10,
                "large_city": 15,
                "metropolis": 20,
                "megalopolis": 30      # Differentiated from 'metropolis'
            }

            # Get the state category
            state_category = get_state_category(adjusted_military_factories, adjusted_civilian_factories, adjusted_dockyards)

            # Assign victory point value based on the state category, with a default value if not found
            victory_point_value = victory_point_value_map.get(state_category, 1)  # Default to 1 if category not in map

            # Generate victory points block
            victory_points_block = ""
            victory_points_building_block = ""
            for province_id in urban_provinces:
                terrain, coastal = get_province_data(province_id)
                if terrain == "urban":  # Ensure it's an urban province
                    victory_points_block += f"\t\tvictory_points = {{ {province_id} {victory_point_value} }}\n"
                    victory_points_building_block += create_victory_point_building(province_id, militarization, coastal)

            # Update localisation file for all victory points in this state
            update_localisation(urban_provinces)

            # Retrieve the resource allocations for this state
            random_resource_factor = random.uniform(0.5, 2)
            oil_for_state = round_value_2((oil_distribution.get(state_id, 0) * random_resource_factor))
            steel_for_state = round_value_2((steel_distribution.get(state_id, 0) * random_resource_factor))
            tungsten_for_state = round_value_2((tungsten_distribution.get(state_id, 0) * random_resource_factor))
            chromium_for_state = round_value_2((chromium_distribution.get(state_id, 0) * random_resource_factor))
            food_for_state = round_value_2((food_distribution.get(state_id, 0) * random_resource_factor))
            supertensiles_for_state = round_value_2((supertensiles_distribution.get(state_id, 0) * random_resource_factor))
            fissiles_for_state = round_value_2((fissiles_distribution.get(state_id, 0) * random_resource_factor))
            rubber_for_state = round_value_2((rubber_distribution.get(state_id, 0) * random_resource_factor))
            aluminium_for_state = round_value_2((aluminium_distribution.get(state_id, 0) * random_resource_factor))

            # Write state info to the output file
            file.write(f"[{state_id}] has {adjusted_military_factories} Military Factories, "
                       f"{adjusted_civilian_factories} Civilian Factories, "
                       f"{adjusted_dockyards} Dockyards and {adjusted_population} Population.\n")
            file.write(f"Its relative value is {relative_value:.4f}\n")
            
            # Get provinces for the current state and print province data
            provinces = get_provinces_from_state(state_id)
            for province_id in provinces:
                terrain, coastal = get_province_data(province_id)
                if terrain and coastal is not None:
                    file.write(f"Province {province_id} has terrain {terrain} and coastal {coastal}\n")
                else:
                    file.write(f"Province {province_id} information not found.\n")
            
            # Step 4: Write the adjusted values to the state's file
            state_file_path = os.path.join("history", "states", f"{state_id}-")
            for filename in os.listdir("history/states"):
                if filename.startswith(f"{state_id}-"):
                    state_file_path = os.path.join("history", "states", filename)
                    break

            # Read the existing state file
            with open(state_file_path, "r") as state_file:
                lines = state_file.readlines()

            # Remove "history = {}" block and "manpower" line, and the last closing brace
            new_lines = []
            inside_history_block = False
            for line in lines:
                if line.strip().startswith("history = {"):
                    inside_history_block = True  # Start of history block
                elif inside_history_block:
                    if line.strip() == "}":
                        inside_history_block = False  # End of history block
                    continue  # Skip all lines inside history block
                elif line.strip().startswith("manpower"):
                    continue  # Skip the manpower line
                elif line.strip().startswith("state_category"):
                    continue  # Skip the state category line
                new_lines.append(line)  # Keep all other lines

            # Remove the final closing brace if it's the last line
            if new_lines and new_lines[-1].strip() == "}":
                new_lines.pop()  # Remove the last closing brace

            # Prepare the new block to add at the end
            new_block = (
                f"\tmanpower={adjusted_population}\n"
                f"\tstate_category={get_state_category(adjusted_military_factories, adjusted_civilian_factories, adjusted_dockyards)}\n"
                f"\tresources = {{ food = {food_for_state} rubber = {rubber_for_state} tungsten = {tungsten_for_state} aluminium = {aluminium_for_state} fissiles = {fissiles_for_state} supertensiles = {supertensiles_for_state} chromium = {chromium_for_state} oil = {oil_for_state} steel = {steel_for_state} }}\n"  # Add the resource block
                f"\thistory={{\n"
                f"\t\towner = {country_tag}\n"
                f"\t\tadd_core_of = {country_tag}\n"
                f"\n"
                f"{victory_points_block}"
                f"\t\tbuildings = {{\n"
                f"\t\t\tinfrastructure = {get_infrastructure(adjusted_military_factories, adjusted_civilian_factories, adjusted_dockyards)}\n"
                f"\t\t\tindustrial_complex = {adjusted_civilian_factories}\n"
                f"\t\t\tarms_factory = {adjusted_military_factories}\n"
                f"\t\t\tdockyard = {adjusted_dockyards}\n"
                f"\t\t\tanti_air_building = {anti_air_building_value}\n"
                f"{victory_points_building_block}\n"
                f"\t\t}}\n"
                f"\t}}\n"
            )

            # Append the new block to the end of the lines
            new_lines.append(new_block)
            new_lines.append("}\n")  # Append the final closing bracket

            # Write the updated lines back to the state file
            with open(state_file_path, "w") as state_file:
                state_file.writelines(new_lines)

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

tk.Label(root, text="Military Factories:").grid(row=2, column=0)
arms_factory_entry = tk.Entry(root)
arms_factory_entry.grid(row=2, column=1)

tk.Label(root, text="Civilian Factories:").grid(row=3, column=0)
industrial_complex_entry = tk.Entry(root)
industrial_complex_entry.grid(row=3, column=1)

tk.Label(root, text="Dockyards:").grid(row=4, column=0)
dockyard_entry = tk.Entry(root)
dockyard_entry.grid(row=4, column=1)

tk.Label(root, text="Population:").grid(row=5, column=0)
manpower_entry = tk.Entry(root)
manpower_entry.grid(row=5, column=1)

# Additional inputs for terrain values
tk.Label(root, text="Seafaringness:").grid(row=6, column=0)
seafaringness_entry = tk.Entry(root)
seafaringness_entry.insert(0, 1.5)
seafaringness_entry.grid(row=6, column=1)

tk.Label(root, text="Militarization:").grid(row=7, column=0)
militarization_entry = tk.Entry(root)
militarization_entry.insert(0, 0)
militarization_entry.grid(row=7, column=1)

tk.Label(root, text="Nuclear Coverage:").grid(row=8, column=0)
nuclear_coverage_entry = tk.Entry(root)
nuclear_coverage_entry.insert(0, 1.0)
nuclear_coverage_entry.grid(row=8, column=1)

# Input fields for terrain values
tk.Label(root, text="Mountain:").grid(row=9, column=0)
mountain_entry = tk.Entry(root)
mountain_entry.insert(0, 0.4)
mountain_entry.grid(row=9, column=1)

tk.Label(root, text="Plains:").grid(row=10, column=0)
plains_entry = tk.Entry(root)
plains_entry.insert(0, 0.6)
plains_entry.grid(row=10, column=1)

tk.Label(root, text="Forest:").grid(row=11, column=0)
forest_entry = tk.Entry(root)
forest_entry.insert(0, 0.5)
forest_entry.grid(row=11, column=1)

tk.Label(root, text="Desert:").grid(row=12, column=0)
desert_entry = tk.Entry(root)
desert_entry.insert(0, 0.2)
desert_entry.grid(row=12, column=1)

tk.Label(root, text="Hills:").grid(row=13, column=0)
hills_entry = tk.Entry(root)
hills_entry.insert(0, 0.7)
hills_entry.grid(row=13, column=1)

tk.Label(root, text="Jungles:").grid(row=14, column=0)
jungles_entry = tk.Entry(root)
jungles_entry.insert(0, 0.3)
jungles_entry.grid(row=14, column=1)

tk.Label(root, text="Frozen:").grid(row=15, column=0)
frozen_entry = tk.Entry(root)
frozen_entry.insert(0, 0.1)
frozen_entry.grid(row=15, column=1)

tk.Label(root, text="Volcanic:").grid(row=16, column=0)
volcanic_entry = tk.Entry(root)
volcanic_entry.insert(0, 0.05)
volcanic_entry.grid(row=16, column=1)

tk.Label(root, text="Urban:").grid(row=17, column=0)
urban_entry = tk.Entry(root)
urban_entry.insert(0, 5)
urban_entry.grid(row=17, column=1)

tk.Label(root, text="Marsh:").grid(row=18, column=0)
marsh_entry = tk.Entry(root)
marsh_entry.insert(0, 0.5)
marsh_entry.grid(row=18, column=1)

tk.Label(root, text="Hotspots:").grid(row=19, column=0)
hotspots_entry = tk.Entry(root)
hotspots_entry.grid(row=19, column=1)

tk.Label(root, text="Hotspot Factor:").grid(row=20, column=0)
hotspot_factor_entry = tk.Entry(root)
hotspot_factor_entry.insert(0, 1.5)
hotspot_factor_entry.grid(row=20, column=1)

tk.Label(root, text="Coldspots:").grid(row=21, column=0)
coldspots_entry = tk.Entry(root)
coldspots_entry.grid(row=21, column=1)

tk.Label(root, text="Coldspot Factor:").grid(row=22, column=0)
coldspot_factor_entry = tk.Entry(root)
coldspot_factor_entry.insert(0, 0.5)
coldspot_factor_entry.grid(row=22, column=1)

tk.Label(root, text="Capital:").grid(row=23, column=0)
capitals_entry = tk.Entry(root)
capitals_entry.grid(row=23, column=1)

tk.Label(root, text="Capital Factor:").grid(row=24, column=0)
capital_factor_entry = tk.Entry(root)
capital_factor_entry.insert(0, 3)
capital_factor_entry.grid(row=24, column=1)

# Add input fields for resources (example: Oil and Steel)
tk.Label(root, text="Total Oil:").grid(row=0, column=2)
total_oil_entry = tk.Entry(root)
total_oil_entry.grid(row=0, column=3)

tk.Label(root, text="States with Oil:").grid(row=1, column=2)
oil_states_entry = tk.Entry(root)
oil_states_entry.grid(row=1, column=3)

tk.Label(root, text="Total Steel:").grid(row=2, column=2)
total_steel_entry = tk.Entry(root)
total_steel_entry.grid(row=2, column=3)

tk.Label(root, text="States with Steel:").grid(row=3, column=2)
steel_states_entry = tk.Entry(root)
steel_states_entry.grid(row=3, column=3)

tk.Label(root, text="Total Aluminium:").grid(row=4, column=2)
total_aluminium_entry = tk.Entry(root)
total_aluminium_entry.grid(row=4, column=3)

tk.Label(root, text="States with Aluminium:").grid(row=5, column=2)
aluminium_states_entry = tk.Entry(root)
aluminium_states_entry.grid(row=5, column=3)

tk.Label(root, text="Total Rubber:").grid(row=6, column=2)
total_rubber_entry = tk.Entry(root)
total_rubber_entry.grid(row=6, column=3)

tk.Label(root, text="States with Rubber:").grid(row=7, column=2)
rubber_states_entry = tk.Entry(root)
rubber_states_entry.grid(row=7, column=3)

tk.Label(root, text="Total Fissiles:").grid(row=8, column=2)
total_fissiles_entry = tk.Entry(root)
total_fissiles_entry.grid(row=8, column=3)

tk.Label(root, text="States with Fissiles:").grid(row=9, column=2)
fissiles_states_entry = tk.Entry(root)
fissiles_states_entry.grid(row=9, column=3)

tk.Label(root, text="Total Tungsten:").grid(row=10, column=2)
total_tungsten_entry = tk.Entry(root)
total_tungsten_entry.grid(row=10, column=3)

tk.Label(root, text="States with Tungsten:").grid(row=11, column=2)
tungsten_states_entry = tk.Entry(root)
tungsten_states_entry.grid(row=11, column=3)

tk.Label(root, text="Total Chromium:").grid(row=12, column=2)
total_chromium_entry = tk.Entry(root)
total_chromium_entry.grid(row=12, column=3)

tk.Label(root, text="States with Chromium:").grid(row=13, column=2)
chromium_states_entry = tk.Entry(root)
chromium_states_entry.grid(row=13, column=3)

tk.Label(root, text="Total Food:").grid(row=14, column=2)
total_food_entry = tk.Entry(root)
total_food_entry.grid(row=14, column=3)

tk.Label(root, text="States with Food:").grid(row=15, column=2)
food_states_entry = tk.Entry(root)
food_states_entry.grid(row=15, column=3)

tk.Label(root, text="Total Supertensiles:").grid(row=16, column=2)
total_supertensiles_entry = tk.Entry(root)
total_supertensiles_entry.grid(row=16, column=3)

tk.Label(root, text="States with Supertensiles:").grid(row=17, column=2)
supertensiles_states_entry = tk.Entry(root)
supertensiles_states_entry.grid(row=17, column=3)

# Create button to trigger nation creation
create_button = tk.Button(root, text="Create Nation", command=create_nation)
create_button.grid(row=29, column=0, columnspan=2)

# Start the GUI main loop
root.mainloop()