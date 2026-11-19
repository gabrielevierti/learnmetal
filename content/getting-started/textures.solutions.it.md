Leggi la texture con `in.uv * 2.0`. Con `.repeat` vedi quattro copie, con `.mirrorRepeat` le copie sono specchiate e le giunture combaciano, e con `.clampToEdge` l'immagine riempie un quarto e i pixel del suo bordo si allungano sul resto. Puoi provare tutti e tre nella demo interattiva qui sopra alzando la scala delle UV.
---
Imposta `minFilter` e `magFilter` a `.nearest` e rimappa le coordinate in modo che il rettangolo mostri un decimo dell'immagine. Ogni texel diventa un quadrato visibile. Torna a `.linear` e i quadrati si fondono in una sfocatura.

{{code}}
---
Aggiungi un float a una struct di uniform per lo stadio di fragment, collegalo con `setFragmentBytes` e impostalo a `sin(time) * 0.5 + 0.5` a ogni frame.

{{code}}
