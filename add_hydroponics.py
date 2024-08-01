import os
import random

# Get the directory where the script is located
directory_path = os.path.dirname(os.path.abspath(__file__))

def process_file(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            contains_owner = any("owner =" in line for line in lines)
            contains_state_category = any(
                "state_category = large_city" in line or
                "state_category = metropolis" in line or
                "state_category = megalopolis" in line
                for line in lines
            )
            contains_excluded_tags = any(
                "ZUS" in line or
                "NMI" in line or
                "NKC" in line
                for line in lines
            )

            if contains_owner and contains_state_category and not contains_excluded_tags:
                # Roll a 33% chance
                if random.random() < 0.90:
                    for i, line in enumerate(lines):
                        if "buildings = {" in line:
                            # Insert the food_silo line right after the "buildings = {" line
                            lines.insert(i + 1, "\t\t\thydroponics_farm = 1\n")
                            break

        # Write the updated content back to the file
        with open(file_path, "w") as file:
            file.writelines(lines)
            print(f"Processed {file_path} successfully!")

    except FileNotFoundError:
        print(f"File not found: {file_path}")

# Process each file in the directory where the script is located
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Adjust the file extension as needed
        file_path = os.path.join(directory_path, filename)
        process_file(file_path)
