#!/usr/bin/env python3
"""Render every figure of the site into assets/img/.

    pip install numpy scipy pillow
    python3 tools/render_figures.py            # everything
    python3 tools/render_figures.py shadow     # only figures whose name contains "shadow"
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import figures_advanced
import figures_basic
from rt import fit, to_image

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"


def main():
    wanted = sys.argv[1:]
    for name, fn in figures_basic.FIGURES + figures_advanced.FIGURES:
        if wanted and not any(w in name for w in wanted):
            continue
        start = time.time()
        img = fit(fn())
        path = OUT / f"{name}.webp"
        path.parent.mkdir(parents=True, exist_ok=True)
        to_image(img).save(path, "WEBP", quality=86, method=6)
        print(f"{name:45s} {img.shape[1]}x{img.shape[0]}  {time.time() - start:5.1f}s  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
