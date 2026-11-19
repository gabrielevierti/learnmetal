# Shadow mapping

Le ombre ancorano gli oggetti al suolo e rivelano come le cose sono disposte nello spazio. La tecnica standard in tempo reale è lo **shadow mapping**, ed è fatta di pezzi che conosci già: un depth buffer e il rendering su texture.

## L'idea

Un punto è in ombra se tra lui e la luce c'è qualcosa. Metti una camera nella luce e disegna la **profondità** della scena in una texture. Quella texture, la **shadow map**, registra per ogni direzione fin dove la luce arriva prima di colpire qualcosa.

Quando calcoli un fragment nel pass principale, trasformalo nella vista della luce e confronta la sua profondità con la shadow map. Se il fragment è più lontano dalla luce del valore salvato, qualcosa di più vicino sta bloccando la luce.

## La texture della shadow map

{{code}}

Il pass **non ha alcun attachment di colore**. Questa volta la profondità va salvata, visto che leggerla è l'intero scopo.

## Le matrici della luce

Una luce direzionale ha raggi paralleli, quindi la sua proiezione è **ortografica**: una scatola senza prospettiva. Aggiungi a `Math.swift`:

{{code}}

{{code}}

La scatola deve contenere tutto ciò che proietta o riceve ombre nella zona che ti interessa. Tienila più stretta che puoi: la risoluzione della shadow map si distribuisce su tutta la scatola.

## Il pass di profondità

La pipeline di questo pass ha una vertex function, nessuna fragment function e nessun formato di colore:

{{code}}

{{code}}

Una vertex function può restituire un semplice `float4`; viene preso come posizione. A ogni frame disegna la scena con questa pipeline dentro `shadowPass` prima del pass principale, usando lo stesso command buffer.

## Usare la shadow map

Nel pass principale la vertex function produce anche la posizione nel clip space della luce:

{{code}}

La fragment function la converte in una coordinata di texture e in una profondità da confrontare:

{{code}}

- Dividere per w non serve con una proiezione ortografica, ma fa funzionare la funzione anche con le luci prospettiche.
- In NDC x e y vanno da -1 a 1 con y verso l'alto, e le coordinate di texture vanno da 0 a 1 con y verso il basso. Da qui la scala `(0.5, -0.5)`. La profondità è già nell'intervallo da 0 a 1 e non va convertita.
- Le texture di profondità hanno un loro tipo negli shader, `depth2d<float>`.

`sample_compare` confronta la profondità di riferimento con la texture e restituisce 1 se il test passa e 0 altrimenti. Il test si configura sul sampler:

{{code}}

Con `.lessEqual` il risultato è 1 dove il fragment sta alla profondità salvata o davanti a essa, cioè dove è illuminato. Applicalo ai termini diffuse e specular e lascia stare l'ambient:

{{code}}

## Shadow acne

Il primo risultato è coperto di strisce scure. La shadow map ha una risoluzione limitata, quindi molti fragment condividono un texel, e su una superficie inclinata metà di loro risulta appena dietro la profondità salvata. È la **shadow acne**.

La cura è un **depth bias**: spingere la profondità salvata un po' più lontano dalla luce. Metal lo applica durante la rasterizzazione del pass delle ombre:

{{code}}

La parte costante si misura in unità che dipendono dal formato della profondità, quindi considera questi numeri un punto di partenza. La parte proporzionale alla pendenza aumenta da sola il bias sulle superfici molto inclinate rispetto alla luce, che sono quelle che ne hanno più bisogno. Troppo bias stacca l'ombra da chi la proietta, un artefatto noto come **peter panning**. Regola finché spariscono entrambi. Per le mesh chiuse aiuta anche disegnare nella shadow map solo le facce posteriori (`setCullMode(.front)`).

## Bordi più morbidi

Poiché il sampler di confronto usa il filtro lineare, la GPU confronta i quattro texel più vicini e mescola i *risultati*. È il **percentage-closer filtering** (PCF) fatto dall'hardware, e ammorbidisce i bordi gratis. Fare la media di qualche lettura in più li ammorbidisce ancora:

{{code}}

## Fuori dalla mappa

I fragment fuori dalla scatola della luce leggono oltre la texture. Con `.clampToEdge` ripetono il texel del bordo, e questo può spalmare ombre su tutta la scena. Restituisci "illuminato" quando `uv` è fuori dall'intervallo da 0 a 1, oppure usa `.clampToBorderColor` con un bordo bianco opaco dove è supportato.

## Oltre una sola mappa

Una mappa sola non può coprire con risoluzione sufficiente una grande scena all'aperto. Le **cascaded shadow map** dividono il frustum della vista in più intervalli, ognuno con la sua mappa, salvate negli strati di una texture `depth2d_array`. Per gli spot usa una proiezione prospettica per la luce e lo stesso codice.

## Esercizi

- Mostra la shadow map su un triangolo a tutto schermo per controllare che cosa vede la luce.
- Imposta il bias a zero, poi a un valore grande, e riconosci l'acne e il peter panning.
- Muovi la luce nel tempo e guarda le ombre seguirla.
