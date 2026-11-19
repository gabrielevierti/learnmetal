# Debug

I bug grafici sono diversi dai bug normali. Per uno schermo nero non c'è uno stack trace, e da una fragment function non puoi stampare. La buona notizia è che gli strumenti di Metal sono tra i migliori di qualsiasi API grafica, e stanno tutti dentro Xcode. Imparare presto a usarli ti farà risparmiare giorni.

## Livello 1: la validazione dell'API

La **Metal API Validation** controlla ogni chiamata che fai: formati dei pixel che non coincidono, buffer mancanti, load action sbagliate, encoder lasciati aperti. Quando qualcosa non va, l'app si ferma sulla chiamata incriminata con un messaggio che di solito nomina l'esatta proprietà:

{{code}}

È attiva in modo predefinito quando esegui da Xcode (**Edit Scheme → Run → Diagnostics**). Non spegnerla mai durante lo sviluppo. Nelle build di release viene disattivata in automatico, quindi ai tuoi utenti non costa nulla.

## Livello 2: la validazione degli shader

Nello stesso pannello dello scheme, **Shader Validation** strumenta i tuoi shader per intercettare ciò che la validazione dell'API non può vedere: leggere oltre la fine di un buffer, leggere una texture mai collegata, accedere a un array fuori dai limiti. Gli accessi sbagliati vengono riportati in console con il nome della funzione e la riga. Rallenta il rendering, quindi attivala quando uno shader si comporta in modo strano.

## Dai un'etichetta a tutto

Ogni oggetto Metal ha una proprietà `label`. Le etichette compaiono nei messaggi di validazione, nel debugger e in Instruments. Un messaggio che parla di "Scene HDR Color" è molto più utile di uno che parla di `<AGXG14GFamilyTexture: 0x12f80a400>`.

{{code}}

Dentro un encoder raggruppa i comandi collegati, così nel debugger compaiono come un albero richiudibile:

{{code}}

## Il GPU frame debugger

Mentre l'app è in esecuzione, clicca l'icona della **fotocamera** (Capture GPU Workload) nella barra di debug di Xcode. Xcode congela un frame e te lo fa smontare:

- **Il navigator** elenca ogni command buffer, pass e draw call, organizzati secondo i tuoi gruppi di debug. Scorri le draw call e guarda il frame costruirsi una chiamata alla volta.
- **Attachments** mostra le texture di colore, profondità e stencil così come sono dopo la draw call selezionata. La geometria della draw call corrente è evidenziata con un contorno.
- **Bound resources** mostra ogni buffer, texture e sampler collegato per la draw call selezionata. Puoi aprire un buffer e vederne i byte disposti secondo la tua struct. È il modo più rapido di trovare una discordanza nel layout degli uniform.
- **Geometry viewer** mostra la mesh dopo la vertex function, in clip space, con gli output di ogni vertice. Quando manca un oggetto guarda prima qui: vedrai subito se è dietro la camera, ritagliato o collassato in un punto.
- **Shader debugger**: seleziona un pixel, clicca **Debug** e segui passo passo l'esecuzione della fragment function per quel preciso pixel, con il valore di ogni variabile a ogni riga. Lo stesso vale per un vertice. È la cosa più vicina a un breakpoint dentro uno shader.
- **Shader editing**: cambia il codice dello shader nel debugger e ricaricalo per vedere l'effetto sul frame catturato senza ricompilare l'app.
- **Dependency viewer** disegna un grafo di tutti i pass e delle texture che scorrono tra loro, con le load e store action. Rende evidenti i pass ridondanti e i salvataggi inutili.
- **Prestazioni e memoria**: il tempo di GPU per pass e per draw call, e un elenco di ogni risorsa con la sua dimensione.

Puoi catturare anche dal codice, per prendere un frame preciso:

{{code}}

La cattura da codice richiede la chiave `MetalCaptureEnabled` impostata a `YES` in Info.plist.

## L'HUD delle prestazioni

Metal può sovrapporre a qualsiasi app Metal un grafico in tempo reale di frame rate, tempo di frame, tempo di GPU e memoria. Attivalo nelle opzioni dello scheme (**Show Graphics HUD**) o con la variabile d'ambiente `MTL_HUD_ENABLED=1`. Tienilo acceso mentre lavori, così un rallentamento improvviso lo noti nel momento in cui viene introdotto.

## Il debug con i colori

La tecnica più vecchia funziona ancora. Quando hai un dubbio su un valore, mandalo in uscita come colore:

{{code}}

Riporta prima nell'intervallo da 0 a 1 i valori che ne escono, altrimenti vedi solo bianco e nero. Il magenta è per tradizione il colore del "questo non dovrebbe mai succedere": `return float4(1, 0, 1, 1);` dentro un ramo ti dice all'istante se viene eseguito.

## Errori dei command buffer

Un command buffer può fallire sulla GPU, per esempio perché finisce la memoria o scade il tempo. Controllalo nel completion handler:

{{code}}

Per avere più dettagli crea il buffer con `MTLCommandBufferDescriptor` ed `errorOptions = .encoderExecutionStatus`. L'errore riporta allora quale encoder, per etichetta, era in esecuzione quando è avvenuto il guasto.

## Instruments

Per le domande sulle prestazioni che riguardano molti frame, come scatti, sincronizzazione tra CPU e GPU e intoppi dovuti alla compilazione degli shader, usa in Instruments i template **Metal System Trace** e **Game Performance**. Mostrano su un'unica linea del tempo la codifica sulla CPU, l'esecuzione sulla GPU e la presentazione a schermo di ogni frame.

## Una checklist per "non viene disegnato niente"

1. C'è un messaggio di validazione in console? Leggilo.
2. Cattura un frame. La draw call c'è? Se no, il tuo codice non l'ha mai emessa.
3. Apri il geometry viewer. I vertici sono dentro il volume di clip?
4. Controlla l'attachment di profondità e la compare function. Sta fallendo tutto il test di profondità?
5. Controlla culling e winding. Prova `setCullMode(.none)`.
6. Guarda i buffer collegati. Le matrici sono sensate o il layout è sfasato?
7. Restituisci un colore pieno dalla fragment function. Se compare, il problema è nello shading.
8. L'alpha è zero con il blending attivo?

Procedi dall'esterno verso l'interno e di solito la causa si trova in pochi minuti.
