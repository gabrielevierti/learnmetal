# Correzione gamma

C'è un errore in ogni immagine che abbiamo disegnato finora. I calcoli della luce danno per scontato che un valore di 0.5 sia luminoso la metà di 1.0. Su uno schermo non è così.

## Gli schermi non sono lineari

Gli schermi seguono lo standard **sRGB**, che è vicino a una curva di potenza con un esponente di 2.2, chiamato **gamma**. Un pixel di valore 0.5 viene mostrato a circa 0.5^2.2 ≈ 0.22 della luminosità piena. Non è un difetto. La vista umana è più sensibile alle differenze tra toni scuri che tra toni chiari, e la curva spende una parte maggiore dei 256 livelli disponibili sulla zona scura, dove li notiamo.

La conseguenza: i file immagine sono salvati già **codificati** per questa curva, e anche tutto ciò che scriviamo sullo schermo viene trattato come codificato.

## Che cosa va storto

Se calcoliamo la luce direttamente sui valori codificati:

- Sommare due luci non raddoppia la luminosità a schermo.
- Le sfumature dal chiaro allo scuro cadono troppo in fretta, e l'ombreggiatura ha terminatori duri e scuri.
- I colori scivolano verso la sovrasaturazione, e l'attenuazione appare sbagliata.

La soluzione è un **flusso di lavoro lineare**: convertire gli input in spazio lineare, fare lì tutti i calcoli e riconvertire il risultato in sRGB soltanto alla fine.

## Metal fa entrambe le conversioni per te

I formati dei pixel che finiscono in `_srgb` dicono a Metal che una texture contiene dati codificati in sRGB:

- **Leggere** una texture sRGB restituisce valori **lineari**. La conversione avviene prima del filtro, che è l'ordine corretto.
- **Scrivere** in un render target sRGB converte in sRGB l'uscita **lineare** dello shader. Anche il blending viene fatto in spazio lineare.

La correzione gamma si riduce quindi a due modifiche di configurazione e a zero righe di shader.

**1. Rendi sRGB il drawable della vista:**

{{code}}

e usa lo stesso formato nei pipeline descriptor che disegnano su di esso.

**2. Carica le texture di colore come sRGB:**

{{code}}

!!! warning "Solo i colori sono sRGB"
    Le texture che contengono **colori** creati da un artista guardando uno schermo sono sRGB: diffuse, albedo, emissive. Le texture che contengono **dati** sono lineari: normal map, specular, roughness, metalness, height, ambient occlusion. Decodificare una normal map come sRGB piega ogni normale e produce un'illuminazione leggermente sbagliata, difficile da diagnosticare.

Se ometti l'opzione `.SRGB`, il loader decide in base ai metadati del file immagine, che può essere o non essere ciò che vuoi. Essere espliciti evita sorprese.

## Farlo a mano

Se non puoi usare un target sRGB, applica la curva alla fine della fragment function:

{{code}}

e decodifica le texture in lettura con `pow(texel, float3(2.2))`. La strada automatica è più accurata, perché la vera curva sRGB non è una pura funzione di potenza, e filtra e mescola nel modo corretto. Fai l'una o l'altra cosa, mai entrambe, altrimenti l'immagine viene slavata.

## Colori costanti

I colori scritti nel codice o scelti con un selettore di colore sono valori sRGB. In un flusso di lavoro lineare vanno convertiti prima dell'uso:

{{code}}

Quando il formato del drawable è sRGB, il `clearColor` della vista è espresso in spazio lineare, quindi gli stessi numeri ora appaiono più luminosi di prima.

## Attenuazione

Fisicamente l'intensità della luce cala con il **quadrato** della distanza:

{{code}}

Senza correzione gamma il risultato è fin troppo duro, perché la curva dello schermo eleva al quadrato il calo un'altra volta. Ecco perché i tutorial più vecchi usano un calo lineare o la formula a tre termini di [Tipi di luce](../lighting/light-casters.html), tarati a occhio su un'uscita non corretta. Con un flusso di lavoro lineare il calo con l'inverso del quadrato appare giusto, e da qui in avanti lo usiamo.

## Che cosa aspettarsi

Dopo il cambio la scena appare più luminosa e più piatta nei mezzitoni, e i valori di luci e materiali tarati in precedenza andranno ritoccati. È normale. Ciò che guadagni è un'illuminazione che si somma correttamente, da cui dipende ogni capitolo da qui alla fine della sezione PBR.

## Wide color

Gli schermi Apple coprono il gamut Display P3, più ampio di sRGB. `MTKView` ha una proprietà `colorspace` (su iOS attraverso il suo layer) e formati dei pixel a gamma estesa come `.bgra10_xr_srgb` per disegnare colori fuori da sRGB. È un argomento avanzato e non serve per imparare, ma è utile sapere che esiste quando un designer chiede perché un rosso appare più spento nel tuo renderer che in Foto.
