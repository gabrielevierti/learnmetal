# Illuminazione

Con la teoria alle spalle, lo shader PBR è breve. Questo capitolo implementa la BRDF di Cook-Torrance per le luci puntiformi, prima con valori di materiale costanti e poi con le texture.

## Le funzioni della BRDF

Ogni formula del capitolo precedente diventa una piccola funzione:

{{code}}

Elevare al quadrato la roughness prima di usarla (`a = roughness²`) fa percepire il parametro come lineare agli artisti. È una convenzione adottata da quasi tutti i motori.

## La fragment function

{{code}}

Ripercorriamo il ciclo:

- La **radianza** è il colore della luce attenuato dall'inverso del quadrato della distanza. Una luce puntiforme consegna tutta la sua energia da una sola direzione, quindi l'integrale dell'equazione della riflettanza si riduce a una valutazione per luce.
- **F0** passa dal valore dei dielettrici, 0.04, all'albedo man mano che il materiale diventa metallico.
- Il termine **specular** è `D·G·F` diviso per il fattore di normalizzazione. La piccola costante evita una divisione per zero.
- `kD` toglie la frazione riflessa ed elimina del tutto il diffuse per i metalli.
- Il risultato viene moltiplicato per `NdotL`, il fattore coseno.

L'uscita è HDR lineare. Passa attraverso il pass di tone mapping del capitolo [HDR](../advanced-lighting/hdr.html) e il drawable sRGB. Non applicare la correzione gamma in questo shader.

Il termine ambient fisso è un segnaposto. Sostituirlo con la vera luce dell'ambiente è il compito dei prossimi due capitoli.

## Una griglia di sfere

La prova standard: una griglia di sfere in cui la metalness cresce dal basso verso l'alto e la roughness da sinistra a destra. La sfera la genera Model I/O:

{{code}}

{{code}}

Quattro luci di colore (300, 300, 300) messe a circa 10 unità davanti alla griglia la illuminano bene. Valori così grandi sono normali con il calo secondo l'inverso del quadrato.

Anche con un termine ambient piatto il risultato colpisce: i dielettrici ruvidi sembrano gesso o gomma, quelli lisci plastica, e i metalli hanno riflessi stretti e colorati.

## PBR con le texture

Sostituisci le costanti con letture da texture, e usa la funzione di normal mapping di [Normal mapping](../advanced-lighting/normal-mapping.html):

{{code}}

Carica la mappa dell'albedo come sRGB e tutte le altre come dati lineari. Molti pacchetti di asset riuniscono occlusion, roughness e metalness nei canali rosso, verde e blu di un'unica texture "ORM", risparmiando due letture.

Con Model I/O estendi il loader dei materiali del capitolo [Mesh](../model-loading/mesh.html) perché legga i semantic `.metallic`, `.roughness`, `.tangentSpaceNormal` e `.ambientOcclusion`, ripiegando su texture da 1 × 1 con i valori scalari quando una proprietà non ha texture.

## Esercizi

- Dai a ogni sfera la stessa roughness e varia solo l'albedo per vedere come i metalli colorano i loro riflessi.
- Trova un set gratuito di materiali PBR, come ferro arrugginito o plastica consumata, e applicalo a una sfera.
