"""
Build side-view walk-cycle pet sprites with pre-baked alpha-interpolated frames
so the runtime never has to do runtime alpha blending (which causes flicker on
Windows when overlapping semi-transparent edges).

Frames are constructed by alpha-compositing stride and pass poses at fractional
weights, producing fully-opaque intermediate frames:
  frame 0: 100% stride
  frame 1:  67% stride + 33% pass
  frame 2:  33% stride + 67% pass
  frame 3: 100% pass

Then mirrored to make the left-facing strip.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

SIZE = 256
WATERMARK_REGION = (0, 0, 230, 140)
TARGET_HEIGHT = 240
FEET_Y = 250
SLIM_SIDE = 0.82
SLIM_FRONT = 0.85


def chroma_key(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    r, g, b = img.split()
    maxrb = ImageChops.lighter(r, b)
    greenness = ImageChops.subtract(g, maxrb)
    alpha = greenness.point(lambda v: max(0, min(255, 255 - v * 6)))
    spill = greenness.point(lambda v: v // 2)
    r2 = ImageChops.add(r, spill)
    b2 = ImageChops.add(b, spill)
    rgba = Image.merge("RGBA", (r2, g, b2, alpha))
    # Harden anti-aliased edge pixels to eliminate DWM flicker from semi-transparent
    # pixels.  α < 128 -> fully transparent, α ≥ 128 -> fully opaque.
    r_ch, g_ch, b_ch, a_ch = rgba.split()
    a_hard = a_ch.point(lambda v: 255 if v >= 128 else 0)
    return Image.merge("RGBA", (r_ch, g_ch, b_ch, a_hard))


def wipe_watermark(img: Image.Image) -> Image.Image:
    img = img.copy()
    px = img.load()
    x0, y0, x1, y1 = WATERMARK_REGION
    for x in range(x0, min(x1, img.width)):
        for y in range(y0, min(y1, img.height)):
            r, g, b, a = px[x, y]
            # After chroma_key (pre-harden), a==0 means truly transparent (green bg),
            # a>0 means character pixel (non-green).  Watermark pixels have a>0.
            if a > 0 and (max(r, g, b) - min(r, g, b) > 30 or max(r, g, b) < 200):
                continue
            px[x, y] = (0, 0, 0, 0)
    return img


def head_center_x(img: Image.Image) -> int:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return img.width // 2
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    crop = img.crop((x0, y0, x1, y0 + max(8, int(h * 0.24))))
    alpha = crop.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    b2 = alpha.getbbox()
    if not b2:
        return (x0 + x1) // 2
    return x0 + (b2[0] + b2[2]) // 2


def normalize(img: Image.Image, slim: float = 1.0) -> Image.Image:
    """Crop to content, scale to TARGET_HEIGHT, head centered, feet at FEET_Y.

    slim < 1.0 horizontally squeezes the character.
    """
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img = img.crop(bbox)
    w, h = img.size
    scale = TARGET_HEIGHT / h
    nw, nh = max(1, round(w * scale * slim)), TARGET_HEIGHT
    img = img.resize((nw, nh), Image.LANCZOS)
    hcx = head_center_x(img)
    x = SIZE // 2 - hcx
    y = FEET_Y - nh
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, (x, y), img)
    return canvas


def harden(img: Image.Image) -> Image.Image:
    """Force every pixel to either fully transparent or fully opaque.
    Eliminates ALL semi-transparent anti-aliasing pixels that cause DWM flicker.
    """
    r, g, b, a = img.split()
    a2 = a.point(lambda v: 255 if v > 0 else 0)
    return Image.merge("RGBA", (r, g, b, a2))


def process(path: str, slim: float = 1.0) -> Image.Image:
    img = Image.open(path)
    img = chroma_key(img)
    img = wipe_watermark(img)
    img = normalize(img, slim=slim)
    # Final pass: nuke any remaining semi-transparent pixels
    img = harden(img)
    return img


# No interpolation — just 2 distinct fully-opaque poses.
# Each cell is the raw normalized sprite with transparent background.
# 4-cell strip: stride / pass / stride / pass.
# All cells are 256×256; transparent background means no flicker from DWM.

def build_walk_strip(stride: Image.Image, passing: Image.Image) -> Image.Image:
    strip = Image.new("RGBA", (SIZE * 4, SIZE), (0, 0, 0, 0))
    strip.paste(stride, (0 * SIZE, 0), stride)
    strip.paste(passing, (1 * SIZE, 0), passing)
    strip.paste(stride, (2 * SIZE, 0), stride)
    strip.paste(passing, (3 * SIZE, 0), passing)
    return strip


def main() -> None:
    stride = process(sys.argv[1], slim=SLIM_SIDE)
    passing = process(sys.argv[2], slim=SLIM_SIDE)

    strip_r = build_walk_strip(stride, passing)
    strip_l = strip_r.transpose(Image.FLIP_LEFT_RIGHT)

    out_dir = Path(__file__).resolve().parent / "assets"
    strip_r.save(out_dir / "pet_walk.png")
    strip_l.save(out_dir / "pet_walk_left.png")

    if len(sys.argv) > 3:
        idle = process(sys.argv[3], slim=SLIM_FRONT)
    else:
        idle = passing.copy()
    idle.save(out_dir / "pet_idle.png")
    print(f"Wrote {out_dir/'pet_walk.png'}, pet_walk_left.png, pet_idle.png")


if __name__ == "__main__":
    main()