#!/usr/bin/env python3
"""Write the procedural textures used by the live demos into assets/textures.js as data URIs.

Data URIs keep the demos working when the site is opened straight from disk, where the
browser refuses to load image files into WebGL.
"""
import base64
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image

import textures as tx
from rt import to_image


def uri(img, size, quality=82):
    im = to_image(np.repeat(img[..., None], 3, -1) if img.ndim == 2 else img).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


crate, crate_spec = tx.crate(512)
brick, height, normal, depth = tx.bricks(512)
items = {
    "crate": uri(crate, 256), "crateSpec": uri(crate_spec, 256), "face": uri(tx.face(256), 256),
    "bricks": uri(brick, 512), "bricksNormal": uri(normal, 512, 92), "bricksDepth": uri(depth, 512, 90),
    "planks": uri(tx.planks(512), 512), "checker": uri(tx.checker(256, (0.9, 0.9, 0.9), (0.45, 0.48, 0.52), 8), 256),
}
out = Path(__file__).resolve().parent.parent / "assets" / "textures.js"
out.write_text("window.LM = window.LM || {};\nLM.textures = {\n" +
               "".join(f'  {k}: "{v}",\n' for k, v in items.items()) + "};\n")
print(out, out.stat().st_size // 1024, "KB")
