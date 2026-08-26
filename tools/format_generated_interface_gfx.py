"""Normalize indentation in generated Legacy of Kattail GFX registries."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "interface"
GENERATED_PREFIXES = ("lok_country_", "lok_shared_", "lok_system_", "zzz_lok_override_")
GENERATED_FILES = {"lok_leader_portraits.gfx"}


def brace_delta(line: str) -> int:
    """Count structural braces while ignoring quoted strings and comments."""
    delta = 0
    quoted = False
    escaped = False
    for char in line:
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted:
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
            continue
        if not quoted and char == "#":
            break
        if not quoted:
            if char == "{":
                delta += 1
            elif char == "}":
                delta -= 1
    return delta


def format_text(text: str) -> str:
    had_final_newline = text.endswith(("\n", "\r"))
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if had_final_newline:
        lines.pop()

    depth = 0
    formatted: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            formatted.append("")
            continue

        closing_brace = stripped.startswith("}")
        indent_depth = max(depth - (1 if closing_brace else 0), 0)
        formatted.append("\t" * indent_depth + stripped)
        depth += brace_delta(stripped)
        if depth < 0:
            raise ValueError("unbalanced closing brace")

    if depth != 0:
        raise ValueError(f"unbalanced braces: final depth {depth}")

    result = "\r\n".join(formatted)
    return result + ("\r\n" if had_final_newline else "")


def should_format(path: Path) -> bool:
    return path.suffix.lower() == ".gfx" and (
        path.name.startswith(GENERATED_PREFIXES) or path.name in GENERATED_FILES
    )


def main() -> None:
    changed = 0
    for path in sorted(INTERFACE.rglob("*.gfx")):
        if not should_format(path):
            continue
        raw = path.read_bytes()
        bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
        text = raw.decode("utf-8-sig")
        formatted = format_text(text)
        output = bom + formatted.encode("utf-8")
        if output != raw:
            path.write_bytes(output)
            changed += 1
    print(f"formatted {changed} generated GFX files")


if __name__ == "__main__":
    main()
