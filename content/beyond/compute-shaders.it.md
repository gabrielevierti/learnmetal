# Compute shader

Una GPU è un computer massicciamente parallelo che, guarda caso, è bravo a disegnare triangoli. Le **compute function**, che in Metal si chiamano kernel, ti permettono di usare quella potenza per qualsiasi cosa: elaborazione di immagini, fisica, sistemi particellari, simulazioni, culling, machine learning. Girano fuori dalla pipeline di rendering, senza vertici né fragment, solo dati in ingresso e dati in uscita.

In Metal il compute non è un'aggiunta. Usa lo stesso device, gli stessi command buffer, buffer, texture e linguaggio di shading del rendering, quindi i risultati passano dall'uno all'altro senza alcuna copia.

## Un primo kernel: elaborare un'immagine

Un kernel è una funzione marcata `kernel` che restituisce `void`. Viene eseguita una volta per ogni punto di una griglia che definisci tu. Per un'immagine la griglia sono i pixel:

{{code}}

- Le texture dichiarano come vi si accede: `access::read`, `access::write` o `access::read_write`. Una texture in cui un kernel scrive deve essere creata con l'uso `.shaderWrite`.
- `[[thread_position_in_grid]]` è la coordinata di questa esecuzione, qui il pixel.
- Non c'è sampler: `read` e `write` indirizzano texel esatti. Puoi comunque passare un sampler e chiamare `sample` con coordinate normalizzate quando vuoi il filtro.

## Eseguirlo

{{code}}

{{code}}

Un compute encoder vive in un command buffer accanto ai render encoder. Un frame tipico può eseguire un compute pass per aggiornare le particelle e poi un render pass che le disegna, in un unico command buffer.

## Thread e threadgroup

La GPU esegue la griglia a lotti chiamati **threadgroup**. I thread di uno stesso gruppo girano insieme e possono condividere una piccola quantità di memoria veloce.

`dispatchThreads` prende la dimensione totale della griglia e la dimensione di un threadgroup, e Metal gestisce le griglie che non sono un multiplo esatto della dimensione del gruppo. Richiede il supporto ai threadgroup non uniformi, che ogni dispositivo Apple silicon ha. Il più vecchio `dispatchThreadgroups` prende invece un numero di *gruppi*, quindi la griglia viene arrotondata per eccesso e il kernel deve controllare da solo le coordinate fuori intervallo:

{{code}}

Le dimensioni usate sopra, larghe quanto `threadExecutionWidth` e alte quanto il massimo consente, sono una buona scelta predefinita per il lavoro in 2D.

## Un sistema particellare

Nei kernel i buffer funzionano come le texture. Qui ogni particella viene mossa da un thread:

{{code}}

Il buffer sta nello spazio di indirizzamento `device` perché il kernel ci scrive. La griglia è a una dimensione:

{{code}}

Poi collega lo stesso buffer a una vertex function di billboard con instancing, come quella di [Vivere senza geometry shader](../advanced-metal/no-geometry-shaders.html), con la sua struct `Particle` modificata perché corrisponda a questa, e disegna. I dati delle particelle non lasciano mai la GPU, e un milione di particelle si anima senza fatica.

!!! warning "Data race"
    I thread girano in parallelo senza un ordine garantito. Ogni thread deve scrivere solo nel proprio elemento. Se un thread legge dati che un altro scrive, come in una sfocatura che legge i vicini, usa risorse separate per ingresso e uscita e scambiale dopo ogni passo. Per i contatori condivisi MSL offre tipi atomici come `atomic_uint`.

## Dove si usa il compute in un renderer

- **Post-processing**: sfocatura, bloom, tone mapping, profondità di campo. Un kernel evita il triangolo a tutto schermo e può leggere e scrivere qualsiasi pixel.
- **Culling**: confronta l'ingombro degli oggetti con il frustum della vista e scrivi un elenco di istanze visibili o un indirect command buffer.
- **Assegnazione delle luci**: costruisci liste di luci per tile o per cluster, per il forward rendering con molte luci.
- **Precalcolo**: la irradiance map e la mappa prefiltrata dei [capitoli sull'IBL](../pbr/diffuse-irradiance.html) si possono generare con kernel che scrivono direttamente nelle facce del cubo.
- **Simulazione**: stoffa, fluidi, stormi.
- **Generazione di mesh**: terreno, marching cubes, skinning.

## Compute o fragment?

Una fragment function a tutto schermo e un kernel possono spesso fare lo stesso lavoro. Le fragment function traggono vantaggio dall'architettura tile-based quando scrivono negli attachment di un render pass, soprattutto in quelli memoryless. I kernel sono più flessibili: letture e scritture arbitrarie, più uscite di dimensioni diverse, memoria condivisa nel threadgroup. Sulle GPU Apple preferisci una fragment function quando il risultato va dritto nel render pass corrente, e un kernel negli altri casi. Quando conta, misura.

## Kernel già pronti

**Metal Performance Shaders** (MPS) è una libreria di kernel ottimizzati: sfocatura gaussiana, convoluzione, istogramma, ridimensionamento di immagini, prodotto di matrici e altro. Per le operazioni standard sulle immagini usala prima di scriverne di tuoi:

{{code}}

## Esercizi

- Scrivi un kernel che inverte un'immagine e mostra il risultato.
- Porta in un kernel la sfocatura a scatola del capitolo sull'SSAO.
- Aggiungi alla simulazione delle particelle un punto attrattore che le tira verso il mouse.
