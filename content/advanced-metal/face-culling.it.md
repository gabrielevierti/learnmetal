# Face culling

Guarda un oggetto chiuso come un cubo da qualsiasi angolo: ne vedi al massimo metà delle facce. Quelle rivolte dall'altra parte sono sempre nascoste da quelle davanti. Il **face culling** dice alla GPU di saltare quei triangoli prima di rasterizzarli, e per le mesh chiuse risparmia circa metà del lavoro sui fragment.

## L'ordine dei vertici

Come fa la GPU a sapere qual è il lato frontale di un triangolo? Dall'ordine in cui i suoi tre vertici compaiono sullo schermo: orario o antiorario. Quell'ordine è il **winding** del triangolo. Quando giri un triangolo, il suo winding visto dalla camera si inverte.

{{code}}

I modelli vengono esportati con un winding coerente, quindi una sola impostazione vale per un'intera mesh.

## Attivare il culling

Il culling è uno stato del render encoder. Non fa parte del pipeline state:

{{code}}

| `MTLCullMode` | Effetto |
| --- | --- |
| `.none` | Disegna entrambi i lati. È il valore predefinito. |
| `.back` | Salta i triangoli rivolti dall'altra parte. |
| `.front` | Salta i triangoli rivolti verso la camera. |

!!! warning "In Metal il fronte predefinito è in senso orario"
    `MTLWinding.clockwise` è il winding frontale predefinito di Metal, l'opposto di OpenGL. Il nostro cubo, e la maggior parte dei file di modelli, hanno il fronte in senso antiorario, quindi chiama sempre `setFrontFacing(.counterClockwise)` insieme a `setCullMode`. Se un modello appare rivoltato, con visibili solo le pareti lontane, la causa è questa.

Lo stato dell'encoder si azzera a ogni nuovo encoder, quindi imposta entrambi all'inizio di ogni pass.

## Quando non fare culling

- **Geometria piatta a due facce**: rettangoli d'erba, foglie, stoffa, finestre. Per quelle draw call disattiva il culling con `setCullMode(.none)`.
- **Oggetti chiusi trasparenti**: potresti volere che le facce interne si vedano attraverso quelle esterne. Disegna prima le facce posteriori (culling `.front`), poi quelle frontali.
- **Trasformazioni specchiate**: una matrice model con una scala negativa su un asse inverte il winding di tutto ciò che disegna. Per quegli oggetti inverti l'impostazione del fronte.

## Scartare le facce frontali

Ogni tanto scartare le facce *frontali* è utile di proposito. Disegnare in una shadow map solo le facce posteriori riduce un artefatto di auto-ombreggiatura, come vedrai in [Shadow mapping](../advanced-lighting/shadow-mapping.html), e un cubo di skybox visto da dentro si può disegnare con il culling frontale o semplicemente con il culling spento.

## Da che parte sono?

Una fragment function può chiedere se appartiene a un triangolo frontale, usando un input predefinito:

{{code}}

È così che i materiali a due facce vengono illuminati correttamente con il culling spento.

## Esercizi

- Attiva il culling delle facce posteriori e vola dentro un cubo.
- Inverti il winding di una faccia del cubo nei dati dei vertici e osserva quale faccia sparisce.
- Colora di verde le facce frontali e di rosso quelle posteriori usando `[[front_facing]]`, con il culling spento.
