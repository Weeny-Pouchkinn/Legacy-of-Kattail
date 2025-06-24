import os
import re
import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import defaultdict

# Pillow is required for reading provinces.bmp
try:
    from PIL import Image
except ImportError as exc:
    raise ImportError("Pillow is required (pip install pillow)") from exc

# -----------------------------
#  CONSTANTS & REGEXES
# -----------------------------
VP_DEFAULT_WEIGHTS = {1: 50, 3: 20, 5: 10, 10: 5, 20: 1}
STATE_FOLDER = os.path.join("history", "states")
DEFINITION_CSV = os.path.join("map", "definition.csv")
PROVINCE_BMP = os.path.join("map", "provinces.bmp")
LOCALISATION_FILE = os.path.join("localisation", "english", "victory_points_l_english.yml")

STATE_ID_REGEX = re.compile(r"^\s*id\s*=\s*(\d+)")
OWNER_REGEX = re.compile(r"owner\s*=\s*(\w{3})")
PROVINCES_BLOCK_REGEX = re.compile(r"provinces\s*=\s*\{([^}]*)\}", re.S)
VP_LINE_REGEX = re.compile(r"victory_points\s*=\s*\{\s*(\d+)\s+\d+\s*\}")

# -----------------------------
#  FILE & MAP UTILITIES
# -----------------------------

def list_state_files(mod_root: str):
    folder = os.path.join(mod_root, STATE_FOLDER)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]


def get_state_info(path: str):
    """Return dict with id, owner, provinces(list[int]), vp_provinces(set[int]), path"""
    with open(path, 'r', encoding='utf-8') as fh:
        data = fh.read()
    state_id = int(STATE_ID_REGEX.search(data).group(1)) if STATE_ID_REGEX.search(data) else None
    owner = OWNER_REGEX.search(data).group(1) if OWNER_REGEX.search(data) else None
    provinces_block = PROVINCES_BLOCK_REGEX.search(data)
    provinces = [int(p) for p in provinces_block.group(1).split() if p.isdigit()] if provinces_block else []
    vp_provs = {int(m.group(1)) for m in VP_LINE_REGEX.finditer(data)}
    return {"id": state_id, "owner": owner, "provinces": provinces, "vp_provinces": vp_provs, "path": path}


def definition_lookup(mod_root: str):
    """Return (lookup dict, color→pid dict). Each lookup entry holds coastal flag and RGB colour."""
    def_path = os.path.join(mod_root, DEFINITION_CSV)
    lookup, color2pid = {}, {}
    with open(def_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            parts = line.rstrip().split(';')
            if len(parts) < 6:
                continue
            pid = int(parts[0])
            r, g, b = map(int, parts[1:4])
            coastal = parts[5].lower() == 'true'
            lookup[pid] = {"coastal": coastal, "color": (r, g, b)}
            color2pid[(r, g, b)] = pid
    return lookup, color2pid


def build_neighbor_map(mod_root: str, color2pid: dict):
    """Scan provinces.bmp and build adjacency map of provinceID → set(neighbour IDs)."""
    bmp_path = os.path.join(mod_root, PROVINCE_BMP)
    img = Image.open(bmp_path).convert('RGB')
    w, h = img.size
    pix = img.load()
    neigh = defaultdict(set)
    for y in range(h):
        for x in range(w):
            c1 = pix[x, y]
            pid1 = color2pid.get(c1)
            if pid1 is None:
                continue
            if x > 0:
                c2 = pix[x - 1, y]
                if c2 != c1:
                    pid2 = color2pid.get(c2)
                    if pid2:
                        neigh[pid1].add(pid2)
                        neigh[pid2].add(pid1)
            if y > 0:
                c2 = pix[x, y - 1]
                if c2 != c1:
                    pid2 = color2pid.get(c2)
                    if pid2:
                        neigh[pid1].add(pid2)
                        neigh[pid2].add(pid1)
    return neigh

# -----------------------------
#  VP CALCULATION HELPERS
# -----------------------------

def weighted_random_vp(weights: dict, rng: random.Random):
    pool = []
    for val, w in weights.items():
        pool.extend([val] * w)
    return rng.choice(pool)


def calc_num_vps(num_provinces: int, ratio: int, min_vp: int, max_vp: int):
    nom = (num_provinces + ratio - 1) // ratio  # ceil division
    return max(min_vp, min(max_vp, nom))


def pick_provinces_no_adj(state, num_vps, all_vp_set, neighbor_map, rng):
    """Pick provinces ensuring none borders an existing or newly‑picked VP."""
    available = list(set(state["provinces"]) - state["vp_provinces"])
    rng.shuffle(available)
    chosen = []
    for pid in available:
        if pid in all_vp_set:
            continue
        if any((n in all_vp_set) for n in neighbor_map.get(pid, [])):
            continue
        if any((n in chosen) for n in neighbor_map.get(pid, [])):
            continue
        chosen.append(pid)
        all_vp_set.add(pid)
        if len(chosen) == num_vps:
            break
    return chosen

# -----------------------------
#  FILE WRITING ROUTINES
# -----------------------------

def append_lines_to_state(path: str, vp_entries: list, building_entries: list):
    with open(path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()

    history_start, brace_level = None, 0
    for idx, line in enumerate(lines):
        if 'history' in line and '{' in line:
            history_start = idx
            brace_level = line.count('{') - line.count('}')
            continue
        if history_start is not None:
            brace_level += line.count('{') - line.count('}')
            if brace_level == 0:
                insert_idx = idx
                break
    else:
        messagebox.showwarning("Parsing error", f"Could not locate history block in {path}")
        return

    insertion = []
    for pid, value in vp_entries:
        insertion.append(f"\t\tvictory_points = {{ {pid} {value} }}\n")
    if building_entries:
        insertion.append("\t\tbuildings = {\n")
        for pid, bd in building_entries:
            insertion.append(f"\t\t\t{pid} = {{\n")
            for k, v in bd.items():
                insertion.append(f"\t\t\t\t{k} = {v}\n")
            insertion.append("\t\t\t}\n")
        insertion.append("\t\t}\n")

    lines[insert_idx:insert_idx] = insertion
    with open(path, 'w', encoding='utf-8') as fh:
        fh.writelines(lines)


def append_localisation(mod_root: str, vp_localisations: dict):
    loc_path = os.path.join(mod_root, LOCALISATION_FILE)
    existing = set()
    if os.path.exists(loc_path):
        with open(loc_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                m = re.match(r"VICTORY_POINTS_(\d+):0\s+\"(.+)\"", line)
                if m:
                    existing.add(m.group(2))

    with open(loc_path, 'a', encoding='utf-8') as fh:
        for pid, name in vp_localisations.items():
            base = name
            idx = 1
            while name in existing:
                name = f"{base}_{idx}"
                idx += 1
            fh.write(f" VICTORY_POINTS_{pid}:0 \"{name}\"\n")
            existing.add(name)

# -----------------------------
#  GUI IMPLEMENTATION
# -----------------------------
class VPSeederGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HOI4 Victory Point Seeder")
        self.resizable(False, False)
        self.rng = random.Random()

        # -------- Scope Selection --------
        self.mode_var = tk.StringVar(value="Country-Wide")
        scope_frame = ttk.LabelFrame(self, text="Select Scope")
        scope_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        ttk.OptionMenu(scope_frame, self.mode_var, "Country-Wide", "Country-Wide", "State-Specific", command=self._toggle_mode).pack(side="left", padx=5)
        self.extra_entry = ttk.Entry(scope_frame, width=30)
        self.extra_entry.pack(side="left", padx=5)
        self.extra_entry.insert(0, "e.g. KTZ or 12 34 56")

        # -------- VP Settings --------
        vp_frame = ttk.LabelFrame(self, text="VP Settings")
        vp_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.min_vp_var, self.max_vp_var, self.ratio_var = tk.IntVar(value=1), tk.IntVar(value=5), tk.IntVar(value=10)
        ttk.Label(vp_frame, text="Min VPs:").grid(row=0, column=0, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.min_vp_var, width=5).grid(row=0, column=1)
        ttk.Label(vp_frame, text="Max VPs:").grid(row=0, column=2, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.max_vp_var, width=5).grid(row=0, column=3)
        ttk.Label(vp_frame, text="Province/VP ratio:").grid(row=0, column=4, sticky="e")
        ttk.Entry(vp_frame, textvariable=self.ratio_var, width=5).grid(row=0, column=5)

        # VP value weights
        self.weight_vars = {v: tk.IntVar(value=w) for v, w in VP_DEFAULT_WEIGHTS.items()}
        w_frame = ttk.Frame(vp_frame)
        w_frame.grid(row=1, column=0, columnspan=6, pady=4)
        col = 0
        for val in sorted(self.weight_vars):
            ttk.Label(w_frame, text=f"Weight {val}:").grid(row=0, column=col)
            ttk.Entry(w_frame, textvariable=self.weight_vars[val], width=4).grid(row=0, column=col + 1)
            col += 2

        # -------- Building Options --------
        build_frame = ttk.LabelFrame(self, text="Buildings")
        build_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.supply_var, self.bunker_var, self.cbunker_var, self.port_var = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        self.bunker_lvl, self.cbunker_lvl, self.port_lvl = tk.IntVar(value=0), tk.IntVar(value=0), tk.IntVar(value=0)
        ttk.Checkbutton(build_frame, text="Add supply hub", variable=self.supply_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(build_frame, text="Add bunkers", variable=self.bunker_var).grid(row=1, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.bunker_lvl, width=3).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(build_frame, text="Add coastal bunkers", variable=self.cbunker_var).grid(row=2, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.cbunker_lvl, width=3).grid(row=2, column=1, sticky="w")
        ttk.Checkbutton(build_frame, text="Add ports", variable=self.port_var).grid(row=3, column=0, sticky="w")
        ttk.Entry(build_frame, textvariable=self.port_lvl, width=3).grid(row=3, column=1, sticky="w")

        # -------- Name Pool --------
        names_frame = ttk.LabelFrame(self, text="Name Pool (\"Name1\" \"Name2\")")
        names_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.names_text = scrolledtext.ScrolledText(names_frame, height=4, width=60)
        self.names_text.pack(fill="both", expand=True)

        # -------- Execute Button --------
        ttk.Button(self, text="Execute", command=self.execute).grid(row=4, column=0, pady=10)

    # -- Helpers --
    def _toggle_mode(self, *_):
        self.extra_entry.delete(0, tk.END)
        if self.mode_var.get() == "Country-Wide":
            self.extra_entry.insert(0, "e.g. KTZ")
        else:
            self.extra_entry.insert(0, "e.g. 12 34 56")

    def execute(self):
        try:
            self._run_seeder(os.getcwd())
            messagebox.showinfo("Success", "VP seeding complete!")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _run_seeder(self, mod_root: str):
        # --- Collect states to edit ---
        mode = self.mode_var.get()
        extra = self.extra_entry.get().strip()
        if not extra:
            raise ValueError("Please specify a country TAG or state IDs")

        state_infos = [get_state_info(p) for p in list_state_files(mod_root)]
        selected = []
        if mode == "Country-Wide":
            for info in state_infos:
                if info["owner"] == extra.upper():
                    selected.append(info)
        else:
            ids = {int(x) for x in extra.split() if x.isdigit()}
            for info in state_infos:
                if info["id"] in ids:
                    selected.append(info)
        if not selected:
            raise ValueError("No matching states found")

        # --- Map data ---
        def_lookup, color2pid = definition_lookup(mod_root)
        neighbor_map = build_neighbor_map(mod_root, color2pid)

        # --- Settings ---
        min_vp, max_vp, ratio = self.min_vp_var.get(), self.max_vp_var.get(), max(1, self.ratio_var.get())
        weights = {v: max(0, var.get()) for v, var in self.weight_vars.items()}
        if sum(weights.values()) == 0:
            raise ValueError("At least one VP weight must be > 0")
        names_pool = re.findall(r"\"([^\"]+)\"", self.names_text.get("1.0", tk.END))
        if not names_pool:
            raise ValueError("No names in pool")
        name_iter = iter(names_pool)

        vp_localisations, rng = {}, self.rng
        all_vp_set = set().union(*(s["vp_provinces"] for s in selected))

        # --- Process each state ---
        for state in selected:
            need = calc_num_vps(len(state["provinces"]), ratio, min_vp, max_vp)
            chosen = pick_provinces_no_adj(state, need, all_vp_set, neighbor_map, rng)
            vp_entries, building_entries = [], []
            for pid in chosen:
                vp_entries.append((pid, weighted_random_vp(weights, rng)))
                bd = {}
                if self.supply_var.get():
                    bd['supply_node'] = 1
                if self.bunker_var.get():
                    bd['bunker'] = self.bunker_lvl.get()
                if def_lookup.get(pid, {}).get('coastal', False):
                    if self.cbunker_var.get():
                        bd['coastal_bunker'] = self.cbunker_lvl.get()
                    if self.port_var.get():
                        bd['naval_base'] = self.port_lvl.get()
                if bd:
                    building_entries.append((pid, bd))
                try:
                    name = next(name_iter)
                except StopIteration:
                    name = "REPLACE_ME"
                vp_localisations[pid] = name
            append_lines_to_state(state['path'], vp_entries, building_entries)

        # --- Localisation ---
        append_localisation(mod_root, vp_localisations)


# -----------------------------
#  ENTRY POINT
# -----------------------------
if __name__ == '__main__':
    VPSeederGUI().mainloop()
