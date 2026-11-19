# Tassellazione

Le superfici dettagliate hanno bisogno di molti triangoli, ma solo dove chi guarda può vedere il dettaglio. Una montagna a un chilometro di distanza non richiede la densità di triangoli del terreno sotto i tuoi piedi. La **tassellazione** permette alla GPU di suddividere al volo una geometria grossolana, finemente quanto chiedi, così una mesh può essere salvata e animata a bassa risoluzione e disegnata ad alta risoluzione.

## Patch

Con la tassellazione non invii più triangoli. Invii **patch**: triangoli o quadrilateri definiti da **punti di controllo**. Per ogni patch fornisci dei **fattori di tassellazione** che dicono quanto finemente suddividerla. Il tessellator della GPU genera i nuovi vertici, e una vertex function speciale calcola la posizione finale di ciascuno.

L'impostazione di Metal è diversa da quella di altre API. Non ci sono stadi separati di hull shader e domain shader. Invece:

1. Un **compute kernel**, o la CPU, scrive i fattori di tassellazione in un buffer.
2. Il tessellator suddivide ogni patch secondo i suoi fattori.
3. Una **post-tessellation vertex function** gira una volta per ogni vertice generato.

## I fattori di tassellazione

Una patch quadrilatera ha quattro **fattori di bordo** e due **fattori interni**. Una patch triangolare ne ha tre e uno. Un fattore di 1 significa nessuna suddivisione; 16 significa che il bordo viene diviso in 16 segmenti. I fattori di bordo sono separati da quelli interni perché due patch vicine possano accordarsi sul bordo in comune e non lasciare crepe, anche quando i loro interni sono suddivisi in modo diverso.

Un kernel che imposta lo stesso fattore per ogni patch:

{{code}}

`MTLQuadTessellationFactorsHalf` è una struct predefinita di sei half float, 12 byte per patch:

{{code}}

In un renderer vero il kernel calcola il fattore di ogni bordo dalla sua distanza dalla camera o dalla sua lunghezza sullo schermo. È la **tassellazione adattiva**. Calcola un fattore per ogni *bordo* dal punto medio di quel bordo, così entrambe le patch che lo condividono ottengono lo stesso valore.

## La pipeline

I punti di controllo stanno in un normale vertex buffer. Il vertex descriptor dice che i dati avanzano per punto di controllo:

{{code}}

Il **partition mode** controlla come vengono divisi i bordi. `.integer` e `.pow2` si agganciano a numeri interi, cosa che provoca scatti visibili quando i fattori cambiano. I modi frazionari aggiungono i nuovi vertici gradualmente, così il dettaglio cresce con dolcezza mentre la camera si avvicina. Il fattore massimo è 16 sui dispositivi iOS più vecchi e 64 sui Mac e sulle GPU Apple recenti.

## La post-tessellation vertex function

{{code}}

- `[[patch(quad, 4)]]` dichiara una patch quadrilatera con quattro punti di controllo.
- `[[position_in_patch]]` è il punto in cui il vertice generato si trova dentro la patch: un `float2` da 0 a 1 per i quadrilateri, e un `float3` di pesi baricentrici per i triangoli.
- Le vertex function non possono calcolare i livelli di mip in automatico, quindi le letture di texture indicano il livello.

È la funzione a decidere che cosa la patch *significa*. Qui è un rettangolo piatto spostato da una height map. Interpreta sedici punti di controllo come una patch di Bézier bicubica e ottieni superfici curve e lisce a partire da una gabbia grossolana.

## Disegnare

{{code}}

Le texture e i sampler dello stadio di vertice hanno le loro chiamate di binding, `setVertexTexture` e `setVertexSamplerState`.

## Le normali delle superfici spostate

Lo spostamento cambia la superficie, quindi le normali originali sono sbagliate. Per una height map calcola la normale dalle altezze vicine, nella vertex function o per fragment:

{{code}}

## Usi

- **Terreno** con livello di dettaglio continuo.
- **Displacement mapping**: vero dettaglio geometrico con profili e ombre corretti, dove il [parallax mapping](../advanced-lighting/parallax-mapping.html) si limita a fingerlo.
- **Superfici lisce**: subdivision surface e patch di Bézier per personaggi e veicoli.

Sull'hardware recente i mesh shader offrono un'altra strada verso gli stessi obiettivi, con più controllo. La tassellazione resta il modo più semplice di ottenere dettaglio adattivo ed è supportata da ogni GPU Apple.

## Esercizi

- Anima il livello di tassellazione e guarda il wireframe infittirsi.
- Calcola nel kernel i fattori per bordo dalla distanza dalla camera.
- Confronta `.integer` e `.fractionalEven` mentre muovi la camera.
