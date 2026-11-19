# Engine: il gioco

Il [renderer](engine-renderer.html) disegna qualunque cosa ci sia nella scena. Questo capitolo parla di ciò che le cose ce le mette e le fa muovere: entità, fisica, input, suono, un'interfaccia. L'esempio è **Marble**, il gioco che accompagna il LearnMetal Engine. Tutto quanto, livello compreso, sta in circa ottocento righe, e quasi ogni riga è una chiamata a qualcosa che questo capitolo spiega.

## Entità e componenti

Un'entità non è altro che un id. Tutto ciò che la rende una biglia, una lampada o un muro sta nei suoi **componenti**: semplici struct, conservate dalla scena. L'engine porta quelli per cui ha dei sistemi: `Transform`, `Camera`, `Light`, `MeshRenderer`, `RigidBody`, `Collider`, `ParticleEmitter`. Un gioco aggiunge i suoi, e non c'è bisogno di farli conoscere all'engine:

{{code}}

Non esiste una classe `Gem` con un metodo di disegno e uno di aggiornamento. Una gemma è un'entità a cui vengono dati cinque componenti, e ognuno fa sì che una parte diversa dell'engine si accorga di lei:

{{code}}

Il renderer vede una mesh e una luce. La fisica vede un trigger. Solo il gioco vede una `Gem`.

Il comportamento, quindi, è un ciclo su tutto ciò che ha i componenti giusti. Questo è l'intera animazione delle gemme:

{{code}}

Dentro la scena i componenti di uno stesso tipo stanno uno dietro l'altro in un unico array, quindi un ciclo come questo legge la memoria in ordine. Il componente `Lifetime` funziona allo stesso modo: un ciclo lo fa scendere e a zero distrugge l'entità. Distruggere dentro un ciclo è sempre sicuro, perché l'entità viene rimossa davvero solo alla fine del passo, come ha mostrato il [primo capitolo](game-engine.html).

<!-- swift -->
C'è un dettaglio di Swift che conta ovunque nel codice di gioco. I componenti sono valori. `scene[entity, RigidBody.self]` ti dà una copia, quindi o lo modifichi sul posto attraverso il subscript, come in `scene[cube, Transform.self]?.rotation = ...`, oppure ne prendi una copia, la modifichi e la salvi di nuovo. Dentro `each` i parametri della closure sono `inout`: ciò che cambi lì viene salvato.
<!-- /swift -->

<!-- cpp -->
C'è un dettaglio del C++ che conta ovunque nel codice di gioco. `scene.get<RigidBody>(entity)` restituisce un puntatore dentro la memoria della scena, oppure `nullptr`. Il puntatore resta valido finché non viene aggiunto o rimosso un componente dello stesso tipo, quindi usalo e lascialo andare; non tenerlo in una variabile membro.
<!-- /cpp -->

## Corpi, collider e trigger

Un `Collider` dà a un'entità una forma: una sfera, una scatola o una capsula. Da solo è un ostacolo statico, che è tutto ciò che serve a un pavimento o a un muro. Aggiungi un `RigidBody` e l'entità si muove. Il livello di Marble è fatto di scatole con collider; la rampa è semplicemente una scatola inclinata.

{{code}}

La fisica è del tipo che vuole la maggior parte dei giochi, a volte chiamata fisica arcade: gravità, rimbalzi, attrito, cose che si spingono a vicenda e si impilano. Lascia fuori di proposito le parti difficili. I corpi non ruotano quando vengono colpiti, non ci sono giunti, e un oggetto molto veloce può attraversarne uno sottile. Quando a un gioco servono queste cose, lo strumento giusto è una libreria di fisica dedicata.

La prima di queste mancanze stonerebbe su una biglia: una palla che scivola senza girare. Quindi la fa girare il gioco, esattamente dell'angolo di cui una palla di quella dimensione ruota percorrendo quella distanza:

{{code}}

Nessuno, guardando, può capire che la rotazione è decorazione. Gran parte della programmazione di giochi è questo: simulare ciò che conta e fingere il resto in modo convincente.

Un collider marcato come **trigger** non blocca niente. Riporta soltanto che cosa gli entra dentro. È così che il gioco sa che una gemma è stata toccata o che il traguardo è stato raggiunto:

{{code}}

Il secondo evento scatta quando due cose solide cominciano a toccarsi, e dice a che velocità si sono incontrate. Il gioco lo usa per una cosa sola: un tonfo il cui volume dipende da quanto forte è atterrata la biglia.

## Input: leggi una volta, usa dopo

Il gioco non chiede mai se il tasto W è premuto. Definisce una volta delle **azioni**, e da quel momento chiede di quelle:

{{code}}

Tastiera e gamepad alimentano la stessa azione, quindi supportarli entrambi non costa niente di più.

Il primo capitolo avvertiva che il passo fisso è il posto sbagliato per leggere l'input, perché gira zero, una o più volte per frame. Quindi `update` legge, e ricorda:

{{code}}

Un salto non viene ricordato come "sì" ma come "sì, per i prossimi 0.15 secondi". Premi il pulsante un attimo prima che la biglia atterri e salterà comunque all'atterraggio. I giocatori non se ne accorgono mai; si accorgono solo dei giochi che non lo fanno.

`fixedUpdate` trasforma poi in movimento ciò che è stato ricordato:

{{code}}

"Avanti" significa lontano dalla camera, così i comandi restano naturali mentre la camera orbita. In aria la biglia si può ancora dirigere, ma solo di poco. E guarda il ramo `isDemo`: l'autopilota produce le stesse due cose che produce un giocatore, una direzione e un salto. Poiché il gioco legge il suo input da due variabili e non dalla tastiera, sostituire il giocatore con un programma ha richiesto una manciata di righe.

## Una piattaforma che porta il suo passeggero

A metà percorso una piattaforma traghetta la biglia oltre un vuoto. È un corpo **cinematico**: si muove, ma niente può spingerlo.

{{code}}

Il modo che viene spontaneo per muoverla è scrivere una nuova posizione a ogni passo. La biglia non la seguirebbe: per la fisica la piattaforma si starebbe teletrasportando, e un corpo che si teletrasporta non ha una velocità da trasmettere attraverso l'attrito. Un corpo cinematico va mosso nel modo che la fisica capisce, con la sua velocità:

{{code}}

Calcola dove deve trovarsi la piattaforma tra un passo, e imposta la velocità che ce la porta in un passo esatto. La piattaforma segue con precisione il suo percorso, e la biglia che le sta sopra viene trasportata dall'attrito come qualsiasi oggetto appoggiato su uno in movimento.

## Suono senza file audio

Marble ha sei effetti sonori e nemmeno un file audio. Ognuno viene calcolato all'avvio del gioco a partire da una forma d'onda, da un'altezza che può scivolare e da una durata:

{{code}}

L'engine sa caricare anche i file audio. Ma per i suoni di un piccolo gioco basta una manciata di numeri, e così il repository resta libero da file con licenze poco chiare.

Riprodurre una clip significa consegnarla al **mixer**. Il sistema operativo chiede audio a piccoli blocchi, molte volte al secondo, su un thread tutto suo. Ogni volta il mixer scorre il suo elenco di suoni in riproduzione, legge il pezzo successivo di ogni clip, lo scala secondo volume e pan, e somma tutto. Un mixer software non è altro che questo.

La velocità a cui una clip viene letta è il suo **pitch**, e può cambiare mentre il suono viene riprodotto. Due effetti del gioco si basano su questo. Ogni gemma suona lo stesso rintocco un po' più acuto della precedente, così raccoglierle dà la sensazione di salire. E il rombo della biglia che rotola è un secondo di rumore, in loop, riprodotto a circa un decimo della sua velocità:

{{code}}

Il suono non parte e non si ferma mai. Viene riprodotto di continuo, ed è semplicemente muto quando la biglia sta ferma o vola.

## L'interfaccia

Il contatore, l'orologio e i messaggi sono disegnati con il **canvas** 2D dell'engine, nato dai capitoli [Rendering del testo](text-rendering.html) e [Un gioco 2D](2d-game.html). Lavora in immediate mode: non ci sono oggetti etichetta da creare e tenere aggiornati. A ogni frame `draw` dice che cosa deve esserci a schermo:

{{code}}

Le posizioni sono in punti a partire dall'angolo in alto a sinistra, e i colori sono i valori sRGB che mostra un selettore di colore. Il canvas trasforma le chiamate in triangoli, e il renderer li disegna a fine frame con il minor numero di draw call che le texture permettono.

Il testo viene da un atlas di font a distance field, ed è per questo che `size` può essere un numero qualsiasi. Quando una gemma viene raccolta, `collectPulse` salta a uno e si spegne, e il contatore si gonfia da 22 a 30 punti e torna indietro senza mai apparire sfocato.

## Un gioco che gioca da solo

Avvia il gioco con `--demo` e nessuno deve toccarlo. Un autopilota fa rotolare la biglia attraverso ogni gemma, aspetta il traghetto, ci sale, salta per prendere la gemma sopra di esso e finisce al traguardo.

È un elenco di waypoint e una sola regola di guida. La regola legge ciò che vedrebbe un giocatore, cioè dove sono la biglia e il traghetto, e restituisce ciò che un giocatore farebbe:

{{code}}

Una demo è piacevole da guardare, ma non è per questo che l'autopilota esiste. Insieme a un'altra opzione diventa un test dell'intero engine:

<!-- swift -->
{{code}}
<!-- /swift -->

<!-- cpp -->
{{code}}
<!-- /cpp -->

Con `--capture` l'engine non apre né una finestra né un dispositivo audio. Disegna in una texture, fa avanzare il tempo di un sessantesimo di secondo esatto per frame, qualunque sia stata la durata reale del frame, e dopo il numero di frame indicato salva l'ultimo come PNG. L'esecuzione è identica ogni volta. Il codice di uscita del programma dice poi se l'autopilota ce l'ha fatta:

{{code}}

Se la fisica lascia cadere la biglia attraverso il traghetto, se un trigger smette di scattare, se una piattaforma del livello viene spostata fuori portata, questo comando fallisce. Il workflow di CI del repository lo esegue a ogni push, per entrambi i linguaggi, e allega l'immagine.

## Test che non hanno bisogno di una GPU

La maggior parte di un engine non è grafica, e tutto ciò che non è grafica si può testare senza una GPU: la matematica, la scena, l'input, la generazione delle mesh, le collisioni e la fisica, l'adattamento delle cascate di ombre, il layout delle struct condivise, la sintesi dei suoni e il mixer. L'engine tiene queste parti libere da Metal proprio perché si possano testare.

{{code}}

<!-- swift -->
Eseguili con `swift test`.
<!-- /swift -->

<!-- cpp -->
Eseguili con `ctest --test-dir build -L unit`.
<!-- /cpp -->

Sono test come questo ad aver permesso di cambiare la fisica senza paura mentre il livello di Marble le veniva progettato intorno.

## Che cosa costruire dopo

Il modo migliore di capire un engine è fargli fare qualcosa che ancora non fa. Qualche idea, più o meno dalla più facile alla più difficile:

- **Un trampolino.** Un trigger che imposta la velocità verso l'alto della biglia. Tutto ciò che ti serve è in questo capitolo.
- **Un secondo livello.** `buildLevel` è un elenco di scatole; scrivine un altro e passaci quando viene raggiunto il traguardo.
- **Una lampada sul traghetto.** Fai di una luce puntiforme una figlia della piattaforma mobile, e guarda `Transform.parent` al lavoro.
- **Suoni nello spazio.** `engine.playSoundAt` prende una posizione e imposta volume e pan in base a dove si trova la camera. Usalo per il tonfo delle casse.
- **Ombre per uno spot.** Un'altra shadow map, con una proiezione prospettica, accanto alle cascate.
- **Un formato di file per i livelli.** Leggi le scatole da un file di testo, poi fai in modo che il gioco lo ricarichi quando cambia, come già fanno gli shader.

Ognuna di queste tocca una parte dell'engine e lascia stare il resto. È a questo, più che a qualsiasi singola tecnica, che serve la disposizione descritta in questi capitoli.

L'ultima idea dell'elenco è stata portata più in là di un file di testo: il [prossimo capitolo](engine-editor.html) parla dell'editor di scene dell'engine.
