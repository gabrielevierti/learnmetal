# Ray tracing

La rasterizzazione risponde molto in fretta a una domanda: quale triangolo copre questo pixel? Tutto il resto, comprese ombre, riflessi e ambient occlusion, è stato finora un'approssimazione costruita sopra: shadow map, environment map, trucchi in screen space. Ognuna da qualche parte cede.

Il **ray tracing** risponde a una domanda più generale: che cosa colpisce per primo un raggio che parte *da qui* e va *da quella parte*? Con questa sola operazione ombre, riflessi e occlusione diventano esatti e quasi banali da esprimere. Metal ha un'API di ray tracing che gira su tutto Apple silicon, con accelerazione hardware sui chip recenti.

Questo capitolo è un'introduzione. Lo scopo è capire i pezzi e tracciare i tuoi primi raggi, poi aggiungere ombre in ray tracing al renderer rasterizzato che hai già.

## Acceleration structure

Confrontare un raggio con ogni triangolo di una scena è senza speranza. Una **acceleration structure** organizza i triangoli in un albero di bounding box, così un raggio può saltarne quasi tutti. Metal costruisce e attraversa questa struttura per te.

I livelli sono due:

- Una **primitive acceleration structure** contiene i triangoli di una mesh.
- Una **instance acceleration structure** contiene molte istanze di strutture primitive, ognuna con la sua trasformazione. Muovere un oggetto significa aggiornare una matrice e riadattare il livello superiore, non ricostruire la mesh.

Prima controlla il supporto:

{{code}}

## Costruire una struttura primitiva

Descrivi la geometria usando i vertex buffer e gli index buffer che hai già:

{{code}}

La costruzione avviene sulla GPU, attraverso un encoder dedicato:

{{code}}

Costruisci la geometria statica una volta sola, al caricamento. Lo stesso encoder può **compattare** una struttura per risparmiare memoria e **riadattarla** dopo che i vertici si sono mossi.

## Intersecare i raggi in uno shader

In Metal il ray tracing non è una pipeline separata. Qualsiasi shader, che sia un kernel o una fragment function, può ricevere una acceleration structure e lanciarvi dei raggi.

{{code}}

{{code}}

Il risultato dell'intersezione ti dice la distanza dal punto colpito, quale primitiva e quale geometria sono state colpite e le coordinate baricentriche del punto dentro il triangolo. Con l'indice della primitiva cerchi i vertici del triangolo nei tuoi buffer e interpoli normali e coordinate di texture. Metal può anche conservare dentro la struttura piccoli dati per primitiva, per rendere più economica questa ricerca.

Esegui questo kernel, mostra la texture di uscita con il triangolo a tutto schermo, e hai un'immagine in ray tracing della tua mesh senza alcuna rasterizzazione.

## Rendering ibrido: ombre in ray tracing

Un path tracer completo è un progetto a sé. L'uso più pratico del ray tracing è quello **ibrido**: rasterizza la scena come prima e usa i raggi solo per gli effetti che la rasterizzazione fa male.

Le ombre sono il guadagno più facile. Nella fragment function di illuminazione lancia un raggio dalla superficie verso la luce. Se colpisce qualcosa, il punto è in ombra:

{{code}}

{{code}}

Confronta con [Shadow mapping](../advanced-lighting/shadow-mapping.html) e [Ombre da luci puntiformi](../advanced-lighting/point-shadows.html): nessun pass in più, nessuna texture di ombre, nessun bias da regolare, nessun limite di risoluzione, e funziona con qualsiasi tipo di luce. `accept_any_intersection(true)` permette all'attraversamento di fermarsi al primo punto colpito, e questo rende economici i raggi d'ombra.

Lo stesso schema dà:

- **Riflessi**: traccia lungo `reflect(-V, N)` e calcola il colore del punto colpito.
- **Ambient occlusion**: traccia alcuni raggi corti nell'emisfero sopra la superficie e conta quelli che colpiscono qualcosa. È occlusione vera, e sostituisce l'[SSAO](../advanced-lighting/ssao.html).
- **Ombre morbide**: punta i raggi verso punti casuali di una luce ad area e fai la media su più frame.

## Rumore e denoising

Un raggio per pixel dà ombre nette e riflessi a specchio. Gli effetti morbidi richiedono molti raggi in direzioni casuali, e un budget in tempo reale ne permette solo pochi per pixel. Il risultato è rumoroso. Il rimedio consueto è **accumulare** i risultati su più frame e fare **denoising**. Metal Performance Shaders include `MPSSVGFDenoiser`, e sui sistemi recenti MetalFX offre un upscaling con denoising.

## Per andare oltre

- Le **instance acceleration structure** per le scene con molti oggetti in movimento (`MTLInstanceAccelerationStructureDescriptor`).
- Le **intersection function** per primitive personalizzate come sfere e curve, e per la geometria con alpha test come il fogliame.
- Il **path tracing**: seguire i raggi per più rimbalzi e calcolare l'illuminazione globale. Il codice di esempio di Apple "Accelerating ray tracing using Metal" è un path tracer compatto e leggibile, ed è il passo successivo naturale.

## La fine, e l'inizio

Questo è l'ultimo capitolo. Sei partito da una vista vuota e ora hai il vocabolario per leggere qualsiasi esempio di Metal, il sorgente di un motore o un articolo di grafica. Scegli qualcosa che vuoi vedere a schermo e costruiscilo. Leggi il codice di esempio di Apple, guarda le sessioni su Metal della WWDC e tieni aperto il frame debugger. C'è sempre un'altra tecnica da imparare, e adesso hai le basi per impararla.
