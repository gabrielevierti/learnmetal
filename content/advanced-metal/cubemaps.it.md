# Cubemap

Una **cubemap** è una texture fatta di sei immagini quadrate disposte come le facce di un cubo. Si legge con una direzione 3D invece che con una coordinata 2D: immagina di stare al centro del cubo e di guardare lungo quella direzione, e ottieni il colore che vedi. Le cubemap si usano per i cieli, per i riflessi e, più avanti, per le ombre omnidirezionali e per l'illuminazione basata su immagini.

## Creare una cubemap

Le sei facce sono salvate come sei **slice** di una sola texture di tipo `.typeCube`, nell'ordine +X, -X, +Y, -Y, +Z, -Z (destra, sinistra, alto, basso, davanti, dietro).

**Da sei file immagine**, la strada più breve passa per Model I/O:

{{code}}

**Da una sola immagine** che contiene le sei facce impilate dall'alto in basso, il texture loader la può dividere:

{{code}}

**A mano**, quando le facce le generi o le decodifichi tu:

{{code}}

## Uno skybox

Uno skybox è un cubo disegnato intorno alla camera con una cubemap come texture, e dà l'illusione di un ambiente immenso. La sua coordinata di texture è semplicemente la posizione locale del cubo, usata come direzione.

{{code}}

Nella vertex function ci sono due trucchi:

- La posizione viene moltiplicata con **w = 0**, che elimina la traslazione della matrice view. Il cielo ruota con la camera ma non si avvicina mai.
- L'uscita è `clip.xyww`. Dopo la divisione prospettica z diventa w / w = **1**, il far plane. Il cielo finisce dietro a tutto.

Disegna il cielo **per ultimo**, dopo tutti gli oggetti opachi, con un depth state che usa `.lessEqual` e non scrive la profondità:

{{code}}

Disegnato per ultimo, i fragment del cielo vengono scartati ovunque sia stato disegnato qualcos'altro, quindi il cielo costa solo i pixel in cui è visibile. `.lessEqual` serve perché la profondità del cielo è uguale al valore di pulizia, 1. La camera sta dentro il cubo, quindi disattiva il culling per questa draw call.

!!! note "Sinistrorso o destrorso"
    Le cubemap usano una convenzione sinistrorsa, una stranezza storica comune a tutte le API grafiche. Se nel tuo mondo destrorso uno skybox appare specchiato, cambia segno alla componente x o z della direzione nello shader.

## Riflessione

Con l'ambiente in una cubemap una superficie a specchio è facile: rifletti la direzione di vista intorno alla normale e usa il risultato per leggere il cielo.

{{code}}

Combinala con una specular map per rendere riflettenti solo alcune parti di un modello.

## Rifrazione

La luce si piega quando passa da un mezzo a un altro. `refract` calcola la direzione piegata dal rapporto tra i due **indici di rifrazione**:

| Materiale | Indice |
| --- | --- |
| Aria | 1.00 |
| Acqua | 1.33 |
| Vetro | 1.52 |
| Diamante | 2.42 |

{{code}}

È una sola rifrazione alla superficie. Fisicamente è incompleta, ma dà un aspetto di vetro convincente.

## Disegnare dentro una cubemap

Un cielo statico non può riflettere oggetti in movimento. Per i riflessi dinamici disegna la scena sei volte dalla posizione dell'oggetto, una per faccia, con un campo visivo di 90 gradi e un rapporto d'aspetto di 1. Scegli la faccia con lo `slice` dell'attachment:

{{code}}

Per via della convenzione delle cubemap queste sei viste vanno costruite con matrici view e projection **sinistrorse**, e i vettori up sono fissati:

| Faccia | Direzione di vista | Up |
| --- | --- | --- |
| +X | ( 1, 0, 0) | (0, 1, 0) |
| -X | (-1, 0, 0) | (0, 1, 0) |
| +Y | ( 0, 1, 0) | (0, 0, -1) |
| -Y | ( 0, -1, 0) | (0, 0, 1) |
| +Z | ( 0, 0, 1) | (0, 1, 0) |
| -Z | ( 0, 0, -1) | (0, 1, 0) |

{{code}}

Una vista sinistrorsa specchia la scena, e questo inverte il winding dei triangoli, quindi usa `setFrontFacing(.clockwise)` mentre disegni le facce. Riuseremo queste funzioni per le [Ombre da luci puntiformi](../advanced-lighting/point-shadows.html) e per l'illuminazione basata su immagini. Sei rendering della scena per frame costano molto; i motori aggiornano queste probe di rado, o una faccia per frame.

## Esercizi

- Disegna lo skybox per primo invece che per ultimo, con la scrittura della profondità spenta, e misura la differenza nel GPU report di Xcode su una scena pesante.
- Mescola riflessione e rifrazione con un fattore che dipende dall'angolo di vista.
