Moltiplica canale per canale. Una luce (0.33, 0.42, 0.18) sull'oggetto corallo (1.0, 0.5, 0.31) dà (0.33, 0.21, 0.06), un verde oliva scuro. Una luce blu pura dà (0, 0, 0.31): l'oggetto appare blu scuro, perché il blu è l'unica luce che può riflettere.
---
Imposta il colore della luce a ogni frame, per esempio in Swift `Float3(sin(time * 2.0), sin(time * 0.7), sin(time * 1.3)) * 0.5 + 0.5`. Il `* 0.5 + 0.5` tiene ogni canale tra 0 e 1. Usa lo stesso valore per il colore del cubo della lampada, così la lampada corrisponde alla luce che emette.
