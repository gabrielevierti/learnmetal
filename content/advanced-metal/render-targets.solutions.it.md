Crea le texture offscreen a metà della dimensione del drawable; il pass a tutto schermo le stira. Con `.nearest` vedi pixel raddoppiati e a blocchi, con `.linear` una sfocatura morbida. Disegnare a risoluzione ridotta e poi ingrandire è un modo consueto di risparmiare tempo di GPU, e MetalFX fa l'ingrandimento molto meglio di un filtro lineare.
---
Aggiungi una seconda piccola texture di colore e disegnaci la scena con una matrice view che guarda lungo `-camera.front`. Poi, nel pass principale, disegna vicino al bordo alto dello schermo un piccolo rettangolo che la legge. Specchia l'immagine in orizzontale ribaltando u, come fa uno specchio vero.

{{code}}
