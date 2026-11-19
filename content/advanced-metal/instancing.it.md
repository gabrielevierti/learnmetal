# Instancing

Un prato, una foresta, una fascia di asteroidi: migliaia di copie della stessa mesh, ognuna con una trasformazione diversa. Fare una draw call per copia spreca tempo di CPU, perché ogni chiamata ha un costo fisso per quanto piccola sia la mesh. L'**instancing** disegna tutte le copie con una sola chiamata.

## Draw call con istanze

Ogni metodo di disegno ha una variante con un `instanceCount`:

{{code}}

La GPU esegue la vertex function per ogni vertice di ogni istanza. L'unica differenza tra le istanze è l'input predefinito `[[instance_id]]`, che conta da 0. Tutto ciò che fa apparire diverse le istanze si ricava da quel numero.

## I dati delle istanze in un buffer

Metti in un buffer una struct per istanza e indicizzala con l'ID dell'istanza:

{{code}}

Usare la matrice model per la normale è corretto solo con rotazioni e scale uniformi. Se ti serve una scala non uniforme, salva una matrice delle normali per ogni istanza.

{{code}}

{{code}}

!!! note "Se vieni da OpenGL"
    Non servono attributi di vertice per istanza con i divisor, e non c'è limite alla dimensione dei dati per istanza. Bastano un buffer e un indice. Se preferisci comunque gli attributi, un layout del vertex descriptor può avanzare una volta per istanza: `layouts[1].stepFunction = .perInstance`.

## Un campo di asteroidi

Genera intorno a un pianeta un anello di rocce disposte, ruotate e scalate a caso:

{{code}}

Disegnati con una chiamata per roccia, già poche migliaia di asteroidi costano a ogni frame un tempo di CPU apprezzabile. Disegnati con l'instancing ne girano fluidi centomila, e il limite diventa quanti triangoli la GPU riesce a riempire.

## Animare le istanze

Dato che il buffer delle istanze è memoria condivisa, aggiornarlo è una semplice scrittura a ogni frame. Usa lo schema con l'anello di buffer di [Dati avanzati](advanced-data.html), così non sovrascrivi dati che la GPU sta ancora leggendo. Per numeri molto grandi, spostare sulla GPU l'aggiornamento stesso con una [compute function](../beyond/compute-shaders.html) toglie del tutto la CPU dal ciclo.

## Il culling e il passo successivo

L'instancing disegna ogni istanza, visibile o no. I mondi grandi fanno il culling sulla CPU e scrivono nel buffer solo le istanze visibili, oppure lo lasciano fare alla GPU: un compute pass confronta ogni istanza con il frustum della vista e scrive le sopravvissute in un **indirect command buffer**, un elenco di draw call codificato dalla GPU stessa (`MTLIndirectCommandBuffer`). Quella tecnica, il rendering guidato dalla GPU, va oltre questa serie, ma l'instancing ne è il primo passo.

## Esercizi

- Disegna una griglia di 100 × 100 cubi con una sola chiamata, colorando ciascuno in base al suo ID di istanza.
- Fai ruotare l'anello di asteroidi passando un uniform con il tempo e ruotando nella vertex function, senza aggiornare alcun buffer dalla CPU.
