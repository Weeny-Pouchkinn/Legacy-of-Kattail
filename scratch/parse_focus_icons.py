import re

with open("common/national_focus/TAK.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Find all focus blocks
# Focus blocks are usually:
# focus = {
#     id = TAK_some_id
#     icon = some_icon
#     ...
# }

focuses = []
# Using regex to find focus ID and icon
focus_blocks = re.findall(r'focus\s*=\s*\{([^}]+?)\}', content, re.DOTALL)
for block in focus_blocks:
    id_match = re.search(r'id\s*=\s*([a-zA-Z0-9_-]+)', block)
    icon_match = re.search(r'icon\s*=\s*([a-zA-Z0-9_-]+)', block)
    if id_match and icon_match:
        focuses.append((id_match.group(1), icon_match.group(1)))

print(f"Total focuses found: {len(focuses)}")
print("Focus ID and Icon listing:")
for fid, icon in focuses:
    print(f"  {fid} -> {icon}")
