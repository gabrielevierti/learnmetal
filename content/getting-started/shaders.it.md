# Shader

Gli shader sono il posto in cui la programmazione grafica avviene davvero. Questo capitolo guarda più da vicino il Metal Shading Language e mostra i due modi in cui i dati arrivano a uno shader: gli attributi per vertice, che vengono interpolati lungo il triangolo, e gli uniform, che restano uguali per un'intera draw call.

## Il linguaggio in breve

MSL si basa su C++14. I tipi che userai di continuo:

| Tipo | Significato |
| --- | --- |
| `float`, `int`, `uint`, `bool` | Scalari. `half` è un float a 16 bit, spesso più veloce sulle GPU mobili. |
| `float2`, `float3`, `float4` | Vettori. Anche `int2`, `uint3`, `half4` e così via. |
| `float3x3`, `float4x4` | Matrici, memorizzate colonna per colonna. |
| `texture2d<float>`, `texturecube<float>`, `depth2d<float>` | Texture. |
| `sampler` | Impostazioni di filtro e di indirizzamento per leggere una texture. |

I vettori supportano lo **swizzling**: `v.xyz`, `v.rg`, `v.zyx`, `color.rgb * color.a`. La libreria standard ha le funzioni che ti aspetti: `dot`, `cross`, `normalize`, `length`, `reflect`, `mix`, `clamp`, `saturate`, `pow`, `smoothstep`, `max`, `min`.

Cose che MSL non permette: ricorsione, lambda, funzioni virtuali, eccezioni, `new` e la libreria standard del C++.

## Passare dati da uno stadio all'altro

Tutto ciò che la vertex function restituisce viene interpolato lungo il triangolo e consegnato alla fragment function. Aggiungi un colore alla struct di uscita:

{{code}}

Ogni vertice calcola un colore dalla propria posizione, e ogni fragment in mezzo riceve una miscela dei tre. Questa interpolazione è automatica per ogni membro della struct.

## Altri attributi di vertice

I colori possono arrivare anche dal vertex buffer. Alternali alle posizioni:

{{code}}

Descrivi il secondo attributo e lo stride più grande:

{{code}}

E ricevilo nello shader:

{{code}}

Il risultato è il classico triangolo con un angolo rosso, uno verde e uno blu che sfumano l'uno nell'altro.

## Uniform

Un **uniform** è un dato che resta costante durante una draw call: un tempo, una matrice di trasformazione, la posizione di una luce. In Metal un uniform è semplicemente una struct in un buffer che lo shader riceve per riferimento.

Dichiara la struct nello shader e aggiungila come parametro:

{{code}}

`constant` è lo spazio di indirizzamento per i dati di buffer in sola lettura. `[[buffer(0)]]` è lo slot 0 della tabella dei buffer del **fragment**. Vertex function e fragment function hanno tabelle separate, quindi il buffer 0 del vertex e il buffer 0 del fragment non hanno niente a che fare l'uno con l'altro.

Dichiara una struct corrispondente in Swift:

{{code}}

Per dati piccoli il modo più semplice di inviarli è `setFragmentBytes`, che copia i byte in un buffer temporaneo gestito da Metal:

{{code}}

Salva `startTime = CACurrentMediaTime()` in `init`; un `Float` non riesce a contenere il valore grezzo con abbastanza precisione. Per lo stadio di vertice c'è il corrispondente `setVertexBytes`. Per dati più grandi di 4 KB, o condivisi da molte draw call, crea tu un `MTLBuffer` e collegalo con `setFragmentBuffer`.

## Tenere allineati i layout di Swift e MSL

La struct Swift e la struct MSL devono avere lo stesso identico layout in memoria. Nessuno lo controlla al posto tuo, e una discordanza produce valori senza senso, non un errore. Tre regole evitano quasi tutti i problemi:

1. In Swift usa i tipi `SIMD` per i vettori e `simd_float4x4` (`float4x4`) per le matrici. `SIMD4<Float>` corrisponde a `float4`, `SIMD2<Float>` a `float2`.
2. `SIMD3<Float>` e il `float3` di MSL occupano entrambi **16 byte**, non 12. Corrispondono tra loro, ma non a tre float sciolti. Quando ti serve un vettore compatto da 12 byte in un buffer, MSL ha `packed_float3`.
3. Per le lunghezze dei buffer usa sempre `MemoryLayout<T>.stride`, non `.size`.

Nella nostra struct `time` occupa 4 byte seguiti da 12 byte di padding, così `tint` comincia all'offset 16 in entrambi i linguaggi.

!!! note "Una sola definizione per i due linguaggi"
    I progetti più grandi mettono le struct condivise in un header C, incluso dal file `.metal` ed esposto a Swift attraverso un bridging header. Così la definizione è una sola e i layout non possono divergere. Questa serie ripete le struct da entrambe le parti perché ogni capitolo si possa leggere da solo.

## Esercizi

- Capovolgi il triangolo intervenendo solo nella vertex function.
- Aggiungi un uniform `float2 offset` per lo stadio di vertice e fai muovere il triangolo in cerchio nel tempo.
- Usa la posizione come colore (`out.color = out.position`). Perché l'angolo in basso a sinistra è nero?
