Aggiungi un uniform intero e scegli in base a quello quando calcoli la coordinata di texture. Ad angolo basso la versione semplice galleggia e si deforma, la versione steep è stabile ma mostra gradini a strati sui pendii, e l'occlusion mapping elimina i gradini.
---
Dalla coordinata di texture e dalla profondità finali avanza verso la luce in spazio tangente. Se a un qualsiasi passo la height map sale sopra il raggio, il punto è in ombra.

{{code}}
