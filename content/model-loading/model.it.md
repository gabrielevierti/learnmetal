# Modello

Di solito un file contiene più mesh disposte in una gerarchia, ognuna con la propria trasformazione. Un tipo `Model` le raccoglie, così caricare e disegnare un file intero richiede una riga per ciascuna delle due cose.

<!-- cpp -->

!!! note "Caricare i modelli in C++"
    Model I/O e i tipi di mesh di MetalKit non fanno parte di metal-cpp. La versione C++ di questa sezione carica file Wavefront OBJ con la libreria a singolo header [tinyobjloader](https://github.com/tinyobjloader/tinyobjloader) e costruisce a mano i buffer di Metal. Le idee sono le stesse: un modello è fatto di mesh, una mesh ha un vertex buffer e un index buffer per ogni materiale, e un materiale è fatto di valori e di texture. Per caricare USD da C++ chiama Model I/O da un piccolo file Objective-C++, come fa per AppKit il codice della finestra in [Preparare il progetto](../getting-started/project-setup.html), oppure converti il modello in OBJ o glTF.

<!-- /cpp -->

## La classe Model

{{code}}

Ogni `MDLObject` può avere una trasformazione relativa al suo genitore. Risalire la catena dei genitori e moltiplicare dà la collocazione della mesh dentro il modello. I file OBJ semplici non hanno gerarchia, quindi il ciclo restituisce soltanto l'identità. I file USD spesso ce l'hanno, e saltare questo passo è il motivo per cui a volte le parti di un modello compaiono ammucchiate nell'origine.

## Disegnare

Ogni nodo combina la matrice del modello con la propria trasformazione di nodo:

{{code}}

Nel renderer:

{{code}}

Aggiungi le luci puntiformi della sezione precedente e hai un modello con texture e illuminato come si deve.

## Dove trovare i modelli

- Apple pubblica modelli USDZ di esempio nella sua galleria AR Quick Look.
- Siti come Sketchfab, Poly Haven e Kenney offrono modelli gratuiti. Controlla la licenza di ciascuno.
- Blender esporta sia OBJ sia USD.

Quando un modello appare sbagliato i soliti sospetti sono, nell'ordine: coordinate di texture ribaltate, normali mancanti, una scala sbagliata di un fattore 100 (centimetri contro metri) e trasformazioni dei nodi ignorate.

## Ingombro e inquadratura

Un modello sconosciuto può avere qualsiasi dimensione. Model I/O ne riporta il bounding box, che permette di scalare e centrare qualsiasi cosa in automatico:

{{code}}

Moltiplica `normalize` nella matrice model e ogni modello entra in una scatola larga due unità intorno all'origine.

## Che cosa abbiamo lasciato fuori

Un loader da produzione gestisce anche l'animazione scheletrica (`MDLSkeleton`, `MDLAnimationBindComponent`), i morph target, le camere e le luci salvate nel file, e tiene una cache delle texture, così un'immagine condivisa da dieci materiali viene caricata una volta sola. Come primo miglioramento aggiungi al loader dei materiali un dizionario da URL a `MTLTexture`.

## Esercizi

- Disegna il modello dieci volte usando le posizioni dei cubi della prima sezione.
- Implementa la cache delle texture.
- Carica un modello senza texture e verifica che la texture di riserva e `baseColor` diano un risultato sensato. Dovrai passare `baseColor` allo shader negli uniform del fragment.
