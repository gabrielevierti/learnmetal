"""A small software renderer used to draw the figures of learnmetal.

It ray-casts boxes, spheres and planes with numpy and then applies the same
shading math that each chapter implements in the Metal Shading Language.
The images are illustrations of the techniques; they are not screenshots of
the Metal example programs.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, zoom

EPS = 1e-4
W, H = 880, 495
FONT = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(size, bold=False, mono=False):
    try:
        return ImageFont.truetype(MONO if mono else (FONT_BOLD if bold else FONT), size)
    except OSError:
        return ImageFont.load_default(size)


# ---------------------------------------------------------------- math

def v(*a):
    return np.array(a, dtype=np.float64)


def norm(a):
    return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-12)


def dot(a, b):
    return np.sum(a * b, axis=-1, keepdims=True)


def reflect(i, n):
    return i - 2 * dot(i, n) * n


def mix(a, b, t):
    return a * (1 - t) + b * t


def sat(x):
    return np.clip(x, 0, 1)


def T(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return np.diag([x, y, z, 1.0])


def R(deg, axis):
    a = math.radians(deg)
    x, y, z = norm(v(*axis))
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[:3, :3] = [
        [c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
        [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
        [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)],
    ]
    return m


# ---------------------------------------------------------------- camera

class Camera:
    def __init__(self, eye, target, fov=45, up=(0, 1, 0), ortho=None):
        self.eye = v(*eye)
        self.f = norm(v(*target) - self.eye)
        self.r = norm(np.cross(self.f, v(*up)))
        self.u = np.cross(self.r, self.f)
        self.tan = math.tan(math.radians(fov) / 2)
        self.ortho = ortho  # half height of an orthographic view, or None

    def rays(self, w, h):
        xs = (np.arange(w) + 0.5) / w * 2 - 1
        ys = 1 - (np.arange(h) + 0.5) / h * 2
        x, y = np.meshgrid(xs * (w / h), ys)
        if self.ortho:
            o = self.eye + (x[..., None] * self.r + y[..., None] * self.u) * self.ortho
            return o, np.broadcast_to(self.f, o.shape).copy()
        d = self.f + (x[..., None] * self.r + y[..., None] * self.u) * self.tan
        return self.eye, norm(d)

    def project(self, p, w, h):
        """World points -> pixel x, y and view depth."""
        q = p - self.eye
        z = q @ self.f
        x = (q @ self.r) / (z * self.tan * (w / h))
        y = (q @ self.u) / (z * self.tan)
        return (x * 0.5 + 0.5) * w, (0.5 - y * 0.5) * h, z


# ---------------------------------------------------------------- objects

class Obj:
    color = v(0.8, 0.8, 0.8)
    tex = None        # albedo texture (h, w, 3)
    spec = 0.5        # float or texture (h, w)
    shin = 32.0
    emissive = False
    casts = True
    uvscale = 1.0

    def setup(self, kw):
        for k, val in kw.items():
            setattr(self, k, val)
        self.color = np.asarray(self.color, dtype=np.float64)


class Box(Obj):
    NL = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
    RT = np.array([[0, 0, -1], [0, 0, 1], [1, 0, 0], [1, 0, 0], [1, 0, 0], [-1, 0, 0]], float)
    UP = np.array([[0, 1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1], [0, 1, 0], [0, 1, 0]], float)

    def __init__(self, M, **kw):
        self.A = M[:3, :3]
        inv = np.linalg.inv(M)
        self.Ai, self.ti = inv[:3, :3], inv[:3, 3]
        self.setup(kw)

    def local(self, P):
        return P @ self.Ai.T + self.ti

    def hit(self, O, D):
        o = self.local(np.broadcast_to(O, D.shape))
        d = D @ self.Ai.T
        with np.errstate(divide="ignore", invalid="ignore"):
            t1, t2 = (-0.5 - o) / d, (0.5 - o) / d
        tn = np.minimum(t1, t2).max(-1)
        tf = np.maximum(t1, t2).min(-1)
        t = np.where(tn > EPS, tn, tf)
        return np.where((tf >= tn) & (t > EPS), t, np.inf)

    def attrs(self, P, D):
        p = self.local(P)
        ax = np.argmax(np.abs(p), -1)
        sign = np.sign(p[np.arange(len(p)), ax])
        face = ax * 2 + (sign < 0)
        r, u = self.RT[face], self.UP[face]
        uv = np.concatenate([dot(p, r) + 0.5, 0.5 - dot(p, u)], -1) * self.uvscale
        n = norm(self.NL[face] @ self.Ai)
        n = np.where(dot(n, D) > 0, -n, n)
        return n, uv, norm(r @ self.A.T)


class Sphere(Obj):
    def __init__(self, c, r, **kw):
        self.c, self.r = v(*c), r
        self.setup(kw)

    def hit(self, O, D):
        oc = np.broadcast_to(O, D.shape) - self.c
        b = np.sum(oc * D, -1)
        disc = b * b - (np.sum(oc * oc, -1) - self.r ** 2)
        with np.errstate(invalid="ignore"):
            t = -b - np.sqrt(disc)
        return np.where((disc > 0) & (t > EPS), t, np.inf)

    def attrs(self, P, D):
        n = (P - self.c) / self.r
        uv = np.stack([np.arctan2(n[:, 2], n[:, 0]) / (2 * math.pi) + 0.5,
                       0.5 - np.arcsin(np.clip(n[:, 1], -1, 1)) / math.pi], -1) * self.uvscale
        t = norm(np.cross(np.broadcast_to(v(0, 1, 0), n.shape), n) + 1e-9)
        return n, uv, t


class Plane(Obj):
    """Horizontal plane at height y, limited to |x|, |z| <= size."""

    def __init__(self, y=0.0, size=1e9, **kw):
        self.y, self.size = y, size
        self.setup(kw)

    def hit(self, O, D):
        O = np.broadcast_to(O, D.shape)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (self.y - O[..., 1]) / D[..., 1]
        p = O + D * np.where(np.isfinite(t), t, 0)[..., None]
        ok = (t > EPS) & (np.abs(p[..., 0]) <= self.size) & (np.abs(p[..., 2]) <= self.size)
        return np.where(ok, t, np.inf)

    def attrs(self, P, D):
        n = np.broadcast_to(v(0, 1, 0), P.shape)
        uv = np.stack([P[:, 0], P[:, 2]], -1) * self.uvscale
        return n, uv, np.broadcast_to(v(1, 0, 0), P.shape)


# ---------------------------------------------------------------- tracing

def trace(objs, O, D):
    shape = D.shape[:-1]
    best = np.full(shape, np.inf)
    idx = np.full(shape, -1)
    for i, o in enumerate(objs):
        t = o.hit(O, D)
        m = t < best
        best[m], idx[m] = t[m], i
    P = np.broadcast_to(O, D.shape) + D * np.where(np.isfinite(best), best, 0)[..., None]
    N = np.zeros(D.shape)
    Tg = np.zeros(D.shape)
    UV = np.zeros(shape + (2,))
    for i, o in enumerate(objs):
        m = idx == i
        if m.any():
            N[m], UV[m], Tg[m] = o.attrs(P[m], D[m])
    return dict(t=best, idx=idx, hit=idx >= 0, P=P, N=N, UV=UV, T=Tg, D=D)


def occluded(objs, P, N, L, dist):
    """True where something blocks the segment from P toward direction L."""
    O = P + N * 2e-3
    out = np.zeros(P.shape[:-1], bool)
    for o in objs:
        if o.casts and not o.emissive:
            out |= o.hit(O, L) < dist
    return out


def sample(tex, uv, repeat=True):
    """Bilinear texture lookup. uv has v pointing down, like Metal."""
    tex = np.asarray(tex)
    h, w = tex.shape[:2]
    x = uv[..., 0] * w - 0.5
    y = uv[..., 1] * h - 0.5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0), (y - y0)
    if tex.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]

    def at(ix, iy):
        if repeat:
            return tex[iy % h, ix % w]
        return tex[np.clip(iy, 0, h - 1), np.clip(ix, 0, w - 1)]

    return (at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx) * (1 - fy) + \
           (at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx) * fy


def surface(g, objs, linear=False):
    """Per-pixel albedo, specular strength, shininess and emissive mask."""
    shape = g["idx"].shape
    A = np.zeros(shape + (3,))
    Sp = np.zeros(shape + (1,))
    Sh = np.full(shape + (1,), 32.0)
    E = np.zeros(shape, bool)
    for i, o in enumerate(objs):
        m = g["idx"] == i
        if not m.any():
            continue
        a = sample(o.tex, g["UV"][m]) * o.color if o.tex is not None else np.broadcast_to(o.color, (m.sum(), 3))
        A[m] = a ** 2.2 if linear else a
        Sp[m, 0] = sample(o.spec, g["UV"][m]) if isinstance(o.spec, np.ndarray) else o.spec
        Sh[m, 0] = o.shin
        E[m] = o.emissive
    return A, Sp, Sh, E


def light_terms(g, light, eye, objs=None):
    """Direction to the light, its radiance at each pixel, and visibility."""
    P, N = g["P"], g["N"]
    if light["type"] == "dir":
        L = np.broadcast_to(norm(-v(*light["dir"])), P.shape)
        dist = np.full(P.shape[:-1], 1e9)
        atten = 1.0
    else:
        to = v(*light["pos"]) - P
        dist = np.linalg.norm(to, axis=-1)
        L = to / dist[..., None]
        att = light.get("att", (1.0, 0.09, 0.032))
        if att == "inv2":
            atten = (1.0 / (dist * dist))[..., None]
        elif att is None:
            atten = 1.0
        else:
            atten = (1.0 / (att[0] + att[1] * dist + att[2] * dist * dist))[..., None]
        if light["type"] == "spot":
            theta = dot(L, norm(-v(*light["dir"])))
            cut, outer = math.cos(math.radians(light["cut"])), math.cos(math.radians(light["outer"]))
            atten = atten * sat((theta - outer) / (cut - outer))
    vis = 1.0
    if objs is not None:
        vis = (~occluded(objs, P, N, L, dist - 1e-2))[..., None].astype(float)
    return L, v(*light["color"]) * atten, vis


def shade(g, objs, eye, lights, ambient=0.1, blinn=True, shadows=False, linear=False,
          diffuse=True, specular=True, N=None, surf=None):
    """Phong / Blinn-Phong shading of a traced image. Returns linear radiance."""
    A, Sp, Sh, E = surf if surf is not None else surface(g, objs, linear)
    N = g["N"] if N is None else N
    V = norm(eye - g["P"])
    out = ambient * A
    for light in lights:
        L, rad, vis = light_terms(g, light, eye, objs if shadows else None)
        nl = np.maximum(dot(N, L), 0)
        c = 0
        if diffuse:
            c = c + nl * A
        if specular:
            if blinn:
                s = np.maximum(dot(N, norm(L + V)), 0) ** Sh
            else:
                s = np.maximum(dot(V, reflect(-L, N)), 0) ** Sh
            c = c + s * Sp * (nl > 0)
        out = out + c * rad * vis
    out[E] = A[E]
    return out


def finish(img, g=None, bg=(0.1, 0.1, 0.1), srgb=False, ss=2, tonemap=None):
    """Background fill, optional tone map and gamma, then downsample."""
    img = np.array(img, dtype=np.float64)
    if g is not None:
        img[~g["hit"]] = bg if not callable(bg) else bg(g["D"][~g["hit"]])
    if tonemap:
        img = tonemap(img)
    if srgb:
        img = np.clip(img, 0, None) ** (1 / 2.2)
    img = sat(img)
    if ss > 1:
        h, w = img.shape[:2]
        img = img.reshape(h // ss, ss, w // ss, ss, 3).mean((1, 3))
    return img


def render(objs, cam, lights, w=W, h=H, ss=2, bg=(0.1, 0.1, 0.1), srgb=False, **kw):
    O, D = cam.rays(w * ss, h * ss)
    g = trace(objs, O, D)
    return finish(shade(g, objs, cam.eye, lights, linear=srgb, **kw), g, bg, srgb, ss)


# ---------------------------------------------------------------- output

def to_image(img):
    return Image.fromarray((sat(np.asarray(img)) * 255 + 0.5).astype(np.uint8))


def label(img, text, size=17):
    im = to_image(img).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    f = font(size, bold=True)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([10, 10, 24 + tw, 16 + size + 10], 7, fill=(0, 0, 0, 150))
    d.text((17, 14), text, font=f, fill=(255, 255, 255, 255))
    return np.asarray(im.convert("RGB")) / 255.0


def panels(images, labels=None, cols=None, gap=6):
    """Lay several equally sized images out in a grid."""
    if labels:
        images = [label(im, t) for im, t in zip(images, labels)]
    cols = cols or len(images)
    rows = math.ceil(len(images) / cols)
    h, w = images[0].shape[:2]
    out = np.ones((rows * h + (rows - 1) * gap, cols * w + (cols - 1) * gap, 3))
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        out[r * (h + gap):r * (h + gap) + h, c * (w + gap):c * (w + gap) + w] = im
    return out


def fit(img, width=W):
    img = np.asarray(img)
    if img.shape[1] == width:
        return img
    f = width / img.shape[1]
    return sat(zoom(img, (f, f, 1), order=1))


def diagram(nodes, arrows=(), size=(W, 300), title=None):
    """Boxes-and-arrows diagram. nodes: (label, x, y, w, h[, accent])."""
    s = 2
    im = Image.new("RGB", (size[0] * s, size[1] * s), (246, 246, 241))
    d = ImageDraw.Draw(im)
    f = font(15 * s)
    if title:
        d.text((20 * s, 12 * s), title, font=font(14 * s, bold=True), fill=(100, 108, 120))
    for a, b in arrows:
        ax, ay, aw, ah = nodes[a][1:5]
        bx, by, bw, bh = nodes[b][1:5]
        if abs((ay + ah / 2) - (by + bh / 2)) < max(ah, bh) / 2:      # side by side
            p0, p1 = (ax + aw, ay + ah / 2), (bx, by + bh / 2)
            if bx < ax:
                p0, p1 = (ax, ay + ah / 2), (bx + bw, by + bh / 2)
        else:                                                         # stacked
            p0, p1 = (ax + aw / 2, ay + ah), (bx + bw / 2, by)
            if by < ay:
                p0, p1 = (ax + aw / 2, ay), (bx + bw / 2, by + bh)
        d.line([p0[0] * s, p0[1] * s, p1[0] * s, p1[1] * s], fill=(90, 96, 106), width=2 * s)
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for da in (2.6, -2.6):
            d.line([p1[0] * s, p1[1] * s,
                    (p1[0] + 9 * math.cos(ang + da)) * s, (p1[1] + 9 * math.sin(ang + da)) * s],
                   fill=(90, 96, 106), width=2 * s)
    for n in nodes:
        text, x, y, w, h = n[:5]
        accent = len(n) > 5 and n[5]
        d.rounded_rectangle([x * s, y * s, (x + w) * s, (y + h) * s], 9 * s,
                            fill=(255, 236, 222) if accent else (255, 255, 255),
                            outline=(194, 71, 10) if accent else (60, 66, 76), width=2 * s)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            ff = font(13 * s, mono=True) if line.startswith("`") else f
            line = line.strip("`")
            tw = d.textlength(line, font=ff)
            d.text(((x + w / 2) * s - tw / 2, (y + h / 2) * s + (i - len(lines) / 2) * 20 * s + 1 * s),
                   line, font=ff, fill=(32, 36, 42))
    return np.asarray(im.resize(size, Image.LANCZOS)) / 255.0


def blur(img, sigma):
    return gaussian_filter(img, sigma=(sigma, sigma, 0))
