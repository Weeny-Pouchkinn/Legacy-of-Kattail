import os
import re

def remove_duplicate_provinces_in_block(content):
    def deduplicate(match):
        block = match.group(0)
        numbers = re.findall(r'\d+', block)
        seen = set()
        unique_numbers = []
        for num in numbers:
            if num not in seen:
                unique_numbers.append(num)
                seen.add(num)
        # Preserve indentation
        indent = re.match(r'\s*', block).group(0)
        return f"{indent}provinces={{\n{indent}\t{' '.join(unique_numbers)}\n{indent}}}"

    return re.sub(r'^\s*provinces=\{[^}]*\}', deduplicate, content, flags=re.MULTILINE)

def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = remove_duplicate_provinces_in_block(content)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Cleaned duplicates in: {filename}")

if __name__ == "__main__":
    main()
