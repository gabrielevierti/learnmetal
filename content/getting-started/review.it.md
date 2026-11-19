# Riepilogo

Questa era la parte difficile. Sai aprire una vista, far passare dei vertici in una pipeline, applicare loro una texture, muoverli con le matrici e volare con una camera dentro il risultato. Tutto ciò che viene dopo si costruisce su questi pezzi.

## Il frame, ancora una volta

{{code}}

Se sai spiegare ogni riga di questa funzione, sei pronto per l'illuminazione.

## Glossario

- **Device** (`MTLDevice`): la GPU, e la fabbrica di tutti gli altri oggetti Metal.
- **Command queue / command buffer**: la coda mette in ordine il lavoro; un buffer contiene i comandi codificati di un frame.
- **Render pass**: una sequenza di disegni dentro un insieme di texture di attachment, descritta da un `MTLRenderPassDescriptor` con load e store action.
- **Render command encoder**: registra i cambi di stato e le draw call di un pass.
- **Drawable**: la texture che in questo frame verrà mostrata a schermo.
- **Vertex function**: viene eseguita per ogni vertice e produce una posizione in clip space.
- **Fragment function**: viene eseguita per ogni pixel coperto e produce un colore.
- **Render pipeline state**: gli shader compilati più il layout dei vertici e i formati degli attachment. Costoso da creare, economico da usare.
- **Vertex descriptor**: fa corrispondere i byte dei vertex buffer agli attributi dello shader.
- **Buffer** (`MTLBuffer`): memoria grezza visibile alla GPU.
- **Uniform**: costanti di una draw call passate agli shader in un buffer.
- **Texture / sampler state**: i dati dell'immagine, e le regole per leggerli.
- **Mipmap**: copie già rimpicciolite di una texture per le superfici lontane.
- **Matrici model / view / projection**: dal locale al mondo, dal mondo alla camera, dalla camera al clip space.
- **NDC**: in Metal x e y da -1 a 1, z da 0 a 1.
- **Depth buffer**: per ogni pixel, il registro della superficie più vicina, usato per nascondere ciò che sta dietro.
- **Delta time**: i secondi trascorsi dal frame precedente.

## Convenzioni usate da qui in avanti

| Cosa | Convenzione |
| --- | --- |
| Mondo | Destrorso, +y in alto, la camera guarda lungo -z |
| Angoli | Radianti nelle matrici, gradi nella classe della camera |
| Slot 0 dei vertex buffer | Dati dei vertici |
| Slot 1 dei vertex buffer | Uniform della draw call |
| Slot 1 dei buffer del fragment | Uniform del fragment (luci, materiali) |
| Ordine dei vertici del triangolo | Il senso antiorario è il fronte |

## I primi errori più comuni

- **Vista nera o vuota**: `view.device` non impostato, oppure il delegate è stato deallocato perché niente tiene in vita il renderer.
- **La creazione della pipeline fallisce**: i formati dei pixel nel pipeline descriptor non coincidono con quelli della vista, oppure il nome di una funzione è scritto male.
- **Uniform senza senso**: i layout delle struct di Swift e di MSL sono diversi, oppure è stato usato `.size` dove serviva `.stride`.
- **Texture capovolte**: coordinate di texture in stile OpenGL.
- **Geometria che sparisce vicino alla camera**: una matrice di proiezione di OpenGL, con profondità da -1 a 1.
- **Non viene disegnato niente e non c'è alcun errore**: il modello è dietro la camera, fuori dal near e dal far plane, oppure la funzione di confronto della profondità scarta tutto.

Leggi con attenzione i messaggi di validazione. Quelli di Metal sono precisi e quasi sempre nominano l'esatta proprietà sbagliata.
