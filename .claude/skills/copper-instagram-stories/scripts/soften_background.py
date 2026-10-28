"""Softly blur the background of a hair photo while keeping the hair sharp.

Usage: python soften_background.py <in.jpg> <out.jpg> [--brightness 0.9] [--blur 9]

Needs rembg (pip install "rembg[cpu]"); the isnet-general-use model downloads on first run.
The subject mask is dilated a little and feathered so flyaways stay sharp and the edge
doesn't look cut out.
"""
import argparse

from PIL import Image, ImageEnhance, ImageFilter
from rembg import new_session, remove


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--brightness", type=float, default=1.0, help="e.g. 0.9 for 10%% darker")
    p.add_argument("--blur", type=float, default=9, help="background blur radius in px")
    a = p.parse_args()

    im = Image.open(a.src).convert("RGB")
    mask = remove(im, session=new_session("isnet-general-use"), only_mask=True, post_process_mask=True)
    mask = mask.convert("L").filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
    out = Image.composite(im, im.filter(ImageFilter.GaussianBlur(a.blur)), mask)
    if a.brightness != 1.0:
        out = ImageEnhance.Brightness(out).enhance(a.brightness)
    out.save(a.out, quality=92)


if __name__ == "__main__":
    main()
