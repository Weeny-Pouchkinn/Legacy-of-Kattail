import os
import re
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# -----------------------------
#  CONSTANTS & HELPERS
# -----------------------------
VP_DEFAULT_WEIGHTS = {1: 50, 3: 20, 5: 10, 10: 5, 20: 1}
STATE_FOLDER = os.path.join("history", "states")
DEFINITION_CSV = os.path.join("map", "definition.csv")
LOCALISATION_FILE = os.path.join("localisation", "english", "victory_points_l_english.yml")

STATE_ID_REGEX = re.compile(r"^\s*id\s*=\s*(\d+)")
OWNER_REGEX = re.compile(r"owner\s*=\s*(\w{3})")
PROVINCES_BLOCK_REGEX = re.compile(r"provinces\s*=\s*\{([^}]*)\}", re.S)
VP_LINE_REGEX = re.compile(r"victory_points\s*=\s*\{\s*(\d+)\s+\d+\s*\}")

# -----------------------------
#  FILE PARSING UTILITIES
# -----------------------------

def list_state_files(mod_root: str):
    folder = os.path.join(mod_root, STATE_FOLDER)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]


def get_state_info(path: str):
    """Return dict with id, owner, provinces(list[int]), vp_provinces(set[int])"""
    with open(path, 'r', encoding='utf-8') as fh:
        data = fh.read()
    state_id_match = STATE_ID_REGEX.search(data)
    state_id = int(state_id_match.group(1)) if state_id_match else None
    owner_match = OWNER_REGEX.search(data)
    owner = owner_match.group(1) if owner_match else None
    provinces_block_match = PROVINCES_BLOCK_REGEX.search(data)
    provinces = []
    if provinces_block_match:
        provinces = [int(p) for p in provinces_block_match.group(1).split() if p.isdigit()]
    vp_provs = set(int(m.group(1)) for m in VP_LINE_REGEX.finditer(data))
    return {"id": state_id, "owner": owner, "provinces": provinces, "vp_provinces": vp_provs, "path": path}


def definition_lookup(mod_root: str):
    definition_path = os.path.join(mod_root, DEFINITION_CSV)
    lookup = {}
    with open(definition_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            parts = line.strip().split(';')
            if len(parts) < 6:
                continue
            pid = int(parts[0])
            coastal_flag = parts[5].lower() == 'true'
            lookup[pid] = {"coastal": coastal_flag}
    return lookup

# -----------------------------
#  VP GENERATION LOGIC
# -----------------------------

def weighted_random_vp(weights: dict):
    pool = []
    for val, w in weights.items():
        pool.extend([val] * w)
    return random.choice(pool)


def calc_num_vps(num_provinces: int, ratio: int, min_vp: int, max_vp: int):
    nom = (num_provinces + ratio - 1) // ratio  # ceil division
    return max(min_vp, min(max_vp, nom))


def pick_provinces(state, num_vps, rng):
    available = list(set(state["provinces"]) - state["vp_provinces"])
    if num_vps > len(available):
        num_vps = len(available)
    return rng.sample(available, num_vps)


def append_lines_to_state(path: str, vp_entries: list, building_entries: list):
    """Insert new lines into the history block just before its closing '}'"""
    with open(path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()

    # find last line of history block (assumes properly nested braces)
    history_start, brace_level = None, 0
    for idx, line in enumerate(lines):
        if 'history' in line and '{' in line:
            history_start = idx
            brace_level = line.count('{') - line.count('}')
            continue
        if history_start is not None:
            brace_level += line.count('{') - line.count('}')
            if brace_level == 0:
                # insert before this line
                insert_idx = idx
                break
    else:
        messagebox.showwarning("Parsing error", f"Could not locate history block in {path}")
        return

    insertion = []
    for vp in vp_entries:
        insertion.append(f"\t\tvictory_points = {{ {vp[0]} {vp[1]} }}\n")
    if building_entries:
        insertion.append("\t\tbuildings = {\n")
        for b in building_entries:
            insertion.append(f"\t\t\t{b[0]} = {{\n")
            for k, v in b[1].items():
                insertion.append(f"\t\t\t\t{k} = {v}\n")
            insertion.append("\t\t\t}\n")
        insertion.append("\t\t}\n")

    lines[insert_idx:insert_idx] = insertion

    with open(path, 'w', encoding='utf-8') as fh:
        fh.writelines(lines)


def append_localisation(mod_root: str, vp_localisations: dict):
    localisation_path = os.path.join(mod_root, LOCALISATION_FILE)
    existing_names = set()
    if os.path.exists(localisation_path):
        with open(localisation_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                match = re.match(r"VICTORY_POINTS_(\d+):0\s+\"(.+)\"", line)
                if match:
                    existing_names.add(match.group(2))

    with open(localisation_path, 'a', encoding='utf-8') as fh:
        for pid, name in vp_localisations.items():
            if name in existing_names:
                idx = 1
                new_name = f"{name}_{idx}"
                while new_name in existing_names:
                    idx += 1
                    new_name = f"{name}_{idx}"
                name = new_name
            fh.write(f" VICTORY_POINTS_{pid}:0 \"{name}\"\n")
            existing_names.add(name)

# -----------------------------
#  GUI IMPLEMENTATION
# -----------------------------
class VPSeederGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HOI4 Victory Point Seeder")
        self.resizable(False, False)
        # random generator instance
        self.rng = random.Random()

        # Section: Mode selection
        self.mode_var = tk.StringVar(value="Country-Wide")
        mode_frame = ttk.LabelFrame(self, text="Select Scope")
        mode_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        mode_menu = ttk.OptionMenu(mode_frame, self.mode_var, "Country-Wide", "Country-Wide", "State-Specific", command=self._toggle_mode)
        mode_menu.pack(side="left", padx=5, pady=5)
        self.extra_entry = ttk.Entry(mode_frame, width=30)
        self.extra_entry.pack(side="left", padx=5)
        self.extra_entry.insert(0, "e.g. KTZ or 12 34 56")

        # Section: VP settings
        vp_frame = ttk.LabelFrame(self, text="VP Settings")
        vp_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.min_vp_var = tk.IntVar(value=1)
        self.max_vp_var = tk.IntVar(value=5)
        self.ratio_var = tk.IntVar(value=10)
        ttk.Label(vp_frame, text="Min VPs per state:").grid(row=0, column=0, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.min_vp_var, width=5).grid(row=0, column=1)
        ttk.Label(vp_frame, text="Max VPs per state:").grid(row=0, column=2, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.max_vp_var, width=5).grid(row=0, column=3)
        ttk.Label(vp_frame, text="Province/VP ratio:").grid(row=0, column=4, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.ratio_var, width=5).grid(row=0, column=5)

        # VP value weights
        self.weight_vars = {val: tk.IntVar(value=w) for val, w in VP_DEFAULT_WEIGHTS.items()}
        w_frame = ttk.Frame(vp_frame)
        w_frame.grid(row=1, column=0, columnspan=6, pady=4)
        col = 0
        for val in sorted(self.weight_vars):
            ttk.Label(w_frame, text=f"Weight {val}:").grid(row=0, column=col, sticky="e")
            ttk.Entry(w_frame, textvariable=self.weight_vars[val], width=5).grid(row=0, column=col+1)
            col += 2

        # Buildings options
        build_frame = ttk.LabelFrame(self, text="Buildings")
        build_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.supply_var = tk.BooleanVar()
        ttk.Checkbutton(build_frame, text="Add supply hub", variable=self.supply_var).grid(row=0, column=0, sticky="w")

        self.bunker_var = tk.BooleanVar()
        self.bunker_lvl = tk.IntVar(value=0)
        ttk.Checkbutton(build_frame, text="Add bunkers", variable=self.bunker_var).grid(row=1, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.bunker_lvl, width=3).grid(row=1, column=1, sticky="w")

        self.cbunker_var = tk.BooleanVar()
        self.cbunker_lvl = tk.IntVar(value=0)
        ttk.Checkbutton(build_frame, text="Add coastal bunkers (coastal provs only)", variable=self.cbunker_var).grid(row=2, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.cbunker_lvl, width=3).grid(row=2, column=1, sticky="w")

        self.port_var = tk.BooleanVar()
        self.port_lvl = tk.IntVar(value=0)
        ttk.Checkbutton(build_frame, text="Add ports (coastal provs only)", variable=self.port_var).grid(row=3, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.port_lvl, width=3).grid(row=3, column=1, sticky="w")

        # Name pool
        names_frame = ttk.LabelFrame(self, text="Name Pool (each name in quotes, separated by space)")
        names_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.names_text = scrolledtext.ScrolledText(names_frame, height=4, width=60)
        self.names_text.pack(fill="both", expand=True)

        # Execute button
        exec_btn = ttk.Button(self, text="Execute", command=self.execute)
        exec_btn.grid(row=4, column=0, pady=10)

    # ---------------------------
    def _toggle_mode(self, *_):
        if self.mode_var.get() == "Country-Wide":
            self.extra_entry.delete(0, tk.END)
            self.extra_entry.insert(0, "e.g. KTZ")
        else:
            self.extra_entry.delete(0, tk.END)
            self.extra_entry.insert(0, "e.g. 12 34 56")

    # ---------------------------
    def execute(self):
        mod_root = os.getcwd()
        try:
            self._run_seeder(mod_root)
            messagebox.showinfo("Done", "VP seeding complete!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------------------
    def _run_seeder(self, mod_root):
        mode = self.mode_var.get()
        extra = self.extra_entry.get().strip()
        if not extra:
            raise ValueError("Please provide a TAG or state IDs.")

        # Gather candidate states
        state_files = list_state_files(mod_root)
        selected_states = []
        for path in state_files:
            info = get_state_info(path)
            if mode == "Country-Wide" and info["owner"] == extra.upper():
                selected_states.append(info)
            elif mode == "State-Specific":
                ids = {int(x) for x in extra.split() if x.isdigit()}
                if info["id"] in ids:
                    selected_states.append(info)

        if not selected_states:
            raise ValueError("No states matched your criteria.")

        # Definition lookup for coastal info
        def_lookup = definition_lookup(mod_root)

        # Read GUI settings
        min_vp, max_vp = self.min_vp_var.get(), self.max_vp_var.get()
        ratio = max(1, self.ratio_var.get())
        weights = {val: max(0, self.weight_vars[val].get()) for val in self.weight_vars}
        if sum(weights.values()) == 0:
            raise ValueError("At least one VP weight must be > 0.")

        names_input = self.names_text.get("1.0", tk.END).strip()
        name_pool = re.findall(r"\"([^\"]+)\"", names_input)
        if not name_pool:
            raise ValueError("Provide at least one name in the name pool.")
        name_iter = iter(name_pool)

        vp_localisations = {}

        # RNG instance ensuring reproducibility if desired
        rng = self.rng

        for state in selected_states:
            num_vps = calc_num_vps(len(state["provinces"]), ratio, min_vp, max_vp)
            chosen_provs = pick_provinces(state, num_vps, rng)
            vp_entries = []
            building_entries = []
            for pid in chosen_provs:
                vp_value = weighted_random_vp(weights)
                vp_entries.append((pid, vp_value))

                # Build building dict
                buildings = {}
                if self.supply_var.get():
                    buildings['supply_node'] = 1
                if self.bunker_var.get():
                    buildings['bunker'] = self.bunker_lvl.get()
                # Coastal-specific buildings
                if def_lookup.get(pid, {}).get('coastal', False):
                    if self.cbunker_var.get():
                        buildings['coastal_bunker'] = self.cbunker_lvl.get()
                    if self.port_var.get():
                        buildings['naval_base'] = self.port_lvl.get()
                if buildings:
                    building_entries.append((pid, buildings))

                # Localisation name
                try:
                    name = next(name_iter)
                except StopIteration:
                    name = "REPLACE_ME"
                vp_localisations[pid] = name

            # Append to state file
            append_lines_to_state(state['path'], vp_entries, building_entries)

        # Append to localisation file
        append_localisation(mod_root, vp_localisations)

# -----------------------------
#  MAIN
# -----------------------------
if __name__ == "__main__":
    gui = VPSeederGUI()
    gui.mainloop()
