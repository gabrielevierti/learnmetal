# learnmetal

A free, step-by-step tutorial site for learning 3D graphics programming with Apple's **Metal** API, in Swift. It follows the classic "from a triangle to PBR" learning path: getting started, lighting, model loading, advanced rendering techniques, advanced lighting, physically based rendering, and a few practical chapters.

## Publish on GitHub Pages

1. Push this repository to GitHub.
2. Open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, branch `main`, folder `/docs`.

The built site is already committed in `docs/`, so no build step is needed on GitHub.

## Editing

All chapters are Markdown files in `content/<section>/<chapter>.md`. The chapter order and titles live in the `SECTIONS` list at the top of `build.py`.

```sh
pip install markdown pygments pillow
python3 build.py          # regenerates docs/
python3 -m http.server -d docs 8000   # preview at http://localhost:8000
```

Markdown extras available in chapters:

- Fenced code blocks with `swift` or `cpp` (used for Metal Shading Language) highlighting.
- Callouts: `!!! note "Title"` and `!!! warning "Title"` followed by an indented body.
- Raw HTML, including inline SVG diagrams.

Figures and the "Example code" box are added by `build.py`: the `FIGURES` and `EXAMPLES` tables near the top say which image goes before which heading and which example belongs to which chapter.

## Example code

`examples/` is a Swift package with 17 runnable macOS examples (`swift run HelloTriangle`, or open `examples/Package.swift` in Xcode). See `examples/README.md`. The build zips this folder into `docs/downloads/learnmetal-examples.zip`, which the site links to.

## Figures

The images in `assets/img/` are illustrations, not screenshots of the Metal examples. They are drawn by a small software renderer that implements the same shading math as the chapters:

```sh
pip install numpy scipy pillow
python3 tools/render_figures.py            # all figures
python3 tools/render_figures.py shadow     # only names containing "shadow"
```

To replace one with a real screenshot, save it as a `.webp` with the same name.

## Layout

```
content/    Markdown sources
assets/     CSS, JavaScript and figures copied into the site
examples/   Swift package with the runnable examples
tools/      Software renderer that draws the figures
docs/       Generated site (served by GitHub Pages)
build.py    Generator
```
