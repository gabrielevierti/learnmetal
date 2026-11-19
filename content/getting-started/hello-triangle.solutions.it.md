Aggiungi altri tre vertici all'array, per esempio il primo triangolo spostato di 0.6 su x e rimpicciolito, e disegna con un numero di vertici pari a 6. La lunghezza del buffer segue l'array da sola.

{{code}}
---
Aggiungi una seconda fragment function, cambia solo `fragmentFunction` nel descriptor e crea da questo un secondo pipeline state. Poi disegna ogni triangolo dopo aver impostato la sua pipeline: vertice iniziale 0 e conteggio 3 con il primo state, vertice iniziale 3 e conteggio 3 con il secondo.

{{code}}
---
Metti un vertice a x = 1.5. Il triangolo viene tagliato dal bordo della vista: la GPU lo ritaglia contro il volume da -1 a 1 e rasterizza solo la parte interna. Niente rientra dal lato opposto e niente va in crash. Il ritaglio su z funziona allo stesso modo, ed è per questo che la geometria davanti al near plane sparisce.
