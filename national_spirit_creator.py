#!/usr/bin/env python3
"""
HoI4 National Spirit Creator with Modifier Autocomplete
-------------------------------------------------------
1. Same functionalities (ideas, loc, GFX, history).
2. When typing in the 'Modifiers' textbox, a small popup shows suggestions
   from a large list if your current typed word matches the start of any known modifier.

Usage:
- Place this script in your mod’s root folder (beside common/, localisation/, etc.).
- Have Python 3 installed, run 'python <this_script>.py'.
- Fill out the fields, type partial modifiers in the "Modifiers" box to see suggestions.

Autocomplete Behavior:
- Triggered on <KeyRelease> event in the modifiers text widget.
- The script finds the "current word" near the cursor. Then it filters suggestions
  that start with that word. A Toplevel with a Listbox is displayed. Click an item
  to insert it. 
- This is a simplified approach, not a fully robust IDE-like solution.
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox


def insert_gfx_section(content, section, block):
    """Insert a definition before the next ownership section comment."""
    line_ending = "\r\n" if "\r\n" in content else "\n"
    marker = re.search(rf"(?mi)^[ \t]*# {re.escape(section)}[ \t]*\r?$", content)
    normalized_block = block.replace("\r\n", "\n").replace("\r", "\n").replace("\n", line_ending)
    if marker:
        next_section = re.search(r"(?mi)^[ \t]*# [A-Z][A-Z ]*[ \t]*\r?$", content[marker.end():])
        position = marker.end() + next_section.start() if next_section else content.rfind("}")
        return content[:position] + line_ending + normalized_block + line_ending + content[position:]
    position = content.rfind("}")
    return content[:position] + line_ending + f"\t# {section}" + line_ending + normalized_block + line_ending + content[position:]

# ---------------------------------------------------------------------------
# Large list of possible HOI4 modifiers (for the 'modifier =' block).
# You can trim or add more as needed.
# ---------------------------------------------------------------------------
# We'll load from 'modifiers_list.txt' in the same folder as the script.
def load_modifiers_list(filename="modifiers_list.txt"):
    """Returns a list of modifiers from the given text file."""
    modifiers = []
    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found, no modifiers loaded.")
        return modifiers
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            modifiers.append(line)
    return modifiers

SUGGESTED_MODIFIERS = load_modifiers_list("modifiers_list.txt")

# Adjust paths for your mod structure:
COMMON_IDEAS_DIR       = os.path.join("common", "ideas")
LOCALISATION_DIR       = os.path.join("localisation", "english")
INTERFACE_DIR          = os.path.join("interface")
ICONS_DIR              = os.path.join("gfx", "interface", "ideas")
HISTORY_COUNTRIES_DIR  = os.path.join("history", "countries")

class NationalSpiritCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HoI4 National Spirit Creator (with Modifier Autocomplete)")

        # Basic GUI variables
        self.country_tag_var        = tk.StringVar()
        self.spirit_id_var          = tk.StringVar()
        self.spirit_name_var        = tk.StringVar()
        self.spirit_desc_var        = tk.StringVar()

        self.include_modifiers_var       = tk.BooleanVar(value=True)
        self.modifiers_text_widget       = None

        self.include_research_bonus_var  = tk.BooleanVar(value=False)
        self.research_bonus_text_widget  = None

        self.include_equipment_bonus_var = tk.BooleanVar(value=False)
        self.equipment_bonus_text_widget = None

        self.use_custom_gfx_var     = tk.BooleanVar(value=False)
        self.picture_override_var   = tk.StringVar()
        self.custom_image_path      = None

        self.present_at_start_var   = tk.BooleanVar(value=False)

        # We'll store the autocomplete popup references
        self.popup_window           = None
        self.listbox_widget         = None

        self.create_widgets()

    def create_widgets(self):
        # Info
        frm_info = tk.LabelFrame(self.root, text="National Spirit Info", padx=5, pady=5)
        frm_info.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        tk.Label(frm_info, text="Country TAG:").grid(row=0, column=0, sticky="w")
        tk.Entry(frm_info, textvariable=self.country_tag_var, width=5).grid(row=0, column=1, sticky="w")

        tk.Label(frm_info, text="Spirit ID:").grid(row=1, column=0, sticky="w")
        tk.Entry(frm_info, textvariable=self.spirit_id_var, width=25).grid(row=1, column=1, sticky="w")

        tk.Label(frm_info, text="Spirit Name:").grid(row=2, column=0, sticky="w")
        tk.Entry(frm_info, textvariable=self.spirit_name_var, width=30).grid(row=2, column=1, sticky="w")

        tk.Label(frm_info, text="Spirit Desc:").grid(row=3, column=0, sticky="nw")
        self.spirit_desc_text = tk.Text(frm_info, width=40, height=10)
        self.spirit_desc_text.grid(row=3, column=1, sticky="w", padx=5)

        tk.Checkbutton(frm_info, text="Present at game start?", variable=self.present_at_start_var)\
            .grid(row=4, column=0, columnspan=2, sticky="w")

        # Idea blocks
        frm_blocks = tk.LabelFrame(self.root, text="Idea Blocks", padx=5, pady=5)
        frm_blocks.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Modifiers
        tk.Checkbutton(frm_blocks, text="Include 'modifier = {}'?", variable=self.include_modifiers_var)\
            .grid(row=0, column=0, sticky="w")
        self.modifiers_text_widget = tk.Text(frm_blocks, width=50, height=3)
        self.modifiers_text_widget.grid(row=1, column=0, padx=5, pady=2)

        # -- Bind key release to show suggestions
        self.modifiers_text_widget.bind("<KeyRelease>", self.on_key_release_modifiers)

        # research_bonus
        tk.Checkbutton(frm_blocks, text="Include 'research_bonus = {}'?", variable=self.include_research_bonus_var)\
            .grid(row=2, column=0, sticky="w")
        self.research_bonus_text_widget = tk.Text(frm_blocks, width=50, height=3)
        self.research_bonus_text_widget.grid(row=3, column=0, padx=5, pady=2)

        # equipment_bonus
        tk.Checkbutton(frm_blocks, text="Include 'equipment_bonus = {}'?", variable=self.include_equipment_bonus_var)\
            .grid(row=4, column=0, sticky="w")
        self.equipment_bonus_text_widget = tk.Text(frm_blocks, width=50, height=4)
        self.equipment_bonus_text_widget.grid(row=5, column=0, padx=5, pady=2)

        # GFX
        frm_gfx = tk.LabelFrame(self.root, text="Custom GFX", padx=5, pady=5)
        frm_gfx.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        tk.Checkbutton(frm_gfx, text="Use custom GFX?", variable=self.use_custom_gfx_var)\
            .grid(row=0, column=0, sticky="w")

        tk.Label(frm_gfx, text="(Optional) picture override:").grid(row=1, column=0, sticky="w")
        tk.Entry(frm_gfx, textvariable=self.picture_override_var, width=25).grid(row=2, column=0, sticky="w")

        tk.Button(frm_gfx, text="Select Icon File...", command=self.select_icon)\
            .grid(row=3, column=0, sticky="w", padx=5, pady=5)

        # Generate
        tk.Button(self.root, text="Generate", command=self.generate)\
            .grid(row=3, column=0, sticky="e", padx=10, pady=10)

    # --------------------------- AUTOCOMPLETE LOGIC ----------------------------------
    def on_key_release_modifiers(self, event):
        """
        Called every time a key is released in the modifiers text box.
        We'll attempt to show a suggestion popup based on the last typed 'word'.
        """
        # If user turned off the modifiers block entirely, skip
        if not self.include_modifiers_var.get():
            self.close_suggestion_box()
            return

        # Get current text and find the 'word' near cursor
        cursor_index = self.modifiers_text_widget.index(tk.INSERT)
        # Convert to line/col
        line, col = cursor_index.split(".")
        line = int(line)
        col = int(col)

        # Get the content of the current line up to col
        current_line = self.modifiers_text_widget.get(f"{line}.0", f"{line}.end")
        # isolate the word near col
        word_start = col
        while word_start > 0 and not current_line[word_start-1].isspace():
            word_start -= 1
        partial_word = current_line[word_start:col]

        # If partial_word is too short or blank, hide popup
        if len(partial_word) < 1:
            self.close_suggestion_box()
            return

        # Filter suggestions
        matches = [m for m in SUGGESTED_MODIFIERS if m.startswith(partial_word)]
        if not matches:
            self.close_suggestion_box()
            return

        # Show or update the suggestions
        self.show_suggestion_box(matches, line, word_start, col)

    def show_suggestion_box(self, matches, line, word_start, col):
        """
        Show a Toplevel with a Listbox containing matches.
        We'll place it near the text widget's cursor for the current line.
        """
        # If we have an existing popup, destroy it
        self.close_suggestion_box()

        self.popup_window = tk.Toplevel(self.root)
        self.popup_window.wm_overrideredirect(True)  # no title bar
        self.popup_window.lift()
        self.popup_window.attributes("-topmost", True)

        # Create a listbox with matches
        self.listbox_widget = tk.Listbox(self.popup_window, height=min(len(matches), 8), width=50)
        self.listbox_widget.pack(side="left", fill="both", expand=True)

        for m in matches:
            self.listbox_widget.insert(tk.END, m)

        # Bind click or double-click
        self.listbox_widget.bind("<Button-1>", self.on_listbox_click)
        self.listbox_widget.bind("<Double-Button-1>", self.on_listbox_click)

        # Position the popup window near the text widget line's bounding box
        x, y = self.get_text_widget_coords(line, col)
        self.popup_window.geometry(f"+{x}+{y}")

    def close_suggestion_box(self):
        if self.popup_window is not None:
            self.popup_window.destroy()
            self.popup_window = None
            self.listbox_widget = None

    def on_listbox_click(self, event):
        """
        User clicked on a suggestion => insert/replace the partial word with the chosen text.
        """
        if not self.listbox_widget:
            return
        selection = self.listbox_widget.curselection()
        if not selection:
            return
        chosen = self.listbox_widget.get(selection[0])

        # Insert it into the text
        # We'll find the partial word again in current line and replace it
        cursor_index = self.modifiers_text_widget.index(tk.INSERT)
        line, col = cursor_index.split(".")
        line = int(line)
        col = int(col)
        current_line = self.modifiers_text_widget.get(f"{line}.0", f"{line}.end")

        word_start = int(col)
        while word_start > 0 and not current_line[word_start-1].isspace():
            word_start -= 1

        # Delete partial from word_start..col
        self.modifiers_text_widget.delete(f"{line}.{word_start}", f"{line}.{col}")
        # Insert the chosen suggestion
        self.modifiers_text_widget.insert(f"{line}.{word_start}", chosen)

        # Move cursor to end of chosen word
        new_col = word_start + len(chosen)
        self.modifiers_text_widget.mark_set(tk.INSERT, f"{line}.{new_col}")

        # close suggestions
        self.close_suggestion_box()

    def get_text_widget_coords(self, line, col):
        """
        Return the (x, y) in the root window's coordinate space
        to place our popup near the text insertion or line start.
        We'll do a naive approach: get the bounding box of the character
        if possible. If the user typed near the end, it might be None -> fallback.
        """
        bbox = self.modifiers_text_widget.bbox(f"{line}.{col}")
        if bbox is None:
            # fallback
            x = self.modifiers_text_widget.winfo_rootx()
            y = self.modifiers_text_widget.winfo_rooty() + self.modifiers_text_widget.winfo_height()
        else:
            text_x = self.modifiers_text_widget.winfo_rootx()
            text_y = self.modifiers_text_widget.winfo_rooty()
            x = text_x + bbox[0]
            y = text_y + bbox[1] + bbox[3]  # below the line
        return (x, y)

    # --------------------------- END AUTOCOMPLETE LOGIC ----------------------------------

    def select_icon(self):
        if not self.use_custom_gfx_var.get():
            messagebox.showinfo("Note", "Check 'Use custom GFX?' first.")
            return
        path = filedialog.askopenfilename(
            title="Select icon file",
            filetypes=[("Images", "*.dds *.png *.tga *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
        )
        if path:
            self.custom_image_path = path
            messagebox.showinfo("Selected Icon", f"Icon: {path}")

    def generate(self):
        # Validate
        tag = self.country_tag_var.get().strip().upper()
        if len(tag) < 3:
            messagebox.showerror("Error", "Country TAG must be at least 3 characters.")
            return
        spirit_id = self.spirit_id_var.get().strip()
        if not spirit_id:
            messagebox.showerror("Error", "Spirit ID cannot be empty.")
            return
        spirit_name = self.spirit_name_var.get().strip() or spirit_id
        spirit_desc = self.spirit_desc_text.get("1.0", "end").strip() or " "

        # Filenames
        ideas_filename = f"lok_{tag}_ideas.txt"
        loc_filename   = f"{tag}_l_english.yml"
        gfx_filename   = f"lok_country_{tag}.gfx"

        # 1) Build the idea block
        lines = [f"        {tag}_{spirit_id} = {{"]
        # If user typed a picture override, we do picture = X
        pic_override = self.picture_override_var.get().strip()
        if pic_override:
            lines.append(f"            picture = {pic_override}")

        lines.append("            allowed = { always = no }")
        lines.append("            removal_cost = -1")

        # Add modifiers if toggled
        if self.include_modifiers_var.get():
            raw_mods = self.modifiers_text_widget.get("1.0", "end").strip()
            mod_lines = [m for m in raw_mods.splitlines() if m.strip() and not m.strip().startswith("#")]
            if mod_lines:
                lines.append("            modifier = {")
                for ml in mod_lines:
                    lines.append(f"                {ml.strip()}")
                lines.append("            }")

        # research_bonus
        if self.include_research_bonus_var.get():
            raw_res = self.research_bonus_text_widget.get("1.0", "end").strip()
            res_lines = [r for r in raw_res.splitlines() if r.strip() and not r.strip().startswith("#")]
            if res_lines:
                lines.append("            research_bonus = {")
                for rl in res_lines:
                    lines.append(f"                {rl.strip()}")
                lines.append("            }")

        # equipment_bonus
        if self.include_equipment_bonus_var.get():
            raw_eq = self.equipment_bonus_text_widget.get("1.0", "end").strip()
            eq_lines = [e for e in raw_eq.splitlines() if e.strip() and not e.strip().startswith("#")]
            if eq_lines:
                lines.append("            equipment_bonus = {")
                for el in eq_lines:
                    lines.append(f"                {el.strip()}")
                lines.append("            }")

        lines.append("        }")
        new_idea_block = "\n".join(lines) + "\n"

        # 2) Insert into ideas file
        self.insert_idea_into_ideas_file(ideas_filename, new_idea_block)

        # 3) Localization
        loc_path = os.path.join(LOCALISATION_DIR, loc_filename)
        self.insert_localization(loc_path, spirit_id, tag, spirit_name, spirit_desc)

        # 4) Custom GFX
        if self.use_custom_gfx_var.get():
            self.handle_custom_gfx(tag, spirit_id, pic_override)

        # 5) If present at start, update or create history
        if self.present_at_start_var.get():
            self.update_history_file(tag, spirit_id)

        # Done
        messagebox.showinfo(
            "Done",
            f"Generated/updated '{spirit_id}' for {tag}.\n"
            f" - ideas -> {ideas_filename}\n"
            f" - loc -> {loc_filename}\n"
            + (f" - gfx -> {gfx_filename}\n" if self.use_custom_gfx_var.get() else "")
            + (" - history updated.\n" if self.present_at_start_var.get() else "")
        )

    def insert_idea_into_ideas_file(self, filename, new_block):
        """
        Ensures the new_block is inserted inside:
         ideas = {
             country = {
                 ...
                 new_block
             }
         }
        """
        full_path = os.path.join(COMMON_IDEAS_DIR, filename)
        if not os.path.exists(full_path):
            content = (
                "ideas = {\n"
                "    country = {\n"
                f"{new_block}"
                "    }\n"
                "}\n"
            )
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return

        with open(full_path, "r", encoding="utf-8") as f:
            data = f.read()

        if "ideas =" not in data:
            # Not well-formed, recreate
            content = (
                "ideas = {\n"
                "    country = {\n"
                f"{new_block}"
                "    }\n"
                "}\n"
            )
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return

        if "country = {" not in data:
            idx = data.index("ideas = {") + len("ideas = {")
            new_data = (
                data[:idx]
                + "\n    country = {\n"
                + new_block
                + "    }\n"
                + data[idx:]
            )
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_data)
            return

        # bracket matching approach
        cindex = data.index("country = {") + len("country = {")
        brace_level = 1
        i = cindex
        insert_pos = None
        while i < len(data):
            if data[i] == '{':
                brace_level += 1
            elif data[i] == '}':
                brace_level -= 1
                if brace_level == 0:
                    insert_pos = i
                    break
            i += 1

        if insert_pos is None:
            # malformed, just append
            new_data = data + "\n" + new_block
        else:
            # insert above }
            new_data = (
                data[:insert_pos].rstrip()
                + "\n"
                + new_block
                + "    "
                + data[insert_pos:]
            )

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_data)

    def insert_localization(self, loc_path, tag, spirit_id, spirit_name, spirit_desc):
        """
        Make sure we have:
         l_english:
          spirit_id: "<spirit_name>"
          spirit_id_desc: "<spirit_desc>"
        """
        name_line = f" {spirit_id}_{tag}: \"{spirit_name}\""
        desc_line = f" {spirit_id}_{tag}_desc: \"{spirit_desc}\""
        if not os.path.exists(loc_path):
            text = "l_english:\n" + name_line + "\n" + desc_line + "\n"
            with open(loc_path, "w", encoding="utf-8-sig") as f:
                f.write(text)
            return

        with open(loc_path, "r", encoding="utf-8-sig") as f:
            data = f.read()
        if "l_english:" not in data:
            data = "l_english:\n" + data
        data = data.strip() + "\n" + name_line + "\n" + desc_line + "\n"
        with open(loc_path, "w", encoding="utf-8-sig") as f:
            f.write(data)

    def handle_custom_gfx(self, tag, spirit_id, pic_override):
        """
        Copy the icon to gfx/interface/ideas/<spirit_id>.ext
        Then define/append the sprite in lok_country_<TAG>.gfx under the IDEAS section with name = GFX_idea_<spirit_id>.
        """
        gfx_file   = f"lok_country_{tag}.gfx"
        gfx_path   = os.path.join(INTERFACE_DIR, gfx_file)

        sprite_name = f"GFX_idea_{tag}_{spirit_id}"
        if self.custom_image_path:
            ext = os.path.splitext(self.custom_image_path)[1]
            final_image_name = f"{tag}_{spirit_id}{ext}"
            target_path = os.path.join(ICONS_DIR, final_image_name)
            shutil.copyfile(self.custom_image_path, target_path)
            texture_line = f"texturefile = \"gfx/interface/ideas/{final_image_name}\""
        else:
            # fallback placeholder
            texture_line = f"texturefile = \"gfx/interface/ideas/{tag}_{spirit_id}.dds\""

        new_sprite_def = (
            "    spriteType = {\n"
            f"        name = \"{sprite_name}\"\n"
            f"        {texture_line}\n"
            "    }\n"
        )

        if not os.path.exists(gfx_path):
            gfx_data = (
                "spriteTypes = {\n"
                "\t# IDEAS\n\n"
                f"{new_sprite_def}"
                "\n\t# FOCUS ICONS\n\n"
                "\t# MODIFIERS\n\n"
                "\t# ESTATES\n\n"
                "}\n"
            )
        else:
            with open(gfx_path, "r", encoding="utf-8") as f:
                gfx_data = f.read()
            if sprite_name not in gfx_data:
                gfx_data = insert_gfx_section(gfx_data, "IDEAS", new_sprite_def)

        with open(gfx_path, "w", encoding="utf-8") as f:
            f.write(gfx_data)

    def update_history_file(self, tag, spirit_id):
        """
        Insert or merge:
          add_ideas = { <spirit_id> }
        right after 'set_convoys' line if found, else at the end.
        If an add_ideas block exists, just merge new spirit.
        """
        found_file = None
        if os.path.isdir(HISTORY_COUNTRIES_DIR):
            for fn in os.listdir(HISTORY_COUNTRIES_DIR):
                if fn.lower().startswith(tag.lower()):
                    found_file = os.path.join(HISTORY_COUNTRIES_DIR, fn)
                    break

        if not found_file:
            # create a new one
            new_name = f"{tag} - Generated.txt"
            found_file = os.path.join(HISTORY_COUNTRIES_DIR, new_name)
            lines = [
                f"# Generated history for {tag}\n",
                "set_convoys = 10\n",  # optional baseline
                "add_ideas = {\n",
                f"    {tag}_{spirit_id}\n",
                "}\n"
            ]
            with open(found_file, "w", encoding="utf-8") as f:
                f.write("".join(lines))
            return

        with open(found_file, "r", encoding="utf-8") as f:
            old_lines = f.readlines()

        in_add_ideas = False
        add_ideas_found = False
        inserted_idea = False
        set_convoys_index = None

        # find 'set_convoys'
        for i, line in enumerate(old_lines):
            if "set_convoys" in line.strip().replace(" ", ""):
                set_convoys_index = i

        new_lines = []
        for i, line in enumerate(old_lines):
            stripped = line.strip()

            # detect an add_ideas block
            if not in_add_ideas and "add_ideas" in stripped and "{" in stripped:
                in_add_ideas = True
                add_ideas_found = True
                new_lines.append(line)
                continue

            if in_add_ideas:
                if "}" in stripped:
                    # before closing, insert new spirit if not found
                    if not inserted_idea:
                        new_lines.append(f"    {spirit_id}\n")
                        inserted_idea = True
                    in_add_ideas = False
                    new_lines.append(line)
                else:
                    if spirit_id in stripped:
                        inserted_idea = True
                    new_lines.append(line)
                continue

            new_lines.append(line)

        # if no add_ideas block found
        if not add_ideas_found:
            block = [
                "add_ideas = {\n",
                f"    {tag}_{spirit_id}\n",
                "}\n"
            ]
            if set_convoys_index is not None:
                # Insert *after* the set_convoys line
                final_lines = []
                for idx, line in enumerate(new_lines):
                    final_lines.append(line)
                    if idx == set_convoys_index:
                        final_lines.extend(block)
                new_lines = final_lines
            else:
                new_lines.append("\n")
                new_lines.extend(block)
        else:
            # if found but not inserted => it was already in the file
            pass

        with open(found_file, "w", encoding="utf-8") as f:
            f.write("".join(new_lines))

def main():
    root = tk.Tk()
    app = NationalSpiritCreatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
