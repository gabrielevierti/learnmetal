# Blending

Il blending è il modo in cui si fa la trasparenza. Invece di sostituire il colore già presente nella texture, il colore di un nuovo fragment viene *combinato* con esso. La quarta componente del colore, l'**alpha**, di solito decide come: 1 è del tutto opaco, 0 è del tutto trasparente.

## Scartare i fragment

Alcune immagini sono o del tutto opache o del tutto trasparenti, come una texture d'erba o di foglie con una sagoma ritagliata. Non hanno bisogno di blending. La fragment function può semplicemente buttare via i fragment trasparenti:

{{code}}

Un fragment scartato non scrive né colore né profondità. Carica queste texture con un sampler che usa `.clampToEdge`; con `.repeat` il filtro lineare mescola la riga in alto con quella in basso e lascia una linea leggera sul bordo.

Sulle GPU tile-based `discard_fragment` impedisce alcune ottimizzazioni di rimozione delle superfici nascoste, quindi usalo solo nelle pipeline che ne hanno bisogno.

## L'equazione di blending

Per le superfici semitrasparenti come il vetro la pipeline calcola

{{code}}

dove **source** è l'uscita della fragment function e **destination** è il colore già salvato. In Metal il blending fa parte del **render pipeline state** e si configura per ogni attachment di colore:

{{code}}

È il classico alpha blending: `risultato = source * alpha + destination * (1 - alpha)`. Una finestra rossa con alpha 0.5 davanti a un muro verde dà una miscela in parti uguali dei due.

Altre configurazioni utili:

| Effetto | Fattore source | Fattore destination |
| --- | --- | --- |
| Alpha blending | `.sourceAlpha` | `.oneMinusSourceAlpha` |
| Alpha premoltiplicato | `.one` | `.oneMinusSourceAlpha` |
| Additivo (fuoco, bagliori) | `.one` o `.sourceAlpha` | `.one` |
| Moltiplicativo (tinta, ombra) | `.destinationColor` | `.zero` |

!!! note "Se vieni da OpenGL"
    Non c'è un `glEnable(GL_BLEND)` da accendere e spegnere tra una draw call e l'altra. Crei un pipeline state per il disegno opaco e un altro per il disegno con blending, e cambi pipeline state.

!!! note "Alpha premoltiplicato"
    Molti loader di immagini, Core Graphics compreso, consegnano i colori già moltiplicati per il loro alpha. Fare il blending di una texture così con `.sourceAlpha` scurisce i bordi. Per i contenuti premoltiplicati usa `.one` come fattore source.

## L'ordine conta

Blending e depth buffer non collaborano. Se una finestra viene disegnata per prima scrive la sua profondità, e tutto ciò che viene disegnato dopo dietro di lei viene scartato dal test di profondità, anche se dovrebbe vedersi attraverso il vetro. La regola per un'immagine corretta:

1. Disegna prima tutti gli oggetti **opachi**.
2. **Ordina** gli oggetti trasparenti per distanza dalla camera.
3. Disegnali **da dietro in avanti**, con il test di profondità acceso e la scrittura della profondità **spenta**.

{{code}}

Ordinare per distanza dell'oggetto non è perfetto. Superfici trasparenti che si intersecano, o molto grandi, possono ancora mescolarsi nell'ordine sbagliato. Le tecniche che eliminano la necessità di ordinare vanno sotto il nome di **order-independent transparency**. Le GPU Apple ne rendono praticabile una famiglia grazie al programmable blending, in cui una fragment function può leggere il colore attuale del pixel che sta scrivendo; incontrerai questa funzione in [Deferred shading](../advanced-lighting/deferred-shading.html).

## Esercizi

- Disegna dei rettangoli d'erba con `discard_fragment`, poi con il blending ma senza ordinamento, e confronta i bordi.
- Disegna le finestre da davanti verso dietro per vedere l'artefatto che l'ordinamento evita.
- Crea una pipeline additiva per le particelle e disegna qualche rettangolo sovrapposto.
