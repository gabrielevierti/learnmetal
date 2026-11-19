# Upscaling con MetalFX

Il costo di un frame cresce con il numero di pixel. **MetalFX** ti permette di disegnare la scena a una risoluzione più bassa e produce un'immagine a piena risoluzione che somiglia molto a una disegnata in modo nativo. Un gioco che disegna a 1280 × 720 e porta a 2560 × 1440 calcola un quarto dei pixel.

MetalFX offre due upscaler e, dal 2025, un upscaler con denoising per il ray tracing e un interpolatore di frame.

| Effetto | Che cosa richiede | Usalo quando |
|---|---|---|
| Scaler spaziale | L'immagine di colore | Vuoi l'integrazione più semplice, o non hai i motion vector |
| Scaler temporale | Colore, profondità, motion vector, jitter della camera | Vuoi la qualità migliore, e con essa l'anti-aliasing |
| Scaler temporale con denoising | Quanto sopra più normali, albedo, roughness | L'immagine è in ray tracing con pochi raggi per pixel |
| Interpolatore di frame | Due frame, profondità, motion vector | Vuoi un frame rate più alto di quello che riesci a disegnare |

Gli scaler sono disponibili da macOS 13 e iOS 16 sui dispositivi con Apple silicon. Lo scaler con denoising e l'interpolatore di frame richiedono i sistemi del 2025 (macOS 26, iOS 26).

## Dove va nel frame

L'upscaling non sostituisce niente nel tuo renderer. È un passo in più, e la sua posizione conta.

1. Disegna la scena a bassa risoluzione in una texture HDR.
2. Fai l'**upscaling** alla risoluzione di uscita.
3. Fai il post-processing a piena risoluzione: bloom, tone mapping.
4. Disegna sopra l'interfaccia utente, a piena risoluzione.

Il testo e gli elementi dell'interfaccia non devono mai passare per l'upscaler: disegnali dopo, a risoluzione nativa.

## Lo scaler spaziale

Lavora su una sola immagine, senza storia. Crealo una volta, e di nuovo ogni volta che cambia una dimensione.

{{code}}

A ogni frame passagli le texture e codificalo nel command buffer, tra un pass e l'altro. Non fa parte di un render pass.

{{code}}

La texture di uscita va creata con l'uso che lo scaler chiede in `outputTextureUsage`, e con `storageMode = .private`.

## Lo scaler temporale

Lo scaler temporale raccoglie dettaglio dai frame precedenti. A ogni frame sposti l'intera immagine di una frazione di pixel, il **jitter**, così che nel giro di alcuni frame ogni pixel venga campionato in molte posizioni. Lo scaler allinea i vecchi frame a quello nuovo usando i **motion vector**, e li mescola. Il risultato ha più dettaglio reale di qualsiasi singolo frame, ed è senza aliasing, quindi l'MSAA diventa superfluo.

Oltre al colore ha bisogno di tre ingressi.

- **La profondità**, dallo stesso pass a bassa risoluzione.
- **I motion vector**: per ogni pixel, di quanto la superficie si è spostata sullo schermo dall'ultimo frame. Disegnali come un attachment di colore in più (`rg16Float`).
- **L'offset di jitter** che in questo frame hai applicato alla proiezione.

{{code}}

### Jitter

Usa una sequenza a bassa discrepanza, come Halton con basi 2 e 3, e sposta la proiezione di quella frazione di pixel.

{{code}}

Se il segno di ciascun termine sia giusto dipende dalla convenzione della tua proiezione. Se l'immagine tremola o si sfoca a camera ferma, inverti un segno alla volta: con i segni corretti una scena statica converge in pochi frame a un'immagine nitida.

### Motion vector

Nella vertex function calcola la posizione in clip space del vertice in questo frame e in quello precedente, entrambe **senza** jitter, e passale avanti. La fragment function le trasforma in una differenza in spazio uv.

{{code}}

Ogni oggetto in movimento ha bisogno della sua matrice model precedente, e la camera della sua matrice view-projection precedente.

### Codifica

{{code}}

Imposta `isDepthReversed` se usi il reverse-Z. Imposta `reset` ogni volta che la storia è inutilizzabile, altrimenti resteranno i fantasmi della vecchia scena.

## Ottenere la qualità giusta

- **Dettaglio delle texture.** Un rendering a bassa risoluzione sceglie livelli di mip più sfocati. Dai ai tuoi sampler un LOD bias negativo pari a `log2(renderWidth / outputWidth)`, per esempio -1 con un upscaling 2×, così le texture conservano la nitidezza della piena risoluzione.
- **Il ghosting** dietro gli oggetti in movimento significa motion vector sbagliati o mancanti. Controlla per primi gli oggetti animati, con skinning e con instancing.
- **Gli effetti trasparenti e le particelle** non hanno motion vector propri. Segnali nella **reactive mask** dello scaler, così lì si fida di più del nuovo frame.
- **L'esposizione.** Lo scaler lavora in HDR lineare e ha bisogno di sapere più o meno quanto luminosa verrà mostrata l'immagine. Attiva `isAutoExposureEnabled` nel descriptor, oppure fornisci una tua texture di esposizione.
- **Risoluzione dinamica.** Crea lo scaler per la dimensione di ingresso più grande e imposta a ogni frame `inputContentWidth` e `inputContentHeight` sulla regione effettivamente disegnata.

## Esercizi

- Aggiungi lo scaler spaziale all'esempio dei render target: disegna a metà dimensione e confronta con lo stiramento `.linear`.
- Visualizza la texture del movimento mentre sposti la camera.
- Con lo scaler temporale in funzione, smetti di inviare l'offset di jitter e descrivi che cosa succede.
