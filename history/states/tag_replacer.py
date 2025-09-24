import os
import sys
import re

def replace_tags_in_files(tags):
    """
    Looks for specified tags in files and replaces/comments out lines.
    This version correctly handles and preserves indentation.

    Args:
        tags (list): A list of 3-letter tag strings to search for.
    """
    print(f"Starting to process files for the following tags: {tags}")
    
    # Get all files in the current directory
    files_in_directory = os.listdir('.')

    # Iterate through each item in the directory
    for filename in files_in_directory:
        # We only want to process regular files, not directories or the script itself
        if os.path.isfile(filename) and filename != os.path.basename(__file__):
            try:
                # Read the entire file content
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original_content = content
                
                # Iterate through each tag to perform the replacement
                for tag in tags:
                    # Create a regular expression pattern to find both lines while
                    # capturing the indentation of the first line.
                    pattern = re.compile(
                        rf"^(\s*)(owner\s*=\s*{tag}.*)\n\1(add_core_of\s*=\s*{tag}.*)",
                        re.MULTILINE
                    )

                    # Define the replacement string. We use the captured indentation (\1)
                    # to align all the new and commented lines.
                    replacement = rf"\1owner = ZZZ\n\1add_core_of = ZZZ\n\1# \2\n\1# \3"

                    # Perform the substitution on the content
                    content = pattern.sub(replacement, content)

                # If the content was modified, write it back to the file
                if content != original_content:
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"Successfully processed and updated file: {filename}")
                else:
                    print(f"No matching tags found in file: {filename}")

            except Exception as e:
                # Print an error message if something goes wrong
                print(f"An error occurred while processing {filename}: {e}")

if __name__ == "__main__":
    # Check if the user has provided tags as command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python tag_replacer.py TAG1 TAG2 TAG3 ...")
        print("Example: python tag_replacer.py PAL PLR AAA")
    else:
        # Get the tags from the command-line arguments
        tags_to_replace = sys.argv[1:]
        replace_tags_in_files(tags_to_replace)