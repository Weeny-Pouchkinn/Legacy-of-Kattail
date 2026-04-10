import os
import re
import sys

def fix_missing_tags(log_file_path):
    if not os.path.exists(log_file_path):
        print(f"Error: Could not find '{log_file_path}'. Please make sure the file exists.")
        return

    # 1. Extract unique 3-letter tags using a regular expression
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

    # Create the directories if they don't exist
    os.makedirs(tags_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    # 3. Append to the country tags file
    with open(tags_file, 'a', encoding='utf-8') as f_tags:
        for tag in tags:
            f_tags.write(f'{tag} = "countries/{tag}.txt"\n')
            
    print(f"Appended tag definitions to {tags_file}")

    # 4. Create the dummy history files
    created_count = 0
    for tag in tags:
        history_filepath = os.path.join(history_dir, f"{tag} - DUMMY.txt")
        
        # Only create if the file doesn't already exist
        if not os.path.exists(history_filepath):
            with open(history_filepath, 'w', encoding='utf-8') as f_hist:
                f_hist.write("#Dummy country so the log stops screaming\n")
            created_count += 1

    print(f"Created {created_count} new dummy files in {history_dir}")
    print("Done!")

if __name__ == "__main__":
    # By default, looks for a file named "errors.txt", but you can pass a specific file as an argument.
    input_file = "errors.txt" if len(sys.argv) < 2 else sys.argv[1]
    fix_missing_tags(input_file)