# Metal 4

Metal 4, presentato nel 2025, è la prima grande revisione dell'API di base di Metal. Niente di ciò che hai imparato è superato: shader, pipeline, texture, render pass e struttura del frame sono le stesse idee. Ciò che cambia è chi è responsabile di che cosa. Metal 4 fa meno cose alle tue spalle, così un renderer grande spende meno tempo di CPU e meno memoria, e i motori scritti per Direct3D 12 o Vulkan vi corrispondono direttamente.

Gira su Apple silicon: Mac con M1 o successivo e iPhone e iPad con A14 o successivo, sui sistemi del 2025 (macOS 26, iOS 26) e più recenti. Fai il controllo a runtime, e tieni come riserva il percorso classico.

!!! warning "Leggilo come una mappa"
    Questo capitolo spiega il modello e mostra la forma del codice. I nomi seguono la documentazione di Apple al momento della stesura, e questa parte di Metal è giovane. Per un lavoro vero parti dall'esempio di Apple *Drawing a triangle with Metal 4*.

## Fianco a fianco con il Metal che conosci

I nuovi tipi hanno il prefisso `MTL4` e vivono accanto ai vecchi. Il device, le texture, i buffer, le library e i render pipeline state sono condivisi.

| Metal | Metal 4 |
|---|---|
| `MTLCommandQueue` | `MTL4CommandQueue` |
| `MTLCommandBuffer`, creato dalla coda, usato una volta | `MTL4CommandBuffer`, creato dal device, riusato |
| memoria gestita da Metal | `MTL4CommandAllocator` |
| `MTLRenderCommandEncoder` | `MTL4RenderCommandEncoder` |
| encoder di compute, di blit e di acceleration structure | `MTL4ComputeCommandEncoder` |
| `setVertexBuffer`, `setFragmentTexture`, ... | `MTL4ArgumentTable` |
| retain automatico e hazard tracking | residency set e barrier |
| `device.makeRenderPipelineState` | `MTL4Compiler` |

Puoi adottarlo per gradi: una parte di un renderer può inviare a una `MTL4CommandQueue` mentre il resto tiene la sua `MTLCommandQueue`, con degli eventi per ordinare il lavoro tra le due.

## Command buffer e allocator

Un command buffer di Metal 4 è un oggetto che vive a lungo. Lo cominci con un **allocator**, che fornisce la memoria in cui vengono scritti i comandi codificati, lo chiudi e ne fai il commit a una coda. Poi lo cominci di nuovo. Tieni un allocator per ogni frame in lavorazione e azzeralo quando torni a usarlo.

{{code}}

{{code}}

Il descriptor del pass è un `MTL4RenderPassDescriptor`; `MTKView` ne offre uno attraverso `currentMTL4RenderPassDescriptor`. Poiché il commit prende un array, più thread possono codificare ciascuno nel proprio command buffer, con il proprio allocator, e i buffer vengono inviati insieme. Un render pass può perfino essere sospeso alla fine di un encoder e ripreso nel successivo, cosa che sostituisce il parallel render encoder.

## Argument table

Nel Metal classico ogni encoder tiene una tabella di binding per ogni stadio, e tu la riempi con `setVertexBuffer`, `setFragmentTexture` e simili. In Metal 4 la tabella è un oggetto a sé. La dimensioni per ciò che i tuoi shader usano, la riempi e la colleghi agli stadi che ne hanno bisogno. La stessa tabella può servire molti encoder e molti frame.

{{code}}

{{code}}

Un binding è un indirizzo o un ID di risorsa, non un oggetto, e un offset è semplice aritmetica sull'indirizzo. Lo shader non cambia: `[[buffer(1)]]` significa ancora slot 1. Questo si sposa in modo naturale con gli argument buffer del capitolo [MSL avanzato](../advanced-metal/advanced-msl.html): metti le texture di un'intera scena in un buffer, e collega quel solo buffer.

## Residency set

I command buffer classici trattengono ogni risorsa che usano e si assicurano che sia disponibile per la GPU. Metal 4 non fa né l'una né l'altra cosa. Le risorse le tieni in vita tu, e dici a Metal di quali ha bisogno la GPU con un **residency set**.

{{code}}

Costruisci il set quando carichi un livello, non a ogni frame. Una risorsa che manca da tutti i set è l'errore classico di Metal 4, e il risultato è indefinito: un oggetto nero, o spazzatura.

## Barrier

Metal 4 non tiene traccia di quale pass scrive una risorsa e quale la legge. Dentro un command buffer gli stadi di pass diversi possono sovrapporsi. Dove uno stadio successivo legge ciò che uno precedente ha scritto, per esempio una fragment function che legge una texture appena riempita da un compute pass, aggiungi una **barrier** sull'encoder che consuma: nomina gli stadi che devono finire e quelli che devono aspettare. Disegnare in una texture in un pass e leggerla nel successivo è il caso di tutti i giorni. Il livello di validazione di Metal segnala le barrier mancanti, quindi tienilo acceso durante il porting.

## Compilare le pipeline

I pipeline state vengono creati da un oggetto compilatore che possiedi tu, a partire da descriptor che nominano le funzioni senza caricarle prima.

{{code}}

Il risultato è un normale `MTLRenderPipelineState`. Tre aggiunte rendono la compilazione degli shader più facile da controllare: varianti asincrone che restituiscono un task a cui puoi dare una priorità; i **flexible pipeline state**, in cui una pipeline compilata viene specializzata a basso costo per impostazioni diverse di blending e di attachment; e la compilazione anticipata, in cui le pipeline raccolte in una sessione di gioco vengono compilate al momento della build in un archivio, così i giocatori non aspettano mai uno shader.

## Che cos'altro è arrivato

- **Un solo compute encoder** per i kernel, i blit e la costruzione delle acceleration structure.
- **Machine learning nel frame**: un `MTL4MachineLearningCommandEncoder` esegue una rete Core ML sulla linea del tempo della GPU, e l'API Shader ML valuta piccole reti dentro una fragment function, per materiali neurali o upscaling appreso.
- **Texture view pool** e risorse **placement sparse** per lo streaming di mondi grandi.
- **Interpolazione di frame e denoising di MetalFX**, descritti nel capitolo precedente.
- La tassellazione non fa parte dell'encoder di Metal 4; usa i [mesh shader](../beyond/mesh-shaders.html).

## Conviene usarlo?

Per imparare, e per un'app con qualche centinaio di draw call, il Metal classico è più semplice ed esattamente altrettanto veloce sulla GPU. A quella scala i suoi retain, il tracking e la residency automatici costano poco ed evitano un'intera classe di bug. Metal 4 ripaga quando conta il costo di CPU della codifica: migliaia di draw call, molti thread, grandi scene in streaming, o un motore che ragiona già in termini di descriptor table e barrier. Ogni concetto di questo libro resta valido tale e quale, ed è la ragione per impararli prima.

## Esercizi

- Elenca ciò che `setFragmentTexture` faceva per te e che una argument table non fa.
- Porta a Metal 4 il renderer del primo triangolo, partendo dal progetto di esempio di Apple.
