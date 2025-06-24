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
TIER_VALUES = {1: 1, 2: 3, 3: 5, 4: 10, 5: 15, 6: 20, 7: 30, 8: 40}
TIER_DEFAULT_WEIGHTS = {1: 30, 2: 30, 3: 20, 4: 10, 5: 0, 6: 0, 7: 0, 8: 0}

TERRAIN_DEFAULT_MODIFIERS = {
    "plains": 1,
    "forest": 0,
    "hills": 0,
    "mountain": -2,
    "desert": -1,
    "marsh": -1,
    "frozen": -2,
    "volcanic": -3,
    "urban": 4,
}
TERRAIN_TYPES = list(TERRAIN_DEFAULT_MODIFIERS.keys())

INFRA_DEFAULT_MODIFIERS = {0: -2, 1: -1, 2: -1, 3: 0, 4: 0, 5: 1}

STATE_FOLDER = os.path.join("history", "states")
DEFINITION_CSV = os.path.join("map", "definition.csv")
PROVINCE_BMP = os.path.join("map", "provinces.bmp")
LOCALISATION_FILE = os.path.join("localisation", "english", "victory_points_l_english.yml")

STATE_ID_REGEX = re.compile(r"^\s*id\s*=\s*(\d+)")
OWNER_REGEX = re.compile(r"owner\s*=\s*(\w{3})")
PROVINCES_BLOCK_REGEX = re.compile(r"provinces\s*=\s*\{([^}]*)\}", re.S)
VP_LINE_REGEX = re.compile(r"victory_points\s*=\s*\{\s*(\d+)\s+\d+\s*\}")
INFRA_REGEX = re.compile(r"infrastructure\s*=\s*(\d+)")

# -----------------------------
#  FILE & MAP UTILITIES
# -----------------------------

def list_state_files(mod_root: str):
    folder = os.path.join(mod_root, STATE_FOLDER)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]


def get_state_info(path: str):
    """Return dict with id, owner, provinces(list[int]), vp_provinces(set[int]), infrastructure(int), path"""
    with open(path, 'r', encoding='utf-8') as fh:
        data = fh.read()
    state_id = int(STATE_ID_REGEX.search(data).group(1)) if STATE_ID_REGEX.search(data) else None
    owner = OWNER_REGEX.search(data).group(1) if OWNER_REGEX.search(data) else None
    provinces_block = PROVINCES_BLOCK_REGEX.search(data)
    provinces = [int(p) for p in provinces_block.group(1).split() if p.isdigit()] if provinces_block else []
    vp_provs = {int(m.group(1)) for m in VP_LINE_REGEX.finditer(data)}
    infra_match = INFRA_REGEX.search(data)
    infrastructure = int(infra_match.group(1)) if infra_match else 0
    return {
        "id": state_id,
        "owner": owner,
        "provinces": provinces,
        "vp_provinces": vp_provs,
        "infrastructure": infrastructure,
        "path": path,
    }


def definition_lookup(mod_root: str):
    """Return (lookup dict, color→pid dict). Each lookup entry holds coastal flag, RGB colour and terrain."""
    def_path = os.path.join(mod_root, DEFINITION_CSV)
    lookup, color2pid = {}, {}
    with open(def_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            parts = line.rstrip().split(';')
            if len(parts) < 7:
                continue
            pid = int(parts[0])
            r, g, b = map(int, parts[1:4])
            coastal = parts[5].lower() == 'true'
            terrain = parts[6].strip().lower()
            lookup[pid] = {"coastal": coastal, "color": (r, g, b), "terrain": terrain}
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

def weighted_random_tier(weights: dict, rng: random.Random):
    pool = []
    for tier, w in weights.items():
        pool.extend([tier] * w)
    return rng.choice(pool)


def calc_num_vps(num_provinces: int, ratio: int, min_vp: int, max_vp: int):
    nom = (num_provinces + ratio - 1) // ratio  # ceil division
    return max(min_vp, min(max_vp, nom))


def pick_provinces_no_adj(available, need, all_vp_set, neighbor_map, rng):
    """Pick provinces ensuring none borders an existing or newly‑picked VP."""
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
        if len(chosen) == need:
            break
    return chosen

# -----------------------------
#  FILE WRITING ROUTINES
# -----------------------------

def append_lines_to_state(path: str, vp_entries: list, building_entries: list):
    """
    Append new Victory Point entries and province‑specific building blocks to a state
    history file **without** duplicating the `buildings` block.

    Rules implemented:
    * If a `buildings = { ... }` block already exists inside the state's `history`
      section, the new province‑level building definitions are inserted *inside*
      that block, just before its closing brace.
    * If no such block exists, we create one (previous behaviour).
    * New `victory_points = { <PID> <VALUE> }` lines are inserted immediately
      before the `buildings` block when it exists, or right before the closing
      brace of the `history` block otherwise.
    * Original indentation is preserved so the file stays tidy and readable.
    """
    import re

    # --- Read state file ---
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # --------------------------------------------------
    # Locate the history block (start & end line indices)
    # --------------------------------------------------
    hist_start = None
    brace_level = 0
    for idx, ln in enumerate(lines):
        if hist_start is None and re.search(r"\bhistory\b", ln) and "{" in ln:
            hist_start = idx
            brace_level = ln.count("{") - ln.count("}")
            continue
        if hist_start is not None:
            brace_level += ln.count("{") - ln.count("}")
            if brace_level == 0:
                hist_end = idx  # this line contains the '}' that closes history
                break
    else:
        raise ValueError(f"Could not locate history block in {path}")

    # ----------------------------------------------------------------
    # Locate an existing buildings block *inside* the history section.
    # ----------------------------------------------------------------
    bld_start = bld_end = None
    brace = 0
    for idx in range(hist_start + 1, hist_end):
        if bld_start is None and re.match(r"\s*buildings\s*=\s*\{", lines[idx]):
            bld_start = idx
            brace = lines[idx].count("{") - lines[idx].count("}")
            continue
        if bld_start is not None:
            brace += lines[idx].count("{") - lines[idx].count("}")
            if brace == 0:
                bld_end = idx  # line with the brace that closes buildings
                break

    # -----------------------------------
    # Prepare Victory Point (VP) entries.
    # -----------------------------------
    # Determine proper indentation for VP lines: reuse the indent of the first
    # existing VP line if present; otherwise fall back to two tabs ("\t\t").
    vp_indent = "\t\t"
    for ln in lines[hist_start:hist_end]:
        if "victory_points" in ln:
            vp_indent = re.match(r"^(\s*)", ln).group(1)
            break
    if bld_start is not None and vp_indent == "\t\t":
        # if no existing VP lines but we *do* have a buildings block, align VPs
        # with that block's indentation.
        vp_indent = re.match(r"^(\s*)", lines[bld_start]).group(1)

    vp_lines = [f"{vp_indent}victory_points = {{ {pid} {val} }}\n" for pid, val in vp_entries]

    # ---------------------------------------
    # Insert building entries *first* so that
    # subsequent VP insertion indices remain
    # easy to reason about.
    # ---------------------------------------
    if building_entries:
        if bld_start is not None and bld_end is not None:
            # Insert inside existing block, before its closing brace.
            base_indent = re.match(r"^(\s*)", lines[bld_start]).group(1) + "\t"
            insert_idx = bld_end  # right **before** the closing brace
            new_bld_lines = []
            for pid, bd in building_entries:
                new_bld_lines.append(f"{base_indent}{pid} = {{\n")
                for k, v in bd.items():
                    new_bld_lines.append(f"{base_indent}\t{k} = {v}\n")
                new_bld_lines.append(f"{base_indent}}}\n")
            lines[insert_idx:insert_idx] = new_bld_lines
            # Adjust bld_end so VP insertion (coming next) is still correct
            bld_end += len(new_bld_lines)
        else:
            # No buildings block yet; we will create one right before history's
            # closing brace after we deal with VP lines.
            pass  # handled later

    # ------------------------------------
    # Insert VP lines at the correct spot.
    # ------------------------------------
    if vp_lines:
        vp_insert_idx = bld_start if bld_start is not None else hist_end
        lines[vp_insert_idx:vp_insert_idx] = vp_lines
        # If we inserted before bld_start, shift indices so later code remains
        # consistent (only needed if a buildings block exists but we *didn't*
        # have one at function entry, which is handled above).
        if bld_start is not None:
            bld_start += len(vp_lines)
            bld_end += len(vp_lines)

    # -------------------------------------------------------------
    # If there *wasn't* a buildings block and we *still* have pending
    # building entries, create a new one now (original behaviour).
    # -------------------------------------------------------------
    if building_entries and bld_start is None:
        new_bld_lines = [f"{vp_indent}buildings = {{\n"]
        for pid, bd in building_entries:
            new_bld_lines.append(f"{vp_indent}\t{pid} = {{\n")
            for k, v in bd.items():
                new_bld_lines.append(f"{vp_indent}\t\t{k} = {v}\n")
            new_bld_lines.append(f"{vp_indent}\t}}\n")
        new_bld_lines.append(f"{vp_indent}}}\n")
        lines[hist_end:hist_end] = new_bld_lines

    # --- Write back to disk ---
    with open(path, "w", encoding="utf-8") as fh:
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
        self.title("HOI4 Victory Point Seeder v3")
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

        # VP Tier weights
        self.tier_weight_vars = {tier: tk.IntVar(value=w) for tier, w in TIER_DEFAULT_WEIGHTS.items()}
        tw_frame = ttk.Frame(vp_frame)
        tw_frame.grid(row=1, column=0, columnspan=6, pady=4)
        col = 0
        for tier in range(1, 9):
            label = f"T{tier} ({TIER_VALUES[tier]})"
            ttk.Label(tw_frame, text=label).grid(row=0, column=col, sticky="w")
            ttk.Entry(tw_frame, textvariable=self.tier_weight_vars[tier], width=3).grid(row=0, column=col + 1)
            col += 2

        # -------- Terrain Options --------
        terrain_frame = ttk.LabelFrame(self, text="Terrain Modifiers & Rules")
        terrain_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.vary_terrain_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(terrain_frame, text="Vary tier based on terrain", variable=self.vary_terrain_var).grid(row=0, column=0, sticky="w")
        self.force_urban_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(terrain_frame, text="Force VPs on urban tiles", variable=self.force_urban_var).grid(row=0, column=1, sticky="w")

        # Terrain modifier entries and forbid checkboxes
        self.terrain_mod_vars = {}
        self.terrain_forbid_vars = {}
        row = 1
        for terr in TERRAIN_TYPES:
            self.terrain_mod_vars[terr] = tk.IntVar(value=TERRAIN_DEFAULT_MODIFIERS.get(terr, 0))
            self.terrain_forbid_vars[terr] = tk.BooleanVar(value=False)
            ttk.Label(terrain_frame, text=terr.capitalize()).grid(row=row, column=0, sticky="e")
            ttk.Entry(terrain_frame, textvariable=self.terrain_mod_vars[terr], width=3).grid(row=row, column=1)
            ttk.Checkbutton(terrain_frame, text="forbid", variable=self.terrain_forbid_vars[terr]).grid(row=row, column=2, sticky="w")
            row += 1

        # -------- Infrastructure Options --------
        infra_frame = ttk.LabelFrame(self, text="Infrastructure Modifiers")
        infra_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.use_infra_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(infra_frame, text="Take infrastructure into account", variable=self.use_infra_var).grid(row=0, column=0, sticky="w")
        self.infra_mod_vars = {}
        for lvl in range(6):
            self.infra_mod_vars[lvl] = tk.IntVar(value=INFRA_DEFAULT_MODIFIERS.get(lvl, 0))
            ttk.Label(infra_frame, text=f"Level {lvl}:").grid(row=lvl + 1, column=0, sticky="e")
            ttk.Entry(infra_frame, textvariable=self.infra_mod_vars[lvl], width=3).grid(row=lvl + 1, column=1, sticky="w")

        # -------- Building Options --------
        build_frame = ttk.LabelFrame(self, text="Buildings")
        build_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
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
        names_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.names_text = scrolledtext.ScrolledText(names_frame, height=4, width=60)
        self.names_text.pack(fill="both", expand=True)

        # -------- Execute Button --------
        ttk.Button(self, text="Execute", command=self.execute).grid(row=6, column=0, pady=10)

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

    # ---------------------------------------------------
    #  Core seeding logic
    # ---------------------------------------------------
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
        tier_weights = {t: max(0, var.get()) for t, var in self.tier_weight_vars.items()}
        if sum(tier_weights.values()) == 0:
            raise ValueError("At least one Tier weight must be > 0")
        vary_terrain = self.vary_terrain_var.get()
        terrain_mods = {t: var.get() for t, var in self.terrain_mod_vars.items()}
        forbid_terrain = {t: var.get() for t, var in self.terrain_forbid_vars.items()}
        force_urban = self.force_urban_var.get()
        use_infra = self.use_infra_var.get()
        infra_mods = {lvl: var.get() for lvl, var in self.infra_mod_vars.items()}

        names_pool = re.findall(r"\"([^\"]+)\"", self.names_text.get("1.0", tk.END))
        if not names_pool:
            raise ValueError("No names in pool")
        name_iter = iter(names_pool)

        vp_localisations, rng = {}, self.rng
        all_vp_set = set().union(*(s["vp_provinces"] for s in selected))

        # --- Process each state ---
        for state in selected:
            # Filter provinces
            avail = [pid for pid in state["provinces"] if pid not in state["vp_provinces"]]
            avail = [pid for pid in avail if not forbid_terrain.get(def_lookup[pid]["terrain"], False)]
            if not avail:
                continue

            need = calc_num_vps(len(state["provinces"]), ratio, min_vp, max_vp)
            chosen = []

            # Force urban provinces first if requested
            if force_urban:
                urban_provs = [pid for pid in avail if def_lookup[pid]["terrain"] == "urban"]
                for pid in urban_provs:
                    if pid in all_vp_set:
                        continue
                    chosen.append(pid)
                    all_vp_set.add(pid)

            remaining_need = max(0, need - len([p for p in chosen if p not in state["vp_provinces"]]))
            # Pick remaining with adjacency rule
            if remaining_need > 0:
                cand = [pid for pid in avail if pid not in chosen]
                chosen.extend(pick_provinces_no_adj(cand, remaining_need, all_vp_set, neighbor_map, rng))

            vp_entries, building_entries = [], []
            for pid in chosen:
                # Roll base tier
                tier = weighted_random_tier(tier_weights, rng)
                # Apply terrain modifier
                terrain = def_lookup[pid]["terrain"]
                if vary_terrain:
                    tier += terrain_mods.get(terrain, 0)
                # Apply infra modifier
                if use_infra:
                    lvl = max(0, min(5, state["infrastructure"]))
                    tier += infra_mods.get(lvl, 0)
                tier = max(1, min(8, tier))
                value = TIER_VALUES[tier]

                vp_entries.append((pid, value))

                # Buildings
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

                # Localisation name assignment
                try:
                    name = next(name_iter)
                except StopIteration:
                    name = "REPLACE_ME"
                vp_localisations[pid] = name

            if vp_entries:
                append_lines_to_state(state['path'], vp_entries, building_entries)

        # --- Localisation ---
        append_localisation(mod_root, vp_localisations)

# -----------------------------
#  ENTRY POINT
# -----------------------------
if __name__ == '__main__':
    VPSeederGUI().mainloop()
