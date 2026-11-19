# Test di profondità

Abbiamo acceso il depth buffer in [Sistemi di coordinate](../getting-started/coordinate-systems.html) e siamo andati avanti. Merita uno sguardo più attento, perché diverse tecniche successive, le ombre prima di tutte, dipendono dal capire con esattezza che cosa contiene.

## Come funziona il test

L'attachment di profondità conserva un valore per pixel. Per ogni fragment la GPU confronta la profondità del fragment con il valore salvato, usando la **compare function** del depth-stencil state corrente. Se il test passa, il fragment viene tenuto e, se la scrittura della profondità è attiva, la sua profondità sostituisce quella salvata. Se fallisce, il fragment viene scartato.

Concettualmente il test avviene dopo la fragment function. In pratica le GPU lo eseguono *prima* ogni volta che possono (**early depth testing**), saltando la fragment function per i pixel nascosti. Le GPU Apple vanno oltre con la hidden surface removal: per la geometria opaca stabiliscono prima quale fragment è visibile in ogni pixel e calcolano solo quello.

## Compare function

| `MTLCompareFunction` | Il fragment passa quando |
| --- | --- |
| `.less` | la sua profondità è minore di quella salvata |
| `.lessEqual` | minore o uguale |
| `.equal` | uguale |
| `.greater`, `.greaterEqual` | maggiore (o uguale) |
| `.notEqual` | diversa |
| `.always` | sempre. È il valore predefinito, cioè nessun test di profondità |
| `.never` | mai |

{{code}}

È comune uno state con il test acceso e la **scrittura spenta**: `isDepthWriteEnabled = false` permette ai fragment di essere nascosti dalla geometria esistente senza modificare il buffer. Lo usano gli oggetti trasparenti e gli effetti particellari.

I depth-stencil state sono oggetti economici e immutabili. Crea all'avvio i pochi che ti servono e passa dall'uno all'altro con `encoder.setDepthStencilState`.

## I valori non sono lineari

Il depth buffer non contiene la distanza. Dopo la matrice di proiezione e la divisione prospettica, la profondità in Metal è

{{code}}

per un punto a distanza `z` davanti alla camera. Vale 0 sul near plane e 1 sul far plane, ma in mezzo è fortemente non lineare. Con near a 0.1 e far a 100, un punto a una sola unità di distanza ha già profondità 0.9, e a 10 unità ha 0.99. La maggior parte della precisione viene spesa vicino alla camera, che è dove l'occhio nota di più gli errori.

## Visualizzare la profondità

L'input predefinito `[[position]]` di una fragment function contiene in x e y le coordinate del pixel e in z la profondità:

{{code}}

Quasi tutto è bianco, a meno di stare molto vicino. Per vedere qualcosa di utile riconverti in distanza lineare:

{{code}}

Tieni da parte questa funzione. Serve agli effetti in screen space come l'SSAO.

## Z-fighting

Quando due superfici sono quasi complanari, le loro profondità si arrotondano allo stesso numero e la vincitrice cambia da pixel a pixel, producendo un motivo a strisce tremolanti chiamato **z-fighting**. I rimedi:

- **Non mettere le superfici così vicine.** Un piccolo scarto che nessuno nota è la cura più semplice.
- **Allontana il near plane.** Passare da 0.01 a 0.1 fa guadagnare molta precisione.
- **Usa un depth buffer float a 32 bit.** `.depth32Float` è supportato ovunque in Metal ed è quello che usiamo. `.depth16Unorm` risparmia memoria a scapito della precisione.
- **Usa un depth bias** per le decal e simili: `encoder.setDepthBias(_:slopeScale:clamp:)` sposta leggermente la profondità di ciò che disegni dopo.

## Reverse-Z

I numeri in virgola mobile hanno la massima precisione vicino a 0, e la mappatura prospettica ha bisogno della massima precisione vicino a 1. Si può fare in modo che le due cose si compensino invertendo l'intervallo: manda il near plane a 1 e il far plane a 0, pulisci la profondità a 0 e fai il test con `.greater`.

{{code}}

Questa impostazione **reverse-Z** dà una precisione quasi uniforme su distanze di vista enormi, ed è la norma nei motori moderni. In Metal funziona proprio perché la profondità delle NDC va da 0 a 1. In questa serie teniamo la direzione convenzionale, così il codice resta facile da confrontare con altro materiale.

## Esercizi

- Disegna la scena con `.always` e spiega il risultato in termini di ordine di disegno.
- Metti due rettangoli a 0.0001 di distanza e allontana la camera finché non iniziano a contendersi i pixel. Poi prova ciascun rimedio.
