import os
import re
import random
import shutil

# Get the directory where the script is located
base_directory = os.path.dirname(os.path.abspath(__file__))
states_directory = os.path.join(base_directory, "history/states")
units_directory = os.path.join(base_directory, "history/units")
countries_directory = os.path.join(base_directory, "history/countries")

# Prompt the user to enter a 3-letter country tag and Share of Divisions (SoD)
country_tag = input("Country Tag: ").strip()
sod = float(input("Share of Divisions (0 to 1): ").strip())

# Function to list all victory points for the specified country tag
def list_victory_points(file_path):
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
for filename in os.listdir(states_directory):
    if filename.endswith(".txt"):  # Adjust the file extension as needed
        file_path = os.path.join(states_directory, filename)
        victory_points_numbers = list_victory_points(file_path)
        all_victory_points_numbers.extend(victory_points_numbers)

# Check if the list of victory points is empty
if not all_victory_points_numbers:
    print("No victory points found for the specified country tag.")
    exit()

# Function to calculate the number of divisions with randomness
def calculate_divisions(base_amount, sod):
    amount = base_amount * sod
    random_amount = amount * random.uniform(0.85, 1.15)
    return int(random_amount) + 1

# Division types and their base amounts
division_types = {
    "Katzen-Schwereinfanterie": 100,
    "Katzen-Infanterie": 200,
    "Katzen-Garnison": 300,
    "Katzen-Bliztruppen": 60,
    "Katzen-Panzergruppe": 30
}

# Calculate the number of divisions for each type
divisions = {div_type: calculate_divisions(base_amount, sod) for div_type, base_amount in division_types.items()}

# Copy and rename the TEMPLATE_1936 file
template_file = os.path.join(units_directory, "TEMPLATE_1936.txt")
new_file = os.path.join(units_directory, f"{country_tag}_1936.txt")
shutil.copy(template_file, new_file)

# Edit the new file to set up the divisions and replace "TAG" under "instant_effect"
with open(new_file, "r") as file:
    lines = file.readlines()

with open(new_file, "w") as file:
    for line in lines:
        if "units = {" in line:
            file.write(line)
            for div_type, count in divisions.items():
                for _ in range(count):
                    file.write(f'\tdivision = {{ location = PROV division_template = "{div_type}" start_experience_factor = 0.3 }}\n')
        else:
            file.write(line.replace("TAG", country_tag))

# Replace "PROV" with random victory points
with open(new_file, "r") as file:
    content = file.read()

for _ in range(content.count("PROV")):
    vp = random.choice(all_victory_points_numbers)
    content = content.replace("PROV", vp, 1)

with open(new_file, "w") as file:
    file.write(content)

# Update the country's file in "history/countries"
country_file = os.path.join(countries_directory, f"{country_tag} - *.txt")
for filename in os.listdir(countries_directory):
    if filename.startswith(country_tag):
        country_file = os.path.join(countries_directory, filename)
        break

with open(country_file, "r") as file:
    lines = file.readlines()

with open(country_file, "w") as file:
    for line in lines:
        if "oob = " in line:
            file.write(f'set_oob = "{country_tag}_1936"\n')
        else:
            file.write(line)

print("Divisions set up successfully!")
