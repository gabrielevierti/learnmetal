# Texture

Dare un colore a ogni vertice non basta per ottenere un muro di mattoni o una cassa di legno. Per avere dettaglio avvolgiamo delle immagini intorno alla geometria. Un'immagine usata così è una **texture**, e leggerne un colore si dice fare **sampling**.

## Coordinate di texture

Ogni vertice riceve una **coordinata di texture** a due dimensioni (spesso chiamata UV) che dice quale punto dell'immagine gli appartiene. Le coordinate vanno da 0 a 1 su entrambi gli assi e vengono interpolate lungo il triangolo come ogni altra uscita del vertice.

!!! warning "In Metal l'origine è in alto a sinistra"
    In Metal la coordinata di texture (0, 0) è l'angolo **in alto a sinistra** dell'immagine e v cresce verso il basso. OpenGL mette (0, 0) in basso a sinistra. Le coordinate copiate dai tutorial di OpenGL, o esportate da strumenti che seguono la convenzione di OpenGL, mostrano le immagini capovolte, a meno di ribaltare v (`v = 1 - v`) o di ribaltare l'immagine al caricamento.

Un rettangolo con posizioni e coordinate di texture:

{{code}}

{{code}}

## Caricare un'immagine

`MTKTextureLoader` di MetalKit decodifica PNG, JPEG, HEIC, TIFF e altri formati comuni e carica il risultato in una nuova `MTLTexture`. Trascina nel progetto un'immagine, per esempio `container.jpg`, e poi:

{{code}}

`.SRGB: false` dice al loader di trattare i valori dei pixel come semplici numeri. Torneremo su questa scelta in [Correzione gamma](../advanced-lighting/gamma-correction.html). Se mai ti servisse l'orientamento di OpenGL, aggiungi `.origin: MTKTextureLoader.Origin.bottomLeft`, che ribalta l'immagine in verticale durante il caricamento.

Le immagini di un asset catalog si caricano per nome con `loader.newTexture(name:scaleFactor:bundle:options:)`.

<!-- cpp -->

!!! note "Caricare le immagini in C++"
    `MTKTextureLoader` appartiene a MetalKit, che metal-cpp non copre. La versione C++ decodifica il file con la libreria a singolo header [stb_image](https://github.com/nothings/stb) e carica i pixel con `replaceRegion`. stb_image restituisce per prima la riga in alto, il che coincide con l'origine in alto a sinistra di Metal. Per avere l'orientamento di OpenGL chiama `stbi_set_flip_vertically_on_load(true)` prima di caricare.

<!-- /cpp -->

## Sampler

Una texture è soltanto pixel. Come vengono letti lo decide un oggetto separato, il **sampler state**:

{{code}}

Gli **address mode** decidono che cosa succede fuori dall'intervallo da 0 a 1:

| Modo | Effetto |
| --- | --- |
| `.clampToEdge` | I pixel del bordo si allungano verso l'esterno. È il valore predefinito. |
| `.repeat` | L'immagine si ripete. |
| `.mirrorRepeat` | L'immagine si ripete, ogni volta specchiata. |
| `.clampToBorderColor` | Fuori c'è un colore di bordo fisso (macOS e dispositivi iOS più recenti). |
| `.clampToZero` | Fuori c'è nero trasparente. |

Il **filtering** decide che cosa succede quando un pixel della texture (un *texel*) non corrisponde uno a uno a un pixel dello schermo. `.nearest` prende il texel più vicino e, ingrandito, appare a blocchi. `.linear` mescola i quattro texel più vicini e appare morbido.

Le **mipmap** sono una catena di copie già rimpicciolite della texture, ognuna grande la metà della precedente. Quando una superficie è lontana, leggere una copia piccola evita lo sfarfallio ed è più veloce. `mipFilter = .linear` mescola i due livelli più vicini, cosa che insieme al filtro lineare in riduzione prende il nome di filtro trilineare. Impostare `samplerDescriptor.maxAnisotropy = 8` rende ancora più nitide le superfici viste molto di taglio.

!!! note "Se vieni da OpenGL"
    Le impostazioni di wrap e di filtro non sono proprietà della texture. Una texture può essere letta attraverso più sampler, e un sampler può servire per tutte le texture.

## Il sampling nello shader

{{code}}

Texture e sampler hanno ciascuno la propria tabella di indici, che si sceglie con `[[texture(n)]]` e `[[sampler(n)]]`. Collegali prima di disegnare:

{{code}}

Eseguilo e il rettangolo mostra la tua immagine.

## Due texture insieme

Una fragment function può leggere molte texture. Carica una seconda immagine, collegala all'indice 1 e mescola:

{{code}}

`mix(a, b, t)` restituisce `a * (1 - t) + b * t`, quindi il risultato è per l'80% la prima texture e per il 20% la seconda.

## Esercizi

- Moltiplica le uv per 2 nella fragment function e prova ogni address mode.
- Passa i filtri a `.nearest` e mostra solo il centro della texture (uv da 0.45 a 0.55) per vedere i singoli texel.
- Aggiungi un uniform che controlla il fattore di `mix` e animalo.
