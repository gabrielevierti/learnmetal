# MSL avanzato

Questo capitolo raccoglie funzioni del Metal Shading Language che non hanno un capitolo tutto loro ma che vale la pena conoscere. Niente di ciò che segue è una lettura obbligata; scorrilo adesso e torna quando te ne serve un pezzo.

## Input e output predefiniti

Gli attributi tra doppie parentesi quadre collegano le variabili ai valori forniti dalla pipeline.

**Input della vertex function**

| Attributo | Tipo | Significato |
| --- | --- | --- |
| `[[vertex_id]]` | `uint` | Indice del vertice in elaborazione. |
| `[[instance_id]]` | `uint` | Indice dell'istanza. Vedi [Instancing](instancing.html). |
| `[[base_vertex]]`, `[[base_instance]]` | `uint` | Offset indicati nella draw call. |

**Output della vertex function**

| Attributo | Tipo | Significato |
| --- | --- | --- |
| `[[position]]` | `float4` | Posizione in clip space. Obbligatorio. |
| `[[point_size]]` | `float` | Dimensione in pixel quando si disegnano primitive `.point`. |
| `[[clip_distance]]` | `float` o array | Piani di ritaglio personalizzati. |
| `[[render_target_array_index]]` | `uint` | Strato o faccia del cubo in cui disegnare. |

**Input della fragment function**

| Attributo | Tipo | Significato |
| --- | --- | --- |
| `[[position]]` | `float4` | Coordinate del pixel (x, y), profondità (z) e 1/w. |
| `[[front_facing]]` | `bool` | Se il triangolo è rivolto verso la camera. |
| `[[point_coord]]` | `float2` | Posizione dentro una primitiva punto, da 0 a 1. |
| `[[sample_id]]`, `[[sample_mask]]` | `uint` | Dettagli del multisampling. |
| `[[color(n)]]` | `float4` | Valore attuale dell'attachment di colore n (GPU Apple). |

**Output della fragment function**

| Attributo | Tipo | Significato |
| --- | --- | --- |
| `[[color(n)]]` | `float4` ecc. | Valore per l'attachment di colore n. |
| `[[depth(any)]]` | `float` | Sostituisce la profondità del fragment. Esistono anche `greater` e `less`. |
| `[[sample_mask]]` | `uint` | Quali campioni scrivere. |

Una fragment function con più output restituisce una struct:

{{code}}

## Controllare l'interpolazione

I membri dell'output del vertice vengono interpolati, in modo predefinito, con la correzione prospettica. Puoi cambiarlo membro per membro:

{{code}}

`[[flat]]` è obbligatorio per i membri interi, come un indice di materiale passato alla fragment function.

## Spazi di indirizzamento

Ogni parametro puntatore o riferimento deve dire dove vive la sua memoria:

- `constant`: dati di buffer in sola lettura. Usalo per gli uniform.
- `device`: dati di buffer in lettura e scrittura. Usalo per gli array grandi e per tutto ciò che una compute function scrive.

{{code}}

Questo esempio mostra anche che un vertex descriptor è facoltativo. Una vertex function può andarsi a prendere i dati da un buffer con un indice, cosa che a volte si chiama **vertex pulling**. Il layout della struct deve allora coincidere esattamente con i byte del buffer, usando `packed_float3` dove i dati sono compatti.

## Function constant

Un valore marcato come **function constant** viene fissato quando la funzione viene specializzata, prima che il pipeline state sia creato. Il compilatore può allora eliminare del tutto i rami morti:

{{code}}

{{code}}

È la risposta di Metal alle varianti di shader fatte con `#ifdef`: una sola funzione nel sorgente, molti pipeline state specializzati.

## Argument buffer

Collegare dieci texture e tre buffer una chiamata alla volta è lento quando le draw call sono migliaia. Un **argument buffer** è una struct di risorse salvata in un buffer e collegata con una sola chiamata:

{{code}}

Dal lato Swift un `MTLArgumentEncoder`, creato dalla funzione con `makeArgumentEncoder(bufferIndex:)`, scrive le risorse nel buffer. Le versioni più recenti del sistema permettono di scrivere direttamente nel buffer gli ID delle risorse. Devi anche dire all'encoder quali risorse il buffer usa, con `useResource(_:usage:stages:)`, così Metal le può tenere sotto controllo. Gli argument buffer possono contenere array di texture, ed è il fondamento del rendering "bindless" e del ray tracing, dove qualsiasi raggio può colpire qualsiasi materiale.

## Sampler definiti nello shader

Un sampler non deve per forza arrivare da Swift. Si può dichiarare come costante:

{{code}}

È comodo negli shader di post-processing, dove le impostazioni non cambiano mai.

## Funzioni delle texture

| Chiamata | Scopo |
| --- | --- |
| `tex.sample(s, uv)` | Lettura filtrata. |
| `tex.sample(s, uv, level(2))` | Legge un livello di mip preciso. |
| `tex.sample(s, uv, bias(1))` | Sposta il livello di mip automatico. |
| `tex.sample(s, uv, gradient2d(dx, dy))` | Fornisci tu le derivate. |
| `tex.read(uint2(x, y), lod)` | Il texel esatto, senza sampler. |
| `tex.gather(s, uv)` | I quattro texel vicini di un canale. |
| `tex.get_width()`, `tex.get_height()`, `tex.get_num_mip_levels()` | Interrogazioni. |
| `depthTex.sample_compare(s, uv, ref)` | Confronto di profondità con filtro, per le ombre. |

## Precisione: half

`half` è un float a 16 bit. Sulle GPU mobili i calcoli a mezza precisione sono più veloci e consumano meno, e la precisione basta per i colori e le direzioni normalizzate. Usa `float` per le posizioni, per le coordinate di texture su texture grandi e per la profondità. I letterali prendono il suffisso `h`: `half3(0.5h)`.

## Derivate

`dfdx(v)` e `dfdy(v)` restituiscono quanto in fretta un valore cambia tra pixel vicini, e `fwidth(v)` è la somma dei loro valori assoluti. Sono gli strumenti per i motivi procedurali senza aliasing e per calcolare la normale piatta di una faccia senza normali nei vertici:

{{code}}

A seconda che il tuo mondo sia destrorso o sinistrorso e del winding, il risultato può richiedere un cambio di segno.
