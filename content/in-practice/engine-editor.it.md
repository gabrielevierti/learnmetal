# Engine: l'editor

I [capitoli precedenti](game-engine.html) hanno costruito il livello di Marble nel codice: una funzione con una riga per scatola. Va bene per un piccolo livello ed è una pena per dieci. Questo capitolo aggiunge ciò che prima o poi cresce in ogni engine: un **editor**, un programma in cui le scene si compongono guardandole.

L'editor non è una tecnologia a parte. È un gioco fatto con l'engine, di circa milleduecento righe, il cui gameplay è per caso modificare scene. Lo rendono possibile tre nuovi pezzi dell'engine, e i giochi li possono usare tutti e tre: un'interfaccia utente, i file di scena e un modo di guardare una scena senza farne parte.

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
{{code}}
<!-- /cpp -->

Tieni premuto il tasto destro del mouse e usa W A S D per volare. Clicca per selezionare, premi W, E o R e trascina una maniglia colorata per spostare, ruotare o scalare. Trascina un numero di lato per cambiarlo, oppure cliccalo e scrivi. F5 avvia la scena.

## Un'interfaccia in immediate mode

Un editor è fatto soprattutto di pannelli pieni di numeri. Il modo consueto di costruirli è un albero di oggetti widget che vanno tenuti allineati ai dati che mostrano. L'engine prende l'altra strada, quella resa popolare da Dear ImGui: l'**immediate mode**. Non ci sono oggetti widget. A ogni frame il programma chiama una funzione per controllo, e quella chiamata sia disegna il controllo sia riporta che cosa ne ha fatto l'utente.

Questa è l'intera sezione dell'inspector per una luce:

{{code}}

Leggila come una descrizione del pannello, dall'alto in basso. Un `if` intorno a una chiamata è il modo in cui un controllo compare solo quando ha senso: una portata per le luci puntiformi e gli spot, gli angoli del cono per i soli spot. Nessun codice nasconde o mostra qualcosa; le righe che non vengono chiamate in questo frame semplicemente non ci sono.

Un controllo è piccolo. Questa è una checkbox, completa:

{{code}}

Chiede la prossima riga del pannello, controlla se il mouse è stato premuto sul suo quadrato, in quel caso inverte il valore, e si disegna con il [canvas](engine-gameplay.html) dell'engine. Il valore vive nei dati di chi chiama e da nessun'altra parte, quindi non c'è niente da sincronizzare.

Il poco che deve sopravvivere da un frame al successivo lo conserva la `Gui`, sotto un id calcolato dal titolo del pannello e dall'etichetta del controllo: quale controllo il mouse sta tenendo, quale campo ha la tastiera, di quanto è scorso ogni pannello. Trascinare un numero significa che il controllo ricorda di essere "attivo" finché il pulsante non viene rilasciato, e che somma al valore il movimento del puntatore in ogni frame nel frattempo.

Due dettagli vale la pena conoscerli prima di scrivere i tuoi controlli. Le righe scorse del tutto fuori da un pannello vengono saltate: non disegnano niente e non reagiscono a niente; una riga che è fuori per metà viene tagliata sul bordo del pannello, perché al canvas si può dire di ritagliare e il renderer lo traduce in uno scissor rectangle. E un elenco a comparsa viene disegnato proprio alla fine del frame, così finisce sopra a tutto; la sua scelta arriva al controllo che l'ha aperto un frame dopo.

Nell'interfaccia niente è un'immagine. Un campo arrotondato è un poligono; un'icona è fatta di poche linee e archi dati allo stesso canvas, quindi è nitida a qualsiasi dimensione. I bordi sono lisci senza multisampling: ogni forma riceve un bordo largo un pixel che sfuma nel trasparente, fatto di normali triangoli con i vertici esterni ad alpha zero.

## Le scene come testo

Ciò che l'editor salva è un file di testo con un'istruzione per riga:

{{code}}

Prima vengono i materiali, poi le entità, ognuna seguita da una riga per componente. Una riga di mesh nomina la mesh e dà la posizione del suo materiale nel file; texture e modelli vengono salvati per nome, mai come dati. Le righe che un lettore non riconosce vengono saltate, quindi una build più vecchia può aprire un file più recente.

Il testo è stato preferito a un formato binario per una ragione: le scene le terrai in git. Una riga per componente significa che spostare una cassa cambia una riga, e il diff dice esattamente questo. Perché sia vero, i numeri vengono scritti nella forma più corta che, riletta, dà lo stesso identico float (`0.22`, non `0.2199999988`), e aprire una scena e salvarla di nuovo non cambia nulla nel file.

Un gioco carica una scena con una sola chiamata:

{{code}}

Ciò che un file di scena contiene sono entità e i componenti propri dell'engine. La logica di gioco resta nel codice: le gemme di Marble e il suo traghetto non sono cose che l'editor conosce. Di solito un gioco carica una scena e poi trova per nome le entità che gli interessano.

## Guardare senza esserci

Il renderer disegna dalla prima camera attiva che trova, e una scena in fase di modifica di solito ne ha già una: quella del gioco. All'editor serve una vista sua, che non la disturbi e che non finisca mai nel file salvato.

{{code}}

La camera è una normale entità, perché il renderer sa guardare solo attraverso entità. La distinguono due cose. `EditorOnly` è un componente vuoto che chi scrive la scena controlla: le entità che lo portano restano fuori dal file. E `cameraOverride` dice al renderer di guardare attraverso questa entità qualunque cosa dicano le camere della scena.

Lo stesso trucco tiene la fisica fuori dai piedi. `engine.isSimulationPaused` fa saltare all'engine i passi di fisica, così una cassa messa a mezz'aria resta lì finché non premi Play.

## La selezione e il gizmo

Cliccare su qualcosa è il [raggio dalla camera](game-engine.html) che l'engine fornisce già, controllato contro ogni entità:

{{code}}

Il controllo si fa contro il bounding box della mesh, che è una scatola allineata agli assi propri della mesh. Invece di ruotare la scatola nel mondo, il raggio viene portato nello spazio della mesh con l'inversa della matrice di mondo, dove il controllo è quello semplice. Luci e camere non hanno mesh, quindi si selezionano come piccole sfere e si disegnano come piccoli dischi.

Le maniglie di un'entità selezionata sono linee 2D: ogni asse viene proiettato sullo schermo e disegnato con il canvas, e questo le tiene della stessa dimensione per quanto lontana sia l'entità. Trascinarne una misura quanto il puntatore si è spostato *lungo quella linea sullo schermo*, e lo trasforma in una modifica della trasformazione:

{{code}}

Per uno spostamento, il percorso in punti viene diviso per il numero di punti che un metro di quell'asse copre sullo schermo, così l'entità resta sotto il puntatore. Rotazione e scala usano lo stesso percorso come angolo e come fattore.

## L'undo gratis

Di solito l'undo è la funzione che impone un'architettura a un editor: ogni operazione diventa un oggetto comando che sa come annullarsi. Avere i file di scena offre un modo molto più economico. Dopo ogni modifica conclusa scrivi la scena come testo, e se è diversa dall'ultima volta tieni il vecchio testo:

{{code}}

L'undo è allora "rileggi il testo precedente". Per una scena di queste dimensioni costa qualche kilobyte a passo, e non può andare fuori sincrono con l'editor, perché non c'è codice per singola operazione che si possa dimenticare. Il controllo sull'interfaccia occupata o su una maniglia tenuta è ciò che fa di un intero trascinamento un passo solo invece di sessanta.

Play è la stessa idea usata una volta:

{{code}}

Premi Play e la scena viene salvata in una stringa, la fisica viene accesa e subentra la camera propria della scena. Premi Stop e la stringa viene riletta: ogni cassa torna dov'era.

## Che cosa non fa

L'editor seleziona una cosa alla volta, non ha drag and drop e usa Ctrl dove un utente Mac si aspetta Command. Modifica solo i componenti dell'engine; non c'è scripting.

È anche il miglior argomento a favore del modo in cui l'engine è costruito. All'editor non è servito quasi niente di nuovo dal renderer, dalla scena o dalla fisica: due flag e un nome su ogni asset. Tutto il resto c'era già, perché era servito prima a un gioco.
