# Parallax mapping

Il normal mapping cambia il modo in cui una superficie è illuminata, ma non che cosa vedi e dove. Con un angolo radente un muro di mattoni con normal map sembra ancora una tavola dipinta, perché i mattoni non nascondono la malta che sta dietro. Il **parallax mapping** sposta le coordinate di texture in base a una height map e all'angolo di vista, così le parti alte sembrano coprire quelle basse.

## L'idea

Accanto alle mappe di colore e delle normali ci serve una **height map**, una texture in scala di grigi che descrive il rilievo della superficie. È più comodo salvare la **profondità**, l'inverso dell'altezza: 0 sulla superficie superiore, 1 nel punto più profondo.

Immagina chi guarda mentre osserva un punto A sul poligono piatto. Sulla superficie vera, quella con i rilievi, la linea di vista avrebbe colpito il rilievo prima, in un punto B, e chi guarda dovrebbe vedere la texture in B. Il parallax mapping stima di quanto far scivolare la coordinata di texture da A verso B.

Tutto questo si fa in **spazio tangente**, dove la superficie è il piano xy e le u e v della texture corrono lungo x e y. La direzione di vista va quindi convertita prima in spazio tangente.

## La direzione di vista in spazio tangente

La matrice TBN del capitolo precedente converte da tangente a mondo. La sua trasposta fa il contrario, perché la matrice è ortonormale:

{{code}}

## Parallax mapping semplice

Leggi la profondità alla coordinata attuale e spostati lungo la direzione di vista di quella quantità:

{{code}}

`scale` controlla l'intensità; sono tipici valori tra 0.05 e 0.1. La divisione per `viewDir.z` rende lo spostamento più grande agli angoli radenti. Poi usa la coordinata spostata per **ogni** lettura di texture del fragment: colore, normale, specular.

{{code}}

Il discard rifila i bordi di un rettangolo singolo, dove le coordinate spostate uscirebbero dalla texture. Sulle superfici che si ripetono lo lasceresti fuori.

!!! note "Convenzioni di segno"
    Se lo spostamento vada sottratto o sommato, e se la sua y vada cambiata di segno, dipende dalla direzione del tuo asse v e della bitangente. Se l'effetto sembra gonfiarsi verso l'interno o scivolare nel verso sbagliato quando muovi la camera, inverti il segno della componente y.

Questa versione a una sola lettura funziona per i rilievi dolci. Sui cambi di altezza ripidi o ad angoli molto bassi la stima è scarsa e la superficie sembra galleggiare.

## Steep parallax mapping

Una stima migliore si ottiene avanzando lungo il raggio di vista a piccoli passi, attraverso un certo numero di strati di profondità, finché il raggio scende sotto la superficie:

{{code}}

Dentro un ciclo la GPU non riesce a calcolare in modo affidabile i livelli di mip automatici, quindi le letture indicano esplicitamente il livello 0. Il risultato è molto più convincente, ma gli strati discreti si notano come gradini.

## Parallax occlusion mapping

I gradini spariscono se, invece di prendere il primo strato sotto la superficie, interpoliamo tra l'ultimo punto sopra la superficie e il primo sotto:

{{code}}

È il **parallax occlusion mapping** (POM). Le due profondità ci dicono quanto dista ciascun punto dalla superficie vera, e una miscela lineare cade molto vicino all'intersezione reale.

## I limiti

- È un'illusione dentro il poligono. Il profilo resta piatto, e l'effetto si rompe agli angoli radenti.
- Costa caro: decine di letture di texture per fragment. Riduci il numero di strati con la distanza.
- Il rilievo non proietta ombre su sé stesso, a meno di far avanzare un secondo raggio verso la luce.

Quando ti serve geometria vera, con profili e ombre veri, sposta i vertici con la [tassellazione](../beyond/tessellation.html).

## Esercizi

- Passa da una variante all'altra con un uniform e confrontale con un angolo di vista basso.
- Implementa l'auto-ombreggiatura avanzando in spazio tangente dal punto trovato verso la luce.
