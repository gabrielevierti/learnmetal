Cambia il segno di y quando scrivi la posizione. Cambia solo la vertex function.

{{code}}
---
Dai alla vertex function una sua struct di uniform, a un indice di buffer libero, e somma l'offset. Sulla CPU imposta `offset = (cos(time), sin(time)) * 0.3` a ogni frame e invialo con `setVertexBytes` all'indice 1.

{{code}}
---
Il vertice in basso a sinistra si trova in (-0.5, -0.5, 0). Usato come colore significa rosso e verde negativi e blu a zero, e l'attachment di colore porta a 0 i valori negativi: per questo quell'angolo è nero. I valori interpolati diventano positivi, e quindi visibili, solo verso destra e verso l'alto del triangolo.
