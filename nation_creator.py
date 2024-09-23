import tkinter as tk
from tkinter import messagebox
import os

def create_nation():
    country_tag = entry_country_tag.get()
    state_ids = entry_state_ids.get().split(',')
    arms_factory = int(entry_arms_factory.get())
    industrial_complex = int(entry_industrial_complex.get())
    dockyard = int(entry_dockyard.get())
    manpower = int(entry_manpower.get())
    
    nuclear_coverage = float(entry_nuclear_coverage.get())
    food_needs_met = float(entry_food_needs_met.get())
    urbanisation = float(entry_urbanisation.get())
    militarization = float(entry_militarization.get())
    randomness = float(entry_randomness.get())
    
    total_states = len(state_ids)
    
    terrain_values = {
        "mountain": float(entry_mountain.get()),
        "plains": float(entry_plains.get()),
        "forest": float(entry_forest.get()),
        "desert": float(entry_desert.get()),
        "hills": float(entry_hills.get()),
        "jungles": float(entry_jungles.get()),
        "frozen": float(entry_frozen.get()),
        "volcanic": float(entry_volcanic.get()),
        "urban": float(entry_urban.get()),
        "marsh": float(entry_marsh.get())
    }
    
    coastal_multiplier = float(entry_coastal.get())
    
    state_values = {}
    total_value = 0
    
    for state_id in state_ids:
        state_id = state_id.strip()
        state_file_path = f"history/states/{state_id}-"
        state_file = None
        for filename in os.listdir("history/states"):
            if filename.startswith(f"{state_id}-"):
                state_file = filename
                break
        
        if state_file:
            with open(f"history/states/{state_file}", 'r') as sf:
                lines = sf.readlines()
                provinces_block = False
                provinces = []
                for line in lines:
                    if "provinces={" in line:
                        provinces_block = True
                    elif "}" in line and provinces_block:
                        provinces_block = False
                    elif provinces_block:
                        provinces.extend(line.strip().split())
            
            state_value = 0
            province_details = []
            
            with open("map/definition.csv", 'r') as df:
                definition_lines = df.readlines()
                for province_id in provinces:
                    for def_line in definition_lines:
                        if def_line.startswith(province_id):
                            parts = def_line.split(';')
                            terrain = parts[-2]
                            coastal = parts[-3] == 'true'
                            province_value = terrain_values.get(terrain, 0)
                            if coastal:
                                province_value *= coastal_multiplier
                            state_value += province_value
                            province_details.append(f"Province {province_id} has terrain {terrain} and coastal {coastal}")
                            break
            
            state_values[state_id] = state_value
            total_value += state_value
    
    with open('nation_data.txt', 'w') as file:
        for state_id in state_ids:
            state_id = state_id.strip()
            state_value = state_values[state_id]
            relative_value = state_value / total_value
            
            adjusted_arms_factory = arms_factory * relative_value
            adjusted_industrial_complex = industrial_complex * relative_value
            adjusted_dockyard = dockyard * relative_value
            adjusted_manpower = manpower * relative_value
            
            file.write(f"{state_id} has {adjusted_arms_factory:.2f} Military Factories, "
                       f"{adjusted_industrial_complex:.2f} Civilian Factories, "
                       f"{adjusted_dockyard:.2f} Dockyards and "
                       f"{adjusted_manpower:.2f} Population. Its value is {state_value:.2f} and its relative value is {relative_value:.2f}\n")
            
            for detail in province_details:
                file.write(detail + "\n")
    
    messagebox.showinfo("Success", "Nation data has been created!")

root = tk.Tk()
root.title("Hearts of Iron IV Mod Creator")

tk.Label(root, text="Country TAG").grid(row=0)
entry_country_tag = tk.Entry(root)
entry_country_tag.grid(row=0, column=1)

tk.Label(root, text="Country State IDs").grid(row=1)
entry_state_ids = tk.Entry(root)
entry_state_ids.grid(row=1, column=1)

tk.Label(root, text="Arms Factory").grid(row=2)
entry_arms_factory = tk.Entry(root)
entry_arms_factory.grid(row=2, column=1)

tk.Label(root, text="Industrial Complex").grid(row=3)
entry_industrial_complex = tk.Entry(root)
entry_industrial_complex.grid(row=3, column=1)

tk.Label(root, text="Dockyard").grid(row=4)
entry_dockyard = tk.Entry(root)
entry_dockyard.grid(row=4, column=1)

tk.Label(root, text="Manpower").grid(row=5)
entry_manpower = tk.Entry(root)
entry_manpower.grid(row=5, column=1)

tk.Label(root, text="Nuclear Coverage").grid(row=6)
entry_nuclear_coverage = tk.Entry(root)
entry_nuclear_coverage.grid(row=6, column=1)

tk.Label(root, text="Food Needs Met").grid(row=7)
entry_food_needs_met = tk.Entry(root)
entry_food_needs_met.grid(row=7, column=1)

tk.Label(root, text="Urbanisation").grid(row=8)
entry_urbanisation = tk.Entry(root)
entry_urbanisation.grid(row=8, column=1)

tk.Label(root, text="Militarization").grid(row=9)
entry_militarization = tk.Entry(root)
entry_militarization.grid(row=9, column=1)

tk.Label(root, text="Randomness").grid(row=10)
entry_randomness = tk.Entry(root)
entry_randomness.grid(row=10, column=1)

tk.Label(root, text="Mountain").grid(row=11)
entry_mountain = tk.Entry(root)
entry_mountain.insert(0, "0.3")
entry_mountain.grid(row=11, column=1)

tk.Label(root, text="Plains").grid(row=12)
entry_plains = tk.Entry(root)
entry_plains.insert(0, "1")
entry_plains.grid(row=12, column=1)

tk.Label(root, text="Forest").grid(row=13)
entry_forest = tk.Entry(root)
entry_forest.insert(0, "0.5")
entry_forest.grid(row=13, column=1)

tk.Label(root, text="Desert").grid(row=14)
entry_desert = tk.Entry(root)
entry_desert.insert(0, "0.2")
entry_desert.grid(row=14, column=1)

tk.Label(root, text="Hills").grid(row=15)
entry_hills = tk.Entry(root)
entry_hills.insert(0, "0.7")
entry_hills.grid(row=15, column=1)

tk.Label(root, text="Jungles").grid(row=16)
entry_jungles = tk.Entry(root)
entry_jungles.insert(0, "0.3")
entry_jungles.grid(row=16, column=1)

tk.Label(root, text="Frozen").grid(row=17)
entry_frozen = tk.Entry(root)
entry_frozen.insert(0, "0.1")
entry_frozen.grid(row=17, column=1)

tk.Label(root, text="Volcanic").grid(row=18)
entry_volcanic = tk.Entry(root)
entry_volcanic.insert(0, "0.05")
entry_volcanic.grid(row=18, column=1)

tk.Label(root, text="Urban").grid(row=19)
entry_urban = tk.Entry(root)
entry_urban.insert(0, "5")
entry_urban.grid(row=19, column=1)

tk.Label(root, text="Marsh").grid(row=20)
entry_marsh = tk.Entry(root)
entry_marsh.insert(0, "0.5")
entry_marsh.grid(row=20, column=1)

tk.Label(root, text="Coastal Multiplier").grid(row=21)
entry_coastal = tk.Entry(root)
entry_coastal.insert(0, "1.25")
entry_coastal.grid(row=21, column=1)

tk.Button(root, text="Create Nation", command=create_nation).grid(row=22, columnspan=2)

root.mainloop()
