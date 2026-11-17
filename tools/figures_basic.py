"""Figures for Getting Started, Lighting, Model Loading and Advanced Metal."""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import convolve, maximum_filter

import textures as tx
from rt import (W, H, Box, Camera, Plane, Sphere, R, S, T, blur, diagram, dot, finish, fit, font, mix, norm,
                occluded, panels, reflect, render, sample, sat, shade, surface, to_image, trace, v)

PW, PH = 440, 248          # one panel of a two-column figure
TEAL = v(0.2, 0.3, 0.3)
CRATE, CRATE_S = tx.crate()
FACE = tx.face()
PLANKS = tx.planks()

CUBES = [(0, 0, 0), (2, 5, -15), (-1.5, -2.2, -2.5), (-3.8, -2, -12.3), (2.4, -0.4, -3.5),
         (-1.7, 3, -7.5), (1.3, -2, -2.5), (1.5, 2, -2.5), (1.5, 0.2, -1.5), (-1.3, 1, -1.5)]
POINT_LIGHTS = [(0.7, 0.2, 2.0), (2.3, -3.3, -4.0), (-4.0, 2.0, -12.0), (0.0, 0.0, -3.0)]


def cubes(**kw):
    kw = {"tex": CRATE, "spec": CRATE_S, **kw}
    return [Box(T(*p) @ R(20 * i, (1, 0.3, 0.5)), **kw) for i, p in enumerate(CUBES)]


def lamp(pos, color=(1, 1, 1), s=0.14):
    return Box(T(*pos) @ S(s), color=color, emissive=True, casts=False)


def ndc(w, h, ss=3):
    xs = (np.arange(w * ss) + 0.5) / (w * ss) * 2 - 1
    ys = 1 - (np.arange(h * ss) + 0.5) / (h * ss) * 2
    return np.meshgrid(xs, ys)


def down(img, ss=3):
    h, w = img.shape[:2]
    return img.reshape(h // ss, ss, w // ss, ss, 3).mean((1, 3))


def tri2d(pts, cols, w=W, h=H, bg=TEAL, flat=False):
    x, y = ndc(w, h)
    (x0, y0), (x1, y1), (x2, y2) = pts
    area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    b1 = ((x - x0) * (y2 - y0) - (x2 - x0) * (y - y0)) / area
    b2 = ((x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)) / area
    b0 = 1 - b1 - b2
    inside = (b0 >= 0) & (b1 >= 0) & (b2 >= 0)
    c = np.asarray(cols, float)
    col = np.broadcast_to(c[0], x.shape + (3,)) if flat else \
        b0[..., None] * c[0] + b1[..., None] * c[1] + b2[..., None] * c[2]
    return down(np.where(inside[..., None], col, bg))


def quad2d(M=np.eye(3), tex=CRATE, w=W, h=H, uvfn=None, tex2=None):
    """Textured unit quad (corners at +-0.5) transformed by a 3x3 matrix in NDC."""
    x, y = ndc(w, h)
    inv = np.linalg.inv(M)
    lx = inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]
    ly = inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]
    inside = (np.abs(lx) <= 0.5) & (np.abs(ly) <= 0.5)
    uv = np.stack([lx + 0.5, 0.5 - ly], -1)
    col = uvfn(uv) if uvfn else sample(tex, uv)
    if tex2 is not None:
        col = mix(col, sample(tex2, uv), 0.2)
    return down(np.where(inside[..., None], col, TEAL))


# ------------------------------------------------------------ getting started

def gs_introduction():
    n = [("MTLDevice", 20, 120, 120, 56, True), ("MTLCommandQueue", 180, 40, 170, 56),
         ("MTLCommandBuffer", 390, 40, 180, 56), ("Render command\nencoder", 610, 40, 170, 56),
         ("Pipeline state\nBuffers, textures", 180, 200, 170, 56), ("Draw calls", 610, 200, 170, 56),
         ("commit()", 390, 200, 180, 56, True)]
    return diagram(n, [(0, 1), (1, 2), (2, 3), (0, 4), (3, 5), (4, 5), (2, 6)], title="How the objects relate")


def gs_project_setup():
    n = [("App", 20, 110, 90, 56), ("ContentView\n(SwiftUI)", 150, 110, 150, 56),
         ("MetalView\n(representable)", 340, 110, 170, 56), ("MTKView", 550, 110, 110, 56, True),
         ("Renderer\n(MTKViewDelegate)", 700, 110, 160, 56, True), ("Shaders.metal", 700, 215, 160, 46)]
    return diagram(n, [(0, 1), (1, 2), (2, 3), (3, 4), (5, 4)], size=(W, 290), title="Project structure")


def gs_hello_view():
    return np.broadcast_to(TEAL, (H, W, 3)).copy()


def gs_hello_triangle():
    orange = [(1, 0.5, 0.2)] * 3
    a = tri2d([(-0.5, -0.5), (0.5, -0.5), (0, 0.5)], orange, PW, PH)
    im = to_image(np.broadcast_to(TEAL, (PH * 3, PW * 3, 3)))
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((x * 0.5 + 0.5) * PW * 3, (0.5 - y * 0.5) * PH * 3)
    q = [P(0.5, 0.5), P(0.5, -0.5), P(-0.5, -0.5), P(-0.5, 0.5)]
    for i, j in [(0, 1), (1, 3), (3, 0), (1, 2), (2, 3)]:
        d.line([q[i], q[j]], fill=(255, 128, 51), width=5)
    b = np.asarray(im.resize((PW, PH), Image.LANCZOS)) / 255.0
    return panels([a, b], ["drawPrimitives", "Indexed rectangle, .lines fill mode"])


def gs_shaders():
    return tri2d([(-0.5, -0.5), (0.5, -0.5), (0, 0.5)], [(1, 0, 0), (0, 1, 0), (0, 0, 1)])


def gs_textures():
    return panels([quad2d(w=PW, h=PH), quad2d(w=PW, h=PH, tex2=FACE)],
                  ["One texture", "mix(texture0, texture1, 0.2)"])


def gs_address_modes():
    def mode(kind):
        def f(uv):
            u = uv * 3 - 1
            if kind == "repeat":
                return sample(FACE, u)
            if kind == "mirror":
                m = np.abs(((u + 1) % 2) - 1)
                return sample(FACE, m, repeat=False)
            c = sample(FACE, np.clip(u, 0.002, 0.998), repeat=False)
            if kind == "zero":
                out = (u < 0).any(-1) | (u > 1).any(-1)
                c = np.where(out[..., None], 0.0, c)
            return c
        return f
    sq = np.array([[1.9 * PH / PW, 0, 0], [0, 1.9, 0], [0, 0, 1]])
    names = [("repeat", ".repeat"), ("mirror", ".mirrorRepeat"), ("edge", ".clampToEdge"), ("zero", ".clampToZero")]
    return panels([quad2d(sq, w=PW, h=PH, uvfn=mode(k)) for k, _ in names], [n for _, n in names], cols=2)


def gs_transformations():
    a = math.radians(35)
    rot = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    M = np.array([[1, 0, 0.5], [0, 1, -0.5], [0, 0, 1]]) @ rot @ np.diag([0.5, 0.5, 1])
    return quad2d(M)


class FarBox(Box):
    """Returns the far intersection, imitating faces drawn without a depth test."""

    def hit(self, O, D):
        o = self.local(np.broadcast_to(O, D.shape))
        d = D @ self.Ai.T
        with np.errstate(divide="ignore", invalid="ignore"):
            t1, t2 = (-0.5 - o) / d, (0.5 - o) / d
        tn, tf = np.minimum(t1, t2).max(-1), np.maximum(t1, t2).min(-1)
        return np.where((tf >= tn) & (tf > 1e-4), tf, np.inf)


def gs_coordinate_systems():
    cam = Camera((0, 0, 3), (0, 0, 0))
    M = R(50, (0.5, 1, 0))
    flat = dict(ambient=1.0, bg=TEAL, w=PW, h=PH)
    a = render([FarBox(M, tex=CRATE)], cam, [], **flat)
    b = render([Box(M, tex=CRATE)], cam, [], **flat)
    return panels([a, b], ["No depth test", "depthCompareFunction = .less"])


def gs_ten_cubes():
    return render(cubes(), Camera((0, 0, 3), (0, 0, 0)), [], ambient=1.0, bg=TEAL)


def gs_camera():
    return render(cubes(), Camera((4.5, 1.8, 3.5), (0, 0, -3.5)), [], ambient=1.0, bg=TEAL)


def gs_review():
    n = [("Local\nspace", 15, 60, 110, 60), ("World\nspace", 160, 60, 110, 60), ("View\nspace", 305, 60, 110, 60),
         ("Clip\nspace", 450, 60, 110, 60, True), ("NDC", 595, 60, 110, 60), ("Pixels", 740, 60, 110, 60)]
    return diagram(n, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)], size=(W, 170),
                   title="model matrix  →  view matrix  →  projection matrix  →  divide by w  →  viewport")


# ------------------------------------------------------------ lighting

LIGHT = (1.2, 1.0, 2.0)
LCAM = Camera((-1.3, 1.3, 3.6), (0.5, 0.25, 0.6), fov=36)
CORAL = (1.0, 0.5, 0.31)


def li_colors():
    return render([Box(np.eye(4), color=CORAL), lamp(LIGHT)], LCAM, [], ambient=1.0)


def li_basic():
    objs = [Box(np.eye(4), color=CORAL, spec=0.5), lamp(LIGHT)]
    L = [dict(type="point", pos=LIGHT, color=(1, 1, 1), att=None)]
    kw = dict(blinn=False, w=440, h=330)
    a = render(objs, LCAM, [], ambient=0.1, **kw)
    b = render(objs, LCAM, L, ambient=0.1, specular=False, **kw)
    c = render(objs, LCAM, L, ambient=0.1, **kw)
    return panels([a, b, c], ["Ambient", "+ Diffuse", "+ Specular"])


def li_materials():
    mats = [((0.08, 0.61, 0.08), 0.70, 77), ((0.75, 0.61, 0.23), 0.55, 51),
            ((0.0, 0.51, 0.51), 0.5, 32), ((0.5, 0.4, 0.4), 0.25, 10)]
    objs = [Box(T(-2.4 + 1.6 * i, 0, 0) @ R(30, (0.3, 1, 0)), color=c, spec=s, shin=sh)
            for i, (c, s, sh) in enumerate(mats)]
    objs.append(lamp((0, 1.4, 2.2)))
    L = [dict(type="point", pos=(0, 1.4, 2.2), color=(1, 1, 1), att=None)]
    img = render(objs, Camera((0, 1.3, 4.6), (0, 0, 0)), L, ambient=0.25, blinn=False, h=330)
    im = to_image(img)
    d = ImageDraw.Draw(im)
    for i, name in enumerate(["Emerald", "Gold", "Cyan plastic", "Red rubber"]):
        x = W / 2 + (-2.4 + 1.6 * i) * 83
        d.text((x - d.textlength(name, font=font(16)) / 2, 292), name, font=font(16), fill=(230, 230, 230))
    return np.asarray(im) / 255.0


def li_lighting_maps():
    L = [dict(type="point", pos=LIGHT, color=(1, 1, 1), att=None)]
    kw = dict(ambient=0.2, blinn=False, w=PW, h=PH)
    a = render([Box(np.eye(4), tex=CRATE, spec=0.5), lamp(LIGHT)], LCAM, L, **kw)
    b = render([Box(np.eye(4), tex=CRATE, spec=CRATE_S), lamp(LIGHT)], LCAM, L, **kw)
    return panels([a, b], ["Diffuse map, uniform specular", "Diffuse + specular map"])


def li_light_casters():
    cam = Camera((0, 0, 3), (0, 0, 0))
    kw = dict(blinn=False, w=440, h=330, bg=(0.05, 0.05, 0.05))
    a = render(cubes(), cam, [dict(type="dir", dir=(-0.2, -1.0, -0.3), color=(0.9, 0.9, 0.9))], ambient=0.1, **kw)
    b = render(cubes() + [lamp(LIGHT)], cam, [dict(type="point", pos=LIGHT, color=(1, 1, 1))], ambient=0.1, **kw)
    c = render(cubes(), cam, [dict(type="spot", pos=(0, 0, 3), dir=(0, 0, -1), cut=12.5, outer=17.5,
                                   color=(1, 1, 1))], ambient=0.06, **kw)
    return panels([a, b, c], ["Directional", "Point", "Spot"])


def multi_light_scene():
    cols = [(1, 0.6, 0.3), (0.4, 0.6, 1), (0.5, 1, 0.5), (1, 0.4, 0.5)]
    objs = cubes() + [lamp(p, c) for p, c in zip(POINT_LIGHTS, cols)]
    L = [dict(type="dir", dir=(-0.2, -1.0, -0.3), color=(0.35, 0.35, 0.4))]
    L += [dict(type="point", pos=p, color=c) for p, c in zip(POINT_LIGHTS, cols)]
    return objs, L


def li_multiple_lights(w=W, h=H):
    objs, L = multi_light_scene()
    return render(objs, Camera((0, 0, 3), (0, 0, 0)), L, ambient=0.06, blinn=False, bg=(0.04, 0.04, 0.06), w=w, h=h)


def li_review():
    n = [("Ambient", 40, 70, 150, 60), ("Diffuse\nmax(dot(N, L), 0)", 250, 70, 190, 60),
         ("Specular\npow(dot(N, H), shininess)", 500, 70, 250, 60), ("Final color", 320, 190, 180, 56, True)]
    return diagram(n, [(0, 3), (1, 3), (2, 3)], size=(W, 270), title="The three terms of the Phong model")


# ------------------------------------------------------------ model loading

def ml_model_io():
    n = [("MDLAsset", 360, 20, 160, 46, True), ("MDLObject\n(transform)", 180, 100, 170, 56),
         ("MDLMesh\nvertex buffers", 530, 100, 170, 56), ("MDLSubmesh\nindex buffer", 400, 200, 170, 56),
         ("MDLSubmesh\nindex buffer", 660, 200, 170, 56), ("MDLMaterial", 400, 295, 170, 44),
         ("MDLMaterial", 660, 295, 170, 44), ("MDLMesh", 100, 200, 150, 56)]
    return diagram(n, [(0, 1), (0, 2), (2, 3), (2, 4), (3, 5), (4, 6), (1, 7)], size=(W, 355),
                   title="A model file as Model I/O sees it")


def ml_mesh():
    s = 2
    im = Image.new("RGB", (W * s, 250 * s), (246, 246, 241))
    d = ImageDraw.Draw(im)
    d.text((20 * s, 12 * s), "One vertex = 32 bytes", font=font(14 * s, bold=True), fill=(100, 108, 120))
    parts = [("position", "float3", 12, (255, 236, 222)), ("normal", "float3", 12, (226, 238, 252)),
             ("uv", "float2", 8, (228, 244, 226))]
    x = 40
    for rep in range(2):
        for name, ty, size, col in parts:
            w = size * 11
            d.rectangle([x * s, 60 * s, (x + w) * s, 120 * s], fill=col if rep == 0 else (236, 236, 232),
                        outline=(60, 66, 76), width=2 * s)
            d.text(((x + 8) * s, 68 * s), name, font=font(15 * s), fill=(32, 36, 42))
            d.text(((x + 8) * s, 92 * s), ty, font=font(12 * s, mono=True), fill=(100, 108, 120))
            if rep == 0:
                d.text((x * s, 128 * s), f"offset {sum(p[2] for p in parts[:parts.index((name, ty, size, col))])}",
                       font=font(12 * s), fill=(100, 108, 120))
            x += w
    d.text((40 * s, 170 * s), "Index buffer (one per submesh)", font=font(14 * s, bold=True), fill=(100, 108, 120))
    for i, val in enumerate([0, 1, 2, 2, 1, 3, 4, 5, 6, 6, 5, 7]):
        d.rectangle([(40 + i * 42) * s, 198 * s, (82 + i * 42) * s, 232 * s], fill=(255, 255, 255),
                    outline=(60, 66, 76), width=2 * s)
        d.text(((55 + i * 42) * s, 205 * s), str(val), font=font(14 * s, mono=True), fill=(32, 36, 42))
    return np.asarray(im.resize((W, 250), Image.LANCZOS)) / 255.0


def ml_model():
    chk = tx.checker(256, (0.9, 0.9, 0.9), (0.55, 0.58, 0.62), 8)
    objs = [Sphere((-1.7, 0, 0), 0.75, tex=chk, color=(0.9, 0.5, 0.3), uvscale=2, spec=0.6, shin=64),
            Box(R(35, (0.2, 1, 0.1)) @ S(1.1), tex=CRATE, spec=CRATE_S),
            Box(T(1.8, -0.1, 0) @ R(-20, (0, 1, 0)) @ S(0.7, 1.3, 0.7), color=(0.35, 0.55, 0.85), spec=0.7, shin=48),
            Plane(-0.75, 6, tex=PLANKS, uvscale=0.25, spec=0.15)]
    L = [dict(type="point", pos=(2, 3, 3), color=(1, 1, 1), att=None)]
    return render(objs, Camera((0, 1.4, 5), (0, 0, 0)), L, ambient=0.15, shadows=True, bg=(0.12, 0.13, 0.16))


# ------------------------------------------------------------ advanced metal

def floor_scene():
    return [Box(T(-1.0, 0.0, -1.0), tex=CRATE, spec=CRATE_S), Box(T(2.0, 0.0, 0.0), tex=CRATE, spec=CRATE_S),
            Plane(-0.5, 12, tex=PLANKS, uvscale=0.2, spec=0.1)]


FCAM = Camera((0.3, 1.4, 4.5), (0.4, 0, 0))


def am_depth():
    cam = Camera((0, 0, 3), (0, 0, 0))
    O, D = cam.rays(PW * 2, PH * 2)
    g = trace(cubes() + [Plane(-3.2, 40)], O, D)
    z = np.where(g["hit"], dot(g["P"] - cam.eye, cam.f)[..., 0], 100.0)
    near, far = 0.1, 100.0
    depth = far * (z - near) / (z * (far - near))
    a = finish(np.repeat(depth[..., None], 3, -1))
    b = finish(np.repeat((z / 25.0)[..., None], 3, -1))
    return panels([a, b], ["Depth buffer value", "Linearized distance"])


def am_stencil():
    objs = floor_scene()
    O, D = FCAM.rays(W * 2, H * 2)
    g = trace(objs, O, D)
    L = [dict(type="dir", dir=(-0.4, -1, -0.5), color=(0.9, 0.9, 0.9))]
    img = shade(g, objs, FCAM.eye, L, ambient=0.3)
    mask = g["idx"] < 2
    mask &= g["hit"]
    grown = maximum_filter(mask, size=25)
    img[grown & ~mask] = v(1.0, 0.55, 0.1)
    return finish(img, g, bg=(0.1, 0.1, 0.1))


def am_blending():
    objs = floor_scene()
    O, D = FCAM.rays(W * 2, H * 2)
    g = trace(objs, O, D)
    L = [dict(type="dir", dir=(-0.4, -1, -0.5), color=(0.9, 0.9, 0.9))]
    img = shade(g, objs, FCAM.eye, L, ambient=0.3)
    img[~g["hit"]] = 0.1
    wins = [((-1.4, 0, 0.6), (0.85, 0.15, 0.15)), ((1.2, 0, 1.2), (0.15, 0.4, 0.9)),
            ((0.2, 0, 2.0), (0.2, 0.75, 0.3)), ((2.6, 0, 1.6), (0.9, 0.75, 0.1))]
    wins.sort(key=lambda w_: -np.linalg.norm(v(*w_[0]) - FCAM.eye))
    for pos, col in wins:
        t = Box(T(*pos) @ S(1, 1, 0.001)).hit(O, D)
        m = t < g["t"]
        img[m] = mix(img[m], v(*col), 0.45)
    return finish(img)


def am_face_culling():
    s = 2
    im = Image.new("RGB", (W * s, 280 * s), (246, 246, 241))
    d = ImageDraw.Draw(im)
    for k, (title, order, fill) in enumerate([("Counter-clockwise: front face", [0, 1, 2], (255, 236, 222)),
                                              ("Clockwise: back face, culled", [0, 2, 1], (232, 232, 228))]):
        ox = 60 + k * 430
        pts = [(ox + 30, 230), (ox + 310, 230), (ox + 170, 60)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=fill, outline=(60, 66, 76), width=2 * s)
        d.text((ox * s, 14 * s), title, font=font(15 * s, bold=True), fill=(60, 66, 76))
        for i, idx in enumerate(order):
            x, y = pts[idx]
            d.ellipse([(x - 14) * s, (y - 14) * s, (x + 14) * s, (y + 14) * s], fill=(194, 71, 10))
            d.text(((x - 5) * s, (y - 10) * s), str(i + 1), font=font(15 * s, bold=True), fill=(255, 255, 255))
        cx, cy = ox + 170, 175
        a0, a1 = (200, 520) if k == 0 else (20, 340)
        d.arc([(cx - 38) * s, (cy - 38) * s, (cx + 38) * s, (cy + 38) * s], a0, a1, fill=(90, 96, 106), width=3 * s)
        end = math.radians(a0 if k == 0 else a1)
        ex, ey = cx + 38 * math.cos(end), cy + 38 * math.sin(end)
        dirn = -1 if k == 0 else 1
        tx_, ty_ = -math.sin(end) * dirn, math.cos(end) * dirn
        for sgn in (-1, 1):
            d.line([ex * s, ey * s, (ex - tx_ * 12 + sgn * ty_ * 7) * s, (ey - ty_ * 12 - sgn * tx_ * 7) * s],
                   fill=(90, 96, 106), width=3 * s)
    return np.asarray(im.resize((W, 280), Image.LANCZOS)) / 255.0


def am_render_targets():
    base = li_multiple_lights(PW, PH)
    gray = np.repeat((base @ v(0.2126, 0.7152, 0.0722))[..., None], 3, -1)
    k = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]], float)
    edges = sat(np.stack([convolve(base[..., c], k) for c in range(3)], -1))
    return panels([base, 1 - base, gray, edges], ["Scene texture", "Inverted", "Grayscale", "Edge kernel"], cols=2)


def refract(I, N, eta):
    c = -dot(N, I)
    k = 1 - eta * eta * (1 - c * c)
    return np.where(k < 0, reflect(I, N), eta * I + (eta * c - np.sqrt(np.maximum(k, 0))) * N)


def am_cubemaps():
    objs = [Sphere((-1.5, 0, 0), 0.85), Box(T(1.5, 0, 0) @ R(35, (0.3, 1, 0.2)) @ S(1.25)),
            Box(T(0, -0.25, -1.6) @ R(15, (0, 1, 0)) @ S(0.9), tex=CRATE)]
    cam = Camera((0, 0.5, 4.6), (0, 0, 0), fov=50)
    O, D = cam.rays(W * 2, H * 2)
    g = trace(objs, O, D)
    img = shade(g, objs, cam.eye, [dict(type="dir", dir=-tx.SUN, color=(1, 1, 1))], ambient=0.5)
    m = g["idx"] == 0
    img[m] = tx.env(reflect(D[m], g["N"][m]), hdr=False)
    m = g["idx"] == 1
    img[m] = tx.env(norm(refract(D[m], g["N"][m], 1 / 1.52)), hdr=False) * v(0.92, 0.97, 1.0)
    return finish(img, g, bg=lambda d: tx.env(d, hdr=False))


def am_advanced_data():
    n = [("Buffer 0\nGPU is drawing frame N", 30, 90, 240, 60), ("Buffer 1\nframe N+1 is queued", 320, 90, 240, 60),
         ("Buffer 2\nCPU writes frame N+2", 610, 90, 240, 60, True), ("Semaphore (3)", 320, 200, 240, 46)]
    return diagram(n, [(0, 1), (1, 2), (3, 1)], size=(W, 270), title="A ring of uniform buffers, one per frame in flight")


def am_advanced_msl():
    pts = [(-0.6, -0.6), (0.6, -0.6), (0, 0.6)]
    cols = [(1, 0.2, 0.2), (0.2, 1, 0.2), (0.2, 0.3, 1)]
    return panels([tri2d(pts, cols, PW, PH, bg=v(0.1, 0.1, 0.1)), tri2d(pts, cols, PW, PH, bg=v(0.1, 0.1, 0.1), flat=True)],
                  ["Default interpolation", "[[flat]]"])


def am_particles():
    rng = np.random.default_rng(3)
    cam = Camera((0, 1.5, 6), (0, 0.8, 0))
    n = 900
    t = rng.random(n)
    ang = rng.random(n) * 2 * math.pi
    rad = (0.15 + t * 1.6) * rng.random(n) ** 0.5
    P = np.stack([np.cos(ang) * rad, t * 3.0 - 0.5, np.sin(ang) * rad], -1)
    x, y, z = cam.project(P, W, H)
    img = np.zeros((H, W, 3))
    yy, xx = np.mgrid[0:H, 0:W]
    for i in np.argsort(-z):
        r = 26 / z[i] * (0.6 + 0.8 * rng.random())
        x0, x1, y0, y1 = int(max(x[i] - 3 * r, 0)), int(min(x[i] + 3 * r, W)), int(max(y[i] - 3 * r, 0)), int(min(y[i] + 3 * r, H))
        if x1 <= x0 or y1 <= y0:
            continue
        d2 = (xx[y0:y1, x0:x1] - x[i]) ** 2 + (yy[y0:y1, x0:x1] - y[i]) ** 2
        col = mix(v(1.0, 0.85, 0.35), v(0.9, 0.15, 0.05), t[i]) * (1 - t[i] * 0.7)
        img[y0:y1, x0:x1] += np.exp(-d2 / (r * r))[..., None] * col * 0.35
    return sat(1 - np.exp(-img * 1.6)) + v(0.03, 0.03, 0.05)


def am_instancing():
    rng = np.random.default_rng(5)
    cam = Camera((0, 11, 34), (0, -1.5, 0), fov=45)
    ss = 2
    w, h = W * ss, H * ss
    img = np.zeros((h, w, 3)) + v(0.01, 0.01, 0.03)
    stars = rng.random((h, w)) > 0.9993
    img[stars] = 0.8
    zbuf = np.full((h, w), np.inf)
    n = 2600
    ang = rng.random(n) * 2 * math.pi
    rad = 17 + rng.normal(0, 1.6, n)
    P = np.stack([np.sin(ang) * rad, rng.normal(0, 0.55, n), np.cos(ang) * rad], -1)
    Rr = rng.uniform(0.08, 0.34, n)
    P = np.vstack([[0, 0, 0], P])
    Rr = np.concatenate([[5.0], Rr])
    tint = np.vstack([[0.55, 0.42, 0.32], np.repeat(rng.uniform(0.35, 0.6, (n, 1)), 3, 1) * v(1, 0.95, 0.88)])
    x, y, z = cam.project(P, w, h)
    Lv = norm(v(dot(v(1, 0.6, 0.8), cam.r)[0], dot(v(1, 0.6, 0.8), cam.u)[0], -dot(v(1, 0.6, 0.8), cam.f)[0]))
    yy, xx = np.mgrid[0:h, 0:w]
    for i in range(len(P)):
        r = Rr[i] / (z[i] * cam.tan) * 0.5 * h
        x0, x1, y0, y1 = int(max(x[i] - r - 1, 0)), int(min(x[i] + r + 2, w)), int(max(y[i] - r - 1, 0)), int(min(y[i] + r + 2, h))
        if x1 <= x0 or y1 <= y0:
            continue
        nx = (xx[y0:y1, x0:x1] - x[i]) / r
        ny = -(yy[y0:y1, x0:x1] - y[i]) / r
        r2 = nx * nx + ny * ny
        inside = r2 < 1
        nz = np.sqrt(np.maximum(1 - r2, 0))
        depth = z[i] - nz * Rr[i]
        m = inside & (depth < zbuf[y0:y1, x0:x1])
        lit = np.maximum(nx * Lv[0] + ny * Lv[1] + nz * Lv[2], 0) * 0.95 + 0.05
        if i == 0:
            band = 0.8 + 0.2 * np.sin(ny * 14 + np.sin(nx * 5) * 1.5)
            lit = lit * band
        img[y0:y1, x0:x1][m] = (lit[..., None] * tint[i])[m]
        zbuf[y0:y1, x0:x1][m] = depth[m]
    return finish(img, ss=ss, srgb=True)


def am_anti_aliasing():
    w, h, up = 55, 31, 8

    def cover(samples):
        offs = [(0.5, 0.5)] if samples == 1 else [(0.375, 0.125), (0.875, 0.375), (0.125, 0.625), (0.625, 0.875)]
        acc = np.zeros((h, w))
        for ox, oy in offs:
            x = (np.arange(w) + ox) / w * 2 - 1
            y = 1 - (np.arange(h) + oy) / h * 2
            x, y = np.meshgrid(x, y)
            (x0, y0), (x1, y1), (x2, y2) = (-0.85, -0.55), (0.8, -0.15), (-0.2, 0.75)
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            b1 = ((x - x0) * (y2 - y0) - (x2 - x0) * (y - y0)) / area
            b2 = ((x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)) / area
            acc += ((1 - b1 - b2 >= 0) & (b1 >= 0) & (b2 >= 0))
        c = (acc / len(offs))[..., None]
        img = mix(v(0.1, 0.1, 0.1), v(0.25, 0.8, 0.45), c)
        return np.repeat(np.repeat(img, up, 0), up, 1)

    return panels([cover(1), cover(4)], ["1 sample per pixel", "4x MSAA"])


FIGURES = [
    ("getting-started/introduction", gs_introduction), ("getting-started/project-setup", gs_project_setup),
    ("getting-started/hello-view", gs_hello_view), ("getting-started/hello-triangle", gs_hello_triangle),
    ("getting-started/shaders", gs_shaders), ("getting-started/textures", gs_textures),
    ("getting-started/address-modes", gs_address_modes), ("getting-started/transformations", gs_transformations),
    ("getting-started/coordinate-systems", gs_coordinate_systems), ("getting-started/ten-cubes", gs_ten_cubes),
    ("getting-started/camera", gs_camera), ("getting-started/review", gs_review),
    ("lighting/colors", li_colors), ("lighting/basic-lighting", li_basic), ("lighting/materials", li_materials),
    ("lighting/lighting-maps", li_lighting_maps), ("lighting/light-casters", li_light_casters),
    ("lighting/multiple-lights", li_multiple_lights), ("lighting/review", li_review),
    ("model-loading/model-io", ml_model_io), ("model-loading/mesh", ml_mesh), ("model-loading/model", ml_model),
    ("advanced-metal/depth-testing", am_depth), ("advanced-metal/stencil-testing", am_stencil),
    ("advanced-metal/blending", am_blending), ("advanced-metal/face-culling", am_face_culling),
    ("advanced-metal/render-targets", am_render_targets), ("advanced-metal/cubemaps", am_cubemaps),
    ("advanced-metal/advanced-data", am_advanced_data), ("advanced-metal/advanced-msl", am_advanced_msl),
    ("advanced-metal/no-geometry-shaders", am_particles), ("advanced-metal/instancing", am_instancing),
    ("advanced-metal/anti-aliasing", am_anti_aliasing),
]
