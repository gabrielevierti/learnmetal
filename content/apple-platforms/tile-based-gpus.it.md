# GPU tile-based

Ogni GPU Apple, dall'iPhone al Mac Studio, è un **tile-based deferred renderer** (TBDR). Disegna un frame in un ordine diverso da quello delle GPU desktop in immediate mode che la maggior parte dei tutorial dà per scontate, e diverse funzioni di Metal esistono solo per questo. Sapere come funziona trasforma un elenco di regole dall'aria strana in buon senso.

## Come una GPU tile-based disegna un pass

Una GPU in immediate mode prende ogni triangolo man mano che arriva e lo calcola direttamente nel framebuffer in memoria. Una GPU Apple lavora in due fasi per ogni render pass.

1. **Tiling.** Esegue le vertex function di ogni draw call del pass, divide lo schermo in piccoli tile (per esempio da 32 × 32 pixel) e annota quali triangoli toccano ciascun tile.
2. **Rendering.** Per ogni tile carica i pixel del tile in una memoria piccola e velocissima dentro la GPU, la **memoria dei tile**; trova quale triangolo è visibile in ogni pixel; calcola solo quelli; e riscrive nella texture il tile finito.

Ne seguono due conseguenze, che spiegano il resto di questo capitolo.

- **Hidden surface removal.** Per la geometria opaca la GPU conosce il triangolo visibile di ogni pixel prima di eseguire qualsiasi fragment function. I fragment nascosti non costano nulla, qualunque sia l'ordine di disegno.
- **Leggere e scrivere le texture è la parte costosa.** Il lavoro dentro la memoria dei tile costa poco. Spostare un tile tra la memoria dei tile e la memoria di sistema costa banda, energia e tempo.

!!! note "Se vieni da OpenGL"
    Su una GPU desktop ordini gli oggetti opachi da davanti a dietro per risparmiare lavoro sui fragment. Sulle GPU Apple lo fa per te la hidden surface removal, purché la pipeline sia opaca. Ciò che gestisci tu sono invece i pass: quanti sono, e che cosa ciascuno carica e salva.

## Load e store action

Ogni attachment di un pass ha una load action, applicata quando un tile comincia, e una store action, applicata quando finisce.

- `.load` copia in ogni tile il vecchio contenuto dalla memoria. Usala solo quando disegni sopra un risultato precedente.
- `.clear` riempie il tile con un valore, senza traffico di memoria. `.dontCare` non fa proprio niente.
- `.store` riscrive il tile. `.dontCare` lo scarta.

La regola: **carica solo ciò che devi conservare, salva solo ciò che leggerai dopo.** Una texture di profondità usata da un solo pass deve essere `.clear` e `.dontCare`. Una texture di colore multisample deve essere `.multisampleResolve`, senza salvare i campioni.

{{code}}

## Texture memoryless

Se un attachment non viene mai caricato e mai salvato, vive soltanto nella memoria dei tile, quindi non ha bisogno di memoria propria. Dagli lo storage mode **memoryless** e Metal non gli alloca niente. In 4K una texture di profondità e una texture di colore multisample 4× fanno insieme centinaia di megabyte risparmiati.

{{code}}

Con MetalKit, su Apple silicon `MTKView` lo fa già per le proprie texture di profondità e multisample.

## Fare di più in un solo pass

Cominciare un nuovo pass significa salvare i tile di quello vecchio e ricaricarli. Il renderer deferred del capitolo [Deferred shading](../advanced-lighting/deferred-shading.html) fa esattamente questo: un pass salva tre texture di G-buffer, un secondo pass le legge. Su una GPU tile-based entrambi i passi possono girare in **un solo** pass, con il G-buffer che non lascia mai la memoria dei tile.

Lo strumento è il **programmable blending**: una fragment function può leggere il valore attuale degli attachment di colore su cui sta disegnando, ricevendoli come parametri.

{{code}}

Gli attachment del G-buffer diventano memoryless, con `.clear` e `.dontCare`; viene salvato solo il colore illuminato. La profondità viene scritta in un attachment di colore `r32Float` in più, perché l'attachment di profondità vero e proprio non si può leggere in questo modo. Il costo del deferred shading scende a poco più di quello del forward rendering, ed è per questo che su iPhone questo schema è la norma.

Il programmable blending ti dà anche equazioni di blending personalizzate e la order-independent transparency. Per i dati per pixel che non entrano in un formato di pixel, gli **image block** e i **tile shader** ti permettono di definire un tuo layout della memoria dei tile e di eseguire su ogni tile, nel mezzo di un render pass, una funzione simile a quelle di compute.

## Mantenere attiva la hidden surface removal

La hidden surface removal può saltare solo i fragment che sa essere coperti da fragment opachi. Tre cose la mettono fuori gioco.

- **Il blending.** Un fragment con blending ha bisogno di ciò che gli sta dietro.
- **`discard_fragment`** e l'alpha test: la GPU non può sapere che il pixel è coperto finché la funzione non è stata eseguita.
- **Scrivere la profondità dalla fragment function**, o leggere l'attachment con il programmable blending.

Quindi disegna in quest'ordine: prima l'**opaco**, poi ciò che usa l'**alpha test**, poi il **traslucido**. Ordinare gli oggetti opachi non serve. Tieni `discard_fragment` fuori dagli shader che non ne hanno bisogno, perché la sua sola presenza, anche se non viene mai eseguito, toglie la draw call dal gruppo degli opachi.

## Altre abitudini che contano

- **Non spezzare un pass.** Chiudere un encoder e aprirne un altro con gli stessi attachment obbliga a un salvataggio e a un caricamento. Codifica in un solo encoder tutto ciò che disegna sulle stesse texture.
- **Evita di leggere il tuo stesso render target** con una lettura di texture nello stesso frame, quando basterebbe il programmable blending.
- **Comprimi le texture** con ASTC e genera le mipmap; sui dispositivi mobili il limite di solito è la banda, non l'aritmetica.
- **Usa formati più piccoli.** `rgba16Float` costa il doppio della banda di `rg11b10Float` e per il colore HDR serve di rado.
- **Usa la mezza precisione** (`half`, `half3`) nelle fragment function per colori e normali. Sulle GPU Apple è più veloce e usa meno registri.
- **Misura.** Il debugger di Metal in Xcode mostra le load e store action di ogni pass, e il report della memoria segnala le texture che potrebbero essere memoryless. Metal System Trace in Instruments mostra separatamente il tempo di tiling e quello di rendering di ogni pass.

## Esercizi

- Trova in uno dei tuoi renderer una texture di profondità che potrebbe essere memoryless, e cambiala.
- Imposta a `.dontCare` la store action dell'attachment di colore e spiega ciò che vedi.
- Aggiungi un `discard_fragment` inutilizzato dietro una condizione su un uniform sempre falsa, e confronta il tempo dei fragment in una scena con molto overdraw.
