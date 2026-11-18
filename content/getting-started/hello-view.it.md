# La prima vista

È il momento del primo codice Metal: un renderer che a ogni frame riempie la finestra con un colore. Non disegna geometria, ma contiene lo scheletro completo di un frame, e ogni capitolo successivo non fa che aggiungervi qualcosa.

<!-- cpp -->

!!! note "Leggere questo capitolo in C++"
    In metal-cpp non ci sono né `MTKView` né delegate. Il tuo renderer tiene il `CAMetalLayer` di [Preparare il progetto](project-setup.html), e `main.cpp` chiama `renderer.draw()` una volta per ciclo. Dove il testo dice `view.currentDrawable`, tu chiami `layer->nextDrawable()`. Dove dice `view.currentRenderPassDescriptor`, compili tu un `MTL::RenderPassDescriptor`, e così le load e store action spiegate più sotto diventano visibili nel tuo codice.

<!-- /cpp -->

## Il renderer

Crea `Renderer.swift`:

{{code}}

Eseguilo. Dovresti vedere una finestra riempita di verde petrolio scuro.

## Il device e la coda

`MTLCreateSystemDefaultDevice()` restituisce la GPU consigliata dal sistema. Su Apple silicon ce n'è una sola. Tutto il resto viene creato a partire da questo device.

La **command queue** si crea una volta e si tiene per tutta la vita dell'app. Garantisce che i command buffer di cui fai il commit vengano eseguiti in ordine.

## Configurare la vista

- `view.device` dice alla vista su quale GPU vivono le sue texture. Senza, non viene disegnato nulla.
- `colorPixelFormat` è il formato della texture mostrata a schermo. `.bgra8Unorm` significa quattro canali a 8 bit memorizzati come blu, verde, rosso, alfa, che gli shader leggono come float da 0 a 1. È il valore predefinito della vista; lo impostiamo in modo esplicito perché lo cambieremo nel capitolo [Correzione gamma](../advanced-lighting/gamma-correction.html).
- `clearColor` è il colore con cui il drawable viene riempito all'inizio di ogni frame.

## Anatomia di un frame

`draw(in:)` viene chiamato una volta per ogni aggiornamento dello schermo, di solito 60 o 120 volte al secondo. Dentro succedono quattro cose.

**1. Ottenere un render pass descriptor.** Un render pass è un blocco di disegno diretto a un insieme di texture, i suoi **attachment**. `currentRenderPassDescriptor` è un descriptor già pronto il cui attachment di colore è la texture del drawable di questo frame. Per ogni attachment un descriptor contiene anche:

- una **load action**: che cosa fare del contenuto esistente quando il pass inizia (`.clear`, `.load` o `.dontCare`),
- una **store action**: che cosa fare del risultato quando finisce (`.store`, `.dontCare` o un multisample resolve).

Il descriptor della vista usa `.clear` con il tuo `clearColor`, e `.store`. Ecco perché otteniamo una finestra colorata senza disegnare niente: la pulizia fa parte dell'inizio del pass.

!!! note "Coming from OpenGL"
    Non esiste una chiamata `glClear`. La pulizia è una proprietà del render pass, e scegliere bene le load e store action conta per le prestazioni sulle GPU tile-based, perché ognuna può far risparmiare o costare una copia intera della texture.

**2. Creare un command buffer e un encoder.** Il command buffer conserva i comandi codificati per questo frame. Il render command encoder traduce le tue chiamate (imposta la pipeline, imposta il buffer, disegna) in comandi GPU per questo singolo pass.

**3. Chiudere l'encoding.** Devi chiamare `endEncoding()` prima di creare un altro encoder o di fare il commit. Dimenticarlo è un errore di validazione.

**4. Presentare e fare il commit.** `present(drawable)` programma la visualizzazione del drawable non appena la GPU finisce questo command buffer. `commit()` consegna il buffer alla coda. La chiamata ritorna subito; la GPU lavora in modo asincrono.

## I drawable sono pochi

`currentDrawable` arriva da un piccolo gruppo, di solito tre texture. Se sono tutte in uso, la chiamata resta in attesa finché una non si libera, e può restituire `nil`. Per questo il metodo inizia con un `guard` e salta semplicemente il frame quando manca qualcosa. Tieni un drawable per il minor tempo possibile e non conservarlo mai.

## Continuo o su richiesta

In modo predefinito `MTKView` ridisegna di continuo a `preferredFramesPerSecond`. Per un'app in stile editor, che cambia solo quando arriva un input, puoi impostare `view.isPaused = true` e `view.enableSetNeedsDisplay = true`, e poi chiedere i frame con `setNeedsDisplay`. Un gioco o un'animazione tengono il comportamento predefinito.

## Esercizi

- Cambia il colore di sfondo a ogni frame usando `CACurrentMediaTime()` e `sin`, in modo che la finestra pulsi.
- Stampa `view.drawableSize` in `mtkView(_:drawableSizeWillChange:)` e ridimensiona la finestra. Nota che la dimensione è in pixel, non in punti: su uno schermo Retina è il doppio di quella della finestra.
