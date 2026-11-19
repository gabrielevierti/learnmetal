# Normal mapping

Un muro di mattoni disegnato come un rettangolo piatto sembra piatto, per quanto sia buona la texture. Lo tradisce l'illuminazione, perché ogni fragment ha la stessa normale. Il **normal mapping** salva una normale diversa per ogni texel, così la luce reagisce a rilievi e scanalature che nella geometria non esistono.

## Le normal map

Una normale è un vettore con componenti da -1 a 1. Salvata in un'immagine, ogni componente viene riportata nell'intervallo da 0 a 1, e lo shader fa l'operazione inversa:

{{code}}

Le normal map appaiono bluastre perché la maggior parte delle normali punta dritta fuori dalla superficie, lungo +z, che viene salvato come il colore (0.5, 0.5, 1.0). Carica le normal map come dati **lineari**, mai come sRGB.

## Lo spazio tangente

Le normali della mappa sono espresse rispetto alla superficie stessa, in **spazio tangente**, dove +z punta fuori dalla superficie. È questo che rende una mappa utilizzabile su un muro rivolto in qualsiasi direzione, o avvolta intorno a un modello curvo. Per usarle nei calcoli della luce ci serve un modo di ruotarle dallo spazio tangente allo spazio mondo.

Quella rotazione è la **matrice TBN**, costruita con tre vettori unitari perpendicolari in ogni vertice:

- **N**, la normale del vertice,
- **T**, la **tangente**, che corre lungo la superficie nella direzione in cui u cresce,
- **B**, la **bitangente**, che corre lungo la superficie nella direzione in cui v cresce.

## Ottenere le tangenti

Le tangenti si calcolano dalle posizioni e dalle coordinate di texture. Model I/O lo fa per te. Aggiungi al vertex descriptor un attributo per la tangente e chiedi la base dopo il caricamento:

{{code}}

{{code}}

Assegnare di nuovo il descriptor fa sì che Model I/O ricomponga i buffer con il nuovo attributo.

Per la geometria costruita a mano, la tangente di un triangolo con lati `e1`, `e2` e differenze di coordinate di texture `(du1, dv1)`, `(du2, dv2)` è:

{{code}}

## Lo shader

La vertex function porta la normale e la tangente in spazio mondo:

{{code}}

La fragment function ricostruisce una base esattamente perpendicolare, poi ruota con essa la normale letta:

{{code}}

`float3x3(T, B, N)` costruisce una matrice con quei vettori come colonne, quindi la moltiplicazione porta un vettore dallo spazio tangente allo spazio mondo. Usa la normale restituita al posto di `normalize(in.normal)` in tutto il codice di illuminazione. Non cambia nient'altro.

## Il canale verde e la mano

Due cose fanno spesso apparire "rivoltata" una superficie con normal map, con i rilievi illuminati come incavi:

- **La convenzione della normal map.** Le mappe esistono in due varianti che differiscono per il segno del canale verde, di solito etichettate OpenGL (+Y) e DirectX (-Y). Quale sia quella giusta dipende dal verso della tua coordinata v e della bitangente. Se i rilievi appaiono invertiti, cambia segno a `tangentNormal.y`.
- **Coordinate di texture specchiate.** I modelli simmetrici spesso specchiano le loro UV, cosa che inverte la bitangente su una metà. Gli esportatori lo codificano come un segno nella quarta componente della tangente. Se ti serve gestirlo, Model I/O offre `addTangentBasis(forTextureCoordinateAttributeNamed:tangentAttributeNamed:bitangentAttributeNamed:)` per salvare una bitangente esplicita.

Un controllo rapido per qualsiasi modello: manda in uscita come colore `N * 0.5 + 0.5`. Colori pastello che cambiano con dolcezza significano che la base è sana.

## Normal map a due canali

Poiché la z di una normale unitaria si può ricalcolare da x e y, le normal map vengono spesso salvate con due canali in un formato compresso, per esempio BC5 sui Mac o EAC RG11 e ASTC sulle GPU Apple:

{{code}}

## Esercizi

- Fai ruotare nel tempo un rettangolo con normal map e verifica che l'illuminazione resti coerente con una luce fissa.
- Scala x e y della normale in spazio tangente con un uniform di "intensità del rilievo" prima di normalizzare.
