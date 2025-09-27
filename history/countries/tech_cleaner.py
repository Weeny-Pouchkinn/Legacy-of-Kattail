import os
import re
import sys

# Define the pattern to search for.
# This pattern matches the literal string "set_technology =", followed by an opening brace "{",
# any content non-greedily (including newlines due to re.DOTALL), and the matching closing brace "}".
# It also handles any surrounding whitespace, including the newline after the closing brace.
BLOCK_PATTERN = re.compile(
    r'set_technology\s*=\s*\{.*?\}\s*',
    re.DOTALL
)

def clean_files_in_directory(directory_path):
    """
    Looks inside every file in the given directory and removes the target block.
    """
    # Get the name of the script itself to avoid trying to modify it
    script_name = os.path.basename(__file__)
    
    print(f"--- Starting file cleanup in: {directory_path} ---")

    files_processed = 0
    files_modified = 0

    try:
        # Iterate over all files in the specified directory
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            # Skip the script file itself and any directories
            if filename == script_name or os.path.isdir(file_path):
                continue

            try:
                # Open the file and read its entire content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Perform the substitution using the compiled regex pattern
                modified_content = BLOCK_PATTERN.sub('', original_content)
                
                files_processed += 1

                # Check if the content was actually changed
                if modified_content != original_content:
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    
                    files_modified += 1
                    print(f"[MODIFIED] Successfully removed block from: {filename}")
                else:
                    print(f"[CLEAN] Block not found in: {filename}")

            except UnicodeDecodeError:
                # Handle binary files or files with non-utf8 encoding
                print(f"[SKIPPED] Cannot read {filename} (not valid text file or encoding issue).")
            except Exception as e:
                print(f"[ERROR] Could not process {filename}: {e}")

    except Exception as e:
        print(f"An error occurred during directory traversal: {e}")
        return

    print("--- Cleanup Complete ---")
    print(f"Total files scanned: {files_processed}")
    print(f"Total files modified: {files_modified}")

if __name__ == "__main__":
    # The script will clean files in the same directory it is run from
    current_directory = os.path.abspath(os.path.dirname(sys.argv[0]))
    clean_files_in_directory(current_directory)
