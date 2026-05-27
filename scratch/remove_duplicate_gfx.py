import re

gfx_file_path = r"c:\Users\elowi\Documents\Paradox Interactive\Hearts of Iron IV\mod\Legacy-of-Kattail\interface\lok_national_focus_icons.gfx"

print("Deduplicating lok_national_focus_icons.gfx...")

with open(gfx_file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the header (everything up to first SpriteType block)
# Focus icon GFX files are organized as:
# spriteTypes = {
#     SpriteType = { ... }
# }

header_match = re.match(r'^.*?(?=\b[sS]priteType\s*=)', content, re.DOTALL)
header = header_match.group(0) if header_match else "spriteTypes = {\n"

# Extract all SpriteType blocks
# We parse blocks by matching bracket nesting or simple split/regex since the format is very uniform
# Each block starts with SpriteType = { and ends with }
blocks = re.findall(r'(\b[sS]priteType\s*=\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', content, re.DOTALL)

print(f"Total GFX blocks parsed: {len(blocks)}")

seen_names = set()
unique_blocks = []

for block in blocks:
    name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
    if name_match:
        name = name_match.group(1)
        if name not in seen_names:
            seen_names.add(name)
            unique_blocks.append(block)
    else:
        # Keep blocks without names (if any)
        unique_blocks.append(block)

print(f"Unique GFX blocks kept: {len(unique_blocks)}")

# Reassemble
new_content = header + "\n\t" + "\n\n\t".join(unique_blocks) + "\n}"

with open(gfx_file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Deduplication complete!")
