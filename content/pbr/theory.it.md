# Teoria

Il **rendering fisicamente corretto** (physically based rendering, PBR) è una famiglia di tecniche che modellano la luce in un modo più vicino alla fisica rispetto a Phong o a Blinn-Phong. Il vantaggio è pratico:

- I materiali appaiono giusti sotto **qualsiasi** illuminazione, senza ritocchi scena per scena.
- Gli artisti creano i materiali con pochi parametri intuitivi che hanno lo stesso significato in ogni motore.

Di solito un modello di illuminazione si dice fisicamente corretto quando soddisfa tre condizioni: si basa su un modello a **microfaccette** delle superfici, **conserva l'energia** e usa una **BRDF** fisicamente corretta. Questo capitolo spiega ciascuna, e il prossimo le trasforma in codice di shader.

## Microfaccette

A scala microscopica nessuna superficie è liscia. È fatta di minuscoli specchi perfetti chiamati **microfaccette**, ognuno rivolto in una sua direzione. Su una superficie ruvida i loro orientamenti variano moltissimo, e la luce in arrivo si disperde ampiamente, producendo riflessi larghi e deboli. Su una superficie liscia sono quasi allineati, e i riflessi sono netti e brillanti.

Non possiamo modellare le singole microfaccette, quindi le descriviamo statisticamente con un solo numero, la **roughness**, da 0 (specchio) a 1 (del tutto ruvido). Ciò che conta per un riflesso è la frazione di microfaccette la cui normale coincide con il **vettore halfway** tra la luce e chi guarda, lo stesso vettore incontrato in [Blinn-Phong](../advanced-lighting/blinn-phong.html).

## Conservazione dell'energia

La luce in uscita non può mai superare quella in entrata, a parte le superfici che emettono luce propria. Quando la luce colpisce una superficie si divide in due parti:

- La parte **riflessa** rimbalza direttamente sulla superficie. È la luce **specular**.
- La parte **rifratta** entra nel materiale, si disperde al suo interno e viene in parte assorbita. Ciò che ne esce, colorato dal materiale, è la luce **diffuse**.

Le due si escludono a vicenda: la luce che è stata riflessa non può essere anche rifratta. Quindi, se viene riflessa una frazione `kS`, per il diffuse resta al massimo `1 - kS`.

I **metalli** si comportano in modo diverso dai non metalli (i **dielettrici**). Un metallo assorbe tutta la luce rifratta, quindi non ha alcun colore diffuse, solo una riflessione speculare colorata. È la base del parametro **metalness**.

## L'equazione della riflettanza

Il PBR si costruisce su questa equazione:

{{code}}

Si legge con più facilità di quanto sembri. La luce `Lo` che lascia il punto `p` verso chi guarda `wo` è la somma, su ogni direzione di arrivo `wi` nell'emisfero `Ω` sopra la superficie, di:

- `Li`, la **radianza** in arrivo da quella direzione, cioè l'intensità e il colore della luce,
- `n · wi`, il solito fattore coseno che indebolisce la luce che arriva radente,
- `fr`, la **BRDF**, che dice quanta della luce proveniente da `wi` viene riflessa verso `wo` da questo materiale.

Per una manciata di luci puntiformi l'integrale si riduce a una semplice somma sulle luci, ed è ciò che fa il prossimo capitolo. Per la luce che arriva dall'intero ambiente dobbiamo risolverlo davvero, ed è l'argomento dei capitoli sull'IBL.

## La BRDF di Cook-Torrance

La BRDF usata in pratica da ogni renderer in tempo reale ha una parte diffuse e una specular:

{{code}}

La parte diffuse è il termine **lambertiano**, una costante: `albedo / π`.

La parte specular è

{{code}}

con tre funzioni, ognuna delle quali approssima un aspetto del comportamento delle microfaccette.

### D: la funzione di distribuzione delle normali

Quante microfaccette sono allineate con il vettore halfway `h`? La distribuzione **Trowbridge-Reitz GGX**, con `α = roughness²`:

{{code}}

Una roughness bassa concentra il risultato in una macchia piccola e intensa. Una alta lo distribuisce.

### G: la funzione di geometria

Le microfaccette si fanno ombra e si coprono a vicenda, soprattutto sulle superfici ruvide ad angoli radenti. L'approssimazione **Schlick-GGX** per una direzione è

{{code}}

dove `k = (roughness + 1)² / 8` per l'illuminazione diretta e `k = roughness² / 2` per l'illuminazione basata su immagini. Il **metodo di Smith** combina le direzioni di vista e di luce: `G = G1(vista) · G1(luce)`.

### F: l'equazione di Fresnel

Ogni superficie diventa più riflettente agli angoli radenti. Guarda un lago dritto dall'alto e vedi il fondo; guardalo di taglio e vedi il cielo. L'approssimazione **Fresnel-Schlick**:

{{code}}

`F0` è la **riflettività di base**, la riflettanza quando si guarda la superficie di fronte. I dielettrici hanno una F0 bassa e senza colore, intorno a 0.04. I metalli ne hanno una alta e colorata:

| Materiale | F0 (RGB lineare) |
| --- | --- |
| Acqua | 0.02, 0.02, 0.02 |
| Plastica, vetro | 0.04, 0.04, 0.04 |
| Ferro | 0.56, 0.57, 0.58 |
| Rame | 0.95, 0.64, 0.54 |
| Oro | 1.00, 0.71, 0.29 |
| Alluminio | 0.91, 0.92, 0.92 |

Nel flusso di lavoro con la metalness, F0 si calcola mescolando 0.04 e il colore dell'albedo in base al valore di metalness.

Il termine di Fresnel F *è* la frazione riflessa `kS`. Quindi `kD = (1 − F)(1 − metalness)`.

## I parametri del materiale

Un materiale PBR nel diffuso flusso di lavoro **metallic-roughness** è composto da:

| Mappa | Spazio colore | Significato |
| --- | --- | --- |
| **Albedo** | sRGB | Colore di base, senza luci né ombre già dipinte. Per i metalli, il colore di F0. |
| **Normal** | lineare | Normale in spazio tangente, come nel normal mapping. |
| **Metallic** | lineare | 0 per i dielettrici, 1 per i metalli. Raramente valori intermedi. |
| **Roughness** | lineare | Ruvidità delle microfaccette. |
| **Ambient occlusion** | lineare | Occlusione delle fessure già calcolata. |

È il modello di materiale usato dalla preview surface di USD e da glTF, quindi gli asset che Model I/O carica vi corrispondono direttamente (`.baseColor`, `.metallic`, `.roughness`, `.tangentSpaceNormal`, `.ambientOcclusion`).

Poiché il PBR dipende da intensità di luce corrette, richiede il flusso di lavoro lineare e la pipeline HDR della sezione precedente. Verifica che ci siano entrambi prima di continuare.
