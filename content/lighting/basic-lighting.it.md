# Illuminazione di base

La luce vera è complicata senza speranza, quindi la grafica in tempo reale usa delle approssimazioni. Quella classica è il **modello di illuminazione di Phong**, che costruisce il colore finale da tre parti semplici:

- **Ambient**: una piccola quantità costante di luce ovunque, al posto della luce che ha rimbalzato per la stanza.
- **Diffuse**: la superficie è tanto più luminosa quanto più è rivolta verso la luce.
- **Specular**: il riflesso lucido nel punto in cui la luce rimbalza verso chi guarda.

## Ambient

{{code}}

Da sola rende soltanto scuro il cubo, ma evita che i lati non illuminati siano nero puro.

## Diffuse

La luce diffusa ha bisogno, per ogni fragment, di due direzioni: la **normale** della superficie e la direzione dal fragment alla luce. Il coseno dell'angolo tra le due, dato dal prodotto scalare dei due vettori unitari, è la luminosità: 1 quando la luce arriva di fronte, 0 quando sfiora la superficie.

Il nostro cubo ha già le normali. Alla fragment function servono la normale e la posizione del fragment in **spazio mondo**, quindi la vertex function passa entrambe:

{{code}}

### La matrice delle normali

Le normali sono direzioni, quindi la traslazione non deve toccarle, e una scala non uniforme le deforma se usi direttamente la matrice model. La matrice corretta per le normali è la **trasposta dell'inversa del blocco 3×3 in alto a sinistra** della matrice model. Calcolala sulla CPU:

{{code}}

Se la matrice model contiene solo rotazioni e scale uniformi va bene anche il blocco 3×3 così com'è, ma la trasposta dell'inversa è sempre giusta.

### Il termine diffuse

{{code}}

Contano due dettagli. Le normali interpolate non hanno più lunghezza 1, quindi normalizzale di nuovo nella fragment function. E `max(..., 0.0)` impedisce che le superfici rivolte dalla parte opposta ricevano luce negativa.

## Specular

Un riflesso compare dove la luce rimbalza sulla superficie dritta nell'occhio. Rifletti la direzione della luce intorno alla normale e confronta il risultato con la direzione verso chi guarda:

{{code}}

`reflect` si aspetta un vettore che punta *verso* la superficie, da qui il segno meno. L'esponente, qui 32, è la **shininess**: valori più alti danno un riflesso più piccolo e più netto.

Dal lato Swift compila i nuovi campi a ogni frame:

{{code}}

Ora il cubo ha facce ben distinte e un riflesso che scivola su di esse mentre ti muovi.

!!! note "Spazio mondo o spazio vista?"
    Calcoliamo la luce in spazio mondo perché è il più facile su cui ragionare. Farlo in spazio vista funziona altrettanto bene, e lì chi guarda è sempre nell'origine. Qualunque cosa tu scelga, tutti i vettori di un calcolo devono stare nello stesso spazio.

## Esercizi

- Fai muovere la luce in cerchio intorno al cubo nel tempo.
- Prova valori di shininess di 2, 8, 64 e 256.
- Fai l'intero calcolo della luce nella vertex function e passa il colore risultante alla fragment function. È il **Gouraud shading**. Perché il riflesso viene peggio?
