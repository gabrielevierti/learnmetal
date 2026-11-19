# Model I/O

Nessuno scrive a mano i vertici di un personaggio. Gli artisti costruiscono i modelli in programmi come Blender e li esportano in file, e il nostro compito è trasformare quei file in vertex buffer, index buffer e texture.

Sulle piattaforme Apple non serve una libreria di terze parti. Il framework di sistema **Model I/O** legge i formati 3D più comuni, e **MetalKit** converte il risultato in oggetti Metal.

<!-- cpp -->

!!! note "Caricare i modelli in C++"
    Model I/O e i tipi di mesh di MetalKit non fanno parte di metal-cpp. La versione C++ di questa sezione carica file Wavefront OBJ con la libreria a singolo header [tinyobjloader](https://github.com/tinyobjloader/tinyobjloader) e costruisce a mano i buffer di Metal. Le idee sono le stesse: un modello è fatto di mesh, una mesh ha un vertex buffer e un index buffer per ogni materiale, e un materiale è fatto di valori e di texture. Per caricare USD da C++ chiama Model I/O da un piccolo file Objective-C++, come fa per AppKit il codice della finestra in [Preparare il progetto](../getting-started/project-setup.html), oppure converti il modello in OBJ o glTF.

<!-- /cpp -->

## I formati

Model I/O importa, tra gli altri:

| Formato | Note |
| --- | --- |
| USD, USDZ, USDA, USDC | La Universal Scene Description di Pixar, il formato preferito da Apple. Supporta materiali, gerarchia e animazione. |
| OBJ (+ MTL) | Semplice e diffuso ovunque. Solo geometria e materiali di base. |
| PLY, STL | Solo geometria, comuni per le scansioni e la stampa 3D. |
| Alembic (ABC) | Cache di animazioni già calcolate. |

!!! note "E glTF e FBX?"
    Model I/O non legge né glTF né FBX. Convertili in USDZ con Reality Converter di Apple o con Blender, oppure usa un loader open source. Per imparare, OBJ e USDZ bastano e avanzano.

## Come è strutturato un modello

Model I/O rappresenta un file come un albero:

- **`MDLAsset`**: il file intero. Un contenitore di oggetti.
- **`MDLObject`**: un nodo con una trasformazione e dei figli.
- **`MDLMesh`**: un nodo che ha geometria. Possiede i vertex buffer e un vertex descriptor.
- **`MDLSubmesh`**: una parte di una mesh disegnata con un solo materiale. Possiede un index buffer.
- **`MDLMaterial`**: proprietà con un nome, come base color, roughness e normal, ognuna delle quali è un valore o una texture.

Una mesh condivide i suoi vertici tra più submesh. La carrozzeria di un'auto può essere una sola mesh con una submesh per la vernice, una per i vetri e una per le cromature.

## Chiedere il layout che vuoi

I file salvano i dati dei vertici nel layout scelto da chi li ha esportati. Model I/O può riordinarli nel layout che i nostri shader si aspettano. Parti dal vertex descriptor di Metal, convertilo e dai un nome agli attributi, così Model I/O sa quale dato va dove:

{{code}}

Dato che è Model I/O a scrivere il buffer per noi, siamo liberi di compattarlo: in un vertex buffer `.float3` occupa 12 byte, quindi un vertice ne occupa 32. Nello spirito è lo stesso layout del nostro cubo, solo senza il padding di Swift. Il `VertexIn` dello shader non cambia affatto; `[[attribute(n)]]` nasconde il layout.

## Caricare l'asset

{{code}}

Il **buffer allocator** è il dettaglio chiave. Con un `MTKMeshBufferAllocator` Model I/O carica i dati dei vertici e degli indici direttamente in `MTLBuffer`, senza copie intermedie.

Subito dopo il caricamento tornano spesso utili due passi facoltativi:

{{code}}

## Da Model I/O a Metal

MetalKit trasforma ogni `MDLMesh` dell'asset in una `MTKMesh`:

{{code}}

Ottieni due array paralleli. Gli oggetti `MTKMesh` contengono i buffer di Metal per disegnare. Gli oggetti `MDLMesh` contengono ancora ciò che a Metal non interessa: materiali e trasformazioni. I prossimi due capitoli li racchiudono in tipi nostri.

## Forme già pronte

Model I/O sa anche generare geometria, cosa comoda per le prove:

{{code}}

Esistono inizializzatori simili per scatole, piani, cilindri, capsule, coni e icosaedri.

!!! warning "Ancora le coordinate di texture"
    Molti file seguono la convenzione di OpenGL, con v verso l'alto. Se le texture di un modello appaiono scombinate o specchiate, ribalta v al caricamento: `mesh.flipTextureCoordinates(inAttributeNamed: MDLVertexAttributeTextureCoordinate)`.
