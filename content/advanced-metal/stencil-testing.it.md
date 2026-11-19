# Test di stencil

Accanto al depth buffer vive lo **stencil buffer**: 8 bit per pixel che puoi scrivere liberamente mentre disegni e controllare in seguito. Permette di marcare delle zone dello schermo e poi di limitare il disegno a quelle. Contorni, portali, specchi e maschere per l'interfaccia sono gli usi classici.

## Attivare uno stencil buffer

Di norma profondità e stencil condividono una sola texture con un formato combinato:

{{code}}

Ogni pipeline state usato nel pass deve dichiarare entrambi i formati.

## Il test di stencil

Per ogni fragment la GPU confronta un **valore di riferimento**, che imposti sull'encoder, con il valore nel buffer. Il confronto e la reazione sono descritti da un `MTLStencilDescriptor` dentro il depth-stencil descriptor:

| Proprietà | Significato |
| --- | --- |
| `stencilCompareFunction` | Come si confrontano il riferimento e il valore salvato. |
| `stencilFailureOperation` | Che cosa fare del valore salvato se il test di stencil fallisce. |
| `depthFailureOperation` | Se il test di stencil passa ma quello di profondità fallisce. |
| `depthStencilPassOperation` | Se passano entrambi. |
| `readMask`, `writeMask` | Maschere di bit applicate nel confronto e nella scrittura. |

Le operazioni sono `.keep`, `.zero`, `.replace` (salva il valore di riferimento), `.incrementClamp`, `.decrementClamp`, `.invert`, `.incrementWrap` e `.decrementWrap`.

Ci sono descriptor separati per i triangoli rivolti verso la camera e per quelli rivolti dall'altra parte, `frontFaceStencil` e `backFaceStencil`.

## Contorni degli oggetti

Un contorno di selezione si disegna in due passi:

1. Disegna l'oggetto normalmente e scrivi 1 nello stencil buffer ovunque sia visibile.
2. Disegna di nuovo l'oggetto, un po' ingrandito e con un colore piatto, solo dove lo stencil **non** vale 1.

La copia ingrandita viene scartata sopra l'oggetto stesso e sopravvive solo in un bordo sottile intorno.

**State 1: scrivi 1 ovunque venga disegnato l'oggetto.**

{{code}}

**State 2: disegna solo dove lo stencil non vale 1, ignorando la profondità.**

{{code}}

**Il disegno:**

{{code}}

Il `solidColorPipelineState` usa una fragment function che restituisce un colore unico. Poiché lo state del contorno usa `.always` per la profondità, il bordo si vede attraverso gli altri oggetti, che è ciò che vuoi per evidenziare una selezione.

!!! note "Contorni migliori"
    Scalare funziona per le forme convesse centrate sulla loro origine. Per modelli qualsiasi sposta invece ogni vertice lungo la sua normale nella vertex function: `position + normal * thickness`.

## Leggere il confronto nel verso giusto

Il confronto si scrive *riferimento* **op** *salvato*. Con `.less` e un riferimento pari a 1, un fragment passa dove `1 < salvato`. È facile leggerlo al contrario.

## Altri usi

- **Portali e specchi**: disegna la forma del portale nello stencil buffer, poi disegna il mondo visto attraverso di esso solo dove lo stencil è impostato.
- **Maschere**: ritaglia l'interfaccia o i contenuti 2D secondo forme qualsiasi.
- **Volumi di luce nel deferred**: marca i pixel che una luce può raggiungere, così lo shader di illuminazione gira solo lì.

## Esercizi

- Fai in modo che il contorno rispetti la profondità, così viene nascosto dagli oggetti più vicini.
- Metti il contorno a uno solo dei cubi.
