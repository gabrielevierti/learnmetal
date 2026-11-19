# Sistemi di coordinate

Nel suo viaggio verso lo schermo un vertice attraversa diversi sistemi di coordinate. Dividere il viaggio in tappe rende semplice ognuna di esse, e tre matrici portano il vertice da una tappa alla successiva. Alla fine di questo capitolo avremo un vero 3D: una vista prospettica di cubi con texture e con la profondità corretta.

## Gli spazi

1. **Spazio locale** (object space): coordinate relative all'origine dell'oggetto stesso, così come sono salvate nel vertex buffer.
2. **Spazio mondo** (world space): dove l'oggetto si trova nella scena. La **matrice model** porta dal locale al mondo.
3. **Spazio vista** (view space, o spazio camera): il mondo visto dalla camera, con la camera nell'origine. La **matrice view** porta dal mondo alla vista.
4. **Clip space**: l'uscita della vertex function. La **matrice di proiezione** porta dalla vista al clip space.
5. **Normalized device coordinates** (NDC): la GPU divide x, y e z del clip space per w (la **divisione prospettica**).
6. **Coordinate di viewport**: le NDC trasformate in pixel.

Le tappe da 2 a 4 le scrivi tu, in una sola riga dello shader:

{{code}}

## Le convenzioni di Metal

{{figure}}

- In NDC x e y vanno da -1 a 1 con **y verso l'alto**. La **z va da 0 a 1**.
- Le coordinate in pixel e le coordinate di texture partono **in alto a sinistra**, con y verso il basso.

!!! note "Se vieni da OpenGL"
    In OpenGL la z delle NDC va da -1 a 1. Una matrice di proiezione copiata da un tutorial di OpenGL mette metà del tuo intervallo di profondità davanti al near plane, e la geometria vicina alla camera sparisce. Usa sempre una matrice di proiezione costruita per una profondità da 0 a 1, come quella qui sotto.

A Metal non importa se il tuo mondo è sinistrorso o destrorso: lo decidono soltanto le tue matrici. Questa serie usa un mondo **destrorso**, come la maggior parte dei tutorial e dei programmi di modellazione: +x a destra, +y in alto, e la camera guarda lungo **-z**.

## Proiezione prospettica

Una proiezione prospettica rende più piccole le cose lontane. È definita da un campo visivo verticale, dal rapporto d'aspetto della vista e da un near plane e un far plane; insieme delimitano un tronco di piramide chiamato **frustum**. Aggiungi a `Math.swift`:

{{code}}

Il `-1` copia in w la z dello spazio vista cambiata di segno. Dopo la divisione prospettica tutto risulta diviso per la propria distanza dalla camera, che è esattamente ciò che la prospettiva è. Tieni il near plane il più lontano possibile (0.1 è un valore tipico). La precisione della profondità si concentra vicino al near plane, e un valore minuscolo come 0.0001 la spreca quasi tutta.

Una proiezione **ortografica**, che non ha prospettiva, compare nel capitolo [Shadow mapping](../advanced-lighting/shadow-mapping.html).

## Model, view, projection

{{code}}

{{code}}

{{code}}

La matrice view allontana tutto il mondo di 3 unità lungo -z. Spostare indietro il mondo e spostare avanti la camera sono la stessa cosa.

## Un cubo

Un rettangolo piatto è una povera demo 3D. Da adesso usiamo una vera struct per i vertici e generiamo un cubo nel codice. Ogni vertice ha una posizione, una **normale** (la direzione verso cui guarda la superficie, che servirà presto per l'illuminazione) e una coordinata di texture:

{{code}}

Sono 36 vertici per un cubo largo un'unità, ordinati in senso antiorario se visti da fuori. Costruisci il vertex descriptor a partire dalla struct stessa, così gli offset non possono mai essere sbagliati:

{{code}}

Tutti e tre gli attributi usano `bufferIndex` 0, il valore predefinito. Poiché `SIMD3<Float>` occupa 16 byte, gli offset sono 0, 16 e 32 e lo stride è 48. Nello shader:

{{code}}

Disegna con `vertexCount: 36`.

## Il depth buffer

Eseguilo e il cubo sembra rivoltato: le facce disegnate dopo coprono quelle disegnate prima, a prescindere da quale sia più vicina. La soluzione è un **depth buffer**, una texture che per ogni pixel conserva la profondità del fragment più vicino disegnato fino a quel momento. Un nuovo fragment viene tenuto solo se è più vicino.

Per attivarlo servono tre passi.

{{code}}

{{code}}

La texture di profondità viene pulita a 1 (il far plane) all'inizio di ogni pass, e `.less` tiene i fragment con una profondità minore di quella salvata.

## Altri cubi

Per disegnare lo stesso cubo in dieci posti bastano dieci matrici model:

{{code}}

## Esercizi

- Cambia a mano il campo visivo e il rapporto d'aspetto e descrivi l'effetto di ciascuno.
- Fai ruotare nel tempo un cubo ogni tre.
- Imposta `depthCompareFunction` a `.always` e a `.greater` e spiega ciò che vedi.
