import tkinter as tk
from tkinter import ttk, messagebox
import os
import random
import re
from collections import defaultdict

def create_gui():
    root = tk.Tk()
    root.title("HOI4 Air Wing Setup")

    # Country TAG entry
    ttk.Label(root, text="Country TAG (3-letter code):").grid(row=0, column=0, padx=5, pady=5)
    tag_entry = ttk.Entry(root)
    tag_entry.grid(row=0, column=1, padx=5, pady=5)

    # Plane entries
    ttk.Label(root, text="Air Wings (one per line as [type] [amount]):").grid(row=1, column=0, padx=5, pady=5)
    planes_text = tk.Text(root, width=40, height=10)
    planes_text.grid(row=1, column=1, padx=5, pady=5)

    def on_confirm():
        country_tag = tag_entry.get().strip().upper()
        if len(country_tag) != 3 or not country_tag.isalpha():
            messagebox.showerror("Error", "Country TAG must be a 3-letter code.")
            return

        # Parse plane entries
        plane_entries = []
        lines = planes_text.get("1.0", tk.END).splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            plane_type, amount = parts[0], parts[1]
            try:
                plane_entries.append((plane_type, int(amount)))
            except ValueError:
                continue

        if not plane_entries:
            messagebox.showerror("Error", "No valid plane entries found.")
            return

        # Find state files
        mod_root = os.path.dirname(os.path.abspath(__file__))
        states_dir = os.path.join(mod_root, 'history', 'states')
        if not os.path.exists(states_dir):
            messagebox.showerror("Error", "history/states directory not found.")
            return

        state_ids = []
        for filename in os.listdir(states_dir):
            if not filename.endswith('.txt'):
                continue
            filepath = os.path.join(states_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check owner and air_base
            if f'owner = {country_tag}' not in content:
                continue
            
            air_base_match = re.search(r'air_base\s*=\s*(\d+)', content)
            if not air_base_match or int(air_base_match.group(1)) < 1:
                continue

            # Extract state ID
            id_match = re.search(r'id\s*=\s*(\d+)', content)
            if id_match:
                state_ids.append(id_match.group(1))

        if not state_ids:
            messagebox.showerror("Error", f"No states found with owner={country_tag} and air_base >= 1.")
            return

        # Select airbases to use
        total_airbases = len(state_ids)
        min_selected = max(1, int(total_airbases * 0.5))
        max_selected = min(total_airbases, int(total_airbases * 0.75))
        selected_count = random.randint(min_selected, max_selected)
        selected_airbases = random.sample(state_ids, selected_count)

        # Distribute planes
        air_wings = defaultdict(list)
        for plane_type, amount in plane_entries:
            state = random.choice(selected_airbases)
            air_wings[state].append((plane_type, amount))

        # Create output file
        units_dir = os.path.join(mod_root, 'history', 'units')
        os.makedirs(units_dir, exist_ok=True)
        output_path = os.path.join(units_dir, f'{country_tag}_1936_air.txt')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('air_wings = {\n')
            for state_id, planes in air_wings.items():
                f.write(f'\t{state_id} = {{\n')
                for plane_type, amount in planes:
                    f.write(f'\t\t{plane_type} = {{ owner = "{country_tag}" amount = {amount} }}\n')
                f.write('\t}\n')
            f.write('}\n')

        messagebox.showinfo("Success", f"Air wings created in {output_path}")

        #Add to country file
        countries_dir = "history/countries"
        country_file_path = None
        for filename in os.listdir(countries_dir):
            if filename.startswith(country_tag):
                country_file_path = os.path.join(countries_dir, filename)
                break

        if country_file_path:
            with open(country_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            with open(country_file_path, 'w', encoding='utf-8') as file:
                for line in lines:
                    file.write(line)
                    if line.startswith("set_oob =") or line.startswith("oob ="):
                        file.write(f"set_air_oob = \"{country_tag}_1936_air\"\n")

    confirm_button = ttk.Button(root, text="Confirm", command=on_confirm)
    confirm_button.grid(row=2, column=0, columnspan=2, pady=5)

    root.mainloop()

if __name__ == '__main__':
    create_gui()