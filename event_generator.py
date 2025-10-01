import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import re

# --- Constants for HOI4 Modding ---
EVENTS_DIR = "events"
LOCALISATION_DIR = os.path.join("localisation", "english")
ID_PATTERN = re.compile(r"id\s*=\s*[A-Z0-9_]+\.(\d+)")

# --- Core Logic for ID Auto-Generation ---

def get_next_event_id(tag, namespace):
    """
    Reads the event file, finds the highest existing ID for the given namespace, 
    and returns the next integer ID. Returns 1 if no events are found.
    """
    filename = os.path.join(EVENTS_DIR, f"{tag.upper()}_events.txt")
    
    if not os.path.exists(filename):
        return 1
    
    max_id = 0
    in_correct_namespace = False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find the start of the correct namespace block
            ns_start_pattern = re.compile(rf"add_namespace\s*=\s*{re.escape(namespace)}", re.IGNORECASE)
            ns_match = ns_start_pattern.search(content)

            if ns_match:
                start_index = ns_match.end()
                
                # Find the end of the current namespace block (start of the next 'add_namespace')
                next_ns_match = re.search(r"add_namespace\s*=", content[start_index:])
                end_index = (start_index + next_ns_match.start()) if next_ns_match else len(content)

                namespace_content = content[start_index:end_index]

                # Find all IDs within this content block
                for match in ID_PATTERN.finditer(namespace_content):
                    event_num = int(match.group(1))
                    if event_num > max_id:
                        max_id = event_num
            
    except Exception as e:
        messagebox.showwarning("ID Auto-Generation Error", f"Could not read events file to find max ID. Defaulting to 1. Error: {e}")
        return 1
        
    return max_id + 1

# --- Helper Functions ---

def create_dirs():
    """Ensures the events and localisation directories exist."""
    os.makedirs(EVENTS_DIR, exist_ok=True)
    os.makedirs(LOCALISATION_DIR, exist_ok=True)

def generate_event_code(data):
    """Generates the HOI4 event code string with conditional blocks."""
    tag = data['tag'].upper()
    event_id = f"{data['namespace']}.{data['id']}"
    event_type = f"{data['type']}_event"
    immediate_effects = data['immediate_effects'].strip()
    
    event_block = f"""
#{data['comment']}
{event_type} = {{
\tid = {event_id}
\timmediate = {{ log = "[GetDateText]: [Root.GetName]: event {event_id}"}}
\ttitle = {event_id}.t
\tdesc = {event_id}.d
\tpicture = {data['picture']}

\tis_triggered_only = yes
"""
    # Conditionally include fire_only_once block
    if data['fire_only_once']:
        event_block += "\tfire_only_once = yes\n"
    
    event_block += "\t\n"
    
    # Conditionally include immediate effects block
    if immediate_effects:
        event_block += f"""\timmediate = {{
{indent_block(immediate_effects, 2)}
\t}}
"""

    # Add options
    for i, option in enumerate(data['options']):
        option_char = chr(ord('a') + i)
        option_name = f"{event_id}.{option_char}"
        
        event_block += f"""
\toption = {{
\t\tname = {option_name}
{indent_block(option['trigger_effect'], 2)}
\t}}
"""
    
    event_block += "}"
    
    return event_block

def generate_localisation_code(data):
    """Generates the HOI4 localisation code string with fixed indentation."""
    event_id = f"{data['namespace']}.{data['id']}"
    loc_block = f"""
 {event_id}.t:0 "{data['name']}"
 {event_id}.d:0 "{data['description'].replace('\n', '\\n')}"
"""
    
    # Add options localisation
    for i, option in enumerate(data['options']):
        option_char = chr(ord('a') + i)
        loc_id = f"{event_id}.{option_char}"
        
        # Option name
        loc_block += f" {loc_id}:0 \"{option['name']}\"\n"
        
        # Option tooltip (custom_effect_tooltip)
        if option['tooltip']:
            loc_block += f" {loc_id}.tooltip:0 \"{option['tooltip']}\"\n"

    return loc_block.strip()

def indent_block(text, level):
    """Indents a block of text for HOI4 file formatting."""
    indent = '\t' * level
    # Only indent if there is content
    if not text.strip():
        return ""
    return '\n'.join([f"{indent}{line}" for line in text.strip().split('\n')])

def append_to_events_file(tag, namespace, event_code):
    """Appends event code to the correct events file, creating it if necessary."""
    filename = os.path.join(EVENTS_DIR, f"{tag.upper()}_events.txt")
    
    is_new_file = not os.path.exists(filename)
    
    # Read/Initialize content
    file_content = ""
    if not is_new_file:
        with open(filename, 'r', encoding='utf-8') as read_f:
            file_content = read_f.read()
            
    namespace_line = f"add_namespace = {namespace}"
    
    if file_content:
        try:
            ns_start_index = file_content.index(namespace_line)
        except ValueError:
            # Namespace not found, prepend it
            with open(filename, 'r+', encoding='utf-8') as f:
                content_to_prepend = f"{namespace_line}\n"
                f.write(content_to_prepend + event_code + "\n\n" + file_content)
                messagebox.showinfo("Success", f"Prepended namespace and event to:\n{filename}")
                return

        # Search for the next 'add_namespace' after the current one
        next_ns_index = file_content.find("add_namespace =", ns_start_index + len(namespace_line))

        # Determine where to insert
        insertion_point = next_ns_index if next_ns_index != -1 else len(file_content)
        
        # Insert the new event with a preceding empty line
        new_content = file_content[:insertion_point].rstrip() + "\n" + event_code + "\n" + file_content[insertion_point:]

        # Write the entire new content back to the file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    else:
        # New file case
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{namespace_line}\n")
            f.write(event_code)
            
    messagebox.showinfo("Success", f"Appended event to events file:\n{filename}")

def append_to_localisation_file(tag, loc_code):
    """Appends localisation code to the correct file, creating it if necessary."""
    filename = os.path.join(LOCALISATION_DIR, f"{tag.upper()}_l_english.yml")
    
    is_new_file = not os.path.exists(filename)
    
    with open(filename, 'a', encoding='utf-8-sig') as f: # utf-8-sig for YAML
        if is_new_file:
            f.write("l_english:\n")
        
        f.write(f"\n{loc_code}\n")
            
    messagebox.showinfo("Success", f"Appended localisation to file:\n{filename}")

# --- GUI Logic ---

class OptionWindow(tk.Toplevel):
    """GUI window for creating a single event option."""
    def __init__(self, master):
        super().__init__(master)
        self.title("Add Event Option")
        self.geometry("600x450")
        self.option_data = None
        
        tk.Label(self, text="Option Name:").pack(pady=5)
        self.name_entry = tk.Entry(self, width=70)
        self.name_entry.pack(pady=5)

        tk.Label(self, text="Option Tooltip (Optional, e.g., for custom_effect_tooltip):").pack(pady=5)
        self.tooltip_text = scrolledtext.ScrolledText(self, width=70, height=5)
        self.tooltip_text.pack(pady=5)

        tk.Label(self, text="Option Trigger + Effect Block (Optional):").pack(pady=5)
        self.effect_text = scrolledtext.ScrolledText(self, width=70, height=10)
        self.effect_text.pack(pady=5)

        tk.Button(self, text="Save Option", command=self.save_option).pack(pady=10)

    def save_option(self):
        name = self.name_entry.get().strip()
        tooltip = self.tooltip_text.get("1.0", tk.END).strip()
        effect = self.effect_text.get("1.0", tk.END).strip()
        
        if not name:
            messagebox.showerror("Error", "Option Name is required.")
            return

        self.option_data = {
            'name': name,
            'tooltip': tooltip,
            'trigger_effect': effect
        }
        self.destroy()

class EventCreatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("HOI4 Event Creator Utility")
        
        self.data = {'options': []}
        self.create_widgets()

    def create_widgets(self):
        # Frame for basic event info
        basic_frame = tk.LabelFrame(self.master, text="Basic Event Info", padx=10, pady=10)
        basic_frame.pack(padx=10, pady=10, fill="x")

        # 1/ Country TAG
        tk.Label(basic_frame, text="1/ Country TAG (3-letter):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.tag_entry = tk.Entry(basic_frame)
        self.tag_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.tag_entry.insert(0, "TAG") 

        # 2/ Namespace
        tk.Label(basic_frame, text="2/ Event Namespace:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.namespace_entry = tk.Entry(basic_frame)
        self.namespace_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.namespace_entry.insert(0, "MOD_event")

        # 3/ Event ID
        tk.Label(basic_frame, text="3/ Event ID (Number):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.id_entry = tk.Entry(basic_frame)
        self.id_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.id_entry.insert(0, "1")
        
        # New: Auto-Generate ID Checkbox
        self.auto_id_var = tk.BooleanVar(self.master)
        self.auto_id_var.set(True) # Default to true for convenience
        self.auto_id_check = tk.Checkbutton(basic_frame, text="Auto-Generate ID (Overrides Manual Entry)", variable=self.auto_id_var)
        self.auto_id_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Shifted rows due to new checkbox
        # 4/ Event Type
        tk.Label(basic_frame, text="4/ Event Type:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.type_var = tk.StringVar(self.master)
        self.type_var.set("country")
        self.type_menu = tk.OptionMenu(basic_frame, self.type_var, "country", "news")
        self.type_menu.grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        # 5/ Event Picture
        tk.Label(basic_frame, text="5/ Event Picture (GFX_...):").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.picture_entry = tk.Entry(basic_frame)
        self.picture_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=2)
        self.picture_entry.insert(0, "GFX_report_event_default")

        # 6/ Fire Only Once
        tk.Label(basic_frame, text="6/ Fire Only Once (Leave unchecked for 'no'):").grid(row=6, column=0, sticky="w", padx=5, pady=2)
        self.fire_once_var = tk.BooleanVar(self.master)
        tk.Checkbutton(basic_frame, text="Yes", variable=self.fire_once_var).grid(row=6, column=1, sticky="w", padx=5, pady=2)

        basic_frame.grid_columnconfigure(1, weight=1)

        # 7/ Immediate Effects
        effect_frame = tk.LabelFrame(self.master, text="7/ Immediate Effects (Leave blank for no 'immediate' block)", padx=10, pady=10)
        effect_frame.pack(padx=10, pady=10, fill="x")
        self.immediate_text = scrolledtext.ScrolledText(effect_frame, width=70, height=5)
        self.immediate_text.pack(fill="x", expand=True)

        # 8 & 9/ Loc Info
        loc_frame = tk.LabelFrame(self.master, text="8 & 9/ Localisation", padx=10, pady=10)
        loc_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(loc_frame, text="8/ Event Name (Title):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = tk.Entry(loc_frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(loc_frame, text="9/ Event Description:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.description_text = scrolledtext.ScrolledText(loc_frame, width=70, height=6)
        self.description_text.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        loc_frame.grid_columnconfigure(1, weight=1)

        # 10/ Options
        options_frame = tk.LabelFrame(self.master, text="10/ Options", padx=10, pady=10)
        options_frame.pack(padx=10, pady=10, fill="x")
        
        self.options_list_box = tk.Listbox(options_frame, height=3)
        self.options_list_box.pack(fill="x", expand=True)
        
        tk.Button(options_frame, text="Add New Option", command=self.add_option).pack(pady=5)

        # 11/ Comment
        comment_frame = tk.LabelFrame(self.master, text="11/ Event Comment", padx=10, pady=10)
        comment_frame.pack(padx=10, pady=10, fill="x")
        tk.Label(comment_frame, text="Comment for Event File (e.g., 'Ask for Pakt'):").pack(pady=2)
        self.comment_entry = tk.Entry(comment_frame)
        self.comment_entry.pack(fill="x", expand=True)
        
        # Submit Button
        tk.Button(self.master, text="GENERATE EVENT FILES", command=self.generate_files, bg="green", fg="white", font=('Arial', 12, 'bold')).pack(pady=20, fill="x")

    def add_option(self):
        option_win = OptionWindow(self.master)
        self.master.wait_window(option_win)
        
        if option_win.option_data:
            self.data['options'].append(option_win.option_data)
            option_name = option_win.option_data['name']
            self.options_list_box.insert(tk.END, f"Option {chr(ord('a') + len(self.data['options']) - 1)}: {option_name}")

    def generate_files(self):
        # 1-6 Basic Validation
        tag = self.tag_entry.get().strip().upper()
        namespace = self.namespace_entry.get().strip()
        
        if not all([tag, namespace]):
            messagebox.showerror("Error", "Country TAG and Namespace are required.")
            return
        
        if len(tag) != 3 or not tag.isalpha():
            messagebox.showerror("Error", "Country TAG must be 3 letters.")
            return

        # ID Handling
        if self.auto_id_var.get():
            event_id = str(get_next_event_id(tag, namespace))
        else:
            event_id = self.id_entry.get().strip()
            if not event_id.isdigit():
                messagebox.showerror("Error", "Manual Event ID must be a number.")
                return

        # 7-11 Data Collection
        self.data.update({
            'tag': tag,
            'namespace': namespace,
            'id': event_id,
            'type': self.type_var.get(),
            'picture': self.picture_entry.get().strip(),
            'fire_only_once': self.fire_once_var.get(),
            'immediate_effects': self.immediate_text.get("1.0", tk.END).strip(),
            'name': self.name_entry.get().strip(),
            'description': self.description_text.get("1.0", tk.END).strip(),
            'comment': self.comment_entry.get().strip()
        })
        
        if not self.data['name'] or not self.data['description']:
            messagebox.showerror("Error", "Event Name and Description are required.")
            return
        
        # --- File Generation ---
        try:
            create_dirs()
            
            # 1. Generate Event Code and Append
            event_code = generate_event_code(self.data)
            append_to_events_file(tag, namespace, event_code)
            
            # 2. Generate Localisation Code and Append
            loc_code = generate_localisation_code(self.data)
            append_to_localisation_file(tag, loc_code)
            
            # Reset for next event
            self.data['options'] = []
            self.options_list_box.delete(0, tk.END)
            self.id_entry.delete(0, tk.END)
            # Re-run auto-generate logic if checked to update the displayed ID for the next event
            if self.auto_id_var.get():
                 next_id = get_next_event_id(tag, namespace)
                 self.id_entry.insert(0, str(next_id))
            else:
                 self.id_entry.insert(0, "1")

        except Exception as e:
            messagebox.showerror("Critical Error", f"An unexpected error occurred during file generation: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = EventCreatorGUI(root)
    # Perform an initial ID auto-generation (default TAG, default namespace)
    initial_id = get_next_event_id("TAG", "MOD_event")
    app.id_entry.delete(0, tk.END)
    app.id_entry.insert(0, str(initial_id))
    root.mainloop()