import tkinter as tk
from tkinter import messagebox
import os
import re

# --- Configuration ---
# IMPORTANT: This script assumes it is run from the root directory of your HOI4 mod.
DYNAMIC_MODIFIERS_FILE = "common/dynamic_modifiers/LOK_dynamic_modifiers.txt"
LOCALISATION_DIR = "localisation/english"

def get_loc_formatting(modifier_name, value, type_str):
    """
    Applies HOI4 color codes and sign logic based on the user's rules.

    Rules derived from the user's examples:
    - GOOD changes: Use the actual sign (+/-) and color (Positive=§G, Negative=§R).
    - BAD changes (like stability_factor = -0.50 BAD -> §R+50%§!): Always use §R,
      and display the absolute value with a '+' sign.
    """
    abs_percent = abs(value * 100)
    # Format to percentage, removing trailing zeros if possible (e.g., 10.00% -> 10%)
    formatted_value = f"{abs_percent:.2f}".rstrip('0').rstrip('.') + "%"

    if type_str == "GOOD":
        if value >= 0:
            color = "§G" # Green for a positive 'good' effect
            sign = "+"
        else:
            color = "§R" # Red for a negative 'good' effect
            sign = "-"
        return f"{color}{sign}{formatted_value}§!"

    elif type_str == "BAD":
        # Based strictly on the user's example (stability_factor = -0.50 BAD -> §R+50%§!):
        # Always Red (§R), always positive sign (+), absolute value.
        color = "§R"
        sign = "+"
        return f"{color}{sign}{formatted_value}§!"
    
    return f"ERROR" # Should not be reached

def parse_modifier_input(input_text):
    """Parses the multiline modifier input."""
    parsed_modifiers = []
    lines = input_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Regex to match: [name] = [value] - [GOOD/BAD]
        # Example: political_power_gain = 0.10 - GOOD
        match = re.match(r"([\w_]+)\s*=\s*([-\d.]+)\s*-\s*(GOOD|BAD)", line, re.IGNORECASE)
        
        if not match:
            messagebox.showerror("Input Error", f"Invalid modifier line format: {line}")
            return None
        
        modifier_name, value_str, type_str = match.groups()
        
        try:
            value = float(value_str)
        except ValueError:
            messagebox.showerror("Input Error", f"Invalid numeric value in line: {line}")
            return None

        parsed_modifiers.append({
            'name': modifier_name,
            'value': value,
            'type': type_str.upper()
        })
    
    if not parsed_modifiers:
        messagebox.showerror("Input Error", "No valid modifiers were entered.")
        return None
        
    return parsed_modifiers

def update_localisation(tag, effect_name, dyn_mod_name, modifiers):
    """Generates and writes the _tt entry to the country's localization file."""
    loc_filepath = os.path.join(LOCALISATION_DIR, f"{tag}_l_english.yml")
    
    # Create directory if it doesn't exist
    os.makedirs(LOCALISATION_DIR, exist_ok=True)

    # 1. Generate the content
    tt_key = f" {effect_name}_tt:0"
    
    # Title line
    loc_lines = [
        f' "{tt_key}\\"Modify §Y${dyn_mod_name}$§! by: \\n'
    ]
    
    # Modifier lines
    for mod in modifiers:
        loc_formatting = get_loc_formatting(mod['name'], mod['value'], mod['type'])
        modifier_loc_key = f"MODIFIER_{mod['name'].upper()}"
        
        loc_lines.append(f'${modifier_loc_key}$: {loc_formatting}\\n')

    # Join lines and close the quote
    loc_value = "".join(loc_lines) + '"'

    # 2. Prepare file content
    try:
        if os.path.exists(loc_filepath):
            with open(loc_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if the file is correctly structured (e.g., starts with l_english:)
            if "l_english:" not in content:
                content = f'l_english:\n{content}'
                
            # Remove existing key if it exists to replace it
            content = re.sub(rf" {effect_name}_tt:0\s*\".*?\"", "", content, flags=re.DOTALL)
            
            # Append the new line
            content = content.strip() + '\n' + loc_value
            
        else:
            # New file content
            content = f'l_english:\n{loc_value}'
        
        # 3. Write to file
        with open(loc_filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\n')
            
        return f"Successfully updated localization: {loc_filepath}"

    except Exception as e:
        return f"ERROR updating localization: {e}"

def update_dynamic_modifiers(dyn_mod_name, modifiers):
    """Updates the dynamic modifier file with the required variable linkages."""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(DYNAMIC_MODIFIERS_FILE), exist_ok=True)

    # 1. Read file content, or create a template if it doesn't exist
    try:
        if os.path.exists(DYNAMIC_MODIFIERS_FILE):
            with open(DYNAMIC_MODIFIERS_FILE, 'r', encoding='utf-8') as f:
                content = f.readlines()
        else:
            messagebox.showinfo("Creating File", f"Creating new file: {DYNAMIC_MODIFIERS_FILE}")
            content = []
    except Exception as e:
        return f"ERROR reading dynamic modifiers file: {e}"

    # 2. Find and update the dynamic modifier block
    start_line = -1
    end_line = -1
    icon_line = -1
    
    # Target definition line (e.g., AUR_the_kaiser_must_return = {)
    target_definition = f"{dyn_mod_name} = {{ \n"

    # Find the block and the insertion point
    for i, line in enumerate(content):
        if line.strip().startswith(f"{dyn_mod_name} = {{"):
            start_line = i
        
        if start_line != -1:
            if start_line < i and 'icon' in line:
                icon_line = i
            
            # Simple check for block end
            if start_line < i and line.strip() == '}' and end_line == -1:
                end_line = i
                break

    # If the block doesn't exist, append it to the end
    if start_line == -1:
        content.append(f"\n{dyn_mod_name} = {{\n")
        content.append("\ticon = generic_focus\n") # Placeholder icon
        icon_line = len(content) - 1 # Insertion point is right after the new icon line
        # The block is added at the end, so we can just append new modifier lines
        start_line = len(content) - 2 # Start is the definition line
        end_line = len(content) # A placeholder for the end where '}' will be added later

    
    # 3. Generate new linkage lines
    new_linkage_lines = []
    
    for mod in modifiers:
        # Expected line: political_power_gain = AUR_the_kaiser_must_return_political_power_gain
        linkage_line = f"\t{mod['name']} = {dyn_mod_name}_{mod['name']}\n"
        
        # Check if the line already exists in the block
        exists = False
        for i in range(start_line + 1, end_line if end_line != len(content) else len(content)):
            if content[i].strip() == linkage_line.strip():
                exists = True
                break
        
        if not exists:
            new_linkage_lines.append(linkage_line)

    # 4. Insert new lines
    if new_linkage_lines:
        if icon_line != -1:
            # Insert after the icon line
            content[icon_line + 1:icon_line + 1] = new_linkage_lines
        else:
            # No icon line found, insert after the definition line
            content[start_line + 1:start_line + 1] = new_linkage_lines

    # Ensure the block is closed if it was newly created
    if start_line == len(content) - 2: # If the definition was appended just above
         content.append("}\n")

    # 5. Write back to file
    try:
        with open(DYNAMIC_MODIFIERS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(content)
            
        return f"Successfully updated dynamic modifiers: {DYNAMIC_MODIFIERS_FILE}"
    except Exception as e:
        return f"ERROR writing dynamic modifiers file: {e}"

# --- GUI Functions ---
def submit_data():
    """Handles the button click and orchestrates the file updates."""
    tag = entry_tag.get().strip().upper()
    effect_name = entry_effect.get().strip()
    dyn_mod_name = entry_dynamic.get().strip()
    modifier_text = text_modifiers.get("1.0", tk.END)

    # Basic Validation
    if not all([tag, effect_name, dyn_mod_name, modifier_text]):
        messagebox.showerror("Validation Error", "All fields must be filled out.")
        return

    if len(tag) != 3 or not tag.isalpha():
        messagebox.showerror("Validation Error", "Affected Country Tag must be exactly 3 letters.")
        return

    # 1. Parse Modifiers
    modifiers = parse_modifier_input(modifier_text)
    if modifiers is None:
        return # Error already shown by parse_modifier_input

    # 2. Update Dynamic Modifiers
    dyn_mod_result = update_dynamic_modifiers(dyn_mod_name, modifiers)
    
    # 3. Update Localization
    loc_result = update_localisation(tag, effect_name, dyn_mod_name, modifiers)

    # 4. Show Results
    result_message = f"Operation Complete!\n\n-- Dynamic Modifiers --\n{dyn_mod_result}\n\n-- Localization --\n{loc_result}"
    messagebox.showinfo("Success", result_message)

# --- GUI Setup ---
root = tk.Tk()
root.title("HOI4 Dynamic Modifier Linker")
root.geometry("600x650")
root.configure(bg='#2e2e2e')

# Style configuration
frame_bg = '#3c3c3c'
label_fg = '#ffffff'
entry_bg = '#4a4a4a'
entry_fg = '#eeeeee'
font_style = ("Arial", 10)
title_font = ("Arial", 14, "bold")

# Main Frame
main_frame = tk.Frame(root, padx=20, pady=20, bg=frame_bg)
main_frame.pack(fill=tk.BOTH, expand=True)

# Title
tk.Label(main_frame, text="HOI4 Dynamic Modifier Setup", font=title_font, fg=label_fg, bg=frame_bg).pack(pady=10)

# 1/ Affected country (Tag)
tk.Label(main_frame, text="1/ Affected Country (3-letter Tag, e.g., AUR):", anchor='w', fg=label_fg, bg=frame_bg, font=font_style).pack(fill='x', pady=(10, 2))
entry_tag = tk.Entry(main_frame, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, font=font_style)
entry_tag.pack(fill='x', ipady=3)

# 2/ Name of effect (Focus/Decision name)
tk.Label(main_frame, text="2/ Effect Name (Focus/Decision key, e.g., AUR_a_constitution):", anchor='w', fg=label_fg, bg=frame_bg, font=font_style).pack(fill='x', pady=(10, 2))
entry_effect = tk.Entry(main_frame, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, font=font_style)
entry_effect.pack(fill='x', ipady=3)

# 3/ Affected dynamic modifier
tk.Label(main_frame, text="3/ Affected Dynamic Modifier (e.g., AUR_the_kaiser_must_return):", anchor='w', fg=label_fg, bg=frame_bg, font=font_style).pack(fill='x', pady=(10, 2))
entry_dynamic = tk.Entry(main_frame, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, font=font_style)
entry_dynamic.pack(fill='x', ipady=3)

# 4/ Affected modifiers (Multiline Textbox)
tk.Label(main_frame, text="4/ Affected Modifiers (One per line, format: [name] = [value] - [GOOD/BAD]):", anchor='w', fg=label_fg, bg=frame_bg, font=font_style).pack(fill='x', pady=(10, 2))
tk.Label(main_frame, text="Example: political_power_gain = 0.10 - GOOD\nExample: stability_factor = -0.50 - BAD", anchor='w', fg='#a0a0a0', bg=frame_bg, font=("Arial", 9)).pack(fill='x')

text_modifiers = tk.Text(main_frame, height=10, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg, font=font_style, padx=5, pady=5)
text_modifiers.pack(fill='both', expand=True, pady=(5, 20))

# Submit Button
submit_button = tk.Button(main_frame, text="Generate & Update Files", command=submit_data, 
                          bg='#4CAF50', fg='white', font=("Arial", 12, "bold"), 
                          activebackground='#45A049', activeforeground='white',
                          bd=0, relief=tk.FLAT, padx=10, pady=5)
submit_button.pack(fill='x', ipady=5)

root.mainloop()
