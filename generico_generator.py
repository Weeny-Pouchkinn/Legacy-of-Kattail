import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import shutil

# Create the GUI application
class PortraitManager:
    def __init__(self, root):
        self.root = root
        self.root.title("HOI4 Portrait Manager")

        # Define input fields for country tag and species name
        self.country_tag_label = tk.Label(root, text="Country Tag:")
        self.country_tag_label.grid(row=0, column=0)
        self.country_tag_entry = tk.Entry(root)
        self.country_tag_entry.grid(row=0, column=1)

        self.species_name_label = tk.Label(root, text="Species Name:")
        self.species_name_label.grid(row=1, column=0)
        self.species_name_entry = tk.Entry(root)
        self.species_name_entry.grid(row=1, column=1)

        # Define buttons for uploading portraits
        self.army_btn = tk.Button(root, text="Upload Army Portraits", command=self.upload_army)
        self.army_btn.grid(row=2, column=0)

        self.navy_btn = tk.Button(root, text="Upload Navy Portraits", command=self.upload_navy)
        self.navy_btn.grid(row=3, column=0)

        self.civilian_btn = tk.Button(root, text="Upload Civilian Portraits", command=self.upload_civilian)
        self.civilian_btn.grid(row=4, column=0)

        # Define confirm button
        self.confirm_btn = tk.Button(root, text="Confirm", command=self.process_portraits)
        self.confirm_btn.grid(row=5, column=0, columnspan=2)

        # Store file paths for different portrait categories
        self.army_portraits = []
        self.navy_portraits = []
        self.civilian_portraits = []

    def upload_army(self):
        self.army_portraits = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.tga")])
        messagebox.showinfo("Army Portraits", f"{len(self.army_portraits)} files uploaded.")

    def upload_navy(self):
        self.navy_portraits = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.tga")])
        messagebox.showinfo("Navy Portraits", f"{len(self.navy_portraits)} files uploaded.")

    def upload_civilian(self):
        self.civilian_portraits = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.tga")])
        messagebox.showinfo("Civilian Portraits", f"{len(self.civilian_portraits)} files uploaded.")

    def convert_to_tga(self, filepath):
        if not filepath.endswith(".tga"):
            img = Image.open(filepath)
            tga_filepath = filepath.rsplit('.', 1)[0] + ".tga"
            img.save(tga_filepath)
            return tga_filepath
        return filepath

    def create_folder_if_not_exist(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def process_portraits(self):
        country_tag = self.country_tag_entry.get().upper()
        species_name = self.species_name_entry.get().lower()

        if not country_tag or not species_name:
            messagebox.showerror("Error", "Please provide both Country Tag and Species Name.")
            return

        # Create necessary directories
        leaders_folder = f"gfx/leaders/{country_tag}"
        ministers_folder = f"gfx/interface/icons/ministers/{country_tag}"
        self.create_folder_if_not_exist(leaders_folder)
        self.create_folder_if_not_exist(ministers_folder)

        # Process each category of portraits
        self.process_category(self.army_portraits, "military", species_name, country_tag, leaders_folder)
        self.process_category(self.navy_portraits, "navy", species_name, country_tag, leaders_folder)
        self.process_category(self.civilian_portraits, "civilian", species_name, country_tag, leaders_folder)

        # Update the .gfx file
        self.update_gfx_file(species_name, country_tag)

        messagebox.showinfo("Success", "Portraits processed successfully!")

    def process_category(self, portraits, category, species_name, country_tag, leaders_folder):
        for idx, portrait in enumerate(portraits, start=1):
            # Convert to .tga if necessary
            tga_path = self.convert_to_tga(portrait)

            # Rename and move to correct folder
            new_filename = f"{species_name}_generic_{category}_{idx}.tga"
            new_filepath = os.path.join(leaders_folder, new_filename)
            shutil.move(tga_path, new_filepath)

    def update_gfx_file(self, species_name, country_tag):
        gfx_file_path = "interface/lok_generic_species_portraits.gfx"

        with open(gfx_file_path, "r") as file:
            lines = file.readlines()

        # Remove the last closing bracket
        if lines[-1].strip() == "}":
            lines.pop()

        # Add sprite definitions
        for idx, category in enumerate(["military", "navy", "civilian"], start=1):
            sprite_type = (
                f'\n\t'
                f'spriteType = {{ name = "GFX_portrait_{species_name}_generic_{category}_{idx}" '
                f'textureFile = "gfx/leaders/{country_tag}/{species_name}_generic_{category}_{idx}.tga" }}\n'
            )
            lines.append(sprite_type)

        # Add back the closing bracket
        lines.append("}\n")

        with open(gfx_file_path, "w") as file:
            file.writelines(lines)

# Main application execution
if __name__ == "__main__":
    root = tk.Tk()
    app = PortraitManager(root)
    root.mainloop()
