import os
import random

# Specify the directory where your state files are located
directory_path = "/history/states"

def process_file(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            contains_owner = any("owner =" in line for line in lines)
            contains_state_category = any(
                "state_category=large_town" in line or
                "state_category=town" in line or
                "state_category=city" in line or
                "state_category=rural" in line or
                "state_category=pastoral" in line
                for line in lines
            )

            if contains_owner and contains_state_category:
                # Roll a 33% chance
                if random.random() < 0.33:
                    for i, line in enumerate(lines):
                        if "buildings = {" in line:
                            # Find the end of the buildings block
                            for j in range(i + 1, len(lines)):
                                if "}" in lines[j]:
                                    # Insert the food_silo line before the closing brace
                                    lines.insert(j, "\t\t\tfood_silo = 1\n")
                                    break

        # Write the updated content back to the file
        with open(file_path, "w") as file:
            file.writelines(lines)
            print(f"Processed {file_path} successfully!")

    except FileNotFoundError:
        print(f"File not found: {file_path}")

# Process each file in the specified directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Adjust the file extension as needed
        file_path = os.path.join(directory_path, filename)
        process_file(file_path)