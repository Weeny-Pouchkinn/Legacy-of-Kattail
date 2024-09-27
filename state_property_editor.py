import re

def modify_value_in_files(country_tag, value_to_modify, factor, folder_path="history/states"):
    # Compile regular expression to find lines like "value_to_modify = number"
    value_pattern = re.compile(rf"{value_to_modify}\s*=\s*(\d+)", re.IGNORECASE)

    # Iterate through all .txt files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r') as file:
                lines = file.readlines()

            # Check if the file contains the owner tag
            if any(f"owner = {country_tag}" in line for line in lines):
                modified = False
                new_lines = []

                # Iterate over each line and modify the value if found
                for line in lines:
                    match = value_pattern.search(line)
                    if match:
                        current_value = int(match.group(1))
                        new_value = round(current_value * factor)
                        line = re.sub(rf"{value_to_modify}\s*=\s*\d+", f"{value_to_modify} = {new_value}", line)
                        modified = True
                        print(f"Modified {value_to_modify} in {filename}: {current_value} -> {new_value}")

                    new_lines.append(line)

                # If a modification was made, overwrite the file with the updated lines
                if modified:
                    with open(filepath, 'w') as file:
                        file.writelines(new_lines)

if __name__ == "__main__":
    # Get inputs from the user
    country_tag = input("Enter Country TAG (e.g., ROQ): ").strip().upper()
    value_to_modify = input("Enter the value to modify (e.g., manpower): ").strip()
    factor = float(input("Enter the factor to modify it with (e.g., 0.75): "))

    # Specify the folder path to the history/states folder
    folder_path = input("Enter the path to the history/states folder (or press enter to use default './history/states'): ").strip() or "history/states"

    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
    else:
        # Modify the values in the files
        modify_value_in_files(country_tag, value_to_modify, factor, folder_path)
