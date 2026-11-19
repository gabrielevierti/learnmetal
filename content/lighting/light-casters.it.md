# Tipi di luce

Finora la luce è stata un punto solo, che illumina in ogni direzione allo stesso modo e senza limiti. Nelle scene reali le sorgenti di luce più comuni sono di tre tipi: luci direzionali, luci puntiformi e spot.

## Luce direzionale

Una luce lontanissima, come il sole, ha raggi che di fatto sono paralleli. La sua posizione è irrilevante; conta solo la sua **direzione**, che è la stessa per ogni fragment.

{{code}}

I calcoli della luce vogliono un vettore che va dal fragment *verso* la luce, quindi cambiale segno:

{{code}}

Tutto il resto rimane uguale. Con `direction = (-0.2, -1.0, -0.3)` tutti e dieci i cubi sono illuminati dall'alto con lo stesso angolo.

## Luce puntiforme

Una luce puntiforme ha una posizione e illumina in tutte le direzioni, ma si affievolisce con la distanza. Questo calo si chiama **attenuazione**. Una formula che rende bene e costa poco:

{{code}}

dove `d` è la distanza dalla luce. Il termine costante di solito vale 1, così il risultato non supera mai 1. I termini lineare e quadratico decidono quanto in fretta la luce si spegne.

| Portata | Costante | Lineare | Quadratico |
| --- | --- | --- | --- |
| 13 | 1.0 | 0.35 | 0.44 |
| 50 | 1.0 | 0.09 | 0.032 |
| 100 | 1.0 | 0.045 | 0.0075 |
| 325 | 1.0 | 0.014 | 0.0007 |

{{code}}

{{code}}

## Spot

Uno spot è una luce puntiforme che illumina solo dentro un cono. Ha bisogno di una posizione, di una direzione e di un angolo di **cutoff**. Per ogni fragment si confronta con il cutoff l'angolo tra la direzione dello spot e la direzione dalla luce al fragment.

Confrontare gli angoli richiederebbe un costoso arcocoseno, quindi confrontiamo i coseni. Passa da Swift il coseno del cutoff:

{{code}}

Un taglio netto dà un brutto cerchio dal bordo duro. Due coni, uno interno e uno esterno appena più grande, danno un bordo morbido: piena luminosità dentro il cono interno, nessuna fuori da quello esterno, e una sfumatura continua in mezzo.

{{code}}

{{code}}

`saturate(x)` limita il valore all'intervallo da 0 a 1. L'ambient non viene toccato, così la scena fuori dal cono non è buio pesto. Ricorda che un coseno *più grande* significa un angolo *più piccolo*, ed è per questo che il confronto sembra rovesciato.

## Una torcia

Una torcia è uno spot attaccato alla camera:

{{code}}

Aggiungi anche l'attenuazione e cammina tra i cubi al buio.

## Esercizi

- Dai alla luce direzionale un colore caldo e un angolo basso, per un tramonto.
- Sperimenta con i termini dell'attenuazione finché una luce puntiforme arriva esattamente ai cubi più vicini.
- Proietta una texture dallo spot, come un proiettore di diapositive: usa come coordinata di texture la posizione del fragment dentro il cono.
