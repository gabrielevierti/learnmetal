# Anti-aliasing

Guarda da vicino il bordo di uno qualsiasi dei cubi che abbiamo disegnato e vedrai una scaletta. Un pixel è o dentro un triangolo o fuori, senza vie di mezzo. Quel motivo a gradini è l'**aliasing**, e le tecniche che lo nascondono si chiamano **anti-aliasing**.

## Perché i bordi fanno aliasing

Il rasterizer controlla per ogni triangolo un solo punto per pixel, il suo centro. Se il centro è coperto, la fragment function viene eseguita e l'intero pixel prende quel colore. Un bordo inclinato avanza quindi a passi di un pixel intero.

Disegnare a una risoluzione più alta e poi ridurre (**supersampling**) risolve il problema, ma calcolare quattro volte tanti pixel costa caro.

## Multisampling

Il **multisample anti-aliasing** (MSAA) dà la maggior parte del beneficio a una frazione del costo. Ogni pixel ha più **punti di campionamento**, di solito quattro, in posizioni diverse al suo interno. Per ogni triangolo:

- copertura e profondità vengono controllate in **ogni campione**,
- la fragment function viene comunque eseguita **una volta sola per pixel**,
- il suo risultato viene salvato in ogni campione che il triangolo copre.

Alla fine i campioni di ogni pixel vengono mediati in un passo chiamato **resolve**. Un pixel coperto per metà da un triangolo finisce come una miscela in parti uguali del colore del triangolo e dello sfondo.

## MSAA con MTKView

`MTKView` gestisce al posto tuo la texture multisample e il resolve. Servono due righe:

{{code}}

{{code}}

Ogni pipeline state usato nel pass deve avere lo stesso numero di campioni degli attachment. Eseguilo e i bordi sono lisci.

Un numero di campioni pari a 4 è supportato da tutti i dispositivi Metal. Gli altri controllali con `device.supportsTextureSampleCount(8)`.

## MSAA nei tuoi render pass

Per i pass offscreen le texture le crei tu. Ti servono due texture di colore: una multisample in cui disegnare e una normale che riceve l'immagine risolta.

{{code}}

La texture di profondità deve essere multisample allo stesso modo. Poi collegale nel render pass descriptor:

{{code}}

La store action `.multisampleResolve` media i campioni in `resolveTexture` alla fine del pass e scarta i dati multisample. Poiché dopo i campioni non servono più, sulle GPU Apple le texture multisample possono essere **memoryless**: l'MSAA 4× allora non costa alcuna memoria in più, solo un po' di lavoro extra dentro ogni tile. È un vero vantaggio delle GPU tile-based, e rende l'MSAA insolitamente economico sui dispositivi Apple.

## I limiti dell'MSAA

L'MSAA liscia solo i **bordi della geometria**. La fragment function gira una volta per pixel, quindi non fa niente per:

- lo sfarfallio all'interno di una superficie dovuto a texture ad alta frequenza o a riflessi speculari netti,
- i bordi creati da `discard_fragment` nelle texture con alpha test. Per quelli attiva `isAlphaToCoverageEnabled` nel pipeline descriptor, che converte l'alpha del fragment in una maschera di copertura dei campioni.

L'MSAA inoltre va poco d'accordo con il [deferred shading](../advanced-lighting/deferred-shading.html), dove l'illuminazione avviene dopo che la geometria è stata appiattita in texture.

## Leggere i singoli campioni

Uno shader può leggere direttamente una texture multisample attraverso il tipo `texture2d_ms<float>`, un campione alla volta:

{{code}}

Un resolve personalizzato conta nel rendering HDR, dove fare il tone mapping di ogni campione prima della media dà bordi luminosi molto più puliti. In quel caso la texture multisample ha bisogno dell'uso `.shaderRead` e non può essere memoryless.

## Altri approcci

- **FXAA e SMAA** sono filtri di post-processing che trovano i bordi nell'immagine finita e sfocano lungo di essi. Costano poco e funzionano con qualsiasi renderer, a prezzo di un po' di nitidezza.
- Il **temporal anti-aliasing** (TAA) sposta la camera di una frazione di pixel a ogni frame e mescola con i frame precedenti. Gestisce anche l'aliasing dello shading, ma ha bisogno dei motion vector e di attenzione per evitare il ghosting.
- **MetalFX** è il framework di upscaling di Apple. Disegni a una risoluzione più bassa e lui ricostruisce un'immagine nitida e senza aliasing a piena risoluzione, con un metodo spaziale o temporale. L'upscaler temporale fa anche da anti-aliasing di alta qualità.

## Esercizi

- Confronta i numeri di campioni 1, 2 e 4 su un triangolo sottile e quasi orizzontale.
- Disegna dell'erba con alpha test con e senza alpha-to-coverage, con MSAA 4×.
