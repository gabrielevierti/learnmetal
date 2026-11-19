# Codice di esempio

Ci sono due gruppi di progetti: gli esempi in Swift per i capitoli principali, e un progetto di partenza in C++ per chi usa metal-cpp.

Il repository comprende un package Swift con esempi eseguibili per i capitoli principali. Ognuno è una piccola app macOS in un solo `main.swift` più un file `Shaders.metal`.

<p><a class="cta" href="../downloads/learnmetal-examples.zip">Scarica tutti gli esempi (.zip)</a></p>

## Eseguire un esempio

Ti servono macOS 13 o successivo e Xcode 15 o successivo. Nella cartella estratta:

{{code}}

Puoi anche aprire `Package.swift` in Xcode, scegliere un esempio dal menu degli scheme e premere Run. Così hai la validazione dell'API, il GPU frame debugger e l'HUD delle prestazioni descritti in [Debug](../in-practice/debugging.html).

## Gli esempi

| Target | Capitoli |
| --- | --- |
| `HelloView` | [La prima vista](../getting-started/hello-view.html) |
| `HelloTriangle` | [Il primo triangolo](../getting-started/hello-triangle.html) |
| `Shaders` | [Shader](../getting-started/shaders.html) |
| `Textures` | [Texture](../getting-started/textures.html) |
| `Transformations` | [Trasformazioni](../getting-started/transformations.html) |
| `CoordinateSystems` | [Sistemi di coordinate](../getting-started/coordinate-systems.html) |
| `Camera` | [Camera](../getting-started/camera.html) |
| `BasicLighting` | [Colori](../lighting/colors.html), [Illuminazione di base](../lighting/basic-lighting.html), [Materiali](../lighting/materials.html) |
| `LightingMaps` | [Mappe di illuminazione](../lighting/lighting-maps.html) |
| `MultipleLights` | [Tipi di luce](../lighting/light-casters.html), [Più luci](../lighting/multiple-lights.html) |
| `ModelLoading` | [Model I/O](../model-loading/model-io.html), [Mesh](../model-loading/mesh.html), [Modello](../model-loading/model.html) |
| `RenderTargets` | [Render target](../advanced-metal/render-targets.html) |
| `Instancing` | [Instancing](../advanced-metal/instancing.html) |
| `ShadowMapping` | [Shadow mapping](../advanced-lighting/shadow-mapping.html) |
| `HDRBloom` | [HDR](../advanced-lighting/hdr.html), [Bloom](../advanced-lighting/bloom.html) |
| `PBR` | [Illuminazione PBR](../pbr/lighting.html) |
| `ComputeParticles` | [Compute shader](../beyond/compute-shaders.html) |

I capitoli che non compaiono in questo elenco hanno il codice solo nel testo.

## In che cosa differiscono dai capitoli

- **Nessun progetto Xcode.** I capitoli costruiscono un'app SwiftUI. Gli esempi usano una piccola libreria, `LearnMetalKit`, che apre una semplice finestra AppKit, così ogni esempio è un file solo.
- **Gli shader vengono compilati all'avvio** dal testo di `Shaders.metal` con `makeLibrary(source:)`. Questo permette a `swift run` di funzionare senza il passo di build di Metal di Xcode. Gli errori degli shader vengono stampati in console.
- **Le texture sono generate nel codice**, quindi non c'è nient'altro da scaricare.
- **Gli esempi da 01 a 03 scrivono a mano il ciclo dei frame.** Quelli successivi lo ereditano da una classe `BaseRenderer` per restare brevi.

## Il progetto di partenza in C++

<p><a class="cta" href="../downloads/learnmetal-cpp-starter.zip">Scarica il progetto di partenza in C++ (.zip)</a></p>

Il progetto di partenza è il capitolo Il primo triangolo in C++: una finestra GLFW, un `CAMetalLayer` e un renderer scritto con metal-cpp di Apple. Richiede `brew install glfw cmake` e una copia di [metal-cpp](https://developer.apple.com/metal/cpp/) estratta nella cartella. Compilalo con CMake come descritto in [Preparare il progetto](../getting-started/project-setup.html). È la base su cui si costruisce il codice C++ dei capitoli.

## L'engine

L'esempio più grande ha un repository tutto suo. Il [LearnMetal Engine]({{engine-repo}}) è un piccolo game engine con un gioco giocabile, scritto in Swift e in C++, che mette al lavoro insieme le tecniche di questo sito. [Un game engine](../in-practice/game-engine.html) lo presenta, e i capitoli successivi percorrono il renderer, il gioco e l'editor.

## Sulle demo interattive e sulle figure

Le demo interattive girano nel tuo browser con WebGL. Lo shader che modifichi è Metal Shading Language, tradotto al volo in GLSL da un piccolo script (`assets/live.js`). Il traduttore copre la parte del linguaggio usata dai capitoli; è un aiuto didattico e non un'implementazione completa di Metal, quindi alcune cose differiscono da un vero Mac, per esempio regole più rigide sul mescolare `int` e `float`.


Le immagini statiche che restano sono illustrazioni. Le disegna un piccolo renderer software nella cartella `tools/` del repository, che implementa con numpy la stessa matematica degli shader di ogni capitolo. Non sono screenshot degli esempi Metal, quindi aspettati piccole differenze nelle texture e nell'inquadratura quando esegui il codice.
