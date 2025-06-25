#!/usr/bin/env python3
"""
Upscale every 40x40 image in the current folder to 60x60.

Usage:
    python upscale_to_60.py
Dependencies:
    pip install Pillow
"""

from pathlib import Path
from PIL import Image

# Image extensions you care about
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}

def upscale(img_path: Path) -> None:
    """Resize image in place from 40x40 ➜ 60x60."""
    with Image.open(img_path) as im:
        if im.size != (40, 40):
            print(f"skip {img_path.name:20} — size {im.size}")
            return
        upscaled = im.resize((60, 60), Image.Resampling.NEAREST)
        upscaled.save(img_path)
        print(f"✔ upscaled {img_path.name}")

def main() -> None:
    for p in Path(".").iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            upscale(p)

if __name__ == "__main__":
    main()
