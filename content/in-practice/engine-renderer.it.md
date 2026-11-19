# Engine: il renderer

Il [capitolo precedente](game-engine.html) ha mostrato un gioco che non nomina mai un render pass. Questo apre la parte del LearnMetal Engine che li nomina tutti: il renderer. Disegna qualunque cosa ci sia nella scena, in sei passi, e ogni passo è un capitolo che hai già letto.

## Da una scena alle draw call

Una scena è una raccolta di entità; la GPU vuole un elenco di draw call. Il renderer comincia ogni frame percorrendo la scena una volta e copiando ciò che gli serve, un passo spesso chiamato **extraction**. Trova la camera e ne calcola le matrici. Raccoglie le luci. E per ogni entità che ha una mesh registra un elemento: la mesh, il materiale, la matrice di mondo e il bounding box della mesh in spazio mondo.

Poi butta via la maggior parte del lavoro prima di farlo. Gli elementi il cui bounding box sta del tutto fuori dalla vista della camera vengono scartati (**frustum culling**). Quelli opachi rimasti vengono ordinati in modo che gli elementi con lo stesso materiale e la stessa mesh stiano vicini, e ogni sequenza così diventa una sola draw call:

{{code}}

È il capitolo [Instancing](../advanced-metal/instancing.html), applicato in automatico. Il gioco non lo chiede mai: quaranta piastrelle identiche sono quaranta entità, e una draw call. Un oggetto isolato è semplicemente un gruppo di uno, così gli shader hanno un solo percorso di codice:

{{code}}

Gli elementi trasparenti sono l'eccezione. Vengono ordinati invece dal più lontano al più vicino, perché il [blending](../advanced-metal/blending.html) dipende dall'ordine.

## Memoria che dura un frame

Matrici delle istanze, uniform della camera, i vertici dell'interfaccia, le particelle: una gran quantità di dati viene ricostruita a ogni frame e dopo non serve più. Creare un buffer Metal per ogni pezzo sarebbe lento, e riusare un solo buffer è pericoloso, perché di solito la GPU sta ancora disegnando il frame precedente quando la CPU comincia a riempire il successivo.

L'engine usa un grande buffer per frame e ne distribuisce i pezzi in ordine. Allocare significa sommare a un offset:

{{code}}

Di questi buffer ce ne sono tre, usati a turno, e un semaforo che parte da tre. Un frame prende un'unità prima di toccare qualsiasi cosa e la restituisce quando la GPU comunica che il frame è finito:

{{code}}

Quando un buffer torna di turno, il frame che lo aveva usato è sicuramente concluso.

## Pipeline a richiesta

Un render pipeline state fissa le funzioni di vertice e di fragment, i formati dei pixel, il numero di campioni e il blending. Le combinazioni si moltiplicano in fretta: lo stesso shader delle mesh viene usato con un target di colore, senza per le ombre, con e senza blending. Elencare a mano ogni combinazione è il tipo di codice a cui manca sempre una voce.

Invece ogni draw call descrive ciò che le serve, e una cache crea la pipeline la prima volta che quella descrizione compare:

{{code}}

Il primo frame crea le pipeline che servono alla scena ed è un po' più lento; dopo, la cache risponde da una tabella.

La cache ha un secondo uso. L'engine compila i suoi shader dai file `.metal` all'avvio, e ogni trenta frame controlla se uno di essi è cambiato su disco. In quel caso li ricompila e svuota la cache. Salva uno shader mentre il gioco gira e l'immagine cambia; se la nuova versione ha un errore, il messaggio viene scritto nel log e restano i vecchi shader.

## I pass

| | Pass | Disegna in |
| --- | --- | --- |
| 1 | Shadow map | uno slice di una texture array di profondità per ogni cascata |
| 2 | Depth pre-pass | profondità e normali in spazio vista |
| 3 | Ambient occlusion, poi una sfocatura | una texture a un canale |
| 4 | Scena | una texture HDR multisample |
| 5 | Bloom | una catena di texture ognuna grande la metà |
| 6 | Tone mapping e interfaccia | il drawable |

## Ombre a cascata

Il capitolo [Shadow mapping](../advanced-lighting/shadow-mapping.html) usava una sola shadow map per una scena piccola. Stendi una mappa su tutto ciò che una camera può vedere e i suoi texel diventano troppo grandi per disegnare un bordo netto. La risposta consueta è tagliare a fette la distanza di vista e dare a ogni fetta la sua mappa: piccola e nitida vicino alla camera, grande e morbida lontano. Sono le **cascate**, e l'engine ne usa quattro.

Adattare una mappa a una fetta ha una sottigliezza. L'adattamento ovvio, una scatola intorno agli angoli della fetta, cambia forma ogni volta che la camera gira, e i bordi delle ombre strisciano. A una sfera intorno alla fetta non importa da che parte guarda la camera. Agganciare il suo centro a texel interi toglie lo sfarfallio che resta quando la camera si muove:

{{code}}

Nella fragment function un pixel sceglie la sua cascata in base alla distanza dalla camera, e legge la shadow map da un punto spinto appena fuori dalla superficie:

{{code}}

Spostare il punto di lettura lungo la normale, invece di sommare un grande bias alla profondità, è ciò che tiene le ombre attaccate agli oggetti che le proiettano. Nove letture di confronto intorno a `uv` ammorbidiscono poi il bordo, come nel capitolo originale.

Ai materiali con i buchi serve una cosa in più. Una recinzione disegnata con una texture ritagliata deve proiettare un'ombra con i buchi, quindi per quei materiali il pass delle ombre esegue una minuscola fragment function il cui unico compito è chiamare `discard_fragment()` dove la texture è trasparente.

## Ambient occlusion

L'[SSAO](../advanced-lighting/ssao.html) ha bisogno della profondità e della normale di ogni pixel prima che la scena venga illuminata. In un renderer deferred ci sono già. In un renderer forward vanno disegnate prima, quindi il pass 2 disegna tutta la geometria opaca in una texture di profondità e in una di normali, e il pass 3 le trasforma in un valore di occlusione per pixel e lo sfoca. Il pass principale legge poi quella texture in base alla posizione del pixel.

Il prezzo è un altro giro sulla geometria opaca. Si può spegnere con una sola impostazione, e allora i pass 2 e 3 non vengono eseguiti affatto.

## Il pass principale

La scena viene disegnata in HDR (`rgba16Float`), con quattro campioni per pixel:

{{code}}

Dopo il pass non servono né la texture di colore multisample né quella di profondità. Sulle GPU Apple l'engine le crea entrambe **memoryless**: esistono solo nella memoria dei tile della GPU mentre il pass è in esecuzione, come spiega il capitolo [GPU tile-based](../apple-platforms/tile-based-gpus.html), e un target HDR multisample 4x che sarebbe costato decine di megabyte non costa niente.

Dentro il pass l'ordine conta:

1. **Gli oggetti opachi**, scrivendo la profondità.
2. **Il cielo**, un solo triangolo messo esattamente sul far plane e disegnato con un test di profondità "minore o uguale". La sua fragment function gira solo sui pixel che nient'altro ha coperto. Disegnarlo per primo vorrebbe dire calcolare tutto lo schermo e poi coprirne la maggior parte.
3. **Gli oggetti trasparenti**, dal più lontano al più vicino, con il test di profondità ma senza scriverla.
4. **Le particelle** e le **linee di debug**.

La fragment function è quella dei capitoli sul [PBR](../pbr/lighting.html), con un ciclo sulle luci. È forward rendering: una funzione calcola un pixel per intero. Si adatta bene alle GPU Apple, perché trovano la superficie visibile di ogni pixel prima di eseguire qualsiasi fragment function, quindi le superfici nascoste non costano nulla; e funziona con il multisampling e con la trasparenza senza casi speciali.

## La luce del cielo

Il cielo non è una texture. È qualche riga di shader: una sfumatura dall'orizzonte allo zenit, il suolo sotto, un alone intorno al sole. All'avvio l'engine disegna quel cielo in una cubemap, una faccia alla volta, e poi filtra la cubemap nelle mappe di cui ha bisogno l'[illuminazione basata su immagini](../pbr/diffuse-irradiance.html):

{{code}}

Ogni chiamata è un piccolo render pass in una faccia e in un livello di mip di una cubemap. Poiché l'illuminazione viene calcolata dalla stessa funzione che disegna il cielo visibile, i riflessi e la luce d'ambiente sono sempre d'accordo con ciò che il giocatore vede. Cambia i colori del cielo o gira il sole, e l'engine se ne accorge ed esegue di nuovo questi pass.

## Il bloom e il pass finale

Il [bloom](../advanced-lighting/bloom.html) tiene le parti dell'immagine più luminose di una soglia e le sfoca attraverso una catena di texture, ognuna grande la metà della precedente: giù lungo la catena, poi di nuovo su, sommando ogni livello a quello più grande. Bagliori ampi e stretti si accumulano, al prezzo di pochi pass molto piccoli.

L'ultimo pass somma il bloom alla scena, applica l'esposizione e la curva di [tone mapping](../advanced-lighting/hdr.html) e scrive nel drawable, il cui formato sRGB si occupa della [gamma](../advanced-lighting/gamma-correction.html). L'interfaccia 2D viene disegnata nello stesso pass, dopo il tone mapping: l'arancione di un titolo deve essere l'arancione scelto dal designer, non ciò che ne fa una curva filmica.

## Vedere che cosa fa

Ogni pass ha un'etichetta e il pass principale è diviso in gruppi di debug, quindi un frame catturato nel GPU debugger di Xcode si legge come la tabella qui sopra. Non costa nulla e fa risparmiare ore, come sosteneva il capitolo [Debug](debugging.html).

Per tutto il resto c'è `engine.debug`, che disegna linee in 3D per un frame: una linea, una scatola, una sfera, gli assi di una trasformazione. F2 lo usa per mostrare ogni collider della scena.

Il [prossimo capitolo](engine-gameplay.html) lascia il renderer e costruisce il gioco.
