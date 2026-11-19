# Deferred shading

Finora abbiamo usato il **forward rendering**: ogni oggetto viene disegnato e illuminato in un colpo solo, e ogni fragment scorre tutte le luci. Due cose lo rendono uno spreco. I fragment che poi vengono coperti da qualcosa di più vicino sono stati illuminati per niente, e il costo cresce come oggetti × luci.

Il **deferred shading** divide il rendering in due fasi:

1. **Geometry pass**: disegna la scena una volta e salva gli *ingressi* dell'illuminazione, come posizione, normale e albedo, in un gruppo di texture chiamato **G-buffer**.
2. **Lighting pass**: per ogni pixel dello schermo leggi il G-buffer e calcola la luce una volta sola.

Il costo dell'illuminazione diventa pixel × luci e non dipende più dalla complessità della scena. Centinaia di luci diventano praticabili.

## Il G-buffer

| Attachment | Formato | Contenuto |
| --- | --- | --- |
| 0 | `.rgba8Unorm_srgb` | Albedo in rgb, intensità speculare in a |
| 1 | `.rgba16Float` | Normale in spazio mondo |
| 2 | `.rgba16Float` | Posizione in spazio mondo |
| depth | `.depth32Float` | Profondità |

Crea ciascuno come texture con uso `[.renderTarget, .shaderRead]` e collega tutti e tre a un solo render pass. La fragment function del geometry pass li riempie:

{{code}}

Qui non avviene alcun calcolo di luce. Il pass costa poco, e il test di profondità garantisce che in ogni pixel finisca solo la superficie più vicina.

Salvare la posizione costa molta memoria. I renderer da produzione la ricostruiscono dal depth buffer e dall'inversa della matrice view-projection, e comprimono le normali in due canali. Comincia dal layout semplice e ottimizza dopo.

## Il lighting pass

Un triangolo a tutto schermo legge il G-buffer e illumina ogni pixel:

{{code}}

`read` prende il texel esatto di questo pixel, senza sampler. Il controllo su `radius` salta le luci troppo lontane per contare.

## I volumi di luce

Scorrere tutte le luci per ogni pixel spreca ancora lavoro, perché la maggior parte delle luci raggiunge solo una piccola parte dello schermo. Il perfezionamento consiste nel disegnare per ogni luce una **sfera** grande quanto il suo raggio, usando l'instancing. La fragment function di ogni sfera illumina solo i pixel che copre e somma il suo risultato con il blending additivo (`.one`, `.one`). Scarta le facce frontali e disattiva la scrittura della profondità, così la luce funziona anche quando la camera è dentro la sfera. Con i volumi, mille piccole luci costano poco più della loro area complessiva sullo schermo.

Calcola il raggio dall'attenuazione: la distanza a cui il contributo della luce scende sotto una piccola soglia, per esempio 5/256.

## Aggiungere il forward rendering

Il deferred shading non può gestire la trasparenza, perché ogni pixel conserva una sola superficie. La struttura consueta è:

1. Geometry pass, poi lighting pass.
2. Sopra, un pass forward per gli oggetti trasparenti, le lampade e lo skybox.

Il pass forward deve usare lo **stesso depth buffer** del geometry pass, così gli oggetti disegnati in forward vengono nascosti correttamente dietro quelli deferred. Collega la texture di profondità del G-buffer al pass forward con `loadAction = .load`.

## Deferred in un solo pass sulle GPU Apple

L'approccio classico salva in memoria l'intero G-buffer e lo rilegge in un secondo pass. Su una GPU tile-based questo costa caro: ogni tile va scritto fuori e ricaricato. Le GPU Apple offrono di meglio.

Su Apple silicon una fragment function può **leggere il contenuto attuale degli attachment di colore** su cui sta disegnando. Si chiama **programmable blending**, o framebuffer fetch. L'intera pipeline deferred sta allora in **un solo render pass**:

- L'attachment 0 è il colore finale illuminato (il drawable o una texture HDR).
- Gli attachment da 1 a 3 sono il G-buffer, creati con `storageMode = .memoryless`, `loadAction = .clear` e `storeAction = .dontCare`.
- Prima disegni la geometria, scrivendo gli attachment da 1 a 3.
- Poi, **nello stesso encoder**, disegni i volumi di luce con una fragment function che riceve il G-buffer in ingresso:

{{code}}

Il G-buffer non lascia mai la memoria dei tile della GPU. Non consuma memoria di sistema né banda, e questo rende il deferred shading praticabile perfino sui telefoni. Sui Mac Intel la funzione non è disponibile, quindi i renderer portabili tengono come riserva il percorso a due pass; controlla `device.supportsFamily(.apple1)`. Il codice di esempio di Apple "Rendering a Scene with Deferred Lighting" mostra i due percorsi fianco a fianco.

Le GPU Apple supportano anche i **tile shader**, funzioni simili a quelle di compute che girano una volta per tile nel mezzo di un render pass. Si usano per costruire liste di luci per tile nel rendering **tiled forward**, un'alternativa che con molte luci conserva i vantaggi del forward shading, MSAA e trasparenza compresi.

## Compromessi

| | Forward | Deferred |
| --- | --- | --- |
| Molte luci | Costoso | Economico |
| Trasparenza | Funziona | Serve un pass forward |
| MSAA | Funziona | Difficile |
| Varietà di materiali | Qualsiasi shader per oggetto | Limitata dal layout del G-buffer |
| Memoria | Poca | Molta, a meno di usare memoryless |

## Esercizi

- Mostra a schermo ogni texture del G-buffer per verificarne il contenuto.
- Spargi 200 piccole luci colorate e confronta il tempo di frame con il renderer forward.
- Ricostruisci la posizione dalla profondità ed elimina l'attachment della posizione.
