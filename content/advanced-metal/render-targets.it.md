# Render target

Finora ogni frame è stato disegnato direttamente nel drawable della vista. Un render pass può invece disegnare in una texture qualsiasi, e quella texture può poi essere letta da un pass successivo. Il rendering su texture è la base del post-processing, delle ombre, dei riflessi, del bloom e del deferred shading. Quasi tutti i capitoli dopo questo lo usano.

!!! note "Se vieni da OpenGL"
    Metal non ha framebuffer object. Il loro ruolo lo svolge l'`MTLRenderPassDescriptor`: una descrizione leggera di quali texture sono gli attachment di colore, profondità e stencil di un pass. Non c'è niente da collegare o scollegare, e non c'è alcun controllo di "completezza".

## Creare le texture

Una texture in cui disegni ha bisogno dell'uso `.renderTarget`. Per leggerla in seguito le serve anche `.shaderRead`:

{{code}}

Lo storage `.private` significa che solo la GPU tocca la texture. Chiama questa funzione da `mtkView(_:drawableSizeWillChange:)`, così le texture seguono la dimensione della finestra.

## Descrivere il pass

{{code}}

Le load e store action meritano un momento di riflessione:

- Il risultato di colore serve dopo, quindi viene **salvato**.
- Il depth buffer serve solo *durante* il pass, quindi `.dontCare` permette alla GPU di buttarlo via.

Sulle GPU Apple una texture di profondità che non viene mai salvata si può perfino creare con `storageMode = .memoryless`. Allora non occupa alcuna memoria, e vive soltanto nella memoria dei tile della GPU mentre il pass è in esecuzione.

## Due pass in un frame

{{code}}

I pipeline state usati nel pass 1 devono dichiarare i formati degli attachment di *quel* pass. Il pass di post-processing non ha bisogno di un attachment di profondità, quindi la sua pipeline lascia `depthAttachmentPixelFormat` non impostato; se la vista ha ancora un formato di profondità, impostalo perché coincida oppure metti `view.depthStencilPixelFormat = .invalid`.

## Il triangolo a tutto schermo

Per eseguire una fragment function su ogni pixel serve una geometria che copra lo schermo. Basta un solo triangolo sovradimensionato, senza alcun vertex buffer. La vertex function costruisce le posizioni dall'indice del vertice, che è un input predefinito:

{{code}}

Il triangolo sporge oltre lo schermo e viene ritagliato su di esso. Il ribaltamento di y fa cadere la uv (0, 0) sull'angolo in alto a sinistra, come l'origine delle texture di Metal, così una texture disegnata da un pass viene mostrata dritta dal successivo senza altre complicazioni. La pipeline di post-processing non ha un vertex descriptor.

Eseguilo e la scena appare esattamente come prima. Il punto è proprio questo: adesso passa attraverso una texture che possiamo manipolare.

## Post-processing

**Inversione e scala di grigi** cambiano un pixel alla volta:

{{code}}

I pesi rispecchiano la sensibilità dell'occhio a ciascun canale.

Gli **effetti a kernel** combinano ogni pixel con i suoi vicini usando una piccola griglia di pesi, un **kernel di convoluzione**:

{{code}}

{{code}}

Usa un sampler con `.clampToEdge`, così ai bordi il kernel non rientra dal lato opposto.

## Esercizi

- Disegna la scena a metà risoluzione e stirala sullo schermo. Confronta i filtri `.nearest` e `.linear`.
- Costruisci uno specchietto retrovisore: disegna la scena una seconda volta in una piccola texture, con la camera girata di 180 gradi, e mostrala su un rettangolo in alto sullo schermo.
