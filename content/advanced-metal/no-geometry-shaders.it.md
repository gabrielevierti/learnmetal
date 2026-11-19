# Vivere senza geometry shader

Altre API hanno uno stadio di **geometry shader** tra lo stadio di vertice e quello di fragment. Riceve una primitiva intera e ne può emettere di nuove: trasformare un punto in un rettangolo, un triangolo in tre linee, un triangolo in sei per le facce di una cubemap.

Metal non ha geometry shader, per scelta. Si adattano male all'hardware delle GPU, soprattutto alle architetture tile-based, e sono lenti quasi ovunque. Ognuno dei loro usi classici ha in Metal un sostituto migliore. Questo capitolo li passa in rassegna.

## Da punti a rettangoli: l'instancing

La demo tipica dei geometry shader espande dei punti in rettangoli rivolti verso la camera, i billboard, per le particelle. In Metal disegna un rettangolo di quattro vertici con un'**istanza** per particella, e costruisci gli angoli nella vertex function:

{{code}}

{{code}}

Nessun vertex buffer per il rettangolo, nessun vertex descriptor, e una sola draw call per qualsiasi numero di particelle.

Per le particelle che restano sempre piccole Metal può anche disegnare direttamente primitive `.point`. Scrivi la dimensione in un output `[[point_size]]` e usa `[[point_coord]]` nella fragment function come coordinata di texture.

## Visualizzare le normali: linee dagli ID dei vertici

Un altro classico: disegnare una breve linea lungo la normale di ogni vertice per fare il debug di una mesh. Disegna primitive `.line` con il doppio dei vertici della mesh, e ricava dall'ID del vertice sia il vertice di partenza sia a quale estremo della linea ti trovi:

{{code}}

{{code}}

Questo schema, cioè leggere da un buffer con un indice calcolato, sostituisce la maggior parte dei geometry shader che emettono una quantità fissa di geometria per ogni input. La stessa idea dà le mesh che esplodono: usa `vertexID / 3` per trovare il triangolo, calcola la normale della faccia dai tre vertici e spingi il vertice verso l'esterno.

## Disegnare su più destinazioni insieme: il layered rendering

I geometry shader si usano anche per mandare una sola draw call su tutte e sei le facce di una cubemap o su più strati di una texture array. Metal copre questo caso con due funzioni.

**Layered rendering**: la vertex function sceglie lo strato di destinazione scrivendo `[[render_target_array_index]]`. Insieme all'instancing, una sola draw call disegna la scena in ogni faccia:

{{code}}

Il render pass descriptor deve impostare `renderTargetArrayLength = 6`, e al pipeline descriptor serve `inputPrimitiveTopology = .triangle`.

**Vertex amplification**: la GPU esegue la vertex function una volta per vertice e replica il risultato su più strati o viewport, con un indice per vista disponibile come `[[amplification_id]]`. È stata introdotta per il rendering stereo, in cui ogni occhio ha bisogno della propria matrice view, e costa meno dell'instancing perché il lavoro in comune viene fatto una volta sola. Imposta `maxVertexAmplificationCount` nel pipeline descriptor e chiama `setVertexAmplificationCount` sull'encoder.

## Generare geometria: compute e mesh shader

Quando la quantità di geometria in uscita è davvero dinamica, gli strumenti sono due.

Una **compute function** può scrivere dei vertici in un buffer che un render pass successivo disegna. È la risposta generale per le mesh procedurali, per il marching cubes e per la simulazione di particelle. Vedi [Compute shader](../beyond/compute-shaders.html).

I **mesh shader**, disponibili sulle GPU Apple e sulle versioni del sistema recenti, sostituiscono lo stadio di vertice con due stadi programmabili. Una **object function** decide quanti gruppi di geometria emettere, per esempio scartando i cluster invisibili, e una **mesh function** manda piccoli lotti di vertici e primitive direttamente al rasterizer. Fanno tutto ciò che facevano i geometry shader, in modo efficiente, e sono il fondamento del moderno rendering guidato dalla GPU. Verifica il supporto con `device.supportsFamily(.metal3)`.

## Suddividere: la tassellazione

Se lo scopo è aggiungere dettaglio a una superficie, suddividendo triangoli o deformando un terreno, lo strumento giusto è il tessellator, trattato in [Tassellazione](../beyond/tessellation.html).

## In sintesi

| Uso dei geometry shader | Sostituto in Metal |
| --- | --- |
| Da punti a rettangoli | Rettangolo con instancing, o primitive punto |
| Normali, wireframe, esplosioni | Vertex pulling con indici calcolati |
| Cubemap o array in un solo pass | `render_target_array_index` con instancing o vertex amplification |
| Geometria procedurale | Compute function, mesh shader |
| Suddivisione | Tassellazione |
