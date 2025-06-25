#!/usr/bin/env python3
"""
Upscale every 40×40 image in the folder to 60×60
with Lanczos → Adaptive-Sharpen, all in linear space.

Needs:
  • ImageMagick installed (≥7 recommended)
  • pip install Wand
"""

from pathlib import Path
from wand.image import Image

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".dds"}

def upscale_and_sharpen(path: Path, sigma: float = 1.0) -> None:
    with Image(filename=str(path)) as img:
        if img.width != 40 or img.height != 40:
            return

        # --- linear colours → resize ---
        img.colorspace = 'rgb'                 # ditch gamma
        img.resize(60, 60, filter='lanczos')   # 1.5×
        
        # --- adaptive edge punch ---
        img.adaptive_sharpen(radius=0, sigma=sigma)  # σ≈1 hits 1-px edges

        # --- back to display space ---
        img.colorspace = 'srgb'
        img.save(filename=str(path.with_stem(path.stem)))

        print(f"✔ {path.name} → {path.stem}_60{path.suffix}")

def main() -> None:
    for p in Path('.').iterdir():
        if p.suffix.lower() in IMAGE_EXTS:
            upscale_and_sharpen(p, sigma=1.0)   # tweak sigma if needed

if __name__ == "__main__":
    main()
