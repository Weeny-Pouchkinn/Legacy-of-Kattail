import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# Attempt to load drag-and-drop library
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    USE_DND = True
except ImportError:
    USE_DND = False

class FocusIconTool:
    def __init__(self, root):
        self.root = root
        self.root.title("HOI4 Focus Icon Importer")
        self.root.geometry("450x380") # Increased height for the new input
        
        # --- UI Elements ---
        tk.Label(root, text="Country Tag ([TAG]):", font=("Arial", 10, "bold")).pack(pady=(15, 0))
        self.tag_entry = tk.Entry(root, width=20, justify="center")
        self.tag_entry.pack()
        
        tk.Label(root, text="Focus Name ([NAME]):", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.name_entry = tk.Entry(root, width=30, justify="center")
        self.name_entry.pack()

        tk.Label(root, text="Credits (Optional):", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.credits_entry = tk.Entry(root, width=30, justify="center")
        self.credits_entry.pack()
        
        tk.Label(root, text="Icon File:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(root, textvariable=self.file_path_var, width=50, state='readonly', justify="center")
        self.file_entry.pack(pady=5)
        
        self.browse_btn = tk.Button(root, text="Browse File Explorer", command=self.browse_file)
        self.browse_btn.pack()
        
        if USE_DND:
            tk.Label(root, text="(You can also drag and drop an image onto this window)", fg="grey").pack(pady=(5,0))
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.drop_file)
        else:
            tk.Label(root, text="(Install 'tkinterdnd2' via pip for drag-and-drop support)", fg="grey").pack(pady=(5,0))

        self.run_btn = tk.Button(root, text="Import Focus Icon", command=self.generate, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.run_btn.pack(pady=15)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Focus Icon",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tga;*.dds"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def drop_file(self, event):
        # Remove curly braces that tkinterdnd2 adds around paths containing spaces
        file_path = event.data.strip('{}')
        self.file_path_var.set(file_path)

    def generate(self):
        tag = self.tag_entry.get().strip().upper()
        name = self.name_entry.get().strip()
        credits = self.credits_entry.get().strip()
        source_file = self.file_path_var.get().strip()

        if not tag or not name or not source_file:
            messagebox.showerror("Error", "Please provide a TAG, a NAME, and select an image file.")
            return

        # 1. Create target directory
        target_dir = os.path.join("gfx", "interface", "goals", tag)
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create directory {target_dir}:\n{e}")
            return

        # 2. Convert and save to TGA
        target_file = os.path.join(target_dir, f"{name}.tga")
        try:
            with Image.open(source_file) as img:
                img.save(target_file, format="TGA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert image to TGA:\n{e}")
            return

        # 3. Update the .gfx file
        gfx_path = os.path.join("interface", "lok_national_focus_icons.gfx")
        if not os.path.exists(gfx_path):
            messagebox.showerror("Error", f"Could not find {gfx_path}. Make sure you run this script in the root of your mod folder.")
            return

        try:
            with open(gfx_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find the last closing bracket in the file
            last_brace_idx = content.rfind("}")
            if last_brace_idx == -1:
                messagebox.showerror("Error", f"Could not find a closing bracket in {gfx_path}.")
                return

            # Format the credit line if the user inputted something
            credit_line = f"\n\t#Icon Credit: {credits}" if credits else ""

            # Prepare the insertion block
            block = f"""{credit_line}
\tSpriteType = {{ 
\t\tname = "GFX_goal_{name}"
\t\ttexturefile = "gfx/interface/goals/{tag}/{name}.tga"
\t}}
\tSpriteType = {{ 
\t\tname = "GFX_goal_{name}_shine"
\t\ttexturefile = "gfx/interface/goals/{tag}/{name}.tga"
\t\teffectFile = "gfx/FX/buttonstate.lua"
\t\tanimation = {{
\t\t\tanimationmaskfile = "gfx/interface/goals/{tag}/{name}.tga"
\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"
\t\t\tanimationrotation = -90.0
\t\t\tanimationlooping = no
\t\t\tanimationtime = 0.75
\t\t\tanimationdelay = 0
\t\t\tanimationblendmode = "add"
\t\t\tanimationtype = "scrolling"
\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}
\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }} 
\t\t}}
\t\tanimation = {{
\t\t\tanimationmaskfile = "gfx/interface/goals/{tag}/{name}.tga"
\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"
\t\t\tanimationrotation = 90.0
\t\t\tanimationlooping = no
\t\t\tanimationtime = 0.75
\t\t\tanimationdelay = 0
\t\t\tanimationblendmode = "add"
\t\t\tanimationtype = "scrolling"
\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}
\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }} 
\t\t}}
\t\tlegacy_lazy_load = no
\t}}
"""
            # Slice the file to insert the code immediately prior to the final bracket
            new_content = content[:last_brace_idx] + block + content[last_brace_idx:]

            with open(gfx_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update .gfx file:\n{e}")
            return

        messagebox.showinfo("Success", f"Success!\nConverted '{name}.tga' into gfx/interface/goals/{tag}/\nInjected definitions into {gfx_path}")
        
        # Reset the input fields for your next upload
        self.name_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)
        self.file_path_var.set("")

if __name__ == "__main__":
    if USE_DND:
        app_root = TkinterDnD.Tk()
    else:
        app_root = tk.Tk()
        
    tool = FocusIconTool(app_root)
    app_root.mainloop()