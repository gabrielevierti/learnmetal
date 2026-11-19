# Un gioco 2D

Finora è stato tutto tecnica. Questo capitolo mette al lavoro una manciata di quelle tecniche in qualcosa di giocabile: un piccolo gioco in cui si rompono mattoni. Una racchetta, una palla, un muro di mattoni. È minuscolo di proposito, così l'intera struttura sta in un capitolo e puoi vedere come si incontrano un renderer e la logica di gioco.

## Che cosa ci serve

- Uno **sprite renderer** che disegna molti rettangoli colorati e con texture in una sola draw call.
- Una **camera ortografica** in unità simili ai pixel.
- Un **game loop** con delta time e input.
- Il **rilevamento delle collisioni** tra un cerchio e dei rettangoli.

## Lo sprite renderer

Uno sprite è un rettangolo con una posizione, una dimensione, un colore e una regione di texture. Usiamo l'[instancing](../advanced-metal/instancing.html): un rettangolo unitario generato nella vertex function e un'istanza per sprite.

{{code}}

Dal lato Swift il renderer raccoglie gli sprite durante il frame e li disegna tutti insieme:

{{code}}

Usa una pipeline con alpha blending. Metti tutte le immagini del gioco in un'unica texture, un **atlas**, e scegli le regioni con `uvRect`, così l'intero gioco è una sola draw call. Per i rettangoli a tinta unita collega una texture bianca da 1 × 1.

## Il campo di gioco

Dai al gioco una dimensione logica fissa, indipendente dalla finestra, con l'origine in alto a sinistra e y verso il basso, cosa comoda in 2D:

{{code}}

Scambiare `bottom` e `top` ribalta l'asse y.

## Gli oggetti di gioco

{{code}}

Un livello è soltanto dati. Caricare i livelli da un file di testo in cui ogni cifra è un tipo di mattone è un'estensione facile.

## Update

{{code}}

Dirigere la palla in base a dove tocca la racchetta è ciò che rende il gioco controllabile. Una riflessione puramente fisica risulterebbe senza vita.

## Cerchio contro rettangolo

Trova il punto del rettangolo più vicino al centro del cerchio con un clamp. Se quel punto dista meno di un raggio, i due si sovrappongono. La direzione dal punto più vicino al centro ci dice quale lato è stato colpito:

{{code}}

Ad alta velocità una palla può attraversare un mattone sottile tra un frame e l'altro. Eseguire l'aggiornamento in più piccoli sotto-passi per frame è la protezione più semplice.

## Render

{{code}}

Il renderer non sa niente delle regole, e il gioco non sa niente di Metal. Mantenere questa separazione è l'abitudine più preziosa di questo capitolo.

## Renderlo piacevole

Il gioco funziona. Ciò che lo rende divertente è la rifinitura, e ogni voce qui sotto riusa una tecnica di questa serie:

- **Particelle**: una scia con blending additivo dietro la palla, disegnata con lo stesso gruppo di sprite.
- **Scosse dello schermo e lampi**: disegna il gioco in una texture e deformala in un [pass di post-processing](../advanced-metal/render-targets.html) per qualche frame dopo un colpo.
- **Bagliore**: il [bloom](../advanced-lighting/bloom.html) sui mattoni luminosi.
- **Punteggio e vite**: il testo con atlas di [Rendering del testo](text-rendering.html).
- **Power-up**: sprite che cadono dai mattoni distrutti e, se presi, cambiano la dimensione della racchetta o la velocità della palla.
- **Suono**: `AVAudioEngine` o `AVAudioPlayer` per gli effetti dei colpi.

## Come proseguire

Aggiungi una macchina a stati per menu, partita, vittoria e sconfitta. Aggiungi dei livelli. Poi prova un gioco diverso con lo stesso gruppo di sprite: il renderer che hai scritto qui basta per moltissimi giochi 2D.
