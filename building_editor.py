import os
import re

def modify_infrastructure(directory):
    # Loop through all files in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Only process if it's a file (skip directories)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as file:
                lines = file.readlines()

            modified = False
            new_lines = []
            owner_found = False
            
            # Loop through each line in the file
            for line in lines:
                # Check for "owner = MCF"
                if 'owner = MCF' in line:
                    owner_found = True
                
                # If "owner = MCF" is found, look for "infrastructure = [number]"
                if owner_found and 'infrastructure =' in line:
                    # Use regular expression to capture the number after "infrastructure ="
                    match = re.search(r'infrastructure = (\d+)', line)
                    if match:
                        current_value = int(match.group(1))
                        # Subtract 1 from the infrastructure value
                        new_value = current_value - 1 if current_value > 0 else 0  # Ensure it doesn't go below 0
                        # Replace the old infrastructure line with the new one
                        line = f"infrastructure = {new_value}\n"
                        modified = True
                
                new_lines.append(line)
            
            # If any modifications were made, rewrite the file
            if modified:
                with open(filepath, 'w') as file:
                    file.writelines(new_lines)
                print(f"Modified: {filename}")

# Usage example: provide the folder path where the files are located
folder_path = 'history/states'
modify_infrastructure(folder_path)
