#!/usr/bin/env python3
"""Static site generator for learnmetal.

    pip install markdown pygments
    python3 build.py

Reads Markdown from content/ and writes the finished site to docs/,
which is what GitHub Pages serves.
"""
import html
import json
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
CPP_DIR = ROOT / "examples-cpp"
GITHUB = "https://github.com/gabrielevierti"
# The LearnMetal Engine lives in a repository of its own. Chapters refer to it as {{engine-repo}}.
ENGINE_REPO = GITHUB + "/learnmetal-engine"
AUTHOR = "Gabriele Vierti"
YEAR = "2026"
OUT = ROOT / "docs"

SITE = "learnmetal"
TAGLINE = "Learn 3D graphics programming with Apple's Metal, from the first triangle to physically based rendering, in Swift or C++."

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
        ("game-engine", "A Game Engine"),
        ("engine-renderer", "Engine: The Renderer"),
        ("engine-gameplay", "Engine: The Game"),
        ("engine-editor", "Engine: The Editor"),
    ]),
    ("beyond", "Beyond", [
        ("compute-shaders", "Compute Shaders"),
        ("tessellation", "Tessellation"),
        ("ray-tracing", "Ray Tracing"),
        ("mesh-shaders", "Mesh Shaders"),
    ]),
    ("apple-platforms", "Apple Platforms", [
        ("tile-based-gpus", "Tile-Based GPUs"),
        ("metalfx", "MetalFX Upscaling"),
        ("metal-4", "Metal 4"),
        ("visionos", "visionOS"),
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
    "in-practice/game-engine": [("in-practice/game-engine", "Marble, the game that comes with the engine: physically based materials, light from the sky, cascaded shadows, bloom and an interface drawn on top.", "What an engine adds")],
    "in-practice/engine-renderer": [("in-practice/engine-renderer", "One frame of Marble, pass by pass. Each picture is the texture that the pass draws into.", "Shadows in cascades")],
    "in-practice/engine-gameplay": [
        ("in-practice/engine-gameplay", "The whole course. The marble starts in the foreground, crosses the gap on the orange platform and finishes on the far right.", "Entities and components"),
        ("in-practice/engine-complete", "The end of an unattended run: the autopilot has collected all eight gems and reached the goal.", "Tests that do not need a GPU")],
    "in-practice/engine-editor": [
        ("in-practice/engine-editor", "The editor with its sample scene. The golden ball is selected: its handles are in the view, its components in the inspector.", "An interface in immediate mode"),
        ("in-practice/engine-editor-materials", "The Materials tab: the surface of the selected material and its texture slots.", "Scenes as text"),
        ("in-practice/engine-editor-play", "After pressing Play: seen through the scene's own camera, the ball has rolled onto the ramp and the fountain is running.", "What it does not do")],
    "beyond/compute-shaders": [("beyond/compute-shaders", "A kernel reads one texture and writes another, one thread per pixel.", "Threads and threadgroups")],
    "beyond/tessellation": [("beyond/tessellation", "The same 4 x 4 grid of quad patches at increasing tessellation factors, displaced by a height function.", "Normals for displaced surfaces")],
    "beyond/ray-tracing": [("beyond/ray-tracing", "Left: what an intersection returns. Right: shadows from one ray per pixel toward the light.", "Noise and denoising")],
}


# Chapter -> [(demo id, heading to insert before, figure it replaces or None)].
DEMOS = {
    "getting-started/hello-view": [("hello-view", "The device and the queue", "getting-started/hello-view")],
    "getting-started/hello-triangle": [("hello-triangle", "Indexed drawing", "getting-started/hello-triangle")],
    "getting-started/shaders": [("shaders", "Uniforms", "getting-started/shaders")],
    "getting-started/textures": [("textures", "Two textures at once", "getting-started/textures")],
    "getting-started/transformations": [("transformations", "Exercises", "getting-started/transformations")],
    "getting-started/coordinate-systems": [("coordinate-systems", "Exercises", "getting-started/ten-cubes")],
    "getting-started/camera": [("camera", "Exercises", "getting-started/camera")],
    "lighting/colors": [("colors", "Exercises", "lighting/colors")],
    "lighting/basic-lighting": [("basic-lighting", "Exercises", "lighting/basic-lighting")],
    "lighting/materials": [("materials", "Real materials", "lighting/materials")],
    "lighting/lighting-maps": [("lighting-maps", "One sampler, many textures", "lighting/lighting-maps")],
    "lighting/light-casters": [("light-casters", "Exercises", "lighting/light-casters")],
    "lighting/multiple-lights": [("multiple-lights", "The cost of many lights", "lighting/multiple-lights")],
    "advanced-metal/depth-testing": [("depth-testing", "Z-fighting", "advanced-metal/depth-testing")],
    "advanced-metal/face-culling": [("face-culling", "Exercises", None)],
    "advanced-metal/stencil-testing": [("stencil-testing", "Reading the comparison correctly", "advanced-metal/stencil-testing")],
    "advanced-metal/blending": [("blending", "Exercises", "advanced-metal/blending")],
    "advanced-lighting/bloom": [("bloom", "Doing it better", None)],
    "advanced-lighting/deferred-shading": [("deferred-shading", "Light volumes", "advanced-lighting/deferred-shading")],
    "advanced-lighting/ssao": [("ssao", "Tuning and cost", "advanced-lighting/ssao")],
    "advanced-metal/render-targets": [("render-targets", "Exercises", "advanced-metal/render-targets")],
    "advanced-metal/cubemaps": [("cubemaps", "Rendering into a cubemap", "advanced-metal/cubemaps")],
    "advanced-metal/instancing": [("instancing", "Animating instances", "advanced-metal/instancing")],
    "advanced-lighting/blinn-phong": [("blinn-phong", "END", "advanced-lighting/blinn-phong")],
    "advanced-lighting/shadow-mapping": [("shadow-mapping", "Softer edges", None)],
    "advanced-lighting/normal-mapping": [("normal-mapping", "Green channel and handedness", "advanced-lighting/normal-mapping")],
    "advanced-lighting/parallax-mapping": [("parallax-mapping", "Limits", "advanced-lighting/parallax-mapping")],
    "advanced-lighting/hdr": [("hdr", "Why it matters beyond bright lights", "advanced-lighting/hdr")],
    "pbr/lighting": [("pbr", "A grid of spheres", None)],
    "in-practice/debugging": [("debugging", "Command buffer errors", "in-practice/debugging")],
    "in-practice/2d-game": [("breakout", "Making it feel good", "in-practice/2d-game")],
    "beyond/tessellation": [("tessellation", "Normals for displaced surfaces", "beyond/tessellation")],
    "beyond/ray-tracing": [("ray-tracing", "Noise and denoising", "beyond/ray-tracing")],
}

BLURBS = {
    "getting-started": "Open a view, draw a triangle, texture it, move it with matrices and fly a camera around it.",
    "lighting": "The Phong model, materials, lighting maps and every kind of light source.",
    "model-loading": "Turn model files into vertex buffers, index buffers and materials with Model I/O.",
    "advanced-metal": "Depth and stencil, blending, render targets, cubemaps, instancing and anti-aliasing.",
    "advanced-lighting": "Shadows, normal and parallax mapping, HDR, bloom, deferred shading and SSAO.",
    "pbr": "Physically based materials and image-based lighting.",
    "in-practice": "Debugging tools, text rendering, a small playable game, and a complete game engine with its editor.",
    "beyond": "Compute shaders, tessellation, ray tracing and mesh shaders.",
    "apple-platforms": "What is specific to Apple hardware: tile-based GPUs, MetalFX, Metal 4 and visionOS.",
    "resources": "Runnable example projects for Swift and C++.",
}

STRINGS = {
    "en": dict(skip="Skip to content", menu="Open the chapter list", search="Search", text_lang="Language of the text",
               code_lang="Language of the host code", theme="Switch between light and dark", chapters="Chapters",
               rights="All rights reserved.", prev="Previous", next="Next", toc="On this page", solution="Show solution",
               path="The path", start="Start with chapter one", get="Get the example projects",
               hero="Learn Metal by changing the code and watching the pixels move.",
               hero_more="Every technique comes with a live demo: edit the shader on the page and it recompiles as you type.",
               tagline=None, untranslated="",
               js=dict(copy="Copy", copied="Copied", none="No results for", loading="Loading the index",
                       progress="{n} of {total} chapters read", reset="Reset progress", read="read")),
    "it": dict(skip="Vai al contenuto", menu="Apri l'elenco dei capitoli", search="Cerca", text_lang="Lingua del testo",
               code_lang="Linguaggio del codice", theme="Passa dal tema chiaro a quello scuro", chapters="Capitoli",
               rights="Tutti i diritti riservati.", prev="Precedente", next="Successivo", toc="In questa pagina",
               solution="Mostra la soluzione", path="Il percorso", start="Inizia dal primo capitolo",
               get="Scarica i progetti di esempio",
               hero="Impara Metal cambiando il codice e guardando i pixel muoversi.",
               hero_more="Ogni tecnica ha una demo interattiva: modifica lo shader nella pagina e si ricompila mentre scrivi.",
               tagline="Impara la grafica 3D con Metal di Apple, dal primo triangolo al rendering fisicamente corretto, in Swift o C++.",
               untranslated=('<div class="lang-note"><strong>Capitolo non ancora tradotto.</strong> '
                             'Per ora il testo di questo capitolo è in inglese. Il codice è lo stesso in entrambe le lingue.</div>'),
               js=dict(compiled="Compilato", error="Errore", resetshader="Ripristina", copylink="Copia link", linkcopied="Link copiato",
                       editshader="Modifica lo shader",
                       copy="Copia", copied="Copiato", none="Nessun risultato per", loading="Carico l'indice",
                       progress="{n} capitoli letti su {total}", reset="Azzera il progresso", read="letto")),
}

IT_CAPTIONS = {
    "Everything is created from the device, and nothing reaches the GPU until the command buffer is committed.": "Tutto viene creato a partire dal device, e niente arriva alla GPU finché non si fa il commit del command buffer.",
    "The pieces of the project. The renderer is where almost all code in this series lives.": "I pezzi del progetto. Il renderer è il posto in cui vive quasi tutto il codice di questa serie.",
    "The result: a view cleared to one color, sixty or more times per second.": "Il risultato: una vista riempita di un solo colore, sessanta o più volte al secondo.",
    "Left: the first triangle. Right: the indexed rectangle drawn with setTriangleFillMode(.lines), showing its two triangles.": "A sinistra: il primo triangolo. A destra: il rettangolo indicizzato disegnato con setTriangleFillMode(.lines), che mostra i suoi due triangoli.",
    "Each vertex has its own color. Every fragment in between receives a blend of the three.": "Ogni vertice ha il suo colore. Ogni fragment in mezzo riceve una miscela dei tre.",
    "Address modes decide what is sampled outside the 0 to 1 range. Here the coordinates run from -1 to 2.": "Gli address mode decidono che cosa viene letto fuori dall'intervallo da 0 a 1. Qui le coordinate vanno da -1 a 2.",
    "A textured rectangle, and two textures blended with mix. It looks stretched because nothing corrects for the window's aspect ratio yet.": "Un rettangolo con texture, e due texture mescolate con mix. Appare deformato perché niente corregge ancora il rapporto d'aspetto della finestra.",
    "Scaled to half size, rotated, then moved to the lower right corner.": "Scalato a metà dimensione, ruotato e poi spostato nell'angolo in basso a destra.",
    "Without a depth test, faces drawn later cover faces that are closer to the camera.": "Senza test di profondità le facce disegnate dopo coprono quelle più vicine alla camera.",
    "Ten cubes from one vertex buffer and ten model matrices.": "Dieci cubi da un solo vertex buffer e dieci matrici model.",
    "The same ten cubes seen from a camera that has moved up and to the right.": "Gli stessi dieci cubi visti da una camera che si è spostata in alto e a destra.",
    "The journey of a vertex.": "Il viaggio di un vertice.",
    "A coral object and a white lamp cube. Without shading the faces are indistinguishable.": "Un oggetto corallo e un cubo lampada bianco. Senza ombreggiatura le facce non si distinguono.",
    "The three terms of the Phong model, added one at a time.": "I tre termini del modello di Phong, aggiunti uno alla volta.",
    "The same cube and the same light with four different materials.": "Lo stesso cubo e la stessa luce con quattro materiali diversi.",
    "With a specular map only the steel frame shines, and the highlight breaks up over its scratches.": "Con una specular map luccica solo il telaio d'acciaio, e il riflesso si spezza sui suoi graffi.",
    "The three kinds of light source on the same scene.": "I tre tipi di sorgente di luce sulla stessa scena.",
    "One directional light and four colored point lights, each drawn as a small lamp cube.": "Una luce direzionale e quattro luci puntiformi colorate, ognuna disegnata come un piccolo cubo lampada.",
    "The packed vertex layout requested from Model I/O, and the index buffer of a submesh.": "Il layout compatto dei vertici chiesto a Model I/O, e l'index buffer di una submesh.",
    "Meshes with different materials and transforms drawn through one Model type.": "Mesh con materiali e trasformazioni diversi disegnate attraverso un unico tipo Model.",
    "Left: raw depth values are almost all close to 1. Right: the same buffer converted back to linear distance.": "A sinistra: i valori grezzi di profondità sono quasi tutti vicini a 1. A destra: lo stesso buffer riconvertito in distanza lineare.",
    "Outlines drawn where the stencil buffer was not marked by the crates.": "Contorni disegnati dove lo stencil buffer non era stato marcato dalle casse.",
    "Semi-transparent windows drawn back to front after the opaque scene.": "Finestre semitrasparenti disegnate da dietro in avanti dopo la scena opaca.",
    "The same triangle seen from the front and from behind.": "Lo stesso triangolo visto da davanti e da dietro.",
    "The scene rendered to a texture, then processed by different fragment functions.": "La scena disegnata in una texture e poi elaborata da fragment function diverse.",
    "A skybox, a sphere that reflects it and a block that refracts it.": "Uno skybox, una sfera che lo riflette e un blocco che lo rifrange.",
    "A [[flat]] member takes the value of the first vertex for the whole triangle.": "Un membro [[flat]] prende il valore del primo vertice per tutto il triangolo.",
    "Hundreds of camera-facing quads from one instanced draw call, with additive blending.": "Centinaia di rettangoli rivolti verso la camera da una sola draw call con instancing, con blending additivo.",
    "Thousands of rocks around a planet in a single draw call.": "Migliaia di rocce intorno a un pianeta in una sola draw call.",
    "A magnified triangle edge. With four samples per pixel, partially covered pixels get intermediate colors.": "Il bordo di un triangolo ingrandito. Con quattro campioni per pixel i pixel coperti in parte prendono colori intermedi.",
    "A light close to a floor. The Phong highlight is cut off behind the light; the Blinn-Phong highlight is not.": "Una luce vicina a un pavimento. Il riflesso di Phong è troncato dietro la luce; quello di Blinn-Phong no.",
    "The same lights with inverse-square falloff. Without gamma correction the falloff is far too harsh.": "Le stesse luci con il calo secondo l'inverso del quadrato. Senza correzione gamma il calo è fin troppo duro.",
    "Left: the scene's depth as seen from the light. Right: the scene shaded with that shadow map.": "A sinistra: la profondità della scena vista dalla luce. A destra: la scena illuminata con quella shadow map.",
    "A point light in the middle of a room casts shadows in every direction.": "Una luce puntiforme al centro di una stanza proietta ombre in ogni direzione.",
    "The same flat quad. The normal map makes light react to bricks and mortar.": "Lo stesso rettangolo piatto. La normal map fa reagire la luce a mattoni e malta.",
    "At a shallow angle, parallax occlusion mapping makes bricks hide the mortar behind them.": "Con un angolo radente il parallax occlusion mapping fa sì che i mattoni nascondano la malta dietro di loro.",
    "The same HDR image clamped and with two tone mapping operators.": "La stessa immagine HDR tagliata e con due operatori di tone mapping.",
    "Pixels brighter than white bleed into their surroundings.": "I pixel più luminosi del bianco sconfinano su ciò che li circonda.",
    "The G-buffer and the result of the lighting pass.": "Il G-buffer e il risultato del lighting pass.",
    "The occlusion buffer, and ambient light without and with it.": "Il buffer di occlusione, e la luce ambient senza e con esso.",
    "One light on five dielectric spheres. Roughness alone changes the highlight from a sharp point to a broad sheen.": "Una luce su cinque sfere dielettriche. La sola roughness trasforma il riflesso da un punto netto a una lucentezza ampia.",
    "Metalness increases from bottom to top, roughness from left to right. Direct lighting only.": "La metalness cresce dal basso verso l'alto, la roughness da sinistra a destra. Solo illuminazione diretta.",
    "An HDR environment and its irradiance map: the cosine-weighted average of the light around every direction.": "Un ambiente HDR e la sua irradiance map: la media, pesata con il coseno, della luce intorno a ogni direzione.",
    "With diffuse image-based lighting the spheres pick up the colors of the sky and the ground. Metals stay dark.": "Con l'illuminazione diffusa basata su immagini le sfere raccolgono i colori del cielo e del suolo. I metalli restano scuri.",
    "The two precomputed halves of the split-sum approximation.": "Le due metà precalcolate della split-sum approximation.",
    "Full image-based lighting: smooth metals mirror the environment, rough ones show a blurred version of it.": "Illuminazione basata su immagini completa: i metalli lisci rispecchiano l'ambiente, quelli ruvidi ne mostrano una versione sfocata.",
    "Debugging by color: intermediate values written out as the fragment color.": "Il debug con i colori: valori intermedi mandati in uscita come colore del fragment.",
    "The glyph atlas, and text composed from one textured quad per character.": "L'atlas di glifi, e il testo composto con un rettangolo con texture per carattere.",
    "The whole game is one instanced draw call of colored rectangles.": "L'intero gioco è una sola draw call con instancing di rettangoli colorati.",
    "Marble, the game that comes with the engine: physically based materials, light from the sky, cascaded shadows, bloom and an interface drawn on top.": "Marble, il gioco che accompagna l'engine: materiali fisicamente corretti, luce del cielo, ombre a cascata, bloom e un'interfaccia disegnata sopra.",
    "One frame of Marble, pass by pass. Each picture is the texture that the pass draws into.": "Un frame di Marble, pass per pass. Ogni immagine è la texture in cui quel pass disegna.",
    "The whole course. The marble starts in the foreground, crosses the gap on the orange platform and finishes on the far right.": "L'intero percorso. La biglia parte in primo piano, attraversa il vuoto sulla piattaforma arancione e finisce all'estrema destra.",
    "The end of an unattended run: the autopilot has collected all eight gems and reached the goal.": "La fine di un'esecuzione senza nessuno ai comandi: l'autopilota ha raccolto tutte e otto le gemme e ha raggiunto il traguardo.",
    "The editor with its sample scene. The golden ball is selected: its handles are in the view, its components in the inspector.": "L'editor con la sua scena di esempio. La sfera dorata è selezionata: le sue maniglie sono nella vista, i suoi componenti nell'inspector.",
    "The Materials tab: the surface of the selected material and its texture slots.": "La scheda Materials: la superficie del materiale selezionato e i suoi slot di texture.",
    "After pressing Play: seen through the scene's own camera, the ball has rolled onto the ramp and the fountain is running.": "Dopo aver premuto Play: vista dalla camera propria della scena, la sfera è rotolata sulla rampa e la fontana è in funzione.",
    "A kernel reads one texture and writes another, one thread per pixel.": "Un kernel legge una texture e ne scrive un'altra, un thread per pixel.",
    "The same 4 x 4 grid of quad patches at increasing tessellation factors, displaced by a height function.": "La stessa griglia 4 x 4 di patch quadrilatere con fattori di tassellazione crescenti, spostata da una funzione di altezza.",
    "Left: what an intersection returns. Right: shadows from one ray per pixel toward the light.": "A sinistra: ciò che restituisce un'intersezione. A destra: ombre con un raggio per pixel verso la luce.",
    "NDC has y up. Textures and pixels have y down.": "Le NDC hanno y verso l'alto. Texture e pixel hanno y verso il basso.",
    "The two highlighted stages are the ones you program.": "I due stadi evidenziati sono quelli che programmi tu.",
}

IT_DEMO_TEXT = {
    "Change the clear color. This is all the first renderer does: clear, present, repeat.": "Cambia il colore di sfondo. È tutto ciò che fa il primo renderer: pulisce, presenta, ripete.",
    "Edit the positions or the color. The shader recompiles as you type.": "Modifica le posizioni o il colore. Lo shader si ricompila mentre scrivi.",
    "Per-vertex colors are interpolated across the triangle. Try out.color = out.position.": "I colori per vertice vengono interpolati lungo il triangolo. Prova out.color = out.position.",
    "Raise the UV scale above 1 to see the address modes, and switch the filter to nearest to see texels.": "Alza la scala delle UV sopra 1 per vedere gli address mode, e passa il filtro a nearest per vedere i texel.",
    "Move the sliders, then switch the order: rotating after translating swings the quad around the origin.": "Muovi gli slider, poi cambia l'ordine: ruotare dopo aver traslato fa girare il rettangolo intorno all'origine.",
    "Turn the depth test off to see faces drawn in submission order, and change the field of view.": "Spegni il test di profondità per vedere le facce disegnate nell'ordine di invio, e cambia il campo visivo.",
    "Click the view, then fly with W A S D (Q and E for down and up) and drag to look around.": "Clicca la vista, poi vola con W A S D (Q ed E per scendere e salire) e trascina per guardarti intorno.",
    "The color you see is the light's color multiplied by the object's color.": "Il colore che vedi è il colore della luce moltiplicato per il colore dell'oggetto.",
    "Drag to orbit. Set a strength to zero to see what each term contributes.": "Trascina per orbitare. Porta a zero un'intensità per vedere il contributo di ciascun termine.",
    "The same cube and the same light. Only the four material values change.": "Lo stesso cubo e la stessa luce. Cambiano solo i quattro valori del materiale.",
    "With the specular map only the steel frame shines. Untick it to give the wood the same highlight.": "Con la specular map luccica solo il telaio d'acciaio. Togli la spunta per dare al legno lo stesso riflesso.",
    "Switch the kind of light. The spotlight is a flashlight attached to the camera: drag to aim it.": "Cambia il tipo di luce. Lo spot è una torcia attaccata alla camera: trascina per puntarla.",
    "A directional light and four colored point lights in one fragment function. Drag to look around.": "Una luce direzionale e quattro luci puntiformi colorate in un'unica fragment function. Trascina per guardarti intorno.",
    "Raw depth is almost white everywhere. Linearized, it becomes a readable distance.": "La profondità grezza è quasi bianca ovunque. Resa lineare, diventa una distanza leggibile.",
    "Front faces are green and back faces red. Cull the front faces to look inside the cube.": "Le facce frontali sono verdi e quelle posteriori rosse. Scarta le facce frontali per guardare dentro il cubo.",
    "The scene is rendered into a texture; this fragment function then runs once per screen pixel.": "La scena viene disegnata in una texture; questa fragment function gira poi una volta per ogni pixel dello schermo.",
    "Drag to orbit. Slide from mirror to glass, and change the refractive index.": "Trascina per orbitare. Passa dallo specchio al vetro, e cambia l'indice di rifrazione.",
    "One draw call. Every cube derives its place in the ring from its instance ID.": "Una sola draw call. Ogni cubo ricava il suo posto nell'anello dal proprio ID di istanza.",
    "A light just above a floor. With Phong and a low exponent the highlight is cut off behind the light.": "Una luce appena sopra un pavimento. Con Phong e un esponente basso il riflesso viene troncato dietro la luce.",
    "Set the bias to zero to see shadow acne, raise it to see peter panning, and turn the filter off for hard edges.": "Porta il bias a zero per vedere la shadow acne, alzalo per vedere il peter panning, e spegni il filtro per avere bordi netti.",
    "A single flat quad. Drag to change the angle and watch the light catch the edges of the bricks.": "Un solo rettangolo piatto. Trascina per cambiare l'angolo e guarda la luce prendere i bordi dei mattoni.",
    "Drag to a shallow angle. With enough layers the bricks hide the mortar behind them.": "Trascina fino a un angolo radente. Con abbastanza strati i mattoni nascondono la malta dietro di loro.",
    "The lights are far brighter than 1.0. Compare clamping with the tone mappers and change the exposure.": "Le luci sono molto più luminose di 1.0. Confronta il taglio con i tone mapper e cambia l'esposizione.",
    "A Cook-Torrance material lit by a point light and a procedural sky. Drag to orbit. Add a value to the Material struct and a control for it appears.": "Un materiale Cook-Torrance illuminato da una luce puntiforme e da un cielo procedurale. Trascina per orbitare. Aggiungi un valore alla struct Material e compare un controllo per quel valore.",
    "Debugging by color: write an intermediate value out as the fragment color.": "Il debug con i colori: manda in uscita un valore intermedio come colore del fragment.",
    "A ray tracer in a fragment function: no triangles, one primary ray per pixel, then shadow and reflection rays.": "Un ray tracer in una fragment function: nessun triangolo, un raggio primario per pixel, poi raggi d'ombra e di riflessione.",
    "Each crate is drawn twice: once marking the stencil buffer, once enlarged and only where the stencil is not marked.": "Ogni cassa viene disegnata due volte: una marcando lo stencil buffer, una ingrandita e solo dove lo stencil non è marcato.",
    "Drag to orbit. Turn sorting off, or let the windows write depth, and watch windows disappear behind each other.": "Trascina per orbitare. Spegni l'ordinamento, o fai scrivere la profondità alle finestre, e guarda le finestre sparire una dietro l'altra.",
    "The scene is rendered into a floating-point texture. Pixels brighter than the threshold are blurred through the mip chain and added back.": "La scena viene disegnata in una texture in virgola mobile. I pixel più luminosi della soglia vengono sfocati attraverso la catena di mip e sommati di nuovo.",
    "The geometry pass fills three textures. This lighting pass then runs once per pixel, whatever the number of objects.": "Il geometry pass riempie tre texture. Questo lighting pass gira poi una volta per pixel, qualunque sia il numero di oggetti.",
    "For every pixel, sample points in a hemisphere above the surface and count how many are hidden behind the G-buffer.": "Per ogni pixel, prendi dei punti in un emisfero sopra la superficie e conta quanti sono nascosti dietro il G-buffer.",
    "A 4 x 4 grid of quad patches. The tessellation factor decides how finely each one is subdivided.": "Una griglia 4 x 4 di patch quadrilatere. Il fattore di tassellazione decide quanto finemente viene suddivisa ciascuna.",
    "Playable: move the paddle with the mouse, a finger, or the arrow keys. Click or press Space to launch.": "Giocabile: muovi la racchetta con il mouse, con un dito o con le frecce. Clicca o premi Spazio per lanciare.",
    "Show the structs and the vertex function": "Mostra le struct e la vertex function"
}

IT_TITLES = {
    "getting-started": "Per iniziare", "lighting": "Illuminazione", "model-loading": "Caricare i modelli",
    "advanced-metal": "Metal avanzato", "advanced-lighting": "Illuminazione avanzata", "pbr": "PBR",
    "in-practice": "In pratica", "beyond": "Oltre", "apple-platforms": "Piattaforme Apple", "resources": "Risorse",
    "getting-started/introduction": "Introduzione", "getting-started/project-setup": "Preparare il progetto",
    "getting-started/hello-view": "La prima vista", "getting-started/hello-triangle": "Il primo triangolo",
    "getting-started/shaders": "Shader", "getting-started/textures": "Texture",
    "getting-started/transformations": "Trasformazioni", "getting-started/coordinate-systems": "Sistemi di coordinate",
    "getting-started/camera": "Camera", "getting-started/review": "Riepilogo",
    "lighting/colors": "Colori", "lighting/basic-lighting": "Illuminazione di base", "lighting/materials": "Materiali",
    "lighting/lighting-maps": "Mappe di illuminazione", "lighting/light-casters": "Tipi di luce",
    "lighting/multiple-lights": "Più luci", "lighting/review": "Riepilogo",
    "model-loading/model-io": "Model I/O", "model-loading/mesh": "Mesh", "model-loading/model": "Modello",
    "advanced-metal/depth-testing": "Test di profondità", "advanced-metal/stencil-testing": "Test di stencil",
    "advanced-metal/blending": "Blending", "advanced-metal/face-culling": "Face culling",
    "advanced-metal/render-targets": "Render target", "advanced-metal/cubemaps": "Cubemap",
    "advanced-metal/advanced-data": "Dati avanzati", "advanced-metal/advanced-msl": "MSL avanzato",
    "advanced-metal/no-geometry-shaders": "Vivere senza geometry shader", "advanced-metal/instancing": "Instancing",
    "advanced-metal/anti-aliasing": "Anti-aliasing",
    "advanced-lighting/blinn-phong": "Blinn-Phong", "advanced-lighting/gamma-correction": "Correzione gamma",
    "advanced-lighting/shadow-mapping": "Shadow mapping", "advanced-lighting/point-shadows": "Ombre da luci puntiformi",
    "advanced-lighting/normal-mapping": "Normal mapping", "advanced-lighting/parallax-mapping": "Parallax mapping",
    "advanced-lighting/hdr": "HDR", "advanced-lighting/bloom": "Bloom",
    "advanced-lighting/deferred-shading": "Deferred shading", "advanced-lighting/ssao": "SSAO",
    "pbr/theory": "Teoria", "pbr/lighting": "Illuminazione", "pbr/diffuse-irradiance": "Irradianza diffusa",
    "pbr/specular-ibl": "IBL speculare",
    "in-practice/debugging": "Debug", "in-practice/text-rendering": "Rendering del testo", "in-practice/2d-game": "Un gioco 2D",
    "in-practice/game-engine": "Un game engine", "in-practice/engine-renderer": "Engine: il renderer",
    "in-practice/engine-gameplay": "Engine: il gioco", "in-practice/engine-editor": "Engine: l'editor",
    "beyond/compute-shaders": "Compute shader", "beyond/tessellation": "Tassellazione", "beyond/ray-tracing": "Ray tracing",
    "beyond/mesh-shaders": "Mesh shader",
    "apple-platforms/tile-based-gpus": "GPU tile-based", "apple-platforms/metalfx": "Upscaling con MetalFX",
    "apple-platforms/metal-4": "Metal 4", "apple-platforms/visionos": "visionOS",
    "resources/examples": "Codice di esempio",
}

BLURBS_IT = {
    "getting-started": "Apri una vista, disegna un triangolo, applicagli una texture, muovilo con le matrici e giraci attorno con una camera.",
    "lighting": "Il modello di Phong, i materiali, le mappe di illuminazione e ogni tipo di sorgente di luce.",
    "model-loading": "Trasforma i file dei modelli in vertex buffer, index buffer e materiali con Model I/O.",
    "advanced-metal": "Profondità e stencil, blending, render target, cubemap, instancing e anti-aliasing.",
    "advanced-lighting": "Ombre, normal e parallax mapping, HDR, bloom, deferred shading e SSAO.",
    "pbr": "Materiali fisicamente corretti e illuminazione basata su immagini.",
    "in-practice": "Strumenti di debug, rendering del testo, un piccolo gioco giocabile e un game engine completo con il suo editor.",
    "beyond": "Compute shader, tassellazione, ray tracing e mesh shader.",
    "apple-platforms": "Ciò che è specifico dell'hardware Apple: GPU tile-based, MetalFX, Metal 4 e visionOS.",
    "resources": "Progetti di esempio eseguibili per Swift e C++.",
}


GH_ICON = ('<svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M8 0a8 8 0 0 0-2.53 15.59c.4.07.55-.17.55-.38'
           'l-.01-1.49c-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66'
           '.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 4 0'
           'c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48l-.01 2.2'
           'c0 .21.15.46.55.38A8 8 0 0 0 8 0Z"/></svg>')

PAGE = """<!DOCTYPE html>
<html lang="{lang}" data-root="{root}" data-site="{site_root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="author" content="{author}">
<link rel="icon" href="{root}assets/favicon.png">
<script>
(function () {{
  var d = document.documentElement, t = null, l = null;
  try {{ t = localStorage.getItem("theme"); l = localStorage.getItem("lang"); }} catch (e) {{}}
  if (!t) t = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  d.dataset.theme = t;
  var q = /[?&]lang=(swift|cpp)/.exec(location.search);      // links can pick a language: page.html?lang=cpp
  if (q) l = q[1];
  d.dataset.lang = l === "cpp" ? "cpp" : "swift";
}})();
</script>
<script>window.LM_T = {strings};</script>
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="stylesheet" href="{root}assets/code.css">
</head>
<body class="{body_class}" data-key="{key}">
<a class="skip" href="#main">{t_skip}</a>
<header class="topbar">
  <button id="menu-toggle" class="icon-btn" aria-label="{t_menu}">
    <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
  </button>
  <a class="brand" href="{site_root}index.html"><img src="{root}assets/logo.png" alt="LearnMetal" width="136" height="32"></a>
  <div class="search" role="search">
    <input id="search" type="search" placeholder="{t_search}" aria-label="{t_search}" autocomplete="off" spellcheck="false">
    <div id="search-results" class="search-results" hidden></div>
  </div>
  <button id="search-toggle" class="icon-btn" aria-label="{t_search}">
    <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
  </button>
  <div class="lang-switch site-lang" role="group" aria-label="{t_text_lang}">
    <a href="{en_url}"{en_cur}>EN</a>
    <a href="{it_url}"{it_cur}>IT</a>
  </div>
  <div class="lang-switch" role="group" aria-label="{t_code_lang}">
    <button type="button" data-set-lang="swift">Swift</button>
    <button type="button" data-set-lang="cpp">C++</button>
  </div>
  <a class="icon-btn" href="{github}" aria-label="{author} on GitHub">{gh}</a>
  <button id="theme-toggle" class="icon-btn" aria-label="{t_theme}">
    <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10 3a7 7 0 0 1 0 14Z" fill="currentColor"/></svg>
  </button>
</header>
<div class="layout">
<nav class="sidebar" id="sidebar" aria-label="{t_chapters}">
{nav}
</nav>
<main class="content" id="main">
{body}
<footer class="site-footer">
  <p>&copy; {year} {author}. {t_rights}</p>
  <p><a href="{github}">{gh} github.com/gabrielevierti</a></p>
</footer>
</main>
{toc}
</div>
<script defer src="{root}assets/textures.js"></script>
<script defer src="{root}assets/live.js"></script>
<script defer src="{root}assets/demos.js"></script>
<script defer src="{root}assets/site.js"></script>
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


def flat_chapters():
    out = []
    for folder, section, chapters in SECTIONS:
        for slug, title in chapters:
            out.append((folder, section, slug, title))
    return out


def title_of(lang, folder, slug=None, default=""):
    if lang == "it":
        return IT_TITLES.get(folder if slug is None else f"{folder}/{slug}", default)
    return default


def build_nav(root, current=None, lang="en"):
    parts = []
    for folder, section, chapters in SECTIONS:
        parts.append(f'<div class="nav-section"><h4>{html.escape(title_of(lang, folder, None, section))}</h4><ul>')
        for slug, title in chapters:
            cls = ' class="active" aria-current="page"' if current == (folder, slug) else ""
            parts.append(f'<li><a{cls} data-key="{folder}/{slug}" href="{root}{folder}/{slug}.html">'
                         f'{html.escape(title_of(lang, folder, slug, title))}</a></li>')
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
    text += ".codehilite { background: var(--code-bg) !important; }\n"
    (OUT / "assets" / "code.css").write_text(text)


def image_tag(name, caption, lang="en"):
    if lang == "it":
        caption = IT_CAPTIONS.get(caption, caption)
    from PIL import Image
    path = ASSETS / "img" / f"{name}.webp"
    w, h = Image.open(path).size
    alt = html.escape(caption or name.split("/")[-1].replace("-", " "))
    cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return f'<figure><img src="../assets/img/{name}.webp" alt="{alt}" width="{w}" height="{h}" loading="lazy">{cap}</figure>'


def demo_tag(demo, fallback):
    fb = f' data-fallback="../assets/img/{fallback}.webp"' if fallback else ""
    return f'<div class="lm-demo" data-demo="{demo}"{fb}></div>'


def headings(lines):
    out, fenced = [], False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            out.append(i)
    return out


def insert_before(lines, key, anchor, block, ref=None):
    target = f"## {anchor}"
    source = ref if ref is not None else lines
    if anchor != "END" and target in source:
        i = source.index(target)
        if ref is not None:
            i = headings(lines)[headings(ref).index(i)]
        lines[i:i] = block
    else:
        if anchor != "END":
            print(f"warning: {key}: heading not found: {anchor!r}")
        lines += block


SWIFT_BLOCK = re.compile(r"^```swift\n.*?^```[ \t]*$", re.S | re.M)
CPP_BLOCK = re.compile(r"^```cpp\n.*?^```[ \t]*$", re.S | re.M)
REGION = re.compile(r"^<!-- (swift|cpp) -->\n(.*?)^<!-- /\1 -->[ \t]*$", re.S | re.M)


FENCE = re.compile(r"^```.*?^```[ \t]*$", re.S | re.M)


def localized(folder, slug, lang):
    """The chapter text in the requested language, and whether it is a translation."""
    english = (CONTENT / folder / f"{slug}.md").read_text()
    path = CONTENT / folder / f"{slug}.{lang}.md"
    if lang == "en" or not path.exists():
        return english, english, lang == "en"
    blocks = iter(FENCE.findall(english))          # {{code}} stands for the next code block of the English text
    text = re.sub(r"^\{\{code\}\}[ \t]*$", lambda m: next(blocks), path.read_text(), flags=re.M)
    figures = iter(re.findall(r"^<figure>.*?^</figure>[ \t]*$", english, flags=re.S | re.M))   # {{figure}}: the next inline figure
    text = re.sub(r"^\{\{figure\}\}[ \t]*$", lambda m: next(figures), text, flags=re.M)
    text = re.sub(r"<figcaption>(.*?)</figcaption>", lambda m: f"<figcaption>{IT_CAPTIONS.get(m.group(1), m.group(1))}</figcaption>", text)
    if next(blocks, None) is not None:
        print(f"warning: {folder}/{slug}.{lang}.md uses fewer code blocks than the English chapter")
    return text, english, True


def preprocess(text, key, folder, slug, ref_text=None, lang="en"):
    """Insert demos, figures, solutions and the example box, then build the Swift / C++ variants."""
    lines = text.split("\n")
    ref = ref_text.split("\n") if ref_text is not None and ref_text != text else None
    replaced = {fig for _, _, fig in DEMOS.get(key, []) if fig}
    for name, caption, anchor in FIGURES.get(key, []):
        if name not in replaced:
            insert_before(lines, key, anchor, ["", image_tag(name, caption, lang), ""], ref)
    for demo, anchor, fallback in DEMOS.get(key, []):
        insert_before(lines, key, anchor, ["", demo_tag(demo, fallback), ""], ref)

    # Mark the end of every exercise, so its solution can be attached after the conversion to HTML.
    inside, n, fenced = False, 0, False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fenced = not fenced
        if fenced:
            continue
        if line.startswith("## "):
            inside = line[3:].strip() in ("Exercises", "Esercizi")
        elif inside and line.startswith("- "):
            lines[i] = f"{line} LMSOL{n}LM"
            n += 1
    if key in EXAMPLES:
        target_name, folder_name = EXAMPLES[key]
        words = (("Progetto di esempio", "si esegue con", "Scarica tutti gli esempi", "oppure guarda", "come eseguirli") if lang == "it"
                 else ("Example project", "run with", "Download all examples", "or see", "how to run them"))
        box = (f'<div class="example-box lang-swift"><strong>{words[0]}</strong> '
               f'<code>examples/Sources/{folder_name}</code>, {words[1]} <code>swift run {target_name}</code>. '
               f'<a href="../downloads/learnmetal-examples.zip">{words[2]}</a> {words[3]} '
               f'<a href="../resources/examples.html">{words[4]}</a>.</div>')
        i = next(k for k, line in enumerate(lines) if line.startswith("# "))
        lines[i + 1:i + 1] = ["", box, ""]
    text = "\n".join(lines)

    # Language-specific prose.
    text = REGION.sub(lambda m: f'\n<div class="lang-{m.group(1)}">\n{md().convert(m.group(2))}\n</div>\n', text)

    # Pair every Swift block with its C++ version from the sidecar file.
    sidecar = CONTENT / folder / f"{slug}.cpp.md"
    swift_count = len(SWIFT_BLOCK.findall(text))
    if sidecar.exists():
        cpp = CPP_BLOCK.findall(sidecar.read_text())
        if len(cpp) != swift_count:
            print(f"warning: {key}: {swift_count} Swift blocks but {len(cpp)} C++ blocks")
        it = iter(cpp)

        def pair(m):
            other = next(it, None)
            if other is None:
                return m.group(0)
            return (f'\n<div class="lang-swift">\n{md().convert(m.group(0))}\n</div>\n'
                    f'<div class="lang-cpp">\n{md().convert(other)}\n</div>\n')

        text = SWIFT_BLOCK.sub(pair, text)
    elif swift_count:
        note = ('<div class="lang-note lang-cpp"><strong>C++ version in progress.</strong> The host code in this chapter is '
                'shown in Swift for now. The shaders are identical in both languages, and the '
                '<a href="../getting-started/project-setup.html">name mapping</a> to metal-cpp is mechanical.</div>')
        if lang == "it":
            note = ('<div class="lang-note lang-cpp"><strong>Versione C++ in preparazione.</strong> Per ora il codice host di questo '
                    'capitolo è mostrato in Swift. Gli shader sono identici nei due linguaggi, e la '
                    '<a href="../getting-started/project-setup.html">corrispondenza dei nomi</a> con metal-cpp è meccanica.</div>')
        lines = text.split("\n")
        i = next(k for k, line in enumerate(lines) if line.startswith("# "))
        lines[i + 1:i + 1] = ["", note, ""]
        text = "\n".join(lines)
    return text


def zip_folder(source, dest, prefix):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(source.rglob("*")):
            rel = f.relative_to(source)
            if f.is_file() and not any(part.startswith(".") or part == "build" for part in rel.parts):
                z.write(f, f"{prefix}/{rel}")


def toc_html(tokens, label):
    items = [t for t in tokens[0]["children"]] if tokens and tokens[0].get("children") else []
    if len(items) < 2:
        return ""
    links = "".join(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in items)
    return f'<aside class="toc" aria-label="{label}"><h4>{label}</h4><ul>{links}</ul></aside>'


def page(lang="en", **kw):
    t = STRINGS[lang]
    defaults = dict(github=GITHUB, author=AUTHOR, year=YEAR, gh=GH_ICON, toc="", body_class="", key="", lang=lang,
                    strings=json.dumps(dict(t["js"], demo=IT_DEMO_TEXT) if lang == "it" else t["js"], ensure_ascii=False),
                    en_cur=' aria-current="true"' if lang == "en" else "", it_cur=' aria-current="true"' if lang == "it" else "")
    defaults.update({f"t_{k}": v for k, v in t.items() if isinstance(v, str)})
    defaults.update(kw)
    return PAGE.format(**defaults)


def attach_solutions(body, folder, slug, lang, label):
    english = CONTENT / folder / f"{slug}.solutions.md"
    path = CONTENT / folder / f"{slug}.solutions.{lang}.md"
    if not path.exists():
        path = english
    text = path.read_text() if path.exists() else ""
    if path != english:                             # {{code}} stands for the next code block of the English solutions
        blocks = iter(FENCE.findall(english.read_text()))
        text = re.sub(r"^\{\{code\}\}[ \t]*$", lambda m: next(blocks), text, flags=re.M)
    solutions = [x.strip() for x in re.split(r"^---[ \t]*$", text, flags=re.M)] if text else []
    count = len(re.findall(r"LMSOL\d+LM", body))
    if solutions and count != len(solutions):
        print(f"warning: {folder}/{slug}: {count} exercises but {len(solutions)} solutions")

    def one(m):
        i = int(m.group(1))
        if i >= len(solutions):
            return ""
        return f'<details class="solution"><summary>{label}</summary>{md().convert(solutions[i])}</details>'

    return re.sub(r"\s*LMSOL(\d+)LM", one, body)


TAG = re.compile(r"<[^>]+>")

# Every sentence of the running text starts on a line of its own. The text is written as ordinary
# paragraphs; this puts a line break after each full stop, question mark or exclamation mark.
PIECE = re.compile(r"(<code>.*?</code>|<[^>]+>)", re.S)
NOT_AN_END = {"e.g", "i.e", "vs", "cf", "es", "p.es", "fig", "ca", "approx", "ecc.)", "etc.)"}
SENTENCE_END = re.compile("([.!?][)\"\u201d\u2019\u00bb]?(?:\ue002\\d+\ue003)*)[ \n]+"
                          "(?=(?:\ue002\\d+\ue003)*(?:[A-Z\u00c0-\u00dd0-9(\u201c\"\u00ab]|\ue000))")


def break_sentences(inner):
    pieces = PIECE.split(inner)
    plain = "".join(p if i % 2 == 0 else (f"\ue000{i}\ue001" if p.startswith("<code>") else f"\ue002{i}\ue003")
                    for i, p in enumerate(pieces))

    def one(m):
        before = re.sub("\ue002\\d+\ue003", "", plain[:m.start()])
        word = re.split(r"[\s(]", before)[-1] if before else ""
        if word.lower() in NOT_AN_END or (len(word) == 1 and word.isalpha() and plain[m.start()] == "."):
            return m.group(0)
        if word.isdigit() and plain[m.start()] == "." and not before[:-len(word)].strip():
            return m.group(0)                       # "1. First step" at the start of a paragraph
        return m.group(1) + "<br>\n"

    plain = SENTENCE_END.sub(one, plain)
    return re.sub("[\ue000\ue002](\\d+)[\ue001\ue003]", lambda m: pieces[int(m.group(1))], plain)


def one_sentence_per_line(body):
    keep = []

    def hide(m):
        keep.append(m.group(0))
        return f"\ue004{len(keep) - 1}\ue005"

    body = re.sub(r"<pre.*?</pre>|<figure.*?</figure>|<table.*?</table>|<h[1-6].*?</h[1-6]>|<summary.*?</summary>"
                  r"|<p class=\"(?:crumb|admonition-title)\">.*?</p>|<div class=\"(?:example-box|lm-demo|lang-note)[^>]*>.*?</div>",
                  hide, body, flags=re.S)
    body = re.sub(r"(<p>)(.*?)(</p>)", lambda m: m.group(1) + break_sentences(m.group(2)) + m.group(3), body, flags=re.S)
    body = re.sub(r"(<li>)((?:(?!<li>|<p>|<ul>|<ol>|<div|<details|\ue004).)*?)(</li>|<ul>|<ol>|<details)",
                  lambda m: m.group(1) + break_sentences(m.group(2)) + m.group(3), body, flags=re.S)
    return re.sub("\ue004(\\d+)\ue005", lambda m: keep[int(m.group(1))], body)


def index_entries(url, title, body):
    """One search entry per section of a page: [url, page title, heading, text]."""
    body = re.sub(r"<pre.*?</pre>|<figure.*?</figure>|<details.*?</details>", " ", body, flags=re.S)
    parts = re.split(r'<h2 id="([^"]+)">(.*?)</h2>', body, flags=re.S)
    out = []

    def clean(x):
        return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", x))).replace(" #", "").strip()

    intro = clean(re.sub(r"<h1.*?</h1>|<p class=\"crumb\">.*?</p>", " ", parts[0], flags=re.S))
    out.append([url, title, "", intro])
    for i in range(1, len(parts), 3):
        out.append([f"{url}#{parts[i]}", title, clean(parts[i + 1]), clean(parts[i + 2])])
    return out


def build_site(lang):
    t = STRINGS[lang]
    out = OUT if lang == "en" else OUT / lang
    up = "" if lang == "en" else "../"            # from this language's root to the site root
    chapters = flat_chapters()
    index, missing, translated = [], [], 0
    for i, (folder, section, slug, title) in enumerate(chapters):
        src = CONTENT / folder / f"{slug}.md"
        if not src.exists():
            missing.append(str(src.relative_to(ROOT)))
            continue
        key = f"{folder}/{slug}"
        text, english, is_translated = localized(folder, slug, lang)
        text, english = (x.replace("{{engine-repo}}", ENGINE_REPO) for x in (text, english))
        translated += is_translated
        m = md()
        body = m.convert(preprocess(text, key, folder, slug, english, lang))
        body = attach_solutions(body, folder, slug, lang, t["solution"])
        body = one_sentence_per_line(body)
        if not is_translated:
            body = re.sub(r"(</h1>)", r"\1" + t["untranslated"], body, count=1)
        if lang != "en":
            body = re.sub(r'="\.\./(assets|downloads)/', r'="../../\1/', body)
        name = title_of(lang, folder, slug, title)
        section_name = title_of(lang, folder, None, section)
        pager = ['<nav class="pager" id="pager">']
        if i > 0:
            pf, _, ps, pt = chapters[i - 1]
            pager.append(f'<a class="prev" href="../{pf}/{ps}.html"><small>{t["prev"]}</small>{html.escape(title_of(lang, pf, ps, pt))}</a>')
        else:
            pager.append("<span></span>")
        if i + 1 < len(chapters):
            nf, _, ns, nt = chapters[i + 1]
            pager.append(f'<a class="next" href="../{nf}/{ns}.html"><small>{t["next"]}</small>{html.escape(title_of(lang, nf, ns, nt))}</a>')
        pager.append("</nav>")
        crumb = f'<p class="crumb">{html.escape(section_name)}</p>'
        dest = out / folder / f"{slug}.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page(
            lang,
            title=f"{name} | {SITE}",
            description=html.escape(f"{section_name}: {name}. {t['tagline'] or TAGLINE}"),
            root=f"../{up}", site_root="../", key=key,
            en_url=f"../{up}{folder}/{slug}.html", it_url=f"../{up}it/{folder}/{slug}.html",
            nav=build_nav("../", (folder, slug), lang),
            body=f"<article>{crumb}{body}</article>{''.join(pager)}",
            toc=toc_html(m.toc_tokens, t["toc"]),
        ))
        index += index_entries(f"{folder}/{slug}.html", name, body)

    # Home page
    first = chapters[0]
    tagline = t["tagline"] or TAGLINE
    hero = f"""
<section class="hero">
  <div class="hero-text">
    <h1>{t["hero"]}</h1>
    <p>{html.escape(tagline)} {t["hero_more"]}</p>
    <p class="hero-actions">
      <a class="cta" href="{first[0]}/{first[2]}.html">{t["start"]}</a>
      <a class="cta ghost" href="resources/examples.html">{t["get"]}</a>
    </p>
  </div>
  <div class="hero-demo"><div class="lm-demo" data-demo="pbr" data-collapse="1"></div></div>
</section>"""
    blurbs = BLURBS_IT if lang == "it" else BLURBS
    rows = [f'<section class="syllabus"><div class="syl-top"><h2>{t["path"]}</h2><p id="progress" class="progress" hidden></p></div><ol>']
    for folder, section, chs in SECTIONS:
        links = "".join(f'<li><a data-key="{folder}/{slug}" href="{folder}/{slug}.html">{html.escape(title_of(lang, folder, slug, title))}</a></li>'
                        for slug, title in chs)
        rows.append(f'<li><div class="syl-head"><h3><a href="{folder}/{chs[0][0]}.html">{html.escape(title_of(lang, folder, None, section))}</a></h3>'
                    f'<p>{html.escape(blurbs.get(folder, ""))}</p></div><ul>{links}</ul></li>')
    rows.append("</ol></section>")
    home = CONTENT / f"index.{lang}.md"
    intro = one_sentence_per_line(md().convert((home if home.exists() else CONTENT / "index.md").read_text()))
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page(
        lang,
        title="LearnMetal | " + ("Impara la grafica con Metal in Swift e C++" if lang == "it" else "Learn Metal graphics programming in Swift and C++"),
        description=html.escape(tagline),
        root=up, site_root="", en_url=f"{up}index.html", it_url=f"{up}it/index.html",
        nav=build_nav("", None, lang),
        body=f"{hero}{''.join(rows)}<article class='home-notes'>{intro}</article>",
        body_class="home",
    ))
    (out / "search-index.js").write_text("window.LM_SEARCH = " + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"[{lang}] {len(chapters) - len(missing)} chapters, {translated} in this language, {len(index)} search entries")
    for m_ in missing:
        print("missing:", m_)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ASSETS, OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    write_code_css()
    zip_folder(EXAMPLES_DIR, OUT / "downloads" / "learnmetal-examples.zip", "learnmetal-examples")
    zip_folder(CPP_DIR, OUT / "downloads" / "learnmetal-cpp-starter.zip", "learnmetal-cpp-starter")
    for lang in ("en", "it"):
        build_site(lang)


if __name__ == "__main__":
    build()
