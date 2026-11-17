"""Figures for Advanced Lighting, PBR, In Practice and Beyond."""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

import textures as tx
from figures_basic import CRATE, CRATE_S, PLANKS, PH, PW, cubes, lamp, li_multiple_lights, multi_light_scene
from rt import (W, H, Box, Camera, Plane, Sphere, R, S, T, blur, dot, finish, font, light_terms, mix, norm,
                occluded, panels, reflect, render, sample, sat, shade, surface, to_image, trace, v)

BRICK, BRICK_H, BRICK_N, BRICK_D = tx.bricks()
P3 = dict(w=440, h=330)       # one panel of a three-column figure


def hdr_down(img, ss=2):
    h, w = img.shape[:2]
    return img.reshape(h // ss, ss, w // ss, ss, 3).mean((1, 3))


def aces(x):
    return sat((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14))


def reinhard(x):
    return x / (x + 1)


def gamma(x):
    return sat(x) ** (1 / 2.2)


# ------------------------------------------------------------ advanced lighting

def al_blinn_phong():
    cam = Camera((0, 0.35, 5.0), (0, -0.5, 0), fov=50)
    floor = [Plane(-0.5, 14, tex=PLANKS, uvscale=0.25, spec=1.0, shin=8)]
    L = [dict(type="point", pos=(0, -0.25, -0.5), color=(1, 1, 1), att=(1, 0.09, 0.032))]
    a = render(floor, cam, L, ambient=0.05, blinn=False, w=PW, h=PH, bg=(0.02, 0.02, 0.02))
    floor[0].shin = 32
    b = render(floor, cam, L, ambient=0.05, blinn=True, w=PW, h=PH, bg=(0.02, 0.02, 0.02))
    return panels([a, b], ["Phong, shininess 8", "Blinn-Phong, shininess 32"])


def al_gamma():
    cam = Camera((0, 2.2, 6), (0, -0.3, -1), fov=50)
    objs = [Plane(-0.5, 14, tex=PLANKS, uvscale=0.25, spec=0.2)] + \
           [Box(T(-3 + 2 * i, 0, -1.5 - i * 0.8) @ R(20 * i, (0, 1, 0)), tex=CRATE, spec=CRATE_S) for i in range(4)]
    pos = [(-3, 0.6, 0.5), (-1, 0.6, 0), (1, 0.6, -0.5), (3, 0.6, -1)]
    objs += [lamp(p, s=0.12) for p in pos]
    L = [dict(type="point", pos=p, color=v(1, 1, 1) * 1.6, att="inv2") for p in pos]
    kw = dict(ambient=0.03, w=PW, h=PH, bg=(0.02, 0.02, 0.02))
    return panels([render(objs, cam, L, **kw), render(objs, cam, L, srgb=True, **kw)],
                  ["No gamma correction", "Linear workflow, sRGB output"])


def shadow_scene():
    return [Plane(-0.5, 12, tex=PLANKS, uvscale=0.2, spec=0.15),
            Box(T(0, 1.0, 0) @ S(0.5), tex=CRATE, spec=CRATE_S),
            Box(T(2, -0.0, 1), tex=CRATE, spec=CRATE_S),
            Box(T(-1.2, -0.0, 1.8) @ R(60, (1, 0, 1)) @ S(0.6), tex=CRATE, spec=CRATE_S)]


def al_shadow_mapping():
    objs = shadow_scene()
    lpos = v(-2, 4, -1) * 1.5
    lcam = Camera(lpos, (0.4, 0, 0.8), ortho=4.2)
    O, D = lcam.rays(PH * 2, PH * 2)
    g = trace(objs, O, D)
    d = np.where(g["hit"], (g["t"] - 3) / 9, 1.0)
    sm = np.repeat(sat(d)[..., None], 3, -1).reshape(PH, 2, PH, 2, 3).mean((1, 3))
    pad = np.zeros((PH, PW, 3)) + 0.06
    x0 = (PW - PH) // 2
    pad[:, x0:x0 + PH] = sm
    cam = Camera((1.2, 3.0, 6.5), (0.4, 0, 0.6), fov=45)
    L = [dict(type="dir", dir=-lpos, color=(1, 1, 1))]
    lit = render(objs, cam, L, ambient=0.12, shadows=True, srgb=True, w=PW, h=PH, bg=(0.02, 0.02, 0.03))
    return panels([pad, lit], ["Shadow map: depth from the light", "Scene with shadows"])


def al_point_shadows():
    room = Box(S(9, 7, 9), tex=PLANKS, uvscale=2, spec=0.05, casts=False)
    rng = np.random.default_rng(2)
    boxes = [Box(T(*p) @ R(a, ax) @ S(s), tex=CRATE, spec=CRATE_S)
             for p, a, ax, s in [((2.2, -1.2, -1.5), 0, (0, 1, 0), 1.0), ((-2.0, 0.6, -2.2), 40, (1, 0, 1), 0.9),
                                 ((-1.6, -2.2, 1.0), 20, (0, 1, 0), 1.2), ((1.2, 1.6, -2.6), 60, (1, 1, 0), 0.7),
                                 ((0.6, -2.6, -1.0), 10, (0, 1, 0), 0.8)]]
    lp = (0, 0, -0.6)
    objs = [room] + boxes + [lamp(lp, s=0.14)]
    L = [dict(type="point", pos=lp, color=v(1, 0.95, 0.85) * 9, att="inv2")]
    cam = Camera((0, 0.2, 4.2), (0, -0.3, -1), fov=62)
    O, D = cam.rays(W * 2, H * 2)
    g = trace(objs, O, D)
    img = shade(g, objs, cam.eye, L, ambient=0.03, shadows=True, linear=True)
    return finish(reinhard(img * 1.2), g, srgb=True)


def brick_wall():
    return Box(S(3.6, 3.6, 0.02), tex=BRICK, uvscale=1.5, spec=0.25, shin=24)


def normal_mapped(g, uv=None):
    uv = g["UV"] if uv is None else uv
    n = sample(BRICK_N, uv) * 2 - 1
    B = np.cross(g["N"], g["T"])
    return norm(g["T"] * n[..., 0:1] + B * n[..., 1:2] + g["N"] * n[..., 2:3])


def wall_image(cam, mode, lp=(0.9, 0.9, 0.9), w=PW, h=PH):
    wall = brick_wall()
    objs = [wall]
    O, D = cam.rays(w * 2, h * 2)
    g = trace(objs, O, D)
    uv = g["UV"]
    if mode == "pom":
        B = np.cross(g["N"], g["T"])
        V = norm(cam.eye - g["P"])
        vt = np.concatenate([dot(V, g["T"]), dot(V, B), dot(V, g["N"])], -1)
        layers, scale = 64, 0.07
        step = np.stack([-vt[..., 0], vt[..., 1]], -1) / np.maximum(vt[..., 2:3], 0.05) * scale / layers
        cur = uv.copy()
        layer = np.zeros(uv.shape[:-1])
        depth = sample(BRICK_D, cur)
        prev_uv, prev_depth, prev_layer = cur.copy(), depth.copy(), layer.copy()
        for _ in range(layers):
            active = layer < depth
            if not active.any():
                break
            prev_uv[active], prev_depth[active], prev_layer[active] = cur[active], depth[active], layer[active]
            cur[active] += step[active]
            layer[active] += 1.0 / layers
            depth[active] = sample(BRICK_D, cur[active])
        after = depth - layer
        before = prev_depth - prev_layer
        wgt = (after / np.minimum(after - before, -1e-6))[..., None]
        uv = mix(cur, prev_uv, sat(wgt))
    A = sample(BRICK, uv) ** 2.2
    N = g["N"] if mode == "flat" else normal_mapped(g, uv)
    surf = (A, np.full(A.shape[:-1] + (1,), 0.25), np.full(A.shape[:-1] + (1,), 24.0), np.zeros(A.shape[:-1], bool))
    L = [dict(type="point", pos=lp, color=v(1, 1, 1) * 2.2, att="inv2")]
    img = shade(g, objs, cam.eye, L, ambient=0.06, N=N, surf=surf)
    return finish(img, g, bg=(0.02, 0.02, 0.02), srgb=True)


def al_normal_mapping():
    cam = Camera((0.5, -0.2, 3.3), (0, 0, 0), fov=50)
    return panels([wall_image(cam, "flat"), wall_image(cam, "normal")], ["Vertex normals only", "With a normal map"])


def al_parallax_mapping():
    cam = Camera((2.5, -0.5, 1.5), (0.2, 0, 0), fov=45)
    lp = (1.2, 1.0, 1.2)
    return panels([wall_image(cam, "normal", lp), wall_image(cam, "pom", lp)],
                  ["Normal mapping", "Parallax occlusion mapping"])


def hdr_scene(w=PW, h=PH, emissive=6.0):
    cols = [(1, 0.25, 0.15), (0.2, 0.5, 1), (0.3, 1, 0.4), (1, 0.8, 0.3)]
    pos = [(-2.4, 0.3, 0.2), (2.6, 0.5, -0.6), (0.4, 0.2, 1.4), (0.2, 1.8, -2.2)]
    objs = [Plane(-0.5, 14, tex=PLANKS, uvscale=0.25, spec=0.2),
            Box(T(-1.0, 0, -1.2) @ R(25, (0, 1, 0)), tex=CRATE, spec=CRATE_S),
            Box(T(1.4, 0, -0.2) @ R(-15, (0, 1, 0)), tex=CRATE, spec=CRATE_S),
            Box(T(0.2, 1.0, -1.0) @ R(40, (0, 1, 0)) @ S(0.6), tex=CRATE, spec=CRATE_S)]
    objs += [lamp(p, v(*c) * emissive, s=0.2) for p, c in zip(pos, cols)]
    L = [dict(type="point", pos=p, color=v(*c) * 5, att="inv2") for p, c in zip(pos, cols)]
    cam = Camera((0.3, 1.6, 5.2), (0.2, 0.1, -0.5), fov=50)
    O, D = cam.rays(w * 2, h * 2)
    g = trace(objs, O, D)
    img = shade(g, objs, cam.eye, L, ambient=0.02, linear=True, shadows=True)
    img[~g["hit"]] = 0.004
    return hdr_down(img)


def al_hdr():
    img = hdr_scene(440, 330) * 1.6
    return panels([gamma(img), gamma(reinhard(img)), gamma(aces(img * 0.7))],
                  ["Clamped at 1.0", "Reinhard", "ACES, exposure 0.7"])


def al_bloom():
    img = hdr_scene()
    lum = img @ v(0.2126, 0.7152, 0.0722)
    bright = np.where((lum > 1.0)[..., None], img, 0)
    glow = sum(blur(bright, s) * k for s, k in [(3, 0.5), (9, 0.6), (22, 0.7)])
    tm = lambda x: gamma(1 - np.exp(-x * 1.1))
    return panels([tm(img), tm(img + glow)], ["Without bloom", "With bloom"])


def al_deferred():
    rng = np.random.default_rng(11)
    objs = [Plane(-0.5, 14, tex=PLANKS, uvscale=0.25, spec=0.2)]
    objs += [Box(T(-3 + 2 * (i % 4), 0, -3 + 2 * (i // 4)) @ R(17 * i, (0, 1, 0)) @ S(0.9), tex=CRATE, spec=CRATE_S)
             for i in range(8)]
    lights = []
    for _ in range(40):
        p = (rng.uniform(-4.5, 4.5), rng.uniform(-0.2, 1.0), rng.uniform(-4.5, 2.5))
        c = mix(v(*rng.random(3)), v(1, 1, 1), 0.25)
        lights.append(dict(type="point", pos=p, color=c * 0.9, att="inv2"))
    cam = Camera((0, 3.2, 6.5), (0, 0, -0.8), fov=50)
    O, D = cam.rays(PW * 2, PH * 2)
    g = trace(objs, O, D)
    A, Sp, Sh, E = surface(g, objs, linear=True)
    hit = g["hit"][..., None]
    lit = shade(g, objs, cam.eye, lights, ambient=0.02, surf=(A, Sp, Sh, E))
    out = [finish(np.where(hit, A ** (1 / 2.2), 0)), finish(np.where(hit, g["N"] * 0.5 + 0.5, 0)),
           finish(np.where(hit, sat(g["P"] * 0.12 + 0.5), 0)), finish(lit, g, bg=(0, 0, 0), srgb=True)]
    return panels(out, ["Albedo + specular", "Normal", "Position", "Lighting pass, 40 lights"], cols=2)


def al_ssao():
    objs = [Plane(-0.5, 14, color=(0.8, 0.8, 0.8)),
            Box(T(-0.9, 0, 0), color=(0.8, 0.8, 0.8)), Box(T(0.25, 0, -0.3) @ R(20, (0, 1, 0)), color=(0.8, 0.8, 0.8)),
            Box(T(-0.3, 0.9, -0.2) @ R(45, (0, 1, 0)) @ S(0.8), color=(0.8, 0.8, 0.8)),
            Sphere((1.5, 0.1, 0.4), 0.6, color=(0.8, 0.8, 0.8)),
            Box(T(0, 1.5, -2.5) @ S(8, 4, 0.2), color=(0.8, 0.8, 0.8))]
    cam = Camera((0.6, 1.6, 4.2), (0.2, 0.2, 0), fov=45)
    O, D = cam.rays(440 * 2, 330 * 2)
    g = trace(objs, O, D)
    rng = np.random.default_rng(1)
    N, P = g["N"], g["P"]
    occ = np.zeros(N.shape[:-1])
    K = 24
    for _ in range(K):
        r = norm(rng.normal(size=N.shape))
        d = norm(N + r * 0.98)                   # cosine-weighted hemisphere direction
        occ += occluded(objs, P, N, d, 0.7)
    ao = gaussian_filter(1 - occ / K, 1.5)[..., None]
    L = [dict(type="dir", dir=(-0.5, -1, -0.6), color=(0.55, 0.55, 0.55))]
    lit = shade(g, objs, cam.eye, L, ambient=0.0, specular=False)
    A = surface(g, objs)[0]
    bg = (0.75, 0.75, 0.75)
    return panels([finish(np.repeat(ao, 3, -1), g, bg=(1, 1, 1)),
                   finish(lit + 0.45 * A, g, bg=bg), finish(lit + 0.45 * A * ao, g, bg=bg)],
                  ["Occlusion buffer", "Constant ambient", "Ambient x occlusion"])


# ------------------------------------------------------------ PBR

def ggx_d(nh, rough):
    a2 = (rough * rough) ** 2
    return a2 / (math.pi * (nh * nh * (a2 - 1) + 1) ** 2)


def g_schlick(x, k):
    return x / (x * (1 - k) + k)


def fresnel(c, F0, rough=None):
    top = 1.0 if rough is None else np.maximum(1 - rough, F0)
    return F0 + (top - F0) * sat(1 - c) ** 5


def sphere_grid(rows=7, cols=7, albedo=(0.55, 0.02, 0.02)):
    objs, props = [], []
    for r in range(rows):
        for c in range(cols):
            objs.append(Sphere(((c - cols // 2) * 1.25, (r - rows // 2) * 1.25, 0), 0.5))
            props.append((r / max(rows - 1, 1), max(c / max(cols - 1, 1), 0.05)))
    return objs, np.array(props), v(*albedo)


def fib_dirs(n):
    i = np.arange(n) + 0.5
    y = 1 - 2 * i / n
    phi = i * math.pi * (3 - math.sqrt(5))
    r = np.sqrt(1 - y * y)
    return np.stack([np.cos(phi) * r, y, np.sin(phi) * r], -1)


def sh_basis(d):
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    return np.stack([0.282095 + 0 * x, 0.488603 * y, 0.488603 * z, 0.488603 * x, 1.092548 * x * y,
                     1.092548 * y * z, 0.315392 * (3 * z * z - 1), 1.092548 * x * z, 0.546274 * (x * x - y * y)], -1)


_dirs = fib_dirs(20000)
SH = (4 * math.pi / len(_dirs)) * sh_basis(_dirs).T @ np.minimum(tx.env(_dirs), 60.0)
SH_A = np.array([math.pi] + [2 * math.pi / 3] * 3 + [math.pi / 4] * 5)


def irradiance(n):
    """Cosine-weighted irradiance divided by pi, like the irradiance cubemap."""
    return np.maximum(sh_basis(n) * SH_A @ SH, 0) / math.pi


ENVMAP = tx.env(tx.equirect_dirs(512, 256))
PREFILTER = [gaussian_filter(ENVMAP, (s, s, 0), mode=("nearest", "wrap", "nearest")) for s in (2, 6, 14, 28, 50)]


def prefiltered(Rd, rough):
    uv = tx.equirect_uv(Rd)
    lv = rough[..., 0] * (len(PREFILTER) - 1)
    out = np.zeros(Rd.shape)
    for i, tex in enumerate(PREFILTER):
        wgt = sat(1 - np.abs(lv - i))[..., None]
        if (wgt > 0).any():
            out += sample(tex, uv) * wgt
    sharp = sat(1 - lv * 2.5)[..., None]
    return mix(out, tx.env(Rd), sharp)


def brdf_lut(n=64, samples=200):
    nv = (np.arange(n) + 0.5) / n
    ro = (np.arange(n) + 0.5) / n
    NV, RO = np.meshgrid(nv, ro)
    i = np.arange(samples)
    xi1 = (i + 0.5) / samples
    bits = np.array([int(f"{k:032b}"[::-1], 2) for k in i]) / 2 ** 32
    a = (RO ** 2)[..., None]
    phi = 2 * math.pi * xi1
    ct = np.sqrt((1 - bits) / (1 + (a * a - 1) * bits))
    st = np.sqrt(1 - ct * ct)
    Hx, Hz = np.cos(phi) * st, ct
    Vx, Vz = np.sqrt(1 - NV ** 2)[..., None], NV[..., None]
    vh = Vx * Hx + Vz * Hz
    Lz = 2 * vh * Hz - Vz
    nl, nh, vh = np.maximum(Lz, 0), np.maximum(Hz, 1e-6), np.maximum(vh, 0)
    k = a / 2
    G = g_schlick(Vz, k) * g_schlick(nl, k)
    gv = np.where(nl > 0, G * vh / (nh * Vz), 0)
    fc = (1 - vh) ** 5
    return np.stack([((1 - fc) * gv).mean(-1), (fc * gv).mean(-1)], -1)


LUT = brdf_lut()


def pbr_image(objs, props, albedo, cam, lights, ambient="flat", w=W, h=H, bg=(0.02, 0.02, 0.02)):
    O, D = cam.rays(w * 2, h * 2)
    g = trace(objs, O, D)
    idx = np.where(g["hit"], g["idx"], 0)
    metal = props[idx, 0][..., None]
    rough = props[idx, 1][..., None]
    N, V = g["N"], -D
    nv = np.maximum(dot(N, V), 1e-4)
    F0 = mix(v(0.04, 0.04, 0.04), albedo, metal)
    Lo = np.zeros(D.shape)
    for light in lights:
        L, rad, _ = light_terms(g, light, cam.eye)
        Hh = norm(L + V)
        nl = np.maximum(dot(N, L), 0)
        k = (rough + 1) ** 2 / 8
        spec = ggx_d(np.maximum(dot(N, Hh), 0), rough) * g_schlick(nv, k) * g_schlick(nl, k) \
            * fresnel(np.maximum(dot(Hh, V), 0), F0) / (4 * nv * nl + 1e-4)
        kd = (1 - fresnel(np.maximum(dot(Hh, V), 0), F0)) * (1 - metal)
        Lo += (kd * albedo / math.pi + spec) * rad * nl
    if ambient == "flat":
        amb = 0.03 * albedo
    else:
        F = fresnel(nv, F0, rough)
        amb = (1 - F) * (1 - metal) * irradiance(N) * albedo
        if ambient == "full":
            lut = sample(LUT, np.concatenate([nv, rough], -1), repeat=False)
            amb = amb + prefiltered(reflect(D, N), rough) * (F * lut[..., 0:1] + lut[..., 1:2])
    img = amb + Lo
    img[~g["hit"]] = bg(D[~g["hit"]]) if callable(bg) else bg
    return gamma(reinhard(hdr_down(img)))


GRID_CAM = Camera((0, 0, 33.0), (0, 0, 0), fov=16)       # a long lens keeps the outer spheres round
GRID_LIGHTS = [dict(type="point", pos=(x, y, 10), color=(300, 300, 300), att="inv2") for x in (-10, 10) for y in (-10, 10)]


def pb_theory():
    objs = [Sphere(((i - 2) * 1.3, 0, 0), 0.55) for i in range(5)]
    props = np.array([(0.0, r) for r in (0.1, 0.3, 0.5, 0.7, 0.9)])
    cam = Camera((0, 0, 13.25), (0, 0, 0), fov=12)      # a long lens keeps the outer spheres round
    L = [dict(type="point", pos=(-3, 4, 6), color=(160, 160, 160), att="inv2")]
    img = pbr_image(objs, props, v(0.2, 0.35, 0.8), cam, L, h=260)
    im = to_image(img)
    d = ImageDraw.Draw(im)
    for i, r in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
        t = f"roughness {r}"
        x = W / 2 + (i - 2) * 1.3 * 93.3
        d.text((x - d.textlength(t, font=font(15)) / 2, 226), t, font=font(15), fill=(225, 225, 225))
    return np.asarray(im) / 255.0


def pb_lighting():
    objs, props, albedo = sphere_grid()
    return pbr_image(objs, props, albedo, GRID_CAM, GRID_LIGHTS)


def pb_irradiance_maps():
    d = tx.equirect_dirs(440, 220)
    return panels([gamma(reinhard(tx.env(d))), gamma(reinhard(irradiance(d) * math.pi))],
                  ["Environment (equirectangular)", "Irradiance map"])


def pb_diffuse_irradiance():
    objs, props, albedo = sphere_grid()
    return pbr_image(objs, props, albedo, GRID_CAM, GRID_LIGHTS, ambient="diffuse", bg=tx.env)


def pb_prefilter():
    w, h = 170, 85
    d = tx.equirect_dirs(w, h)
    uv = tx.equirect_uv(d)
    strip = [gamma(reinhard(tx.env(d)))] + [gamma(reinhard(sample(PREFILTER[i], uv))) for i in (1, 2, 3, 4)]
    row = panels(strip, None)
    lut = np.concatenate([sample(LUT, np.stack(np.meshgrid((np.arange(220) + 0.5) / 220, (np.arange(220) + 0.5) / 220), -1),
                                 repeat=False), np.zeros((220, 220, 1))], -1)
    canvas = np.ones((row.shape[0] + 250 + 30, W, 3)) * (246 / 255)
    canvas[10:10 + row.shape[0], (W - row.shape[1]) // 2:(W - row.shape[1]) // 2 + row.shape[1]] = row
    canvas[row.shape[0] + 46:row.shape[0] + 266, 330:550] = lut
    im = to_image(canvas)
    dr = ImageDraw.Draw(im)
    dr.text((14, row.shape[0] + 16), "Prefiltered environment: mip 0 (roughness 0) to mip 4 (roughness 1)",
            font=font(15), fill=(60, 66, 76))
    dr.text((564, row.shape[0] + 140), "BRDF lookup table", font=font(15, bold=True), fill=(60, 66, 76))
    dr.text((564, row.shape[0] + 164), "x: n · v      y: roughness (0 at top)", font=font(14), fill=(100, 108, 120))
    dr.text((564, row.shape[0] + 186), "red: scale     green: bias", font=font(14), fill=(100, 108, 120))
    return np.asarray(im) / 255.0


def pb_specular_ibl():
    objs, props, albedo = sphere_grid()
    return pbr_image(objs, props, albedo, GRID_CAM, GRID_LIGHTS, ambient="full", bg=tx.env)


# ------------------------------------------------------------ in practice

def debug_scene():
    chk = tx.checker(256, (0.9, 0.9, 0.9), (0.55, 0.58, 0.62), 8)
    return [Sphere((-1.5, 0, 0), 0.75, tex=chk, color=(0.9, 0.5, 0.3), uvscale=2, spec=0.6, shin=64),
            Box(T(0.3, 0, 0) @ R(35, (0.2, 1, 0.1)) @ S(1.1), tex=CRATE, spec=CRATE_S),
            Plane(-0.75, 6, tex=PLANKS, uvscale=0.25, spec=0.15)]


def ip_debugging():
    objs = debug_scene()
    cam = Camera((0, 1.4, 4.4), (-0.4, 0, 0))
    O, D = cam.rays(PW * 2, PH * 2)
    g = trace(objs, O, D)
    hit = g["hit"][..., None]
    L = [dict(type="point", pos=(2, 3, 3), color=(1, 1, 1), att=None)]
    lit = finish(shade(g, objs, cam.eye, L, ambient=0.15, shadows=True), g, bg=(0.12, 0.13, 0.16))
    uv = g["UV"] - np.floor(g["UV"])
    z = dot(g["P"] - cam.eye, cam.f) / 9
    out = [lit, finish(np.where(hit, g["N"] * 0.5 + 0.5, 0)),
           finish(np.where(hit, np.concatenate([uv, np.zeros(uv.shape[:-1] + (1,))], -1), 0)),
           finish(np.where(hit, np.repeat(z, 3, -1), 1))]
    return panels(out, ["Final image", "normal * 0.5 + 0.5", "float4(uv, 0, 1)", "Linear depth"], cols=2)


def ip_text():
    s = 2
    w, h = 436 * s, 300 * s
    atlas = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(atlas)
    f = font(26 * s)
    x, y = 8 * s, 8 * s
    for code in range(33, 127):
        ch = chr(code)
        bb = d.textbbox((0, 0), ch, font=f)
        cw = bb[2] - bb[0] + 6 * s
        if x + cw > w - 8 * s:
            x, y = 8 * s, y + 38 * s
        d.text((x - bb[0] + 3 * s, y), ch, font=f, fill=(255, 255, 255))
        d.rectangle([x, y + 2 * s, x + cw, y + 36 * s], outline=(70, 70, 70))
        x += cw + 2 * s
    scene = Image.new("RGB", (w, h), (51, 77, 77))
    d = ImageDraw.Draw(scene)
    d.text((20 * s, 20 * s), "FPS: 120", font=font(22 * s, mono=True), fill=(120, 255, 140))
    d.text((20 * s, 110 * s), "learnmetal", font=font(54 * s, bold=True), fill=(255, 138, 76))
    d.text((22 * s, 180 * s), "Text is just textured quads.", font=font(24 * s), fill=(235, 235, 235))
    quad_x = 20 * s
    for ch in "learnmetal":
        cw = d.textlength(ch, font=font(54 * s, bold=True))
        d.rectangle([quad_x, 112 * s, quad_x + cw, 172 * s], outline=(255, 255, 255, 90))
        quad_x += cw
    conv = lambda im: np.asarray(im.resize((w // s, h // s), Image.LANCZOS)) / 255.0
    return panels([conv(atlas), conv(scene)], ["Glyph atlas (.r8Unorm)", "One quad per character"])


def ip_game():
    s = 2
    im = Image.new("RGB", (800 * s, 600 * s), (16, 18, 28))
    d = ImageDraw.Draw(im)
    pal = [(230, 77, 77), (230, 153, 51), (77, 204, 102), (77, 128, 230)]
    rng = np.random.default_rng(4)
    bw = 800 / 12
    for row in range(6):
        for col in range(12):
            if rng.random() < 0.14 and row > 2:
                continue
            x, y = col * bw, 60 + row * 24
            c = pal[row % 4]
            d.rounded_rectangle([(x + 1) * s, (y + 1) * s, (x + bw - 2) * s, (y + 22) * s], 3 * s, fill=c)
            d.line([(x + 4) * s, (y + 4) * s, (x + bw - 6) * s, (y + 4) * s], fill=tuple(min(255, k + 50) for k in c), width=2 * s)
    d.rounded_rectangle([330 * s, 570 * s, 430 * s, 586 * s], 6 * s, fill=(230, 230, 230))
    for i in range(14):
        a = int(18 + i * 9)
        cx, cy = 455 - i * 5.5, 395 + i * 9.5
        r = 3 + i * 0.45
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=(a + 60, a + 40, a))
    d.ellipse([445 * s, 380 * s, 465 * s, 400 * s], fill=(255, 255, 255))
    d.text((16 * s, 14 * s), "SCORE 1250", font=font(20 * s, mono=True), fill=(235, 235, 235))
    d.text((650 * s, 14 * s), "LIVES 3", font=font(20 * s, mono=True), fill=(235, 235, 235))
    return np.asarray(im.resize((W, int(600 * W / 800)), Image.LANCZOS)) / 255.0


# ------------------------------------------------------------ beyond

def by_compute():
    base = li_multiple_lights(PW, PH)
    gray = np.repeat((base @ v(0.2126, 0.7152, 0.0722))[..., None], 3, -1)
    return panels([base, gray], ["Input texture", "Output of the grayscale kernel"])


def terrain_height(x, z):
    return (np.sin(x * 1.3) * np.cos(z * 1.1) * 0.5 + np.sin(x * 2.9 + 1.0) * np.sin(z * 2.3) * 0.22
            + np.cos(x * 0.6 - z * 0.8) * 0.45)


def by_tessellation():
    cam = Camera((0, 3.4, 6.2), (0, -0.2, 0), fov=45)
    out = []
    for n in (4, 12, 32):
        s = 2
        w, h = 440 * s, 330 * s
        im = Image.new("RGB", (w, h), (18, 20, 24))
        d = ImageDraw.Draw(im)
        g = np.linspace(-3, 3, n + 1)
        X, Z = np.meshgrid(g, g)
        P = np.stack([X, terrain_height(X, Z), Z], -1)
        px, py, _ = cam.project(P.reshape(-1, 3), w, h)
        px, py = px.reshape(n + 1, n + 1), py.reshape(n + 1, n + 1)
        hgt = P[..., 1]
        for i in range(n + 1):
            for j in range(n + 1):
                c = tuple(int(k) for k in mix(v(60, 120, 90), v(255, 170, 90), sat((hgt[i, j] + 0.9) / 1.9)))
                if j < n:
                    d.line([px[i, j], py[i, j], px[i, j + 1], py[i, j + 1]], fill=c, width=s)
                if i < n:
                    d.line([px[i, j], py[i, j], px[i + 1, j], py[i + 1, j]], fill=c, width=s)
                if i < n and j < n:
                    d.line([px[i, j], py[i, j], px[i + 1, j + 1], py[i + 1, j + 1]], fill=c, width=s)
        out.append(np.asarray(im.resize((440, 330), Image.LANCZOS)) / 255.0)
    return panels(out, ["Factor 1", "Factor 3", "Factor 8"])


def by_ray_tracing():
    objs = [Plane(-0.5, 9, color=(0.75, 0.75, 0.75)),
            Box(T(-1.1, 0, 0) @ R(25, (0, 1, 0)), color=(0.85, 0.35, 0.25)),
            Box(T(0.7, 0.25, -0.5) @ R(-20, (0, 1, 0)) @ S(1, 1.5, 1), color=(0.3, 0.5, 0.85)),
            Sphere((0.4, 0.0, 1.2), 0.5, color=(0.9, 0.75, 0.3), spec=0.8, shin=96)]
    cam = Camera((0.8, 2.2, 5.2), (0, 0.1, 0), fov=42)
    O, D = cam.rays(PW * 2, PH * 2)
    g = trace(objs, O, D)
    uv = g["UV"] - np.floor(g["UV"])
    u, vv = uv[..., 0], 1 - uv[..., 1]
    lower = vv <= u
    bary = np.where(lower[..., None], np.stack([1 - u, u - vv, vv], -1), np.stack([1 - vv, u, vv - u], -1))
    a = finish(bary, g, bg=(0.1, 0.1, 0.15))
    L = [dict(type="point", pos=(-2.5, 4, 2.5), color=v(1, 1, 1) * 26, att="inv2")]
    b = finish(reinhard(shade(g, objs, cam.eye, L, ambient=0.05, shadows=True, linear=True)), g,
               bg=(0.02, 0.02, 0.03), srgb=True)
    return panels([a, b], ["Barycentric coordinates of each hit", "Ray traced shadows"])


FIGURES = [
    ("advanced-lighting/blinn-phong", al_blinn_phong), ("advanced-lighting/gamma-correction", al_gamma),
    ("advanced-lighting/shadow-mapping", al_shadow_mapping), ("advanced-lighting/point-shadows", al_point_shadows),
    ("advanced-lighting/normal-mapping", al_normal_mapping), ("advanced-lighting/parallax-mapping", al_parallax_mapping),
    ("advanced-lighting/hdr", al_hdr), ("advanced-lighting/bloom", al_bloom),
    ("advanced-lighting/deferred-shading", al_deferred), ("advanced-lighting/ssao", al_ssao),
    ("pbr/theory", pb_theory), ("pbr/lighting", pb_lighting), ("pbr/irradiance-maps", pb_irradiance_maps),
    ("pbr/diffuse-irradiance", pb_diffuse_irradiance), ("pbr/prefilter", pb_prefilter),
    ("pbr/specular-ibl", pb_specular_ibl),
    ("in-practice/debugging", ip_debugging), ("in-practice/text-rendering", ip_text), ("in-practice/2d-game", ip_game),
    ("beyond/compute-shaders", by_compute), ("beyond/tessellation", by_tessellation), ("beyond/ray-tracing", by_ray_tracing),
]
