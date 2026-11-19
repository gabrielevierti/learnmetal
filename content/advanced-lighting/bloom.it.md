# Bloom

Un monitor non può mostrare una luce abbagliante quanto lo sarebbe nella realtà. Quello che possiamo fare è imitare ciò che le luci forti fanno in una fotocamera o nell'occhio: il loro bagliore sconfina sull'immagine intorno. Questo effetto è il **bloom**, ed è uno dei modi più economici di far sembrare luminosa una scena.

La ricetta ha tre passi:

1. Estrarre in una texture separata le parti luminose della scena HDR.
2. Sfocare quella texture.
3. Sommare il risultato sfocato alla scena, e poi fare il tone mapping.

## Estrarre le zone luminose

Potremmo eseguire un pass sulla texture della scena per scegliere i pixel luminosi. Un modo più pulito è far scrivere alla fragment function della scena **due attachment di colore** insieme, cosa che si chiama multiple render target (MRT):

{{code}}

Una soglia di 1.0 ha senso solo perché la scena è disegnata in HDR: brillano soltanto i pixel più luminosi del bianco dello schermo. Dai al render pass e alla pipeline un secondo attachment:

{{code}}

Ogni pipeline usata in quel pass deve dichiarare entrambi gli attachment. Una fragment function che non deve scrivere in uno dei due, come lo shader della lampada, può lasciarlo fuori dalla sua struct di output; con `writeMask = []` sull'attachment puoi anche disattivare le scritture in modo esplicito.

## Sfocatura gaussiana

Una **sfocatura gaussiana** fa la media di ogni pixel con i suoi vicini, pesati con una curva a campana. Un kernel bidimensionale da 9 × 9 costerebbe 81 letture per pixel. La gaussiana è **separabile**: sfocare in orizzontale e poi in verticale dà lo stesso identico risultato con 9 + 9 letture.

{{code}}

## Ping-pong

Un pass non può leggere dalla texture in cui sta scrivendo, quindi la sfocatura alterna due texture: da A a B in orizzontale, da B ad A in verticale, e di nuovo per una sfocatura più forte.

{{code}}

La load action è `.dontCare` perché il triangolo a tutto schermo sovrascrive comunque ogni pixel. Su una GPU tile-based saltare il caricamento è prestazione gratis.

## Combinare

Il pass finale somma alla scena il bagliore sfocato e poi fa il tone mapping:

{{code}}

Il bloom viene sommato **prima** del tone mapping, così il bagliore viene compresso insieme a tutto il resto.

## Farlo meglio

Dieci pass a piena risoluzione con un kernel piccolo danno un bagliore stretto a un costo alto. Il bloom moderno lavora invece su una **catena di mip**:

1. Riduci ripetutamente la texture luminosa, dimezzandone ogni volta la dimensione, per cinque o sei livelli.
2. Risali, ingrandendo ogni livello con una piccola sfocatura e sommandolo a quello più grande successivo.

Ogni livello contribuisce con un bagliore più ampio, il costo totale è circa un pass e un terzo a piena risoluzione, e il risultato è un alone largo e morbido. È l'approccio usato dalla maggior parte dei motori attuali, e toglie anche la necessità di una soglia netta: mescolare alla scena una piccola frazione della catena sfocata risulta più naturale.

Vale la pena conoscere due scorciatoie specifiche di Metal:

- **Metal Performance Shaders** include filtri di immagine già ottimizzati. `MPSImageGaussianBlur(device:sigma:)` sfoca una texture con una chiamata: `blur.encode(commandBuffer:sourceTexture:destinationTexture:)`.
- Una sfocatura può anche girare come [compute function](../beyond/compute-shaders.html), evitando di preparare dei render pass per elaborare immagini.

## Esercizi

- Cambia il numero di iterazioni della sfocatura e guarda il bagliore allargarsi.
- Esegui la sfocatura a metà risoluzione e confronta la qualità e il tempo di GPU.
- Implementa la catena di riduzione e di ingrandimento.
