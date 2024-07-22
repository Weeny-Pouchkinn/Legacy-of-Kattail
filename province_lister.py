import os
import re

# Get the directory where the script is located
directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history/states")

# Prompt the user to enter a 3-letter country tag
country_tag = input("Country Tag: ").strip()

def process_file(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            owner_tag = f"owner = {country_tag}"
            if any(owner_tag in line for line in lines):
                victory_points_numbers = []
                for line in lines:
                    if "victory_points = {" in line:
                        # Extract the first number from the line
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            victory_points_numbers.append(numbers[0])
                return victory_points_numbers
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return []

# List to store all victory points numbers
all_victory_points_numbers = []

# Process each file in the "history/states" directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):  # Adjust the file extension as needed
        file_path = os.path.join(directory_path, filename)
        victory_points_numbers = process_file(file_path)
        all_victory_points_numbers.extend(victory_points_numbers)

# Print all the victory points numbers
print("Victory Points Numbers:")
print(" ".join(all_victory_points_numbers))
