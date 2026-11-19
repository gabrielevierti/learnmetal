# Camera

Una matrice view fissa mostra la scena da un punto solo. Una camera con cui volare dentro la scena è una matrice view ricostruita a ogni frame a partire da una posizione e da una direzione, entrambe guidate dall'input.

## La matrice look-at

Una camera è definita da dove si trova, da che cosa guarda e da qual è il suo alto. Da questi tre dati ricaviamo tre assi perpendicolari e costruiamo una matrice che porta il mondo nel sistema di riferimento della camera. Aggiungi a `Math.swift`:

{{code}}

La parte di rotazione allinea il mondo agli assi della camera, e l'ultima colonna porta la camera nell'origine. Provala facendo orbitare la camera intorno alla scena:

{{code}}

## Una camera libera

Per muoversi liberamente conserva una posizione e due angoli. Lo **yaw** gira a sinistra e a destra, il **pitch** guarda in alto e in basso.

{{code}}

`front` trasforma i due angoli in una direzione con un po' di trigonometria. Il pitch è limitato poco prima dei 90 gradi perché guardando dritto in alto `front` diventa parallelo al vettore up, e il prodotto vettoriale dentro `lookAt` si annulla.

## Delta time

I frame non durano tutti lo stesso tempo. Il movimento va moltiplicato per il tempo trascorso dall'ultimo frame, il **delta time**, altrimenti la velocità della camera dipenderebbe dal frame rate:

{{code}}

## Input

AppKit e UIKit consegnano l'input sotto forma di eventi, cosa scomoda per un game loop che vuole chiedere "W è premuto in questo momento?". Il framework **GameController** permette di interrogare tastiera e mouse sia su macOS sia su iPadOS:

{{code}}

Il movimento del mouse arriva attraverso un handler che riporta gli spostamenti. Registralo una volta sola, per esempio nell'`init` del renderer:

{{code}}

`deltaY` è positivo quando il mouse sale, quindi il pitch aumenta e la camera guarda in alto. Su macOS la finestra deve essere quella attiva perché l'interrogazione della tastiera funzioni; cliccala una volta dopo l'avvio. Lo stesso framework legge i controller di gioco attraverso `GCController`, che su iPhone è la scelta naturale.

<!-- cpp -->

!!! note "L'input in C++"
    La versione C++ usa GLFW, da cui arriva già la finestra, al posto del framework GameController. `glfwGetKey` interroga la tastiera, e le callback del cursore e dello scroll consegnano il movimento del mouse. GLFW riporta la posizione del cursore con y che cresce verso il basso, quindi la callback sottrae nell'ordine inverso per far aumentare il pitch quando il mouse sale.

<!-- /cpp -->

## Mettere tutto insieme

{{code}}

Lo zoom non è altro che un campo visivo più stretto. Ora puoi volare intorno ai dieci cubi del capitolo precedente.

## Esercizi

- Trasforma la camera libera in una camera in prima persona che non può lasciare il piano del terreno (tieni fisso `position.y`).
- Aggiungi Q ed E per salire e scendere in verticale.
- Tieni premuto Shift per triplicare la velocità di movimento.
