# Mesh

MetalKit ci ha consegnato degli oggetti `MTKMesh`. Questo capitolo ne apre uno, lo disegna e lo racchiude insieme ai suoi materiali in un piccolo tipo nostro.

<!-- cpp -->

!!! note "Caricare i modelli in C++"
    Model I/O e i tipi di mesh di MetalKit non fanno parte di metal-cpp. La versione C++ di questa sezione carica file Wavefront OBJ con la libreria a singolo header [tinyobjloader](https://github.com/tinyobjloader/tinyobjloader) e costruisce a mano i buffer di Metal. Le idee sono le stesse: un modello è fatto di mesh, una mesh ha un vertex buffer e un index buffer per ogni materiale, e un materiale è fatto di valori e di texture. Per caricare USD da C++ chiama Model I/O da un piccolo file Objective-C++, come fa per AppKit il codice della finestra in [Preparare il progetto](../getting-started/project-setup.html), oppure converti il modello in OBJ o glTF.

<!-- /cpp -->

## Dentro una MTKMesh

| Proprietà | Contenuto |
| --- | --- |
| `vertexBuffers` | Un array di `MTKMeshBuffer`, ognuno con un `buffer` (`MTLBuffer`) e un `offset` al suo interno. |
| `vertexDescriptor` | Il vertex descriptor di Model I/O dei dati. |
| `submeshes` | Un array di `MTKSubmesh`. |
| `vertexCount` | Il numero di vertici. |

e ogni `MTKSubmesh` ha:

| Proprietà | Contenuto |
| --- | --- |
| `indexBuffer` | Un `MTKMeshBuffer` con gli indici. |
| `indexCount`, `indexType` | Quanti indici ci sono e se sono a 16 o a 32 bit. |
| `primitiveType` | Di solito `.triangle`. |

Gli offset sono importanti. L'allocator può mettere più mesh in un unico grande `MTLBuffer`, quindi passa sempre l'offset quando colleghi un buffer.

## Disegnare una mesh

{{code}}

Con il layout del capitolo precedente c'è un solo vertex buffer, collegato allo slot 0, e lo slot 1 resta libero per gli uniform come prima.

Al pipeline state serve il vertex descriptor di Metal corrispondente. Puoi riusare quello costruito a mano oppure ricavarlo dalla mesh:

{{code}}

## Materiali

Ogni `MDLSubmesh` ha un `MDLMaterial` facoltativo. Un materiale è un sacco di proprietà che si cercano per **semantic**:

{{code}}

Una proprietà può essere un semplice valore oppure una texture, quindi gestiamo entrambi i casi. Un piccolo tipo di materiale per lo shader di Phong della sezione sull'illuminazione:

{{code}}

Il caso della texture copre le immagini incorporate negli archivi USDZ (dopo `asset.loadTextures()`), e il caso dell'URL copre i file OBJ che fanno riferimento a immagini su disco accanto al file `.mtl`.

!!! note "Il flag sRGB"
    Le texture di colore sono salvate in sRGB, quelle di dati come le specular map o le normal map no. Fino al capitolo [Correzione gamma](../advanced-lighting/gamma-correction.html) passa `false` per tutte, così il risultato coincide con quello dei capitoli precedenti.

## Un tipo Mesh

Metti insieme la mesh di Metal e un materiale per ogni submesh:

{{code}}

## Una texture di riserva

Uno shader che legge una texture deve averne una collegata. Per i materiali senza texture collega una texture bianca da 1×1, che nella moltiplicazione non cambia nulla:

{{code}}

È anche la tua prima texture fatta a mano: un descriptor, `makeTexture`, e `replace` per caricare i byte.
