"""Procedural textures and the procedural sky used by the figure renderer."""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from rt import v, norm, dot, mix, sat

rng = np.random.default_rng(7)


def _noise(n, scale):
    return gaussian_filter(rng.random((n, n)), scale, mode="wrap")


def crate(n=256):
    """Wooden crate with a steel frame: (diffuse rgb, specular gray)."""
    y, x = np.mgrid[0:n, 0:n] / n
    grain = gaussian_filter(rng.random((n, n)), (n / 6, 0.8), mode="wrap")
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    wood = mix(v(0.42, 0.26, 0.12), v(0.66, 0.45, 0.24), grain[..., None])
    plank = np.abs(((x * 5) % 1) - 0.5) > 0.47
    wood[plank] *= 0.45
    b = 0.11
    border = (x < b) | (x > 1 - b) | (y < b) | (y > 1 - b)
    brace = np.abs(x - y) < 0.05
    steel_mask = border | brace
    scratch = gaussian_filter(rng.random((n, n)), (0.6, 5), mode="wrap")
    scratch = (scratch - scratch.min()) / (scratch.max() - scratch.min())
    steel = mix(v(0.33, 0.35, 0.38), v(0.62, 0.64, 0.67), scratch[..., None])
    edge = steel_mask & ~((x < b - 0.012) | (x > 1 - b + 0.012) | (y < b - 0.012) | (y > 1 - b + 0.012)
                          | (np.abs(x - y) < 0.038))
    diffuse = np.where(steel_mask[..., None], steel, wood)
    diffuse[edge] *= 0.55
    for cx in (b / 2, 1 - b / 2):
        for cy in (b / 2, 0.5, 1 - b / 2):
            for px, py in ((cx, cy), (cy, cx)):
                r = np.hypot(x - px, y - py)
                diffuse[r < 0.022] = v(0.2, 0.21, 0.23)
    specular = np.where(steel_mask, 0.35 + 0.65 * scratch, 0.0)
    return diffuse, specular


def face(n=256):
    """A simple smiley on a pale background, used as the second texture."""
    im = Image.new("RGB", (n, n), (235, 240, 245))
    d = ImageDraw.Draw(im)
    d.ellipse([n * 0.1, n * 0.1, n * 0.9, n * 0.9], fill=(250, 205, 60), outline=(60, 50, 20), width=n // 50)
    for ex in (0.36, 0.64):
        d.ellipse([n * (ex - 0.05), n * 0.34, n * (ex + 0.05), n * 0.48], fill=(60, 50, 20))
    d.arc([n * 0.3, n * 0.35, n * 0.7, n * 0.75], 20, 160, fill=(60, 50, 20), width=n // 40)
    return np.asarray(im) / 255.0


def bricks(n=512):
    """Brick wall: (albedo, height, normal map, depth)."""
    y, x = np.mgrid[0:n, 0:n] / n
    rows, cols = 8, 4
    ry = y * rows
    row = np.floor(ry)
    rx = x * cols + 0.5 * (row % 2)
    col = np.floor(rx)
    fx, fy = rx - col, ry - row
    mx, my = 0.035, 0.09
    edge = np.minimum(np.minimum(fx, 1 - fx) / mx, np.minimum(fy, 1 - fy) / my)
    height = sat(edge) ** 0.6
    tint = np.sin(row * 12.9898 + (col % cols) * 78.233) * 43758.5453
    tint = (tint - np.floor(tint))[..., None]
    rough = _noise(n, 2)[..., None]
    rough = (rough - rough.min()) / (rough.max() - rough.min())
    brick = mix(v(0.50, 0.17, 0.11), v(0.68, 0.30, 0.20), tint) * (0.8 + 0.4 * rough)
    mortar = v(0.62, 0.60, 0.56) * (0.8 + 0.3 * rough)
    albedo = mix(mortar, brick, height[..., None] ** 2)
    height = height * (0.9 + 0.1 * rough[..., 0])
    # Normal map, +y pointing up in the image (rows grow downward).
    strength = 5.0
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * n / 2 / n * strength * 8
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * n / 2 / n * strength * 8
    nrm = norm(np.stack([-dx, dy, np.ones_like(dx)], -1))
    return albedo, height, nrm * 0.5 + 0.5, 1 - height


def planks(n=512):
    """Wooden floor boards."""
    y, x = np.mgrid[0:n, 0:n] / n
    board = np.floor(y * 6)
    grain = gaussian_filter(rng.random((n, n)), (0.8, n / 5), mode="wrap")
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    shade = (np.sin(board * 91.7) * 0.5 + 0.5)[..., None]
    wood = mix(v(0.36, 0.23, 0.12), v(0.60, 0.42, 0.24), grain[..., None]) * (0.8 + 0.3 * shade)
    gap = (np.abs(((y * 6) % 1) - 0.5) > 0.485) | (np.abs((((x + board * 0.37) * 2) % 1) - 0.5) > 0.495)
    wood[gap] *= 0.4
    return wood


def checker(n=256, a=(0.85, 0.85, 0.85), b=(0.35, 0.37, 0.4), k=8):
    y, x = np.mgrid[0:n, 0:n]
    m = ((x // (n // k)) + (y // (n // k))) % 2
    return np.where(m[..., None] == 0, v(*a), v(*b))


SUN = norm(v(0.55, 0.42, -0.6))


def env(d, hdr=True):
    """Procedural sky with a sun, hills and a checkered ground. d: unit directions."""
    y = d[..., 1:2]
    sky = mix(v(0.78, 0.86, 0.98), v(0.16, 0.36, 0.80), sat(y) ** 0.55)
    s = sat(dot(d, SUN))
    sky = sky + v(1.0, 0.9, 0.7) * (s ** 30 * 0.5 + (s ** 900 * 60 if hdr else s ** 900 * 2))
    az = np.arctan2(d[..., 2:3], d[..., 0:1])
    hill = 0.05 + 0.035 * np.sin(az * 5) + 0.02 * np.sin(az * 11 + 1)
    sky = np.where(y < hill, v(0.16, 0.30, 0.16) * (0.7 + 2 * sat(y / 0.1)), sky)
    with np.errstate(divide="ignore", invalid="ignore"):
        gx = np.where(y < 0, d[..., 0:1] / -y, 0)
        gz = np.where(y < 0, d[..., 2:3] / -y, 0)
    chk = (np.floor(gx * 1.2) + np.floor(gz * 1.2)) % 2
    ground = mix(v(0.50, 0.47, 0.42), v(0.30, 0.28, 0.26), chk)
    ground = mix(v(0.42, 0.44, 0.40), ground, sat(-y * 3.5))
    return np.where(y > 0, sky, ground)


def equirect_dirs(w, h):
    u = (np.arange(w) + 0.5) / w
    t = (np.arange(h) + 0.5) / h
    phi, theta = np.meshgrid((u - 0.5) * 2 * math.pi, (0.5 - t) * math.pi)
    return np.stack([np.cos(theta) * np.cos(phi), np.sin(theta), np.cos(theta) * np.sin(phi)], -1)


def equirect_uv(d):
    return np.stack([np.arctan2(d[..., 2], d[..., 0]) / (2 * math.pi) + 0.5,
                     0.5 - np.arcsin(np.clip(d[..., 1], -1, 1)) / math.pi], -1)
