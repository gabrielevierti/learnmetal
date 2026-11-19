Calcola la posizione dal tempo a ogni frame e usala sia per l'uniform sia per la matrice model della lampada: `(cos(time) * 2, 1, sin(time) * 2)`. La demo interattiva qui sopra fa esattamente questo.
---
A 2 il riflesso copre quasi tutta la faccia e sembra altra luce diffusa. A 8 è un alone largo e morbido, a 64 una piccola macchia, e a 256 un puntino, come nel metallo lucidato o nella plastica bagnata. L'esponente restringe soltanto il lobo; non ne cambia la luminosità massima.
---
La vertex function calcola un colore per vertice e il rasterizer lo interpola in modo lineare. Un riflesso che cade in mezzo a una faccia va perso del tutto, perché nessun vertice lo vede, e uno vicino a un angolo viene spalmato su tutto il triangolo. Su un cubo con 2 triangoli per faccia l'effetto è estremo. L'illuminazione per fragment valuta la formula in ogni pixel, e il riflesso mantiene la sua forma.
