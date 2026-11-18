# Preparare il progetto

Per preparare un progetto Metal bastano pochi minuti. Metal fa parte del sistema, quindi non c'è niente da compilare prima di poter disegnare.

Usa il selettore **Swift / C++** in cima alla pagina per scegliere il linguaggio. I capitoli, gli shader e le demo interattive sono uguali per entrambi; cambia solo il codice dell'applicazione.

## Che cosa serve

- Un Mac con una versione recente di macOS.
- Xcode, gratuito sul Mac App Store. A chi usa C++ bastano i command line tools.

Gli esempi sono per macOS perché è il ciclo più rapido: premi Run e compare una finestra.

<!-- swift -->

Tutto, tranne le poche righe che ospitano la vista, funziona senza modifiche su iOS, e le differenze sono mostrate qui sotto.

!!! note "Simulatore o dispositivo?"
    Metal funziona nel Simulatore iOS, ma con funzionalità e prestazioni ridotte. Quando il tuo obiettivo è iPhone o iPad, prova su un dispositivo vero.

## Creare il progetto

1. In Xcode scegli **File → New → Project**.
2. Seleziona **macOS → App**.
3. Chiamalo `LearnMetal`, imposta **Interface** su **SwiftUI** e **Language** su **Swift**.

Xcode offre anche un template **Game** con Metal come tecnologia. Genera un cubo che ruota già funzionante: bello da vedere, ma nasconde proprio le parti che vogliamo scrivere noi, quindi partiamo da un'app vuota.

## MetalKit e MTKView

Per disegnare con Metal serve una superficie che il sistema possa mettere a schermo. La via di basso livello è un `CAMetalLayer` con un display link gestito da te. **MetalKit** racchiude entrambi in una vista chiamata `MTKView` che:

- possiede il layer e a ogni frame ti consegna un nuovo **drawable** (una texture che verrà mostrata a schermo),
- crea per te, su richiesta, le texture di profondità e di multisampling,
- chiama il tuo codice una volta per ogni aggiornamento dello schermo.

Dici alla vista che cosa disegnare dandole un **delegate**, un oggetto che implementa due metodi di `MTKViewDelegate`. Quel delegate è il nostro renderer, ed è lì che vivrà quasi tutto il codice di questa serie.

## Ospitare la vista in SwiftUI

`MTKView` è una vista AppKit (UIKit su iOS), quindi a SwiftUI serve un piccolo adattatore. Aggiungi un nuovo file Swift `MetalView.swift`:

{{code}}

Il coordinator esiste per un solo motivo: `MTKView` tiene il suo delegate con un riferimento debole, quindi qualcos'altro deve mantenere in vita il renderer.

Su iOS l'adattatore è lo stesso con nomi diversi: adotta `UIViewRepresentable` e implementa `makeUIView` e `updateUIView`.

Poi mostra la vista in `ContentView.swift`:

{{code}}

Il progetto non compila ancora perché `Renderer` non esiste. È l'argomento del prossimo capitolo.

## Dove vanno gli shader

Gli shader stanno in file con estensione `.metal`. Creane uno con **File → New → File → Metal File** e chiamalo `Shaders.metal`. Xcode gli dà questo contenuto:

{{code}}

Per ora lascialo così. Ogni file `.metal` che appartiene al target dell'app viene compilato durante la build e incluso automaticamente nell'app.

## Attivare le reti di sicurezza

Apri **Product → Scheme → Edit Scheme → Run → Diagnostics** (in alcune versioni di Xcode le opzioni di Metal sono sotto **Options**) e controlla che **Metal API Validation** sia attiva. La validazione controlla ogni chiamata a Metal e, quando fai qualcosa di non permesso, si ferma con un messaggio leggibile invece di mostrare uno schermo nero. È attiva in modo predefinito nelle esecuzioni di debug, e conviene lasciarla così. **Shader Validation**, nello stesso posto, intercetta le letture fuori dai limiti e altri errori simili dentro gli shader; attivala ogni volta che uno shader si comporta male.

<!-- /swift -->

<!-- cpp -->

## metal-cpp

Metal è un'API Objective-C. **metal-cpp** è il wrapper C++ ufficiale di Apple, fatto di soli header: ogni classe e ogni metodo di Metal ha un equivalente C++ senza costi aggiuntivi. Scaricalo da [developer.apple.com/metal/cpp](https://developer.apple.com/metal/cpp/) e decomprimilo nel progetto in una cartella `metal-cpp`.

La corrispondenza con i nomi Objective-C e Swift è meccanica:

| Swift | C++ con metal-cpp |
| --- | --- |
| `MTLDevice`, `MTLBuffer` | `MTL::Device*`, `MTL::Buffer*` |
| `device.makeCommandQueue()` | `device->newCommandQueue()` |
| `MTLRenderPipelineDescriptor()` | `MTL::RenderPipelineDescriptor::alloc()->init()` |
| `descriptor.colorAttachments[0].pixelFormat = .bgra8Unorm` | `descriptor->colorAttachments()->object(0)->setPixelFormat(MTL::PixelFormatBGRA8Unorm)` |
| `encoder.setVertexBuffer(buffer, offset: 0, index: 0)` | `encoder->setVertexBuffer(buffer, 0, 0)` |
| `"vertex_main"` | `MTLSTR("vertex_main")` |

Tre regole coprono la gestione della memoria, perché in C++ non c'è ARC:

- Gli oggetti che ottieni da un metodo che inizia con `new`, o da `alloc()->init()`, sono **tuoi**. Chiama `release()` quando hai finito.
- Tutto il resto è **autoreleased**: valido finché non viene rilasciato l'`NS::AutoreleasePool` che lo racchiude. Crea un pool all'inizio di ogni frame.
- Per tenere un oggetto autoreleased, chiama `retain()`.

L'implementazione del wrapper va compilata esattamente una volta. Crea `metal_impl.cpp`:

{{code}}

## Una finestra

metal-cpp copre Metal, Foundation e QuartzCore. Non copre AppKit né MetalKit, quindi `MTKView` non c'è. Apriamo una finestra con **GLFW** (`brew install glfw cmake`) e le agganciamo un `CAMetalLayer`. Quel singolo passaggio deve toccare AppKit, quindi sta in un minuscolo file Objective-C++, `glfw_bridge.mm`:

{{code}}

`main.cpp` crea la finestra, il device e il renderer, ed esegue il ciclo:

{{code}}

Il layer fa la parte che in Swift fa `MTKView`: ogni volta che glielo chiedi ti consegna un **drawable**, una texture che verrà mostrata a schermo. Presentare un drawable aspetta lo schermo, quindi questo ciclo gira alla frequenza di aggiornamento del display.

Ovunque un capitolo nomini `MTKView`, l'equivalente C++ è una di tre cose che fai da te: chiedere al layer il prossimo drawable, compilare un render pass descriptor o creare una texture di profondità. Ognuna viene mostrata la prima volta che serve.

## Compilare con CMake

{{code}}

{{code}}

Il progetto non compila ancora perché `Renderer` non esiste. È l'argomento del prossimo capitolo.

## Dove vanno gli shader

Gli shader stanno in un file chiamato `Shaders.metal`:

{{code}}

Xcode compila i file `.metal` durante la build. Fuori da Xcode la via più semplice è compilare il sorgente all'avvio dell'app, così un errore nello shader viene anche segnalato nel terminale con il numero di riga:

{{code}}

Per un'app da distribuire precompileresti con `xcrun metal` e `xcrun metallib` e caricheresti il file `.metallib` risultante.

## Attivare le reti di sicurezza

Il livello di validazione di Metal controlla ogni chiamata e, quando fai qualcosa di non permesso, si ferma con un messaggio leggibile invece di mostrare uno schermo nero. Fuori da Xcode si attiva con le variabili d'ambiente:

{{code}}

Lascia `MTL_DEBUG_LAYER` attivo ogni volta che sviluppi. Un progetto di partenza con tutti i file di questo capitolo e dei due successivi è nella cartella `examples-cpp` del repository.

<!-- /cpp -->

Il capitolo [Debug](../in-practice/debugging.html) tratta questi strumenti a fondo. Puoi leggerlo quando vuoi.
