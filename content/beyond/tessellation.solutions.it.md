Passa al kernel dei fattori `level = 1.0 + 7.5 * (sin(time) * 0.5 + 0.5)` a ogni frame. Con un partition mode frazionario i nuovi vertici escono con dolcezza dai bordi esistenti. La demo interattiva ha uno slider per il fattore.
---
Dai al kernel i punti di controllo e la posizione della camera. Per ogni bordo prendi il punto medio, calcola la distanza dalla camera e trasformala in un fattore. Per l'interno usa la media dei fattori di bordo.

{{code}}

Poiché il fattore dipende solo dagli estremi del bordo, entrambe le patch che condividono un bordo calcolano lo stesso valore e non compaiono crepe.
---
Con `.integer` il fattore si aggancia a numeri interi, quindi la mesh cambia a scatti visibili mentre ti muovi. Con `.fractionalEven` i nuovi vertici crescono da quelli esistenti, e la transizione è continua. I modi frazionari non costano niente in più e sono la scelta predefinita giusta per tutto ciò che si muove.
