# visionOS

Su Apple Vision Pro la maggior parte delle app disegna con RealityKit. Quando vuoi un renderer tuo, per un game engine o una visualizzazione, disegni contenuti **completamente immersivi** con Metal attraverso un framework chiamato **Compositor Services**. I tuoi shader e le tue pipeline sono quelli di questo libro. Di nuovo c'è tutto ciò che sta intorno al frame: gli occhi sono due, la camera è la testa di una persona e la scadenza è rigida.

## Che cosa cambia

- **Due viste.** Ogni frame viene disegnato una volta per occhio, con una matrice view e una di proiezione diverse per ciascuno.
- **La camera non è tua.** La matrice view arriva dalla posizione tracciata del visore, attraverso ARKit.
- **Il ciclo dei frame non è tuo.** Non ci sono né `MTKView` né display link. Compositor Services ti dà i frame e ti dice quando cominciare a lavorare su ciascuno.
- **Il sistema riproietta.** Appena prima della visualizzazione il sistema deforma la tua immagine per farla corrispondere all'ultima posizione della testa. Per farlo ha bisogno del tuo depth buffer, quindi la profondità deve essere corretta per ogni pixel che disegni.
- **Foveation.** Il visore disegna la periferia a una risoluzione più bassa. Lo ottieni quasi gratis, ma cambia il modo in cui funzionano i viewport e il post-processing.
- **La latenza è comfort.** Qui un frame in ritardo non è un piccolo scatto. Punta alla frequenza dello schermo, 90 frame al secondo o più, a ogni frame.

## L'app e il layer

Il punto d'ingresso è SwiftUI. Un `ImmersiveSpace` il cui contenuto è un `CompositorLayer` ti consegna un `LayerRenderer`, l'oggetto che sostituisce la vista. Da lì avvia un thread di rendering dedicato; non disegnare mai sul thread principale.

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
Il punto d'ingresso di un'app visionOS è sempre SwiftUI, quindi in un progetto C++ resta un piccolo file Swift come quello qui sotto. Tutto il resto può essere C++: Compositor Services ha un'API C (`cp_layer_renderer_t`, `cp_frame_t`, `cp_drawable_t`), che è quella usata dai motori. La closure Swift passa il layer renderer a una funzione C che avvia il tuo thread di rendering.

{{code}}

Su visionOS non c'è GLFW, e a metal-cpp serve un ponte: l'API C restituisce oggetti texture di Objective-C, che converti in `MTL::Texture*` in un file Objective-C++, come nel `glfw_bridge.mm` del progetto di partenza per macOS.
<!-- /cpp -->

Il **layout** decide come vengono salvate le immagini dei due occhi. `.dedicated` dà una texture per occhio e richiede due render pass. `.layered` dà una sola texture array con uno slice per occhio, e ti permette di disegnare entrambi gli occhi in un pass. Preferisci layered.

## Il ciclo dei frame

Il ciclo segue lo stato del layer: aspetta finché è in pausa, disegna finché è in esecuzione, ed esci quando viene invalidato.

<!-- swift -->
{{code}}
<!-- /swift -->

Un frame ha due fasi che annunci al sistema. Nella fase di **update** esegui tutto ciò che non dipende da dove si trova la testa: animazione, fisica, input. Poi dormi fino all'ultimo momento ragionevole, chiedi la posa della testa ed entri nella fase di **submission**, in cui codifichi e fai il commit. Aspettare conta: più tardi leggi la posa, meno il sistema deve correggere.

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
Con l'API C lo stesso frame si legge così. Ogni chiamata corrisponde uno a uno a un metodo Swift.

{{code}}
<!-- /cpp -->

`worldTracking` è un `WorldTrackingProvider` di ARKit che avvii una volta con `ARKitSession().run([worldTracking])`. Impostare `deviceAnchor` sul drawable dice al sistema per quale posa hai disegnato, così può correggere la differenza.

## Due occhi, due matrici

Ogni drawable ha un elenco di viste, di norma due. Una vista dà la trasformazione dell'occhio rispetto al dispositivo, e il drawable calcola la proiezione dell'occhio. Entrambe sono diverse per ciascun occhio, e la proiezione non è simmetrica, quindi non costruirla da un campo visivo.

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
In C++ leggi gli stessi valori con `cp_drawable_get_view`, `cp_view_get_transform` e `cp_drawable_compute_projection`, e la trasformazione del dispositivo con `ar_anchor_get_origin_from_anchor_transform`. La matrice view è `simd_inverse(simd_mul(deviceTransform, eyeTransform))`.
<!-- /cpp -->

visionOS usa il **reverse-Z**: la proiezione manda il near plane alla profondità 1 e il far plane a 0. Pulisci la profondità a 0 e confronta con `.greater`. Le unità sono metri, e l'origine sta sul pavimento nel punto in cui lo spazio è stato aperto.

## Entrambi gli occhi in un pass

Con il layout layered il render pass disegna su una texture array. La **vertex amplification** esegue la vertex function una volta per occhio per ogni draw call e instrada ogni risultato verso il suo slice, così la scena viene codificata una volta sola.

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
Con metal-cpp il render pass si costruisce allo stesso modo, a partire da `cp_drawable_get_color_texture(drawable, 0)`, `cp_drawable_get_depth_texture(drawable, 0)`, `cp_drawable_get_view_count(drawable)` e `cp_drawable_get_rasterization_rate_map(drawable, 0)`. Poi chiama `encoder->setViewports`, `encoder->setVertexAmplificationCount(count, mappings)` e collega l'array di uniform per occhio.
<!-- /cpp -->

Al pipeline descriptor serve `maxVertexAmplificationCount = 2`, e la vertex function sceglie le sue matrici con l'indice di amplificazione.

{{code}}

Nota che cosa viene salvato: a differenza del Mac, l'attachment di profondità usa `.store`, perché il compositor lo legge. È l'unico punto in cui il consiglio del capitolo sulle [GPU tile-based](tile-based-gpus.html) non vale.

## Note pratiche

- **Foveation e post-processing.** Con una rasterization rate map la texture non è uniforme, quindi un pass a tutto schermo che la legge deve convertire le coordinate attraverso la mappa. Comincia senza post-processing.
- **Passthrough.** Per l'immersione mista, in cui i tuoi contenuti compaiono nella stanza della persona, pulisci a nero trasparente e scrivi alpha premoltiplicato; il sistema compone dietro di te l'immagine delle videocamere.
- **Input.** Non ci sono né tasti né mouse. Pizzichi e sguardi arrivano come eventi spaziali sul layer renderer, e le mani attraverso l'hand tracking di ARKit.
- **Il Simulatore** non supporta tutti i layout né la foveation. Controlla le capacità invece di darle per scontate, come fa la configurazione qui sopra.
- **Budget.** Due viste ad alta risoluzione e a 90 Hz lasciano pochi millisecondi di tempo di GPU. La scelta consueta è il forward rendering con MSAA, pochi pass e shader a mezza precisione.

## Esercizi

- Disegna la scena dei dieci cubi di Per iniziare due metri davanti alla posizione di partenza.
- Dai a ogni occhio un colore di sfondo diverso e verifica che gli strati siano instradati correttamente.
- Passa al layout dedicated e disegna con due pass. Confronta il tempo di CPU della codifica.
