# Mesh shader

Una vertex function riceve un vertice e restituisce un vertice. Non può creare geometria, e non può buttare via un oggetto intero. Una pipeline con **mesh shader** sostituisce lo stadio di vertice con due stadi programmabili che sanno fare entrambe le cose, interamente sulla GPU. È la risposta di Metal ai geometry shader di altre API, e da Metal 4 è anche il sostituto consigliato della tassellazione.

## Due nuovi stadi

- L'**object stage** gira una volta per oggetto, o per cluster di triangoli. Decide se quell'oggetto è visibile, quanto dettaglio merita e quante mesh lanciare per lui. Può passare allo stadio successivo un piccolo blocco di dati, il **payload**. Questo stadio è facoltativo.
- Il **mesh stage** gira una volta per mesh e scrive i vertici, gli indici e il numero di primitive di una piccola mesh. Poi il rasterizer prosegue come al solito, e la fragment function non cambia.

Entrambi gli stadi girano come i compute kernel: lanci una griglia di threadgroup, e ogni thread conosce il proprio indice.

Una piccola mesh di qualche centinaio di triangoli al massimo si chiama **meshlet**. Dividere in anticipo un modello grande in meshlet, e farne il culling nell'object stage, è l'uso principale di questa pipeline: i triangoli che non si possono vedere non arrivano mai al rasterizer.

## La mesh function

Il tipo di uscita è un template `mesh`: il tipo dei vertici, il tipo dei dati per primitiva, il numero massimo di vertici e di primitive, e la topologia.

{{code}}

`set_primitive_count` è ciò che rende flessibile lo stadio: scrivi 0 e la mesh non produce niente. La fragment function riceve i dati dei vertici interpolati e, se li chiede, i dati per primitiva.

{{code}}

## La pipeline e la draw call

La pipeline usa un suo tipo di descriptor. Non c'è vertex descriptor, perché non ci sono vertex buffer: la mesh function legge i buffer che vuole.

{{code}}

I buffer si collegano stadio per stadio con `setMeshBuffer` e `setObjectBuffer`, e la draw call lancia dei threadgroup invece di contare vertici.

{{code}}

Senza una object function, la griglia che passi è la griglia dei threadgroup di mesh.

## Aggiungere l'object stage

Con una object function la griglia nella draw call è la griglia dei threadgroup di *object*, e ognuno di essi decide quanti threadgroup di mesh lanciare.

{{code}}

La mesh function riceve il payload con `const object_data Payload &payload [[payload]]`. Nel pipeline descriptor imposta `objectFunction`, `payloadMemoryLength` (la dimensione della struct del payload) e `maxTotalThreadgroupsPerMeshGrid` (qui 64).

## Quando usarli

- **Culling dei meshlet.** Culling per cluster contro il frustum, delle facce posteriori e per occlusione, nei modelli densi.
- **Geometria procedurale.** Erba, capelli, particelle come rettangoli, patch di terreno: geometria che altrimenti richiederebbe un compute pass e un buffer intermedio.
- **Livello di dettaglio sulla GPU**, scelto per cluster e per frame.
- **Sostituire i geometry shader** nei porting da altre API, e la tassellazione in Metal 4.

I mesh shader richiedono Metal 3: i Mac con Apple silicon, e gli iPhone e iPad con chip A14 o successivo. Controlla `device.supportsFamily(.metal3)`. Per un normale modello disegnato una volta la pipeline con i vertici è più semplice e altrettanto veloce.

## Esercizi

- Cambia il numero di rettangoli modificando solo la dimensione della griglia nella draw call.
- Fai restituire alla mesh function zero primitive per un rettangolo sì e uno no, come una scacchiera.
- Aggiungi l'object stage e colora ogni cluster in base al suo livello di dettaglio.
