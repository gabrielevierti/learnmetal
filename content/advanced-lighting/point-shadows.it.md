# Ombre da luci puntiformi

Una shadow map direzionale copre una sola direzione. Una luce puntiforme illumina in tutte le direzioni, quindi una mappa piatta non può contenere le sue ombre. La risposta è una shadow map a **cubo**: sei mappe di profondità disposte intorno alla luce, lette con la direzione che va dalla luce al fragment.

## Il piano

1. Disegna la scena sei volte dalla posizione della luce, una per ogni faccia del cubo, salvando per ogni fragment la **distanza dalla luce**.
2. Nel pass principale leggi il cubo con il vettore dalla luce al fragment e confronta la distanza salvata con quella reale.

Salvare la distanza lineare invece della profondità proiettata rende il confronto banale e il bias facile da scegliere.

## La texture di profondità a cubo

{{code}}

## Sei viste

Usa le funzioni sinistrorse e la tabella delle facce del capitolo [Cubemap](../advanced-metal/cubemaps.html). Ogni faccia ha un campo visivo di 90 gradi e un rapporto d'aspetto di 1, così i sei frustum combaciano esattamente:

{{code}}

Disegna un pass per faccia, scegliendo la faccia con lo `slice` dell'attachment:

{{code}}

I sei pass si possono fondere in uno solo con il layered rendering, come descritto in [Vivere senza geometry shader](../advanced-metal/no-geometry-shaders.html). Comincia dal ciclo; è più facile da mettere a punto.

## Scrivere la distanza come profondità

La fragment function sostituisce il valore di profondità con la distanza lineare dalla luce, scalata nell'intervallo da 0 a 1:

{{code}}

`[[depth(any)]]` permette a una fragment function di rimpiazzare la profondità calcolata dal rasterizer. Questa volta la pipeline ha una fragment function, ma ancora nessun attachment di colore.

## Leggere il cubo

Nel pass principale:

{{code}}

La direzione non ha bisogno di essere normalizzata. Il cubo sceglie da solo la faccia e il texel. Con un sampler di confronto puoi scriverlo come `shadowCube.sample_compare(s, lightToFragment, currentDepth - bias)` e avere in più il filtro dell'hardware.

## Bordi morbidi

Per una mappa 2D facevamo la media dei texel vicini. Per un cubo sposta invece la **direzione** di lettura. Venti spostamenti ben distribuiti danno un buon risultato:

{{code}}

Far crescere il raggio con la distanza rende le ombre più nette vicino a chi le proietta e più morbide lontano, che è come si comportano le ombre vere.

## Il costo

Le ombre delle luci puntiformi disegnano la scena sei volte in più per ogni luce. Tieni basso il numero di luci puntiformi che proiettano ombre, fai il culling degli oggetti faccia per faccia e aggiorna la mappa solo quando la luce o gli oggetti vicini si muovono.

## Esercizi

- Visualizza la distanza salvata restituendo `float4(float3(closestDepth), 1)`.
- Converti i sei pass in un solo pass a strati.
