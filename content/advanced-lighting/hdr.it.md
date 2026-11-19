# HDR

I valori di colore scritti in una texture a 8 bit vengono limitati all'intervallo da 0 a 1. Metti in una scena più luci forti e ampie zone superano 1 nella somma, vengono tagliate e diventano una macchia bianca senza dettagli. Tutto il dettaglio delle zone luminose è perso.

Il rendering **high dynamic range** permette ai colori di superare 1 mentre l'immagine viene costruita, e converte il risultato in un intervallo visualizzabile solo alla fine, in un passo chiamato **tone mapping**.

## Render target in virgola mobile

La scena viene disegnata in una texture con un formato in virgola mobile, che conserva valori ben oltre 1 senza tagliarli:

{{code}}

| Formato | Note |
| --- | --- |
| `.rgba16Float` | La scelta standard. Half float a 16 bit per canale. |
| `.rg11b10Float` | Metà della memoria, niente alpha, precisione un po' inferiore. Buono sui dispositivi mobili. |
| `.rgba32Float` | Per il colore serve di rado. |

Imposta il formato di colore delle pipeline della scena perché coincida, e disegna la scena come in [Render target](../advanced-metal/render-targets.html). Gli shader di illuminazione non cambiano. Smettono semplicemente di essere tagliati.

## Tone mapping

Un pass a tutto schermo legge la texture HDR e la riporta all'intervallo da 0 a 1 per il drawable.

L'operatore più semplice è **Reinhard**, che divide ogni colore per sé stesso più uno. I valori alti vengono compressi verso 1 e quelli bassi restano quasi intatti:

{{code}}

Il drawable dovrebbe avere un formato sRGB, come impostato in [Correzione gamma](gamma-correction.html), così il risultato viene codificato in gamma automaticamente. Il tone mapping viene sempre prima della codifica gamma.

## Esposizione

Una fotocamera si adatta alla luminosità di una scena con la sua esposizione. Un tone mapper con **esposizione** ci dà lo stesso controllo:

{{code}}

Un'esposizione bassa rivela il dettaglio nelle zone luminose e schiaccia quelle scure; una alta fa il contrario. Così puoi disegnare un interno in penombra e un esterno al sole con gli stessi valori fisici di luce, cambiando solo l'esposizione. L'esposizione automatica, o **eye adaptation**, calcola la luminosità media del frame, per esempio dal livello di mip più piccolo della texture HDR, e avvicina gradualmente l'esposizione a un valore obiettivo.

## Curve filmiche

Reinhard tende a dare immagini slavate. Le curve simili a quelle della pellicola tengono più contrasto e attenuano le alte luci con più grazia. Un'approssimazione compatta e diffusa della curva ACES, di Krzysztof Narkowicz:

{{code}}

Il tone mapper è una delle cose che più contribuiscono all'aspetto complessivo di un renderer. Provane diversi.

## Una scena di prova

Costruisci un lungo tunnel con un cubo allungato e rivolto verso l'interno, con una luce molto forte in fondo, di colore intorno a (200, 200, 200), e alcune luci colorate deboli lungo le pareti. Senza HDR il fondo è una macchia bianca. Con l'HDR e il controllo dell'esposizione vedi la texture della parete fin sotto la luce.

## Perché conta al di là delle luci forti

- Il **bloom** ha bisogno di sapere quali pixel sono più luminosi del bianco. Vedi il [prossimo capitolo](bloom.html).
- Il **rendering fisicamente corretto** usa intensità di luce del mondo reale, che coprono un intervallo enorme.
- Effetti di post-processing come la profondità di campo e il motion blur risultano molto più naturali se calcolati su valori HDR.

## Mostrare direttamente l'HDR

Gli schermi Apple con **Extended Dynamic Range** (EDR) possono mostrare valori più luminosi del bianco standard. Un layer Metal lo attiva usando un formato di drawable in virgola mobile (`.rgba16Float`), uno spazio colore lineare esteso e `wantsExtendedDynamicRangeContent = true` sul `CAMetalLayer`. I valori sopra 1.0 vengono allora mostrati più luminosi del bianco dell'interfaccia, fino a un margine che lo schermo riporta e che cambia con le impostazioni di luminosità. Il tone mapping si fa comunque, ma verso l'intervallo disponibile sullo schermo invece che da 0 a 1. È un miglioramento che vale la pena fare quando il resto della pipeline è a posto.

## Esercizi

- Aggiungi dei tasti per alzare e abbassare l'esposizione.
- Mostra Reinhard sulla metà sinistra dello schermo e ACES sulla destra.
