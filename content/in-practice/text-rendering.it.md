# Rendering del testo

Prima o poi vorrai disegnare del testo: un contatore di frame, un punteggio, un'etichetta sopra un oggetto. Metal non ha alcun supporto per il testo. Disegna triangoli. Il testo si disegna quindi come rettangoli con texture, uno per carattere, con una texture che contiene le forme dei caratteri.

## Le opzioni

- **Lasciar fare al sistema.** Per l'interfaccia che sta sopra la tua vista, metti un'etichetta SwiftUI o UIKit sopra la `MTKView`. È gratis, nitida, localizzata e accessibile. Per gli overlay di debug e i menu di solito è la risposta giusta.
- **Disegnare le stringhe in texture.** Disegna un'intera stringa con Core Text in una bitmap e mostrala su un rettangolo. Va bene per il testo che cambia di rado.
- **Un atlas di glifi.** Disegna ogni carattere una volta sola in un'unica texture, poi componi qualsiasi stringa con dei rettangoli. È l'approccio classico per il testo dentro la scena 3D o per il testo che cambia a ogni frame, ed è quello che costruiamo in questo capitolo.

## Glifi e metriche

Un font è una raccolta di **glifi**, le forme dei caratteri. Per disporli correttamente ci servono alcune misure per ogni glifo, tutte relative alla **baseline** su cui il testo poggia:

- il **bounding box**: il rettangolo occupato dalla forma, che può scendere sotto la baseline per lettere come g e p,
- l'**advance**: di quanto spostare la penna verso destra prima di disegnare il glifo successivo.

**Core Text** fornisce entrambe, e sa disegnare i glifi in una bitmap di Core Graphics.

## Costruire l'atlas

Disegniamo i caratteri ASCII stampabili in una bitmap a un solo canale, disponendoli in righe, e annotiamo dove è finito ciascuno.

{{code}}

La memoria della bitmap comincia dalla riga in alto dell'immagine, che coincide con l'origine in alto a sinistra delle texture di Metal. Vanno convertite solo le posizioni dei glifi, che Core Graphics misura dal basso.

## Costruire i rettangoli per una stringa

Per ogni carattere cerca il suo glifo, emetti due triangoli e fai avanzare la penna:

{{code}}

Le posizioni sono in pixel con y verso l'alto, e `origin` è l'inizio della baseline.

## Gli shader

Il testo si disegna con una **proiezione ortografica** che porta le coordinate in pixel direttamente sullo schermo:

{{code}}

{{code}}

L'atlas contiene solo la copertura. Il colore arriva da un uniform, quindi un solo atlas serve per testo di ogni colore. La pipeline ha bisogno dell'**alpha blending** attivo, come nel capitolo [Blending](../advanced-metal/blending.html), e il testo va disegnato per ultimo con il test di profondità spento.

## Disegnare

{{code}}

Alloca `textBuffer` una volta sola, grande abbastanza per il testo più lungo che prevedi, e riscrivilo a ogni frame.

## I limiti di questo approccio

- **Scalare sfoca.** Un atlas bitmap è nitido alla dimensione a cui è stato disegnato. Disegna l'atlas alla dimensione in pixel a cui lo mostrerai, ricordando che gli schermi Retina hanno due o tre pixel per punto.
- **Solo scritture semplici.** Far corrispondere un carattere a un glifo ignora il kerning, le legature, i segni combinanti, il testo da destra a sinistra e le scritture complesse. Per un'impaginazione corretta lascia che sia Core Text a comporre la stringa (`CTLineCreateWithAttributedString`, poi leggi i suoi glyph run) e disegna dal tuo atlas i glifi e le posizioni che restituisce.
- **Solo ASCII.** Un atlas dinamico che aggiunge i glifi a richiesta toglie questo limite.

## Signed distance field

Per il testo che deve restare nitido a qualsiasi dimensione, soprattutto in 3D, salva nell'atlas un **signed distance field** al posto della copertura: ogni texel contiene la distanza dal bordo del glifo più vicino. Il filtro bilineare interpola le distanze in modo fedele, quindi il bordo si può ricostruire netto a qualsiasi ingrandimento:

{{code}}

Contorni, bagliori e ombre portate diventano ciascuno un `smoothstep` in più. I distance field a più canali (MSDF) conservano inoltre gli angoli vivi, e sono la tecnica che oggi usa la maggior parte dei motori.
