# SSAO

Il nostro termine ambient è una costante, quindi angoli, pieghe e spazi tra gli oggetti sono luminosi quanto le superfici aperte. Nella realtà questi punti ricevono meno luce indiretta, perché la geometria vicina ne blocca una parte. L'effetto si chiama **ambient occlusion**, e aggiungerlo dà alla scena la profondità e il contatto che la luce ambient piatta non ha.

Calcolare la vera occlusione richiede di tracciare raggi contro la scena. La **screen-space ambient occlusion** (SSAO) la approssima usando solo ciò che è già a schermo: il depth buffer.

## Come funziona

Per ogni pixel prendi un certo numero di punti in un piccolo **emisfero** sopra la superficie, orientato lungo la normale. Per ogni punto controlla il G-buffer: c'è geometria davanti a quel punto? La frazione di punti bloccati è l'occlusione del pixel.

L'SSAO si inserisce in modo naturale dopo un pass di G-buffer. Ha bisogno di posizioni e normali in **spazio vista**, quindi o le salvi così o le trasformi in lettura. Lavorare in spazio vista riduce i confronti di profondità a un confronto tra z.

## Il kernel di campioni

Genera 64 punti casuali dentro un emisfero unitario rivolto lungo +z, in spazio tangente. Scalali in modo che ne cadano di più vicino all'origine, perché ciò che occlude da vicino conta di più:

{{code}}

Salva il kernel in un buffer per lo shader.

## Rotazione casuale

64 campioni per pixel sono già tanti, e non bastano ancora a evitare bande visibili. Ruotare il kernel in modo diverso in ogni pixel trasforma le bande in un rumore fine, che una sfocatura poi elimina. Una minuscola texture 4 × 4 di vettori casuali, ripetuta su tutto lo schermo, fornisce le rotazioni:

{{code}}

## Lo shader dell'SSAO

L'uscita è una texture a un solo canale (`.r8Unorm`) che contiene il fattore di occlusione.

{{code}}

Punti da notare:

- Nel nostro spazio vista destrorso la camera guarda lungo -z, quindi una z **più grande** è più vicina alla camera. Un campione è occluso quando la superficie della scena in quel pixel è più vicina del campione.
- Il `bias`, intorno a 0.025, impedisce a una superficie piatta di occludere sé stessa.
- Il **controllo sul raggio** impedisce a un oggetto lontano sullo sfondo di scurire il bordo di qualcosa che gli sta davanti.
- Leggere `pixel % 4` ripete la texture di rumore su tutto lo schermo senza un sampler.
- La proiezione verso le coordinate di texture ribalta y, come per le shadow map.

Un raggio di circa 0.5 unità di mondo è un buon punto di partenza.

## Sfocatura

Il risultato grezzo ha un motivo di rumore 4 × 4 ben visibile. Una sfocatura a scatola della stessa dimensione lo elimina esattamente:

{{code}}

## Applicarla

L'ambient occlusion riguarda **solo la luce ambient**. Nel lighting pass del deferred:

{{code}}

Moltiplicare per l'occlusione l'intero risultato illuminato è un errore comune. Scurisce le superfici illuminate direttamente, e l'effetto è sporco.

## Regolazione e costo

- Calcola l'SSAO a **metà risoluzione**. È informazione a bassa frequenza, e la sfocatura nasconde la differenza.
- Con una buona sfocatura bastano spesso da 16 a 32 campioni.
- Elevare il risultato a potenza (`pow(ao, 2.0)`) aumenta il contrasto.

L'SSAO conosce solo le superfici visibili, quindi l'occlusione può comparire o sparire quando gli oggetti entrano ed escono dallo schermo. Varianti come HBAO e GTAO migliorano l'accuratezza, e il [ray tracing](../beyond/ray-tracing.html) calcola la vera ambient occlusion sull'hardware che lo supporta.

## Esercizi

- Manda a schermo l'occlusione grezza e quella sfocata.
- Varia il raggio e il numero di campioni e trova l'impostazione più economica che renda ancora bene.
