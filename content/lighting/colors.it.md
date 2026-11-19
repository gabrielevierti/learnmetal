# Colori

L'illuminazione è l'arte di calcolare di che colore deve apparire una superficie. Prima di qualsiasi vero calcolo di luce ci servono un modello del colore e una scena da illuminare.

## Il colore come numeri

Un colore è fatto di tre numeri: quanto rosso, quanto verde e quanto blu. Negli shader ogni canale è un float in cui 0 è niente e 1 è la piena intensità.

{{code}}

Il colore che vediamo su un oggetto è la parte della luce in arrivo che l'oggetto **riflette**. Un oggetto color corallo illuminato da luce bianca riflette tutto il rosso, metà del verde e circa un terzo del blu, e assorbe il resto. Nel codice la riflessione è una moltiplicazione componente per componente:

{{code}}

Con una luce verde lo stesso oggetto appare molto diverso:

{{code}}

Non c'è luce rossa o blu da riflettere, quindi resta solo un verde scuro. Quella singola moltiplicazione è il cuore di ogni modello di illuminazione di questa serie.

## Una scena da illuminare

Ci servono due cose: un oggetto, e qualcosa che mostri dov'è la luce. Sono entrambi cubi, disegnati con due pipeline state diversi.

La fragment function dell'oggetto moltiplica i due colori:

{{code}}

{{code}}

Il cubo della lampada non deve risentire affatto dell'illuminazione, quindi riceve una sua fragment function banale:

{{code}}

Crea un secondo pipeline state che usa la stessa vertex function e `fragment_light`:

{{code}}

Un descriptor è solo una ricetta. Puoi cambiare una proprietà e crearne un altro state.

## Disegnarli entrambi

{{code}}

Imposta il colore di sfondo della vista a qualcosa di scuro, per esempio (0.1, 0.1, 0.1), così la lampada risalta. Adesso hai un cubo corallo piatto e un piccolo cubo bianco. Quello corallo non ha ancora ombreggiatura, quindi le sue facce non si distinguono. Il prossimo capitolo lo sistema.

## Esercizi

- Cambia il colore della luce e prova a prevedere il colore dell'oggetto prima di eseguire.
- Anima il colore della luce con `sin(time)` su ogni canale, a velocità diverse.
