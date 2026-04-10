import os
import re
import sys

def fix_missing_tags(log_file_path):
    if not os.path.exists(log_file_path):
        print(f"Error: Could not find '{log_file_path}'. Please make sure the file exists.")
        return

    # 1. Extract unique 3-letter tags
    tags = set()
    tag_pattern = re.compile(r": ([A-Z]{3}) - is not in the tag list")
    
    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = tag_pattern.search(line)
            if match:
                tags.add(match.group(1))
                
    if not tags:
        print("No missing tags found in the provided file.")
        return
        
    print(f"Found {len(tags)} missing tags: {', '.join(tags)}")

    # 2. Define target directories
    tags_dir = os.path.join("common", "country_tags")
    tags_file = os.path.join(tags_dir, "zz_dummy_tags.txt")
    history_dir = os.path.join("history", "countries")
    common_countries_dir = os.path.join("common", "countries")
    colors_file = os.path.join(common_countries_dir, "colors.txt")

    # Create the directories if they don't exist
    os.makedirs(tags_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(common_countries_dir, exist_ok=True)

    # 3. Append to the country tags file
    with open(tags_file, 'a', encoding='utf-8') as f_tags:
        for tag in tags:
            f_tags.write(f'{tag} = "countries/{tag}.txt"\n')
            
    print(f"Appended tag definitions to {tags_file}")

    # 4. Create dummy history, country files, and append to colors
    history_created = 0
    common_created = 0
    
    # Open colors.txt in append mode. 'a' creates the file if it doesn't exist.
    with open(colors_file, 'a', encoding='utf-8') as f_colors:
        # Add a safety newline so we don't append to the end of an existing line
        f_colors.write("\n") 
        
        for tag in tags:
            # Create the history file
            history_filepath = os.path.join(history_dir, f"{tag} - DUMMY.txt")
            if not os.path.exists(history_filepath):
                with open(history_filepath, 'w', encoding='utf-8') as f_hist:
                    f_hist.write("#Dummy country so the log stops screaming\n")
                history_created += 1

            # Create the common/countries file
            country_filepath = os.path.join(common_countries_dir, f"{tag}.txt")
            if not os.path.exists(country_filepath):
                with open(country_filepath, 'w', encoding='utf-8') as f_country:
                    f_country.write("graphical_culture = western_european_gfx\n")
                    f_country.write("graphical_culture_2d = western_european_2d\n")
                    f_country.write("color = rgb { 1 1 1 }\n")
                common_created += 1
            
            # Append the color definition to colors.txt
            f_colors.write(f"{tag} = {{ color = rgb {{ 1 1 1 }} color_ui = rgb {{ 1 1 1 }} }}\n")

    print(f"Created {history_created} new dummy files in {history_dir}")
    print(f"Created {common_created} new country files in {common_countries_dir}")
    print(f"Appended color definitions to {colors_file}")
    print("Done!")

if __name__ == "__main__":
    input_file = "errors.txt" if len(sys.argv) < 2 else sys.argv[1]
    fix_missing_tags(input_file)