# Un game engine

Finora ogni capitolo ha costruito una tecnica isolata: una shadow map qui, una catena di bloom là, ognuna nel suo piccolo programma. Questo capitolo e i tre successivi le mettono insieme. Il risultato è il **LearnMetal Engine**: un piccolo game engine fatto interamente con Metal, scritto due volte, una in Swift e una in C++, con sopra un piccolo gioco completo e un editor con cui costruire le scene.

È piccolo di proposito. L'engine sta tra le cinque e le seimila righe in ciascun linguaggio, commenti compresi, ed è fatto per essere letto. Non contiene nessuna tecnica che tu non abbia incontrato in queste pagine; di nuovo c'è il modo in cui i pezzi sono disposti perché lavorino insieme.

<p><a class="cta" href="{{engine-repo}}">Prendi l'engine su GitHub</a> <a class="cta ghost" href="{{engine-repo}}/archive/refs/heads/main.zip">Scaricalo come .zip</a></p>

## Scaricarlo ed eseguirlo

L'engine vive in un repository tutto suo. Ti servono macOS 13 o successivo e Xcode 15 o successivo.

<!-- swift -->
{{code}}

Se vuoi il debugger e gli strumenti per la GPU, apri invece `Package.swift` in Xcode.
<!-- /swift -->

<!-- cpp -->
La versione C++ ha bisogno anche di CMake 3.24 o successivo. La prima configurazione scarica le quattro librerie che usa: GLFW, metal-cpp, stb e miniaudio.

{{code}}
<!-- /cpp -->

Così parte **Marble**, il gioco di esempio. Rotola con W A S D, salta con Spazio, guardati intorno con le frecce o trascinando il mouse. Raccogli le otto gemme e raggiungi il disco luminoso. Funziona anche un gamepad.

Premi **F1** per le statistiche e **F2** per vedere le forme della fisica.

## Che cosa aggiunge un engine

I programmi di esempio di questo sito hanno ciascuno una classe renderer che sa esattamente che cosa disegna: "un cubo e un pavimento", "nove sfere". Questo smette di funzionare nel momento in cui l'elenco delle cose da disegnare viene deciso mentre il programma gira. Un engine è ciò che ottieni quando separi **ciò che esiste** da **come viene disegnato**:

- Una **scena** contiene le cose che esistono: entità con una posizione, una mesh, una luce, un corpo fisico.
- Un **renderer** disegna qualunque cosa ci sia nella scena, senza sapere di che gioco si tratta.
- I **sistemi** cambiano la scena nel tempo: la fisica, le particelle, la logica propria del gioco.
- Un **ciclo** li esegue tutti in un ordine fisso, a ogni frame.

Intorno a questi stanno i servizi che un gioco dà per scontati: caricare file, l'input, il suono, un modo di disegnare un'interfaccia.

## La forma di un gioco

Un gioco è un oggetto con poche funzioni che l'engine chiama al momento giusto. Eccone uno completo: un cubo che gira, illuminato da un sole, con un'ombra.

{{code}}

Dentro non c'è alcun render pass, alcun pipeline state, alcun buffer. Il gioco dice che cosa esiste; tutto ciò che viene dai capitoli precedenti avviene dentro `engine.run`.

Nota come vengono puntati la camera e il sole. Entrambi guardano lungo il proprio asse z negativo, come la camera del capitolo [Camera](../getting-started/camera.html), quindi dare loro una rotazione significa dare loro una direzione.

## Il frame

`Engine` possiede il ciclo. A ogni frame fa le stesse cose nello stesso ordine:

{{code}}

Dopo, il renderer disegna la scena, e sopra di essa il canvas 2D.

L'ordine non è arbitrario. La fisica gira prima dell'`update` del gioco, così la logica di gioco vede dove sono finite le cose. Le matrici di mondo vengono calcolate dopo tutto ciò che può spostare un'entità, e prima dei due sistemi che ne hanno bisogno: le particelle e il renderer. Le entità distrutte durante il frame vengono rimosse solo in punti fissi, così nessun sistema tiene mai un riferimento a qualcosa che è sparito a metà strada.

## Un passo fisso per la fisica

Il rendering impiega un tempo diverso a ogni frame. Se la fisica avanzasse di quella stessa quantità variabile, una palla rimbalzerebbe in modo un po' diverso su ogni macchina, e un frame lento potrebbe farla passare attraverso un pavimento. Quindi la fisica avanza sempre di un sessantesimo di secondo esatto, e l'engine decide quanti di questi passi stanno nel tempo trascorso:

{{code}}

Il tempo reale viene versato nell'accumulatore e prelevato in porzioni fisse. Su uno schermo a 120 Hz un frame su due non esegue alcun passo; dopo un intoppo un frame ne esegue diversi, fino a un limite.

Ciò che resta nell'accumulatore è una frazione di passo, `alpha`. Il renderer non mostra i corpi nella loro ultima posizione fisica, ma in una miscela tra la precedente e l'ultima, a `alpha` del percorso. È questo che rende fluido il movimento anche se la fisica conosce solo sessanta istanti al secondo.

Vale la pena ricordare una conseguenza: una funzione che gira "zero, una o più volte per frame" è il posto sbagliato per chiedere se un tasto è stato appena premuto. Leggi l'input in `update` e ricordalo; applica le forze in `fixedUpdate`.

## Un'unica fonte di verità per la GPU

Ogni capitolo con un buffer di uniform aveva lo stesso avvertimento: la struct nello shader e la struct nel codice host devono coincidere byte per byte, e nessuno lo controlla. In un engine con una dozzina di struct del genere e due linguaggi host, sperare non basta.

L'engine dichiara ogni struct una volta sola, in un header C letto da tutti e tre i compilatori. Dentro uno shader i nomi di `simd` vengono fatti corrispondere ai tipi propri dello shader. Ridotto a una sola struct, l'header è così:

{{code}}

Gli shader lo includono con `#include`. Il codice host lo importa così:

{{code}}

Gli slot di binding stanno nello stesso header, quindi `[[buffer(LMBufferInstances)]]` in uno shader e l'indice passato all'encoder sono la stessa costante, non due numeri che per caso coincidono.

Due regole tengono al sicuro l'header. Niente `bool`, la cui dimensione cambia da un linguaggio all'altro. E ricorda che un `float3` occupa sedici byte in tutti e tre i linguaggi: i test unitari controllano la dimensione di ogni struct, quindi un errore fa fallire un test e non un frame.

## Dove è finito ogni capitolo

| Capitolo | Nell'engine |
| --- | --- |
| [Shader](../getting-started/shaders.html) | `Rendering/ShaderLibrary`, che compila i file `.metal` all'avvio e li ricarica quando cambiano |
| [Texture](../getting-started/textures.html) | `Rendering/Texture`, `Assets/Assets` |
| [Trasformazioni](../getting-started/transformations.html), [Camera](../getting-started/camera.html) | `Math/Math`, `Scene/Scene` |
| [Più luci](../lighting/multiple-lights.html) | `Shaders/Lighting.metal` |
| [Modello](../model-loading/model.html) | `Assets/MeshData`, con un suo lettore di file OBJ |
| [Blending](../advanced-metal/blending.html), [Face culling](../advanced-metal/face-culling.html) | materiali trasparenti e ritagliati in `Rendering/RenderPasses` |
| [Render target](../advanced-metal/render-targets.html), [Anti-aliasing](../advanced-metal/anti-aliasing.html) | il pass principale in HDR e multisample |
| [Cubemap](../advanced-metal/cubemaps.html) | `Rendering/Environment`, `Shaders/Sky.metal` |
| [Instancing](../advanced-metal/instancing.html) | automatico, in `Renderer.makeBatches` |
| [Shadow mapping](../advanced-lighting/shadow-mapping.html) | `Rendering/Cascades`: quattro shadow map invece di una |
| [Normal mapping](../advanced-lighting/normal-mapping.html) | tangenti in `Assets/MeshData`, `Shaders/Forward.metal` |
| [HDR](../advanced-lighting/hdr.html), [Bloom](../advanced-lighting/bloom.html), [SSAO](../advanced-lighting/ssao.html) | `Shaders/Post.metal` |
| [PBR](../pbr/lighting.html), [Irradianza diffusa](../pbr/diffuse-irradiance.html), [IBL speculare](../pbr/specular-ibl.html) | `Shaders/Lighting.metal`, `Shaders/IBL.metal` |
| [Debug](debugging.html) | etichette su ogni pass, `Rendering/DebugDraw` |
| [Rendering del testo](text-rendering.html), [Un gioco 2D](2d-game.html) | `Rendering/Canvas`, con font a distance field |
| [GPU tile-based](../apple-platforms/tile-based-gpus.html) | target memoryless, load e store action scelte pass per pass |

Non è entrato tutto. Non ci sono i [contorni con lo stencil](../advanced-metal/stencil-testing.html), né un [percorso deferred](../advanced-lighting/deferred-shading.html), né le [ombre delle luci puntiformi](../advanced-lighting/point-shadows.html), né il [parallax mapping](../advanced-lighting/parallax-mapping.html), né niente della sezione Oltre. Un engine piccolo che fa bene poche cose è un posto migliore per aggiungerle di uno grande che fa tutto a metà.

Il [prossimo capitolo](engine-renderer.html) apre il renderer.
