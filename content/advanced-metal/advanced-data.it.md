# Dati avanzati

Buffer e texture sono stati finora scatole nere create con una chiamata. Questo capitolo le apre: dove vive la loro memoria, come aggiornarla in modo efficiente a ogni frame e come copiare dati sulla GPU.

## I buffer sono soltanto memoria

Un `MTLBuffer` è un blocco di byte senza tipo. Metal non gli attribuisce alcun significato. Lo stesso buffer può contenere vertici nella prima metà e uniform nella seconda, e quale parte usare lo dici con il parametro `offset` quando lo colleghi.

Crea un buffer vuoto e riempilo dopo:

{{code}}

`buffer.contents()` restituisce un puntatore grezzo alla memoria. Scrivere attraverso di esso è il modo più veloce di aggiornare i dati:

{{code}}

oppure, per un array:

{{code}}

## Storage mode

Lo **storage mode** di una risorsa dice chi può accedere alla sua memoria.

| Modo | Accesso CPU | Accesso GPU | Note |
| --- | --- | --- | --- |
| `.shared` | sì | sì | Una sola copia in memoria, visibile a entrambe. È il valore predefinito per i buffer su Apple silicon. |
| `.private` | no | sì | Solo GPU. Il migliore per i render target e per i dati statici. |
| `.managed` | sì | sì | Due copie sincronizzate. Ha senso solo sui Mac con GPU discreta. |
| `.memoryless` | no | durante un pass | Solo texture, GPU Apple. Esiste soltanto mentre un render pass è in esecuzione. |

Apple silicon ha una **memoria unificata**: CPU e GPU condividono la stessa RAM fisica. Un buffer shared non viene copiato quando la GPU lo usa, quindi "caricare" dei dati non è altro che scrivere in memoria. Regole pratiche:

- Dati che riscrivi a ogni frame: `.shared`.
- Texture in cui disegni e mesh statiche che non tocchi più: `.private`.
- Attachment di profondità o multisample che non conservi: `.memoryless`.

## Aggiornare gli uniform senza rischi

`setVertexBytes` è comodo, ma è limitato a 4 KB per chiamata e copia i dati ogni volta. Un renderer vero tiene gli uniform in buffer. C'è un pericolo: la GPU lavora in ritardo rispetto alla CPU. Se sovrascrivi un buffer per il frame N+1 mentre la GPU sta ancora disegnando il frame N, il frame N legge i dati sbagliati.

La cura consueta è un piccolo **anello di buffer**, uno per ogni frame in lavorazione, con un semaforo che impedisce alla CPU di andare troppo avanti:

{{code}}

{{code}}

`setVertexBufferOffset` costa molto meno che ricollegare un buffer. Un solo grande buffer con un offset per oggetto è il modo in cui migliaia di draw call restano veloci. Assicurati che ogni uscita anticipata dopo `wait()` segnali il semaforo, altrimenti l'app si blocca dopo tre frame.

## Copiare sulla GPU: il blit encoder

Un terzo tipo di encoder, accanto a quello di render e a quello di compute, sposta dati tra le risorse:

{{code}}

Il blit encoder è anche il modo di riempire una risorsa `.private`: scrivi i dati in un buffer shared di appoggio e copiali dall'altra parte con un blit.

## Rileggere i dati

Per rileggere dei pixel, il risultato deve trovarsi in memoria visibile alla CPU dopo che la GPU ha finito:

{{code}}

Non bloccare mai il ciclo di rendering con `waitUntilCompleted()` per avere i risultati. Usa il completion handler.

## I texture descriptor per intero

`MTLTextureDescriptor` offre più di larghezza e altezza:

| Proprietà | Uso |
| --- | --- |
| `textureType` | `.type2D`, `.type2DArray`, `.typeCube`, `.type3D`, `.type2DMultisample` e altri. |
| `pixelFormat` | Disposizione e precisione dei canali. |
| `mipmapLevelCount` | Numero di livelli di mip. |
| `arrayLength` | Strati di una texture array. |
| `sampleCount` | Campioni per pixel nel multisampling. |
| `usage` | `.shaderRead`, `.shaderWrite`, `.renderTarget`, `.pixelFormatView`. Dichiara solo ciò che ti serve; permette a Metal di ottimizzare. |
| `storageMode` | Come sopra. |

Le **texture array** impilano in una sola texture molte immagini della stessa dimensione, che nello shader si indicizzano per strato con `texture2d_array<float>`. Sostituiscono gli atlas di texture senza i problemi di sbavatura.

## Esercizi

- Converti la scena dei dieci cubi da `setVertexBytes` allo schema con l'anello di buffer.
- Disegna la scena in una texture, rileggila e salvala come PNG con Core Graphics.
