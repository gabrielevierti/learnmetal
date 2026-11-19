# Più luci

È raro che una scena abbia una luce sola. Questo capitolo mette insieme tutta la sezione sull'illuminazione: una luce direzionale, quattro luci puntiformi e una torcia, tutte in un'unica fragment function. Il trucco sta nell'organizzazione: una funzione per ogni tipo di luce, e i risultati sommati.

## Funzioni negli shader

MSL è C++, quindi le normali funzioni di supporto funzionano. Tutto ciò che non è marcato `vertex`, `fragment` o `kernel` è una funzione qualunque che puoi chiamare. Marca le funzioni di supporto come `static`, così restano private al file.

{{code}}

`calcSpotLight` è la funzione della luce puntiforme con l'intensità del cono del capitolo precedente moltiplicata nei termini diffuse e specular.

Raccogliere le proprietà della superficie in una struct `Surface` tiene corte le liste dei parametri e fa sì che le texture vengano lette una volta sola, e non una volta per luce.

## Array negli uniform

Un array di dimensione fissa dentro la struct degli uniform contiene le luci puntiformi:

{{code}}

{{code}}

## Il lato Swift

Swift non ha array C di dimensione fissa nelle struct, ma una **tupla** di elementi identici ha lo stesso layout in memoria:

{{code}}

Con numeri più grandi diventa scomodo. L'alternativa che scala è mettere le luci in un loro `MTLBuffer` e passare un puntatore più un conteggio:

{{code}}

{{code}}

Un buffer collegato a uno shader è soltanto memoria, e un parametro puntatore permette allo shader di indicizzarlo come un array di qualsiasi lunghezza. È molto più flessibile degli array di uniform delle API più vecchie, ed è la forma che useremo da adesso.

## Preparare la scena

Quattro luci puntiformi in posizioni diverse, ognuna disegnata come un piccolo cubo lampada con la pipeline senza illuminazione del capitolo [Colori](colors.html):

{{code}}

## Il costo di molte luci

Ogni fragment valuta ogni luce, quindi il costo è fragment × luci. Una manciata va bene. Centinaia no, e risolvere questo problema è lo scopo del [Deferred shading](../advanced-lighting/deferred-shading.html), più avanti.

## Esercizi

- Ricrea atmosfere diverse cambiando solo i colori delle luci e il colore di sfondo: un deserto a mezzogiorno, una fabbrica in penombra, un corridoio horror illuminato dalla sola torcia.
- Muovi le luci nel tempo riscrivendo a ogni frame il contenuto del buffer attraverso `lightBuffer.contents()`.
