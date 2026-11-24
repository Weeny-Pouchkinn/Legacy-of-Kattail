"""The supplied Ministermaker main-script transformation, without file side effects.

Uses ministermaker.py's 37x51 resize, 5-degree rotation, centred 65x67 canvas,
and its own border at (8, 1). The separate Test/ bulk variant is not the entry
point supplied by the user. The bundled border is byte-identical to border.png.
"""
from pathlib import Path

from PIL import Image

BORDER_PATH = Path(__file__).resolve().parent / 'assets/ministermaker_border.png'
SMALL_SIZE = (65, 67)


def generate_small_portrait(source, border=None):
    base = source.convert('RGBA').resize((37, 51))
    base = base.rotate(5, expand=True)
    canvas = Image.new('RGBA', SMALL_SIZE)
    left = (canvas.width - base.width) // 2
    top = (canvas.height - base.height) // 2
    canvas.alpha_composite(base, (left, top))
    if border is None:
        with Image.open(BORDER_PATH) as opened:
            border = opened.convert('RGBA')
    else:
        border = border.convert('RGBA')
    border = border.resize(SMALL_SIZE)
    canvas.alpha_composite(border, (8, 1))
    return canvas
