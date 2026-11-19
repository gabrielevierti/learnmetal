# Mappe di illuminazione

Un materiale con un solo colore per oggetto è ancora troppo grossolano. Una cassa di legno con un telaio d'acciaio è fatta di due materiali su una stessa superficie: il legno è opaco, l'acciaio è lucido. La risposta è salvare le proprietà del materiale in texture, così possono variare da pixel a pixel. Queste texture si chiamano **lighting map**.

## Diffuse map

Una **diffuse map** è ciò che i capitoli precedenti chiamavano semplicemente texture: un'immagine che contiene il colore della superficie in ogni punto. Sostituisci il colore diffuse del materiale con una lettura dalla texture, e usa lo stesso valore per l'ambient:

{{code}}

Ricorda di accorciare la struct `Material` di Swift perché corrisponda.

## Specular map

La **specular map** è una seconda immagine, di solito in scala di grigi, che dice quanto intensamente ogni punto riflette. Per la cassa è nera sul legno e chiara sul telaio d'acciaio, con graffi e usura dipinti sopra. Nero significa nessun riflesso; bianco significa riflesso pieno.

Carica entrambe le immagini e collegale ai due slot delle texture:

{{code}}

{{code}}

Adesso luccica solo il bordo metallico della cassa, e il riflesso si spezza sui suoi graffi.

## Un sampler, molte texture

Entrambe le mappe vengono lette attraverso lo stesso sampler. Un sampler descrive *come* leggere, e questo è quasi sempre uguale per tutte le mappe di un materiale: un solo sampler state è la norma.

## Texture a un solo canale

Una specular map in scala di grigi, caricata come RGBA, spreca tre canali. Metal ha formati a un canale come `.r8Unorm`, e `MTKTextureLoader` carica così un PNG salvato in scala di grigi. Nello shader leggi allora solo `.r`:

{{code}}

Le pipeline di asset reali vanno oltre e impacchettano più mappe in scala di grigi nei canali di una sola texture, per esempio la roughness nel verde e la metalness nel blu. Lo vedrai nella sezione PBR.

## Esercizi

- Inverti la specular map nello shader, così luccica il legno e non l'acciaio.
- Usa una specular map colorata e guarda come tinge i riflessi.
- Aggiungi una **emission map**: una terza texture il cui colore viene sommato al risultato senza tener conto dell'illuminazione, in modo che alcune parti dell'oggetto sembrino brillare.
