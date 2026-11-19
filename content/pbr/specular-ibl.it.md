# IBL speculare

La metà diffuse dell'illuminazione basata su immagini dipendeva solo dalla normale, quindi una piccola cubemap la risolveva. La metà specular è più difficile:

{{code}}

Dipende dalla normale, dalla direzione di vista, dalla roughness e da F0. Precalcolare ogni combinazione è impossibile. La **split-sum approximation** di Epic Games spezza l'integrale in due parti che *si possono* precalcolare:

1. Una **environment map prefiltrata**: l'ambiente sfocato della quantità giusta per ogni livello di roughness.
2. Una **tabella di lookup della BRDF**: una texture 2D che contiene il resto della risposta della BRDF.

## Parte 1: l'environment map prefiltrata

Una superficie ruvida riflette un cono ampio dell'ambiente, una liscia un cono stretto. Salviamo versioni sempre più sfocate dell'ambiente nei **livelli di mip** di una cubemap: il livello 0 per la roughness 0, l'ultimo per la roughness 1. Al momento del rendering il vettore di riflessione e la roughness scelgono la direzione e il livello di mip.

L'approssimazione suppone che la direzione di vista coincida con la direzione di riflessione e con la normale, perché al momento del precalcolo la direzione di vista non è nota. Il prezzo è un certo allungamento dei riflessi agli angoli radenti, per il resto difficile da notare.

### Importance sampling

Fare la media dell'ambiente in modo uniforme richiederebbe migliaia di campioni. L'**importance sampling** genera direzioni di campionamento concentrate dove la distribuzione GGX è grande, e ne bastano poche decine. Servono numeri quasi casuali ben distribuiti, per i quali la scelta abituale è la **sequenza di Hammersley**:

{{code}}

### Lo shader di prefiltro

{{code}}

### Disegnare la catena di mip

Crea una texture a cubo con le mipmap, intorno a 128 o 256 per faccia, e disegna ogni livello di mip con una roughness diversa, usando il `level` dell'attachment:

{{code}}

Ogni livello di mip è grande la metà del precedente, e il viewport segue da solo la dimensione dell'attachment. Usa un sampler con filtro lineare sui mip, altrimenti la scelta del mip per ogni campione nello shader non ha effetto.

In Metal il filtro delle cubemap è continuo da una faccia all'altra, quindi nei livelli sfocati non si vedono giunture sui bordi delle facce.

## Parte 2: la tabella di lookup della BRDF

La seconda metà della split sum dipende da due soli numeri: `n · v` e la roughness. Il suo risultato, una **scala** e un **bias** da applicare a F0, sta nei canali rosso e verde di una texture 2D. La tabella è la stessa per ogni ambiente, quindi calcolala una volta sola, o addirittura distribuiscila come immagine.

{{code}}

Disegnala con il triangolo a tutto schermo in una texture `.rg16Float` da 512 × 512. Il risultato è una sfumatura morbida dal rosso al giallo.

## Mettere tutto insieme

{{code}}

Leggi la tabella di lookup con un sampler in clamp. La coordinata di texture per la roughness deve corrispondere a come hai disegnato la tabella: qui la riga 0, quella in alto, è la roughness 0.

Adesso le sfere di metallo prendono vita. Quelle lisce rispecchiano l'ambiente, quelle ruvide ne mostrano una versione morbida e sfocata, e tutto è colorato correttamente da F0. Insieme all'illuminazione diretta delle luci puntiformi, questa è una pipeline PBR completa.

## Oltre una sola probe

Una environment map descrive la luce in un punto solo. Dentro un edificio una sfera rifletterebbe il cielo attraverso i muri. I motori dispongono in un livello molte **reflection probe**, ognuna con la sua mappa prefiltrata, e mescolano le più vicine. Le **screen-space reflection** e, sull'hardware che lo permette, i riflessi in [ray tracing](../beyond/ray-tracing.html) aggiungono ciò che le probe non possono catturare: gli oggetti vicini e in movimento.

## Esercizi

- Mostra come skybox ogni livello di mip della mappa prefiltrata.
- Precalcola una volta le tre texture dell'IBL e tienile in cache su disco.
- Carica un modello PBR completo e mettilo in tre ambienti diversi senza cambiarne il materiale.
