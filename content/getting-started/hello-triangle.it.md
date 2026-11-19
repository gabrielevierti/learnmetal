# Il primo triangolo

In Metal, come in ogni API per GPU, tutto ciò che vedi è fatto di triangoli. Per disegnare il primo servono tre pezzi nuovi: i dati dei vertici in un buffer, una coppia di shader e un render pipeline state che li lega. È il gradino più ripido di tutta la serie. Una volta che funziona, il resto è variazione.

## La pipeline grafica

La pipeline è la sequenza di passaggi che trasforma coordinate 3D in pixel colorati.

{{figure}}

- La **vertex function** viene eseguita una volta per vertice e ne produce la posizione finale.
- La GPU assembla i vertici in triangoli e li **rasterizza**: calcola quali pixel copre ogni triangolo e produce un **fragment** per ciascuno.
- La **fragment function** viene eseguita una volta per fragment e ne produce il colore.
- I test di profondità e di stencil e il blending decidono come quel colore finisce nella texture.

## I dati dei vertici

Metal si aspetta le posizioni finali in **coordinate normalizzate del dispositivo** (NDC): x e y vanno da -1 a 1 attraverso la vista, con x verso destra e y verso l'alto, e z va da 0 a 1 entrando nello schermo. Tutto ciò che sta fuori viene tagliato. Un triangolo al centro della vista:

{{code}}

La GPU non sa leggere un array Swift. I dati devono stare in un `MTLBuffer`. Aggiungi una proprietà e crea il buffer in `init`:

{{code}}

Il buffer è fatto solo di byte. Metal non sa ancora che sono gruppi di tre float.

## Gli shader

Apri `Shaders.metal` e scrivi le due funzioni:

{{code}}

Le annotazioni tra doppie parentesi quadre sono il modo in cui MSL collega le variabili dello shader al mondo esterno:

- `vertex` e `fragment` segnano le funzioni come punti d'ingresso della pipeline.
- `[[stage_in]]` significa «l'input per vertice (o per fragment) assemblato per questo stadio».
- `[[attribute(0)]]` dice che questo membro arriva dall'attributo di vertice 0, che descriviamo più sotto.
- `[[position]]` segna l'output che contiene la posizione in clip space. È un `float4`; la quarta componente `w` per ora vale 1 e diventa importante con la prospettiva.

La fragment function restituisce un colore arancione come float RGBA.

## Il vertex descriptor

Un `MTLVertexDescriptor` spiega la disposizione del vertex buffer, così Metal può riempire `VertexIn`:

{{code}}

L'attributo 0 è fatto di tre float, parte dal byte 0 di ogni vertice e viene letto dal buffer collegato all'indice 0. Ogni vertice dista 12 byte dal successivo.

## Il render pipeline state

Il pipeline state unisce le funzioni shader, la disposizione dei vertici e il formato dei pixel della texture in cui si disegna:

{{code}}

`makeDefaultLibrary()` carica gli shader compilati dal bundle dell'app. Creare un pipeline state compila gli shader per la GPU ed è lento, quindi fallo sempre al caricamento e mai a ogni frame. Il formato dei pixel deve coincidere con il `colorPixelFormat` della vista; una discordanza è il primo errore di validazione più comune.

!!! note "Se vieni da OpenGL"
    Un pipeline state è più o meno un programma shader linkato, più la disposizione degli attributi del VAO, più lo stato del blending, tutto congelato in un solo oggetto. Non c'è nessuna danza di binding tra VAO e VBO.

## Disegnare

In `draw(in:)`, tra la creazione dell'encoder e la sua chiusura:

{{code}}

`index: 0` è lo slot del buffer a cui si riferisce il `bufferIndex` del vertex descriptor. Esegui l'app e dovresti vedere un triangolo arancione.

## Disegno indicizzato

Un rettangolo è fatto di due triangoli che condividono due vertici. Invece di duplicarli, memorizza ogni vertice una volta sola e descrivi i triangoli con gli indici:

{{code}}

{{code}}

Per vedere i triangoli stessi, chiama `encoder.setTriangleFillMode(.lines)` prima di disegnare.

## Esercizi

- Disegna due triangoli affiancati aggiungendo altri tre vertici e cambiando `vertexCount`.
- Crea un secondo pipeline state con una fragment function che restituisce il giallo, e disegna con quello il secondo triangolo.
- Sposta un vertice fuori dall'intervallo da -1 a 1 e guardalo mentre viene tagliato.
