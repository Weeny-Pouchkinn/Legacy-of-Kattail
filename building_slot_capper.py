import os
import re
import sys
from collections import namedtuple

# --- Configuration ---

# 1. Buildings that count towards the occupied slot total.
BUILDING_TYPES_TO_COUNT = {
    "food_silo",
    "industrial_complex",
    "arms_factory",
    "dockyard",
    "hydroponics_farm",
    "rocket_site",
    "synthetic_refinery",
}

# 2. State categories and their corresponding building slot capacity.
# Sorted by slots in ascending order for easy calculation of the smallest required category.
CATEGORY_SLOTS = [
    ("wasteland", 0),
    ("pastoral", 1),
    ("rural", 2),
    ("town", 4),
    ("large_town", 5),
    ("city", 6),
    ("large_city", 8),
    ("metropolis", 10),
    ("megalopolis", 12),
]
# Create a quick lookup map for reference
CATEGORY_MAP = dict(CATEGORY_SLOTS)

# Directory relative to the script location
STATES_DIR = "history/states"

# --- Utility Functions ---

def find_required_category(building_count):
    """
    Finds the category with the least amount of slots that can still accommodate
    the current building count.
    """
    for category, slots in CATEGORY_SLOTS:
        if building_count <= slots:
            return category
    
    # If the count exceeds the max category (megalopolis), return the max.
    return "megalopolis"

def process_state_file(filepath, target_tag):
    """
    Reads the state file, checks the owner, counts buildings, and replaces
    the state_category if necessary.
    """
    print(f"\nProcessing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Check if the target TAG is the owner of the state
    owner_pattern = re.compile(rf'owner\s*=\s*{target_tag}', re.IGNORECASE)
    if not owner_pattern.search(content):
        print(f"  --> Skipping: Owner is not {target_tag}.")
        return

    print(f"  --> State owned by {target_tag}. Analyzing buildings...")

    # 2. Extract the 'buildings' block content
    # This regex attempts to find the buildings block and capture its content
    buildings_block_match = re.search(r'buildings\s*=\s*\{([^}]+)\}', content, re.DOTALL)

    if not buildings_block_match:
        print("  --> Warning: 'buildings' block not found. Assuming 0 buildings for counting.")
        building_count = 0
    else:
        buildings_block_content = buildings_block_match.group(1)
        building_count = 0
        
        # Regex to find any of the specified building types and their assigned number
        # Example: 'arms_factory = 3'
        
        # Prepare a list of regex patterns for the buildings we care about
        # NOTE: This list of patterns is not strictly needed for the subsequent search,
        # but kept here for clarity on which buildings are being tracked.
        building_patterns = [
            re.compile(rf'^\s*{building}\s*=\s*(\d+)', re.MULTILINE)
            for building in BUILDING_TYPES_TO_COUNT
        ]
        
        for building_type in BUILDING_TYPES_TO_COUNT:
            # We search specifically for each building type in the content of the block
            match = re.search(rf'{building_type}\s*=\s*(\d+)', buildings_block_content)
            if match:
                count = int(match.group(1))
                building_count += count
                print(f"    - Found {building_type}: {count}")

    print(f"  --> Total count of tracked buildings: {building_count}")

    # 3. Determine the required new category
    new_category = find_required_category(building_count)
    
    # 4. Find the current category and calculate the change
    
    # Pattern to find the current state category line. 
    # Capture Group 1: The leading whitespace to preserve indentation.
    # Capture Group 2: The current category name.
    category_line_pattern = re.compile(r'^(\s*)state_category\s*=\s*([a-zA-Z_]+)\s*$', re.MULTILINE)
    current_category_match = category_line_pattern.search(content)

    if not current_category_match:
        print("  --> Error: 'state_category' line not found. Cannot modify.")
        return

    current_category = current_category_match.group(2) # Group 2 contains the category name
    
    # Check current capacity (default to 0 if category is unknown)
    current_capacity = CATEGORY_MAP.get(current_category, 0)
    
    if new_category == current_category:
        print(f"  --> Category is already {current_category} (Slots: {current_capacity}). No change needed.")
        return
    
    new_capacity = CATEGORY_MAP.get(new_category)

    if new_capacity is None:
        print(f"  --> Error: Calculated new category '{new_category}' is invalid. Aborting file write.")
        return

    print(f"  --> Current Category: {current_category} (Slots: {current_capacity})")
    print(f"  --> New Required Category: {new_category} (Slots: {new_capacity})")

    # 5. Perform the replacement
    # Use backreference \1 to re-insert the captured leading whitespace (indentation)
    new_content = category_line_pattern.sub(rf'\1state_category = {new_category}', content)

    # 6. Write the modified content back to the file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  --> SUCCESS: Updated category from {current_category} to {new_category}.")
    except Exception as e:
        print(f"  --> ERROR writing file: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cap_building_slots.py <COUNTRY_TAG>")
        print("Example: python cap_building_slots.py GER")
        sys.exit(1)

    target_tag = sys.argv[1].upper()
    print(f"Starting slot capping for country TAG: {target_tag}")
    
    if not os.path.isdir(STATES_DIR):
        print(f"\nError: Could not find the directory '{STATES_DIR}'.")
        print("Please ensure the script is run from the mod's root directory.")
        sys.exit(1)

    # Iterate over all files in the states directory
    for filename in os.listdir(STATES_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(STATES_DIR, filename)
            process_state_file(filepath, target_tag)
            
    print("\n\nScript finished processing all state files.")
    print("----------------------------------------")
    print(f"Building slots capped for all states owned by {target_tag} (if possible).")