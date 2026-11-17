#!/usr/bin/env python3
"""Static site generator for learnmetal.

    pip install markdown pygments
    python3 build.py

Reads Markdown from content/ and writes the finished site to docs/,
which is what GitHub Pages serves.
"""
import html
import re
import shutil
import zipfile
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
EXAMPLES_DIR = ROOT / "examples"
OUT = ROOT / "docs"

SITE = "learnmetal"
TAGLINE = "Learn modern 3D graphics programming with Apple's Metal, from the first triangle to physically based rendering."

# (folder, section title, [(slug, chapter title), ...])
SECTIONS = [
    ("getting-started", "Getting Started", [
        ("introduction", "Introduction"),
        ("project-setup", "Project Setup"),
        ("hello-view", "Hello View"),
        ("hello-triangle", "Hello Triangle"),
        ("shaders", "Shaders"),
        ("textures", "Textures"),
        ("transformations", "Transformations"),
        ("coordinate-systems", "Coordinate Systems"),
        ("camera", "Camera"),
        ("review", "Review"),
    ]),
    ("lighting", "Lighting", [
        ("colors", "Colors"),
        ("basic-lighting", "Basic Lighting"),
        ("materials", "Materials"),
        ("lighting-maps", "Lighting Maps"),
        ("light-casters", "Light Casters"),
        ("multiple-lights", "Multiple Lights"),
        ("review", "Review"),
    ]),
    ("model-loading", "Model Loading", [
        ("model-io", "Model I/O"),
        ("mesh", "Mesh"),
        ("model", "Model"),
    ]),
    ("advanced-metal", "Advanced Metal", [
        ("depth-testing", "Depth Testing"),
        ("stencil-testing", "Stencil Testing"),
        ("blending", "Blending"),
        ("face-culling", "Face Culling"),
        ("render-targets", "Render Targets"),
        ("cubemaps", "Cubemaps"),
        ("advanced-data", "Advanced Data"),
        ("advanced-msl", "Advanced MSL"),
        ("no-geometry-shaders", "Life Without Geometry Shaders"),
        ("instancing", "Instancing"),
        ("anti-aliasing", "Anti-Aliasing"),
    ]),
    ("advanced-lighting", "Advanced Lighting", [
        ("blinn-phong", "Blinn-Phong"),
        ("gamma-correction", "Gamma Correction"),
        ("shadow-mapping", "Shadow Mapping"),
        ("point-shadows", "Point Shadows"),
        ("normal-mapping", "Normal Mapping"),
        ("parallax-mapping", "Parallax Mapping"),
        ("hdr", "HDR"),
        ("bloom", "Bloom"),
        ("deferred-shading", "Deferred Shading"),
        ("ssao", "SSAO"),
    ]),
    ("pbr", "PBR", [
        ("theory", "Theory"),
        ("lighting", "Lighting"),
        ("diffuse-irradiance", "Diffuse Irradiance"),
        ("specular-ibl", "Specular IBL"),
    ]),
    ("in-practice", "In Practice", [
        ("debugging", "Debugging"),
        ("text-rendering", "Text Rendering"),
        ("2d-game", "A 2D Game"),
    ]),
    ("beyond", "Beyond", [
        ("compute-shaders", "Compute Shaders"),
        ("tessellation", "Tessellation"),
        ("ray-tracing", "Ray Tracing"),
    ]),
    ("resources", "Resources", [
        ("examples", "Example Code"),
    ]),
]

# Chapter -> (swift target, folder under examples/Sources).
EXAMPLES = {
    "getting-started/hello-view": ("HelloView", "01-HelloView"),
    "getting-started/hello-triangle": ("HelloTriangle", "02-HelloTriangle"),
    "getting-started/shaders": ("Shaders", "03-Shaders"),
    "getting-started/textures": ("Textures", "04-Textures"),
    "getting-started/transformations": ("Transformations", "05-Transformations"),
    "getting-started/coordinate-systems": ("CoordinateSystems", "06-CoordinateSystems"),
    "getting-started/camera": ("Camera", "07-Camera"),
    "lighting/colors": ("BasicLighting", "08-BasicLighting"),
    "lighting/basic-lighting": ("BasicLighting", "08-BasicLighting"),
    "lighting/materials": ("BasicLighting", "08-BasicLighting"),
    "lighting/lighting-maps": ("LightingMaps", "09-LightingMaps"),
    "lighting/light-casters": ("MultipleLights", "10-MultipleLights"),
    "lighting/multiple-lights": ("MultipleLights", "10-MultipleLights"),
    "model-loading/model-io": ("ModelLoading", "11-ModelLoading"),
    "model-loading/mesh": ("ModelLoading", "11-ModelLoading"),
    "model-loading/model": ("ModelLoading", "11-ModelLoading"),
    "advanced-metal/render-targets": ("RenderTargets", "12-RenderTargets"),
    "advanced-metal/instancing": ("Instancing", "13-Instancing"),
    "advanced-metal/no-geometry-shaders": ("ComputeParticles", "17-ComputeParticles"),
    "advanced-lighting/shadow-mapping": ("ShadowMapping", "14-ShadowMapping"),
    "advanced-lighting/hdr": ("HDRBloom", "15-HDRBloom"),
    "advanced-lighting/bloom": ("HDRBloom", "15-HDRBloom"),
    "pbr/lighting": ("PBR", "16-PBR"),
    "beyond/compute-shaders": ("ComputeParticles", "17-ComputeParticles"),
}

# Chapter -> [(image under assets/img, caption, heading to insert before)].
# The heading is matched against "## Heading" lines; "END" appends to the chapter.
FIGURES = {
    "getting-started/introduction": [("getting-started/introduction", "Everything is created from the device, and nothing reaches the GPU until the command buffer is committed.", "State objects instead of a state machine")],
    "getting-started/project-setup": [("getting-started/project-setup", "The pieces of the project. The renderer is where almost all code in this series lives.", "Where shaders go")],
    "getting-started/hello-view": [("getting-started/hello-view", "The result: a view cleared to one color, sixty or more times per second.", "The device and the queue")],
    "getting-started/hello-triangle": [("getting-started/hello-triangle", "Left: the first triangle. Right: the indexed rectangle drawn with setTriangleFillMode(.lines), showing its two triangles.", "Exercises")],
    "getting-started/shaders": [("getting-started/shaders", "Each vertex has its own color. Every fragment in between receives a blend of the three.", "Uniforms")],
    "getting-started/textures": [
        ("getting-started/address-modes", "Address modes decide what is sampled outside the 0 to 1 range. Here the coordinates run from -1 to 2.", "Sampling in the shader"),
        ("getting-started/textures", "A textured rectangle, and two textures blended with mix. It looks stretched because nothing corrects for the window's aspect ratio yet.", "Exercises")],
    "getting-started/transformations": [("getting-started/transformations", "Scaled to half size, rotated, then moved to the lower right corner.", "Exercises")],
    "getting-started/coordinate-systems": [
        ("getting-started/coordinate-systems", "Without a depth test, faces drawn later cover faces that are closer to the camera.", "More cubes"),
        ("getting-started/ten-cubes", "Ten cubes from one vertex buffer and ten model matrices.", "Exercises")],
    "getting-started/camera": [("getting-started/camera", "The same ten cubes seen from a camera that has moved up and to the right.", "Exercises")],
    "getting-started/review": [("getting-started/review", "The journey of a vertex.", "Glossary")],
    "lighting/colors": [("lighting/colors", "A coral object and a white lamp cube. Without shading the faces are indistinguishable.", "Exercises")],
    "lighting/basic-lighting": [("lighting/basic-lighting", "The three terms of the Phong model, added one at a time.", "Exercises")],
    "lighting/materials": [("lighting/materials", "The same cube and the same light with four different materials.", "Exercises")],
    "lighting/lighting-maps": [("lighting/lighting-maps", "With a specular map only the steel frame shines, and the highlight breaks up over its scratches.", "One sampler, many textures")],
    "lighting/light-casters": [("lighting/light-casters", "The three kinds of light source on the same scene.", "A flashlight")],
    "lighting/multiple-lights": [("lighting/multiple-lights", "One directional light and four colored point lights, each drawn as a small lamp cube.", "The cost of many lights")],
    "lighting/review": [("lighting/review", "", "What changed in the renderer")],
    "model-loading/model-io": [("model-loading/model-io", "", "Asking for the layout you want")],
    "model-loading/mesh": [("model-loading/mesh", "The packed vertex layout requested from Model I/O, and the index buffer of a submesh.", "Drawing a mesh")],
    "model-loading/model": [("model-loading/model", "Meshes with different materials and transforms drawn through one Model type.", "Finding models")],
    "advanced-metal/depth-testing": [("advanced-metal/depth-testing", "Left: raw depth values are almost all close to 1. Right: the same buffer converted back to linear distance.", "Z-fighting")],
    "advanced-metal/stencil-testing": [("advanced-metal/stencil-testing", "Outlines drawn where the stencil buffer was not marked by the crates.", "Reading the comparison correctly")],
    "advanced-metal/blending": [("advanced-metal/blending", "Semi-transparent windows drawn back to front after the opaque scene.", "Exercises")],
    "advanced-metal/face-culling": [("advanced-metal/face-culling", "The same triangle seen from the front and from behind.", "Enabling culling")],
    "advanced-metal/render-targets": [("advanced-metal/render-targets", "The scene rendered to a texture, then processed by different fragment functions.", "Exercises")],
    "advanced-metal/cubemaps": [("advanced-metal/cubemaps", "A skybox, a sphere that reflects it and a block that refracts it.", "Rendering into a cubemap")],
    "advanced-metal/advanced-data": [("advanced-metal/advanced-data", "", "Copying on the GPU: the blit encoder")],
    "advanced-metal/advanced-msl": [("advanced-metal/advanced-msl", "A [[flat]] member takes the value of the first vertex for the whole triangle.", "Address spaces")],
    "advanced-metal/no-geometry-shaders": [("advanced-metal/no-geometry-shaders", "Hundreds of camera-facing quads from one instanced draw call, with additive blending.", "Visualizing normals: lines from vertex IDs")],
    "advanced-metal/instancing": [("advanced-metal/instancing", "Thousands of rocks around a planet in a single draw call.", "Animating instances")],
    "advanced-metal/anti-aliasing": [("advanced-metal/anti-aliasing", "A magnified triangle edge. With four samples per pixel, partially covered pixels get intermediate colors.", "MSAA with MTKView")],
    "advanced-lighting/blinn-phong": [("advanced-lighting/blinn-phong", "A light close to a floor. The Phong highlight is cut off behind the light; the Blinn-Phong highlight is not.", "END")],
    "advanced-lighting/gamma-correction": [("advanced-lighting/gamma-correction", "The same lights with inverse-square falloff. Without gamma correction the falloff is far too harsh.", "Wide color")],
    "advanced-lighting/shadow-mapping": [("advanced-lighting/shadow-mapping", "Left: the scene's depth as seen from the light. Right: the scene shaded with that shadow map.", "Outside the map")],
    "advanced-lighting/point-shadows": [("advanced-lighting/point-shadows", "A point light in the middle of a room casts shadows in every direction.", "Cost")],
    "advanced-lighting/normal-mapping": [("advanced-lighting/normal-mapping", "The same flat quad. The normal map makes light react to bricks and mortar.", "Green channel and handedness")],
    "advanced-lighting/parallax-mapping": [("advanced-lighting/parallax-mapping", "At a shallow angle, parallax occlusion mapping makes bricks hide the mortar behind them.", "Limits")],
    "advanced-lighting/hdr": [("advanced-lighting/hdr", "The same HDR image clamped and with two tone mapping operators.", "Why it matters beyond bright lights")],
    "advanced-lighting/bloom": [("advanced-lighting/bloom", "Pixels brighter than white bleed into their surroundings.", "Doing it better")],
    "advanced-lighting/deferred-shading": [("advanced-lighting/deferred-shading", "The G-buffer and the result of the lighting pass.", "Light volumes")],
    "advanced-lighting/ssao": [("advanced-lighting/ssao", "The occlusion buffer, and ambient light without and with it.", "Tuning and cost")],
    "pbr/theory": [("pbr/theory", "One light on five dielectric spheres. Roughness alone changes the highlight from a sharp point to a broad sheen.", "Material parameters")],
    "pbr/lighting": [("pbr/lighting", "Metalness increases from bottom to top, roughness from left to right. Direct lighting only.", "Textured PBR")],
    "pbr/diffuse-irradiance": [
        ("pbr/irradiance-maps", "An HDR environment and its irradiance map: the cosine-weighted average of the light around every direction.", "Using it"),
        ("pbr/diffuse-irradiance", "With diffuse image-based lighting the spheres pick up the colors of the sky and the ground. Metals stay dark.", "Alternatives")],
    "pbr/specular-ibl": [
        ("pbr/prefilter", "The two precomputed halves of the split-sum approximation.", "Putting it together"),
        ("pbr/specular-ibl", "Full image-based lighting: smooth metals mirror the environment, rough ones show a blurred version of it.", "Beyond a single probe")],
    "in-practice/debugging": [("in-practice/debugging", "Debugging by color: intermediate values written out as the fragment color.", "Command buffer errors")],
    "in-practice/text-rendering": [("in-practice/text-rendering", "The glyph atlas, and text composed from one textured quad per character.", "Limits of this approach")],
    "in-practice/2d-game": [("in-practice/2d-game", "The whole game is one instanced draw call of colored rectangles.", "Making it feel good")],
    "beyond/compute-shaders": [("beyond/compute-shaders", "A kernel reads one texture and writes another, one thread per pixel.", "Threads and threadgroups")],
    "beyond/tessellation": [("beyond/tessellation", "The same 4 x 4 grid of quad patches at increasing tessellation factors, displaced by a height function.", "Normals for displaced surfaces")],
    "beyond/ray-tracing": [("beyond/ray-tracing", "Left: what an intersection returns. Right: shadows from one ray per pixel toward the light.", "Noise and denoising")],
}

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<script>
(function () {{
  var t = null;
  try {{ t = localStorage.getItem("theme"); }} catch (e) {{}}
  if (!t) t = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  document.documentElement.dataset.theme = t;
}})();
</script>
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="stylesheet" href="{root}assets/code.css">
</head>
<body>
<header class="topbar">
  <button id="menu-toggle" class="icon-btn" aria-label="Toggle navigation">&#9776;</button>
  <a class="brand" href="{root}index.html">learn<span>metal</span></a>
  <button id="theme-toggle" class="icon-btn" aria-label="Toggle dark mode">&#9680;</button>
</header>
<div class="layout">
<nav class="sidebar" id="sidebar">
{nav}
</nav>
<main class="content">
{body}
</main>
</div>
<script src="{root}assets/site.js"></script>
</body>
</html>
"""


def md():
    return markdown.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "admonition", "toc", "attr_list"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "codehilite"},
            "toc": {"permalink": "#"},
        },
    )


def image_tag(name, caption):
    from PIL import Image
    path = ASSETS / "img" / f"{name}.webp"
    w, h = Image.open(path).size
    alt = html.escape(caption or name.split("/")[-1].replace("-", " "))
    cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return f'<figure><img src="../assets/img/{name}.webp" alt="{alt}" width="{w}" height="{h}" loading="lazy">{cap}</figure>'


def preprocess(text, key):
    """Insert the example box and the figures into a chapter's Markdown."""
    lines = text.split("\n")
    for name, caption, anchor in FIGURES.get(key, []):
        block = ["", image_tag(name, caption), ""]
        target = f"## {anchor}"
        if anchor != "END" and target in lines:
            i = lines.index(target)
            lines[i:i] = block
        else:
            if anchor != "END":
                print(f"warning: {key}: heading not found: {anchor!r}")
            lines += block
    if key in EXAMPLES:
        target_name, folder = EXAMPLES[key]
        box = (f'<div class="example-box"><strong>Example code</strong> <code>examples/Sources/{folder}</code>, '
               f'run with <code>swift run {target_name}</code>. '
               f'<a href="../downloads/learnmetal-examples.zip">Download all examples</a> or see '
               f'<a href="../resources/examples.html">how to run them</a>.</div>')
        i = next(k for k, line in enumerate(lines) if line.startswith("# "))
        lines[i + 1:i + 1] = ["", box, ""]
    return "\n".join(lines)


def write_examples_zip():
    dest = OUT / "downloads" / "learnmetal-examples.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(EXAMPLES_DIR.rglob("*")):
            rel = f.relative_to(EXAMPLES_DIR)
            if f.is_file() and not any(part.startswith(".") for part in rel.parts):
                z.write(f, f"learnmetal-examples/{rel}")


def flat_chapters():
    out = []
    for folder, section, chapters in SECTIONS:
        for slug, title in chapters:
            out.append((folder, section, slug, title))
    return out


def build_nav(root, current=None):
    parts = []
    for folder, section, chapters in SECTIONS:
        parts.append(f'<div class="nav-section"><h4>{html.escape(section)}</h4><ul>')
        for slug, title in chapters:
            cls = ' class="active"' if current == (folder, slug) else ""
            parts.append(f'<li><a{cls} href="{root}{folder}/{slug}.html">{html.escape(title)}</a></li>')
        parts.append("</ul></div>")
    return "\n".join(parts)


def write_code_css():
    def css(style, scope):
        try:
            fmt = HtmlFormatter(style=style)
        except Exception:
            fmt = HtmlFormatter(style="default")
        return fmt.get_style_defs(f'html[data-theme="{scope}"] .codehilite')

    text = css("friendly", "light") + "\n" + css("github-dark", "dark") + "\n"
    # Let the site stylesheet own the block background.
    text += ".codehilite { background: var(--code-bg) !important; }\n"
    (OUT / "assets" / "code.css").write_text(text)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    write_code_css()
    write_examples_zip()

    chapters = flat_chapters()
    missing = []
    for i, (folder, section, slug, title) in enumerate(chapters):
        src = CONTENT / folder / f"{slug}.md"
        if not src.exists():
            missing.append(str(src.relative_to(ROOT)))
            continue
        body = md().convert(preprocess(src.read_text(), f"{folder}/{slug}"))
        pager = ['<div class="pager">']
        if i > 0:
            pf, _, ps, pt = chapters[i - 1]
            pager.append(f'<a class="prev" href="../{pf}/{ps}.html"><small>Previous</small>{html.escape(pt)}</a>')
        else:
            pager.append("<span></span>")
        if i + 1 < len(chapters):
            nf, _, ns, nt = chapters[i + 1]
            pager.append(f'<a class="next" href="../{nf}/{ns}.html"><small>Next</small>{html.escape(nt)}</a>')
        pager.append("</div>")
        crumb = f'<p class="crumb">{html.escape(section)}</p>'
        page = PAGE.format(
            title=f"{title} · {SITE}",
            description=html.escape(f"{section}: {title}. {TAGLINE}"),
            root="../",
            nav=build_nav("../", (folder, slug)),
            body=f"<article>{crumb}{body}</article>{''.join(pager)}",
        )
        dest = OUT / folder / f"{slug}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)

    # Home page
    intro = md().convert((CONTENT / "index.md").read_text())
    cards = ['<div class="cards">']
    for folder, section, chs in SECTIONS:
        cards.append(f'<section class="card"><h3>{html.escape(section)}</h3><ol>')
        for slug, title in chs:
            cards.append(f'<li><a href="{folder}/{slug}.html">{html.escape(title)}</a></li>')
        cards.append("</ol></section>")
    cards.append("</div>")
    first = chapters[0]
    hero = (
        '<div class="hero"><h1>learn<span>metal</span></h1>'
        f"<p>{html.escape(TAGLINE)}</p>"
        f'<a class="cta" href="{first[0]}/{first[2]}.html">Start learning</a></div>'
    )
    page = PAGE.format(
        title=f"{SITE} · Learn Metal graphics programming",
        description=html.escape(TAGLINE),
        root="",
        nav=build_nav(""),
        body=f"{hero}<article>{intro}</article>{''.join(cards)}",
    )
    (OUT / "index.html").write_text(page)

    print(f"Built {len(chapters) - len(missing)} chapters into {OUT.relative_to(ROOT)}/")
    if missing:
        print("Missing sources:")
        for m in missing:
            print("  ", m)


if __name__ == "__main__":
    build()
