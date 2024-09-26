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

        messagebox.showinfo("Success", "Portraits processed successfully!")

    def process_category(self, portraits, category, species_name, country_tag, leaders_folder):
            portrait_entries = []  # List to store each GFX entry
            for idx, portrait in enumerate(portraits, start=1):
                # Convert to .tga if necessary
                tga_path = self.convert_to_tga(portrait)

                # Rename and copy to the correct folder
                new_filename = f"{species_name}_generic_{category}_{idx}.tga"
                new_filepath = os.path.join(leaders_folder, new_filename)
                shutil.copy(tga_path, new_filepath)

                # Collect the GFX entry for later use in misc_portraits.txt
                gfx_entry = f"GFX_portrait_{species_name}_generic_{category}_{idx}"
                portrait_entries.append(gfx_entry)

                # Update the .gfx file with each portrait's ID
                self.update_gfx_file(species_name, country_tag, category, idx)

                #Make small portrait
                # Open the base image and border image
                base_image = Image.open(f'gfx/leaders/{country_tag}/{species_name}_generic_{category}_{idx}.tga').convert('RGBA')
                border_image = Image.open('minister_border.png').convert('RGBA')

                # Resize the base image
                base_image = base_image.resize((35, 51))

                # Rotate the base image 5 degrees counter-clockwise and expand the output to fit the whole rotated image
                base_image = base_image.rotate(5, expand=True)

                # Create a new image with the desired size for the canvas
                canvas = Image.new('RGBA', (65, 67))

                # Calculate the position to center the base image on the canvas, shifted by 9 pixels to the left and 2 pixels up
                left = (canvas.width - base_image.width) // 2 - 7
                top = (canvas.height - base_image.height) // 2 - 2

                # Paste the base image onto the canvas using alpha_composite
                canvas.alpha_composite(base_image, (left, top))

                # Resize the border image to match the size of the canvas
                border_image = border_image.resize((canvas.width, canvas.height))

                # Paste the border image onto the canvas at the desired position, shifted by 9 pixels to the left and 2 pixels up
                canvas.alpha_composite(border_image, (7 - 7, 2 - 2))

                # Save the result
                canvas.save(f'gfx/interface/ministers/{country_tag}/{species_name}_generic_{category}_{idx}.tga')

            # After processing all portraits for the category, update the misc_portraits.txt
            self.update_misc_portraits(country_tag, species_name, category, portrait_entries)

    def update_gfx_file(self, species_name, country_tag, category, idx):
        gfx_file_path = "interface/lok_generic_species_portraits.gfx"

        with open(gfx_file_path, "r") as file:
            lines = file.readlines()

        # Remove the last closing bracket if it exists
        if lines[-1].strip() == "}":
            lines.pop()

        # Add a spriteType definition for the current portrait
        sprite_type = (
            f'\t'
            f'spriteType = {{ name = "GFX_portrait_{species_name}_generic_{category}_{idx}" '
            f'textureFile = "gfx/leaders/{country_tag}/{species_name}_generic_{category}_{idx}.tga" }}\n'
            f'\t'
            f'spriteType = {{ name = "GFX_portrait_{species_name}_generic_{category}_{idx}_small" '
            f'textureFile = "gfx/interface/ministers/{country_tag}/{species_name}_generic_{category}_{idx}.tga" }}\n'
        )
        lines.append(sprite_type)

        # Add the closing bracket back
        lines.append("}\n")

        with open(gfx_file_path, "w") as file:
            file.writelines(lines)

    def update_misc_portraits(self, country_tag, species_name, category, portrait_entries):
        misc_file_path = os.path.join("portraits", "misc_portraits.txt")
        self.create_folder_if_not_exist("portraits")  # Ensure the folder exists

        if not os.path.exists(misc_file_path):
            # Initialize the file if it doesn't exist
            with open(misc_file_path, "w") as file:
                file.write("")

        # Build the block of entries for the current category
        male_entries = ' '.join([f'"{entry}"' for entry in portrait_entries])
        female_entries = ' '.join([f'"{entry}"' for entry in portrait_entries])

        with open(misc_file_path, "a") as file:
            file.write(f"\n{country_tag} = {{\n")
            file.write(f"\tpolitical = {{\n")

            if category == "military":
                file.write(f"\t\tcommunism = {{\n\t\t\tmale = {{ {male_entries} }}\n\t\t\tfemale = {{ {female_entries} }}\n\t\t}}\n")
                file.write(f"\t\tfascism = {{\n\t\t\tmale = {{ {male_entries} }}\n\t\t\tfemale = {{ {female_entries} }}\n\t\t}}\n")
            elif category == "civilian":
                file.write(f"\t\tdemocratic = {{\n\t\t\tmale = {{ {male_entries} }}\n\t\t\tfemale = {{ {female_entries} }}\n\t\t}}\n")
                file.write(f"\t\tneutrality = {{\n\t\t\tmale = {{ {male_entries} }}\n\t\t\tfemale = {{ {female_entries} }}\n\t\t}}\n")

            file.write("\t}\n")
            file.write(f"\tarmy = {{\n\t\tmale = {{ {male_entries} }}\n\t\tfemale = {{ {female_entries} }}\n\t}}\n")
            
            if category == "navy":
                file.write(f"\tnavy = {{\n\t\tmale = {{ {male_entries} }}\n\t\tfemale = {{ {female_entries} }}\n\t}}\n")

            file.write("}\n")

# Main application execution
if __name__ == "__main__":
    root = tk.Tk()
    app = PortraitManager(root)
    root.mainloop()